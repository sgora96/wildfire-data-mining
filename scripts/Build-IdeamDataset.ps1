<#
.SYNOPSIS
    Extrae y consolida la base de datos nacional de incendios de la cobertura
    vegetal del IDEAM (archivos bd_icv_nacional_*.xlsx) sin depender de Python.

.DESCRIPTION
    Los .xlsx son en realidad archivos ZIP con XML adentro. Este script:
      1. Lee xl/sharedStrings.xml de cada libro para resolver los textos.
      2. Recorre cada hoja de datos (una por año) fila a fila y celda a celda.
      3. Escribe un CSV crudo por hoja en data/raw/.
      4. Consolida todas las hojas en un unico dataset nacional
         (data/processed/incendios_ideam_2010_2024.csv).
      5. Genera el subconjunto regional de Cundinamarca
         (data/processed/incendios_ideam_cundinamarca_2010_2024.csv).
      6. Calcula un diagnostico inicial de calidad (nulos, duplicados,
         cobertura) en data/processed/calidad_resumen.json.

.NOTES
    Se ejecuta una sola vez para poblar el dataset base del entregable R1.
    Los .xlsx originales NO se versionan en git (quedan en la raiz del repo
    de datos); solo los CSV derivados en data/raw y data/processed.
#>

param(
    [string]$SourceDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

Add-Type -AssemblyName System.IO.Compression.FileSystem

$File2010 = Join-Path $SourceDir "bd_icv_nacional_2010_2020.xlsx"
$File2021 = Join-Path $SourceDir "bd_icv_nacional_2021_2023_2024_0.xlsx"
$RawDir = Join-Path $ProjectDir "data\raw"
$ProcessedDir = Join-Path $ProjectDir "data\processed"

New-Item -ItemType Directory -Force -Path $RawDir | Out-Null
New-Item -ItemType Directory -Force -Path $ProcessedDir | Out-Null

if (-not (Test-Path $File2010)) { throw "No se encontro $File2010" }
if (-not (Test-Path $File2021)) { throw "No se encontro $File2021" }

# --------------------------------------------------------------------------
# Esquema canonico: columnas B..AI del formato oficial IDEAM (35 campos,
# la columna A no se usa). "FECHA_REGISTRO" corresponde al campo que el
# IDEAM etiqueta "DIA" pero que en realidad guarda la fecha completa
# (serial de Excel) -> se documenta como hallazgo de calidad.
# --------------------------------------------------------------------------
$ColumnMap = [ordered]@{
    B  = "ANIO"
    C  = "MES"
    D  = "FECHA_REGISTRO"
    E  = "DEPARTAMENTO"
    F  = "MUNICIPIO"
    G  = "VEREDA_CORREGIMIENTO"
    H  = "PREDIO_BARRIO"
    I  = "AREA_PROTEGIDA_NACIONAL"
    J  = "LATITUD"
    K  = "LONGITUD"
    L  = "ELEVACION_MSNM"
    M  = "AREA_COPA_HA"
    N  = "AREA_SUPERFICIAL_HA"
    O  = "AREA_SUBTERRANEO_HA"
    P  = "AREA_MIXTO_HA"
    Q  = "AREA_OTRO_TIPO_HA"
    R  = "CAUSA_QUEMA_FUERA_CONTROL"
    S  = "CAUSA_DESCUIDO_NEGLIGENCIA"
    T  = "CAUSA_INTENCIONAL"
    U  = "CAUSA_ACCIDENTAL"
    V  = "CAUSA_REACTIVACION_FOCOS"
    W  = "CAUSA_OTRA"
    X  = "COB_BOSQUE_NATURAL_DENSO"
    Y  = "COB_BOSQUE_INTERVENIDO"
    Z  = "COB_BOSQUE_PLANTADO"
    AA = "COB_BOSQUE_SECO"
    AB = "COB_CULTIVOS"
    AC = "COB_PARAMOS"
    AD = "COB_SABANAS_PASTIZALES"
    AE = "COB_PASTOS_MANEJADOS"
    AF = "COB_RASTROJO"
    AG = "COB_VEGETACION_SECA"
    AH = "COB_COBERTURA_SIN_DETERMINAR"
    AI = "AREA_TOTAL_HA"
}

# La hoja BD_ICV_2024 usa una plantilla distinta: AÑO se corre a la columna A
# y aparece un campo nuevo "ENTIDAD REPORTA" en B; de C en adelante coincide
# exactamente con las demas hojas. Se documenta como inconsistencia de
# formato entre fuentes/anios en el diagnostico de calidad.
$ColumnMap2024 = [ordered]@{ A = "ANIO"; B = "ENTIDAD_REPORTA" }
foreach ($k in $ColumnMap.Keys) {
    if ($k -eq "B") { continue }  # B ya esta re-mapeada arriba para 2024
    $ColumnMap2024[$k] = $ColumnMap[$k]
}

$OutputColumns = @($ColumnMap.Values) + @("ENTIDAD_REPORTA", "FUENTE_HOJA")

function Get-SharedStrings {
    param([System.IO.Compression.ZipArchive]$Zip)
    $entry = $Zip.GetEntry("xl/sharedStrings.xml")
    if (-not $entry) { return @() }
    $reader = New-Object System.IO.StreamReader($entry.Open())
    $xmlText = $reader.ReadToEnd()
    $reader.Close()
    [xml]$xml = $xmlText
    $siNodes = $xml.sst.si
    $result = New-Object System.Collections.Generic.List[string]
    foreach ($node in $siNodes) {
        if ($node.t -and $node.t -is [string]) {
            $result.Add($node.t) | Out-Null
        }
        elseif ($node.t) {
            $result.Add($node.t.InnerText) | Out-Null
        }
        elseif ($node.r) {
            $joined = ($node.r | ForEach-Object { $_.t.InnerText }) -join ""
            $result.Add($joined) | Out-Null
        }
        else {
            $result.Add($node.InnerText) | Out-Null
        }
    }
    return $result
}

function ConvertFrom-ExcelSerialDate {
    param([double]$Serial)
    # Epoca de Excel: 1899-12-30 (compensa el bug del "ano bisiesto 1900").
    $epoch = Get-Date -Year 1899 -Month 12 -Day 30 -Hour 0 -Minute 0 -Second 0
    return $epoch.AddDays($Serial).ToString("yyyy-MM-dd")
}

$cellRegex = [regex]'<c r="(?<ref>[A-Z]{1,3})\d+"(?<attrs>[^>]*?)(?:/>|>(?<inner>.*?)</c>)'
$rowRegex = [regex]'<row r="(?<num>\d+)"[^>]*>(?<content>.*?)</row>'
$vRegex = [regex]'<v>(?<val>[^<]*)</v>'

function Read-SheetRows {
    param(
        [System.IO.Compression.ZipArchive]$Zip,
        [string]$SheetPath,
        [System.Collections.Generic.List[string]]$SharedStrings,
        [int]$DataStartRow,
        [int]$DataEndRow,
        [string]$FuenteHoja,
        [System.Collections.Specialized.OrderedDictionary]$Map = $ColumnMap
    )

    $entry = $Zip.GetEntry($SheetPath)
    if (-not $entry) { throw "No existe la hoja $SheetPath" }
    $reader = New-Object System.IO.StreamReader($entry.Open())
    $xmlText = $reader.ReadToEnd()
    $reader.Close()

    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($rowMatch in $rowRegex.Matches($xmlText)) {
        $rowNum = [int]$rowMatch.Groups["num"].Value
        if ($rowNum -lt $DataStartRow -or $rowNum -gt $DataEndRow) { continue }

        $record = [ordered]@{}
        foreach ($name in $OutputColumns) { if ($name -ne "FUENTE_HOJA") { $record[$name] = "" } }

        $content = $rowMatch.Groups["content"].Value
        foreach ($cellMatch in $cellRegex.Matches($content)) {
            $ref = $cellMatch.Groups["ref"].Value
            if (-not $Map.Contains($ref)) { continue }
            $colName = $Map[$ref]

            $attrs = $cellMatch.Groups["attrs"].Value
            $inner = $cellMatch.Groups["inner"].Value
            if ([string]::IsNullOrEmpty($inner)) { continue }

            $vMatch = $vRegex.Match($inner)
            if (-not $vMatch.Success) { continue }
            $raw = [System.Net.WebUtility]::HtmlDecode($vMatch.Groups["val"].Value)

            if ($attrs -match 't="s"') {
                $sIdx = [int]$raw
                $value = if ($sIdx -ge 0 -and $sIdx -lt $SharedStrings.Count) { $SharedStrings[$sIdx] } else { "" }
            }
            elseif ($colName -eq "FECHA_REGISTRO") {
                $num = 0.0
                if ([double]::TryParse($raw, [ref]$num)) {
                    $value = ConvertFrom-ExcelSerialDate -Serial $num
                }
                else { $value = $raw }
            }
            else {
                $value = $raw
            }

            $record[$colName] = ($value -replace "`r`n", " " -replace "`n", " ").Trim()
        }

        $record["FUENTE_HOJA"] = $FuenteHoja
        $rows.Add([pscustomobject]$record) | Out-Null
    }
    return $rows
}

Write-Host "Leyendo $File2010 ..." -ForegroundColor Cyan
$zip1 = [System.IO.Compression.ZipFile]::OpenRead($File2010)
$ss1 = Get-SharedStrings -Zip $zip1
$rows2010_2020 = Read-SheetRows -Zip $zip1 -SheetPath "xl/worksheets/sheet2.xml" -SharedStrings $ss1 -DataStartRow 8 -DataEndRow 23164 -FuenteHoja "BD_ICV_2010_2020"
$zip1.Dispose()
Write-Host ("  -> {0} registros" -f $rows2010_2020.Count)
$rows2010_2020 | Select-Object $OutputColumns | Export-Csv -Path (Join-Path $RawDir "ideam_incendios_2010_2020.csv") -NoTypeInformation -Encoding UTF8

Write-Host "Leyendo $File2021 ..." -ForegroundColor Cyan
$zip2 = [System.IO.Compression.ZipFile]::OpenRead($File2021)
$ss2 = Get-SharedStrings -Zip $zip2

$sheetsCfg = @(
    @{ Path = "xl/worksheets/sheet1.xml"; Start = 8;  End = 969;  Fuente = "BD_ICV_2021" },
    @{ Path = "xl/worksheets/sheet2.xml"; Start = 9;  End = 4952; Fuente = "BD_ICV_2022" },
    @{ Path = "xl/worksheets/sheet3.xml"; Start = 9;  End = 3086; Fuente = "BD_ICV_2023" },
    @{ Path = "xl/worksheets/sheet4.xml"; Start = 4;  End = 7892; Fuente = "BD_ICV_2024" }
)

$rowsRecientes = New-Object System.Collections.Generic.List[object]
foreach ($cfg in $sheetsCfg) {
    $mapToUse = if ($cfg.Fuente -eq "BD_ICV_2024") { $ColumnMap2024 } else { $ColumnMap }
    $chunk = Read-SheetRows -Zip $zip2 -SheetPath $cfg.Path -SharedStrings $ss2 -DataStartRow $cfg.Start -DataEndRow $cfg.End -FuenteHoja $cfg.Fuente -Map $mapToUse
    Write-Host ("  -> {0}: {1} registros" -f $cfg.Fuente, $chunk.Count)
    $chunk | Select-Object $OutputColumns | Export-Csv -Path (Join-Path $RawDir ("ideam_incendios_{0}.csv" -f ($cfg.Fuente -replace "BD_ICV_", ""))) -NoTypeInformation -Encoding UTF8
    foreach ($r in $chunk) { $rowsRecientes.Add($r) | Out-Null }
}
$zip2.Dispose()

# --------------------------------------------------------------------------
# Consolidacion nacional
# --------------------------------------------------------------------------
$all = New-Object System.Collections.Generic.List[object]
foreach ($r in $rows2010_2020) { $all.Add($r) | Out-Null }
foreach ($r in $rowsRecientes) { $all.Add($r) | Out-Null }

Write-Host ("Total consolidado nacional: {0} registros" -f $all.Count) -ForegroundColor Green

$nationalPath = Join-Path $ProcessedDir "incendios_ideam_2010_2024.csv"
$all | Select-Object $OutputColumns | Export-Csv -Path $nationalPath -NoTypeInformation -Encoding UTF8

# --------------------------------------------------------------------------
# Subconjunto regional: Cundinamarca
# --------------------------------------------------------------------------
$regional = $all | Where-Object { $_.DEPARTAMENTO -and $_.DEPARTAMENTO.Trim().ToUpperInvariant() -eq "CUNDINAMARCA" }
$regionalPath = Join-Path $ProcessedDir "incendios_ideam_cundinamarca_2010_2024.csv"
$regional | Select-Object $OutputColumns | Export-Csv -Path $regionalPath -NoTypeInformation -Encoding UTF8
Write-Host ("Subconjunto Cundinamarca: {0} registros" -f $regional.Count) -ForegroundColor Green

# --------------------------------------------------------------------------
# Diagnostico inicial de calidad
# --------------------------------------------------------------------------
$totalRows = $all.Count
$nullStats = [ordered]@{}
foreach ($col in $OutputColumns) {
    $empty = ($all | Where-Object { [string]::IsNullOrWhiteSpace($_.$col) }).Count
    $nullStats[$col] = [math]::Round(100.0 * $empty / [math]::Max($totalRows,1), 2)
}

$seen = @{}
$dupCount = 0
foreach ($r in $all) {
    $key = ($OutputColumns | ForEach-Object { $r.$_ }) -join "|"
    if ($seen.ContainsKey($key)) { $dupCount++ } else { $seen[$key] = $true }
}

$deptos = $all | Where-Object { $_.DEPARTAMENTO } | Select-Object -ExpandProperty DEPARTAMENTO -Unique
$anioValues = $all | Where-Object { $_.ANIO -match '^\d{4}$' } | ForEach-Object { [int]$_.ANIO }
$anioMin = if ($anioValues) { ($anioValues | Measure-Object -Minimum).Minimum } else { $null }
$anioMax = if ($anioValues) { ($anioValues | Measure-Object -Maximum).Maximum } else { $null }

$summary = [ordered]@{
    generado                     = (Get-Date).ToString("yyyy-MM-dd")
    total_registros              = $totalRows
    total_registros_regional     = $regional.Count
    registros_duplicados         = $dupCount
    departamentos_distintos      = $deptos.Count
    anio_min                     = $anioMin
    anio_max                     = $anioMax
    porcentaje_nulos_por_columna = $nullStats
    registros_por_hoja           = [ordered]@{
        "2010_2020" = $rows2010_2020.Count
        "2021"      = ($rowsRecientes | Where-Object { $_.FUENTE_HOJA -eq "BD_ICV_2021" }).Count
        "2022"      = ($rowsRecientes | Where-Object { $_.FUENTE_HOJA -eq "BD_ICV_2022" }).Count
        "2023"      = ($rowsRecientes | Where-Object { $_.FUENTE_HOJA -eq "BD_ICV_2023" }).Count
        "2024"      = ($rowsRecientes | Where-Object { $_.FUENTE_HOJA -eq "BD_ICV_2024" }).Count
    }
}

$summaryPath = Join-Path $ProcessedDir "calidad_resumen.json"
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryPath -Encoding UTF8

Write-Host "`nListo." -ForegroundColor Yellow
Write-Host "  data/raw/ideam_incendios_*.csv"
Write-Host "  data/processed/incendios_ideam_2010_2024.csv"
Write-Host "  data/processed/incendios_ideam_cundinamarca_2010_2024.csv"
Write-Host "  data/processed/calidad_resumen.json"
