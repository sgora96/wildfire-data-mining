# Modelo de datos base y medidas comunes (Power BI)

Archivo: `powerbi/Wildfire_ConocimientoEvidente.pbix`
Fuente: `data/processed/incendios_ideam_tratado_2010_2024.csv` (IDEAM, BD-ICV tratada en la Etapa 2; 35.355 eventos, 2010-2024).
Unidad de análisis: cada fila es un evento de incendio de cobertura vegetal reportado.

## 1. Consultas de Power Query

| Consulta | Se carga al modelo | Descripción |
|---|---|---|
| `RutaCSV` | No (parámetro) | Ruta local del CSV. Cada integrante la cambia en *Transformar datos > Administrar parámetros*. |
| `Eventos_base` | No | Lee el CSV (UTF-8, separador coma), promueve encabezados, convierte celdas vacías en nulo y agrega `ID_EVENTO` (índice desde 1). |
| `Eventos` | Sí | Tabla de hechos: 1 fila = 1 evento. |
| `Causas` | Sí | Evento ↔ tipo de causa afirmativa. |
| `Coberturas` | Sí | Evento ↔ tipo de cobertura con hectáreas > 0. |
| `Dim_Departamento` | Sí | Departamentos distintos de `Eventos`. |
| `Dim_Periodo` | Sí | Calendario año-mes 2010-2024. |
| `_Medidas` | Sí | Tabla vacía que solo contiene las medidas DAX. |

### Tabla `Eventos`

- Columnas conservadas: `ID_EVENTO`, `ANIO`, `MES_NORM`, `DEPARTAMENTO_NORM`, `MUNICIPIO_NORM`, `FUENTE_HOJA`, `ENTIDAD_REPORTA`, `AREA_PROTEGIDA_NACIONAL`, `AREA_TOTAL_HA_NUM`, `LATITUD_DEC`, `LONGITUD_DEC`, `COORDENADAS_VALIDAS`, `ELEVACION_MSNM_NUM`, `REGISTRO_INCOMPLETO`, `ANIO_FECHA_INCONSISTENTE`, `AREA_TOTAL_ATIPICO`.
- No se cargan: columnas `*_TEXTO_RESIDUAL`, columnas `COB_*` y `AREA_*` sin `_NUM`, `LATITUD`/`LONGITUD` crudas, `FECHA_REGISTRO`, `VEREDA_CORREGIMIENTO`, `PREDIO_BARRIO`. Las columnas de causa y cobertura viven en sus propias tablas.
- Tipos asignados con configuración regional `en-US`, porque el CSV usa punto decimal.
- Columnas nuevas:
  - `MES_NUM`: Enero = 1 … Diciembre = 12; "Sin reporte" y nulos quedan en nulo.
  - `ANIO_MES` = `ANIO * 100 + MES_NUM`; nulo si falta el año o el mes.
  - `DEPARTAMENTO_NORM` nulo se reemplaza por "Sin departamento" (43 eventos).
  - `CLASE_TAMANO`: "≤ 1 ha", "1–10 ha" (más de 1 hasta 10), "10–100 ha" (más de 10 hasta 100), "> 100 ha" y "Sin dato" (área nula).
  - `ORDEN_TAMANO`: 1 a 5, para ordenar las clases de tamaño.

### Tabla `Causas` — regla de limpieza

Se desdinamizan las 6 columnas `CAUSA_*` (las celdas nulas se descartan) y se clasifica cada marca:

| Tipo de marca | Valores encontrados (filas) | Decisión |
|---|---|---|
| Afirmativa genérica | `X` (1.178), `x` (659), `1` (24), `SI` (6) | Se asigna la causa de la columna donde está la marca. |
| Letra de la propia causa | `Q` (343), `I` (305), `O` (212), `D` (181), `A` (77), `R` (16) | Se asigna la causa de la columna (Q = quema fuera de control, D = descuido o negligencia, I = intencional, A = accidental, R = reactivación de focos, O = otra). |
| Texto que nombra una causa | "Accidental" (408), "Intencional" (332), "Quemas fuera de control" (199), "Descuido y negligencia" (155), "Otros" (90), "Reactivación de focos" (12), "rayo seco" (1) | Se asigna la causa que nombra el texto, aunque esté en la columna de otra causa ("Otros" y "rayo seco" → Otra). |
| Negativa | `0` (5) | Se descarta: indica que no hubo esa causa. |
| No informativa | "Sin definir" (368), "CONTROLADA" (1) | Se descarta: no identifica una causa. |

Después se eliminan duplicados (evento, causa). Un evento puede tener más de una causa.
Nombres finales de `TIPO_CAUSA`: Quema fuera de control, Descuido o negligencia, Intencional, Accidental, Reactivación de focos, Otra.

### Tabla `Coberturas`

Se desdinamizan las 11 columnas `COB_*_NUM`, se descartan nulos y se dejan solo las filas con `HECTAREAS > 0`. Un valor 0 se interpreta como "no hubo esa cobertura" y un nulo como "no informado". Nombres legibles: Bosque natural denso, Bosque intervenido, Bosque plantado, Bosque seco, Cultivos, Páramos, Sabanas y pastizales, Pastos manejados, Rastrojo, Vegetación seca, Cobertura sin determinar.

## 2. Relaciones

Todas de varios a uno, con dirección de filtro **única** (sin filtros bidireccionales):

| Desde (varios) | Hacia (uno) |
|---|---|
| `Eventos[DEPARTAMENTO_NORM]` | `Dim_Departamento[DEPARTAMENTO_NORM]` |
| `Eventos[ANIO_MES]` | `Dim_Periodo[ANIO_MES]` |
| `Causas[ID_EVENTO]` | `Eventos[ID_EVENTO]` |
| `Coberturas[ID_EVENTO]` | `Eventos[ID_EVENTO]` |

Consecuencias para el grupo:

- Los filtros de departamento y periodo llegan a `Eventos` y de ahí a `Causas` y `Coberturas`; no fluyen en sentido contrario.
- Para contar eventos por tipo de causa o de cobertura se usa `DISTINCTCOUNT(Causas[ID_EVENTO])` o `DISTINCTCOUNT(Coberturas[ID_EVENTO])`.
- Para hectáreas por tipo de cobertura se usa `SUM(Coberturas[HECTAREAS])`. No se debe sumar `Eventos[AREA_TOTAL_HA_NUM]` cortado por cobertura, porque repetiría el área del evento en cada tipo.
- Los porcentajes por causa pueden sumar más de 100 %, porque un evento puede tener varias causas.
- Otras opciones del archivo: *Fecha/hora automática* desactivada; `Dim_Periodo[MES_NOMBRE]` ordenada por `MES_NUM`; `ANIO`, `ANIO_MES`, `MES_NUM` e `ID_EVENTO` con resumen "No resumir".

## 3. Medidas base (tabla `_Medidas`)

| Medida | Fórmula DAX | Qué calcula y denominador |
|---|---|---|
| Total Eventos | `COUNTROWS(Eventos)` | Número de eventos reportados en el contexto de filtro. Es el denominador general. |
| Eventos con Hectareas | `COUNT(Eventos[AREA_TOTAL_HA_NUM])` | Eventos con área total informada (no cuenta nulos). Denominador para indicadores de tamaño. |
| Hectareas Totales | `SUM(Eventos[AREA_TOTAL_HA_NUM])` | Suma de hectáreas de los eventos con área informada. |
| Hectareas Mediana | `MEDIAN(Eventos[AREA_TOTAL_HA_NUM])` | Tamaño típico de un evento. Se prefiere a la media porque la distribución es muy asimétrica. |
| Hectareas Promedio | `AVERAGE(Eventos[AREA_TOTAL_HA_NUM])` | Media de hectáreas por evento con área informada; se muestra junto a la mediana para evidenciar la asimetría. |
| Eventos con Causa | `CALCULATE(DISTINCTCOUNT(Causas[ID_EVENTO]))` | Eventos con al menos una causa afirmativa. |
| Eventos con Cobertura | `CALCULATE(DISTINCTCOUNT(Coberturas[ID_EVENTO]))` | Eventos con al menos una cobertura con hectáreas > 0. |
| % Eventos con Causa | `DIVIDE([Eventos con Causa], [Total Eventos])` | Proporción de eventos con causa registrada. Denominador: total de eventos del filtro. |
| % Eventos con Cobertura | `DIVIDE([Eventos con Cobertura], [Total Eventos])` | Proporción de eventos con cobertura registrada. Denominador: total de eventos del filtro. |
| Hectareas por Cobertura | `SUM(Coberturas[HECTAREAS])` | Hectáreas afectadas por tipo de cobertura (solo eventos que informan cobertura). |

Formato: conteos como enteros con separador de miles; hectáreas con 1 decimal; porcentajes con 1 decimal.
Convención para las medidas de cada página: prefijo `P1_`, `P2_`, `P3_` o `P4_`, guardadas en `_Medidas`.

## 4. Comprobaciones del modelo

Valores de Power BI comparados con pandas sobre el mismo CSV (sin filtros):

| Comprobación | Power BI | pandas |
|---|---|---|
| Filas `Eventos` | 35.355 | 35.355 |
| Filas `Causas` (eventos distintos) | 4.198 (4.148) | 4.198 (4.148) |
| Filas `Coberturas` (eventos distintos) | 16.618 (14.907) | 16.618 (14.907) |
| Filas `Dim_Departamento` | 34 | 33 + "Sin departamento" |
| Filas `Dim_Periodo` | 180 | 15 años × 12 meses |
| Total Eventos | 35.355 | 35.355 |
| Eventos con Hectareas | 34.580 | 34.580 (775 nulos) |
| Hectareas Totales | 1.612.918,0 | 1.612.918,0 |
| Hectareas Mediana | 2,0 | 2,0 |
| Hectareas Promedio | 46,6 | 46,6 |
| Eventos con Causa / % | 4.148 / 11,7 % | 4.148 / 11,7 % |
| Eventos con Cobertura / % | 14.907 / 42,2 % | 14.907 / 42,2 % |
| Hectareas por Cobertura | 669.358,0 | 669.357,9 |

- Todos los `ID_EVENTO` de `Causas` y `Coberturas` existen en `Eventos` (se generan desde la misma consulta `Eventos_base`), por lo que no hay registros huérfanos.
- Suma de coberturas por evento frente a `AREA_TOTAL_HA_NUM`: de los 14.907 eventos con cobertura, 14.903 tienen área total; en 14.813 (99,4 %) ambas cifras coinciden (diferencia ≤ 0,01 ha), en 15 la suma de coberturas es mayor y en 75 es menor.

## 5. Limitaciones del modelo

- Solo 4.148 de 35.355 eventos (11,7 %) tienen una causa afirmativa: todo análisis por causa se calcula sobre ese subconjunto.
- Solo 14.907 eventos (42,2 %) informan cobertura; por eso `Hectareas por Cobertura` (≈ 669 mil ha) es mucho menor que `Hectareas Totales` (≈ 1,6 millones de ha). No son cifras comparables entre sí.
- 17 eventos no tienen año o mes válido (sin año, mes nulo o "Sin reporte"): no se relacionan con `Dim_Periodo` y no aparecen al filtrar por periodo.
- 43 eventos sin departamento se agrupan como "Sin departamento".
- 775 eventos no tienen área total; se excluyen de mediana, promedio y suma de hectáreas y se clasifican como "Sin dato" en `CLASE_TAMANO`.
