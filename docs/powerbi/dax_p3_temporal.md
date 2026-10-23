# Medidas DAX de la página 3 (comportamiento temporal)

Todas las medidas viven en la tabla `_Medidas` y usan `Total Eventos` de la base. El tiempo se toma de la tabla `Dim_Periodo` (calendario año-mes 2010-2024), que se relaciona con `Eventos[ANIO_MES]`; por eso los 17 eventos sin año o mes válido no aparecen en ningún gráfico por periodo. Los segmentadores de departamento (`Dim_Departamento[DEPARTAMENTO_NORM]`) y de mes (`Dim_Periodo[MES_NOMBRE]`) filtran todas las medidas de la página.

## P3_Eventos Ultimo Anio

```dax
P3_Eventos Ultimo Anio =
VAR a = MAX(Dim_Periodo[ANIO])
RETURN CALCULATE([Total Eventos], Dim_Periodo[ANIO] = a)
```

Eventos del último año del calendario (2024). Se guarda el año en una variable porque una función de agregación no se puede usar directamente dentro del filtro de `CALCULATE`. Si se selecciona un mes en el segmentador, cuenta solo ese mes de 2024. Sin filtros: 7.785.

## P3_Eventos Anio Anterior

```dax
P3_Eventos Anio Anterior =
VAR a = MAX(Dim_Periodo[ANIO]) - 1
RETURN CALCULATE([Total Eventos], Dim_Periodo[ANIO] = a)
```

Eventos del año anterior al último (2023), con los mismos filtros de mes y departamento. Al conservar el filtro de mes, la comparación es entre periodos equivalentes (por ejemplo enero a marzo de 2024 frente a enero a marzo de 2023). Sin filtros: 2.898.

## P3_Variacion Interanual

```dax
P3_Variacion Interanual =
DIVIDE([P3_Eventos Ultimo Anio] - [P3_Eventos Anio Anterior], [P3_Eventos Anio Anterior])
```

Variación porcentual del último año frente al anterior. Denominador: eventos del año anterior (queda en blanco si es cero). Sin filtros: +168,6 %.

## P3_Mes Pico

```dax
P3_Mes Pico =
VAR t = ADDCOLUMNS(VALUES(Dim_Periodo[MES_NOMBRE]), "@n", [Total Eventos])
VAR m = MAXX(t, [@n])
RETURN CONCATENATEX(FILTER(t, [@n] = m), Dim_Periodo[MES_NOMBRE], ", ")
```

Nombre del mes (o de los meses, si hay empate) con más eventos en el contexto de filtro actual. Sin filtros: Enero (7.676 eventos).

## P3_% Eventos por Mes

```dax
P3_% Eventos por Mes =
DIVIDE(
    [Total Eventos],
    CALCULATE([Total Eventos], REMOVEFILTERS(Dim_Periodo[MES_NOMBRE]), REMOVEFILTERS(Dim_Periodo[MES_NUM]))
)
```

Porcentaje de los eventos que cae en cada mes. Denominador: total de eventos del filtro actual, sin el filtro de mes (35.355 sin filtros; el denominador incluye los eventos sin año o mes válido, de modo que los porcentajes de los 12 meses suman un poco menos de 100 %).

## Medidas de texto para las tarjetas

```dax
P3_Eventos Ultimo Anio (texto) = FORMAT([P3_Eventos Ultimo Anio], "#,0", "es-CO")
P3_Eventos Anio Anterior (texto) = FORMAT([P3_Eventos Anio Anterior], "#,0", "es-CO")
```

Solo sirven para mostrar el número con punto de miles en las tarjetas (las tarjetas numéricas lo abrevian como "8 mil"). Los cálculos usan las medidas numéricas.

## Indicadores de la página

| Indicador | Medida | Valor sin filtros |
|---|---|---|
| Eventos del último año (2024) | `P3_Eventos Ultimo Anio` | 7.785 |
| Eventos del año anterior (2023) | `P3_Eventos Anio Anterior` | 2.898 |
| Variación frente al año anterior | `P3_Variacion Interanual` | +168,6 % |
| Mes con más eventos | `P3_Mes Pico` | Enero |

## Comprobación contra pandas

Los valores del tablero se compararon con los calculados en pandas sobre `incendios_ideam_tratado_2010_2024.csv`:

| Comprobación | Power BI | pandas |
|---|---|---|
| Eventos con año y mes válidos | 35.338 | 35.338 (17 fuera del calendario) |
| Eventos 2024 / 2023 | 7.785 / 2.898 | 7.785 / 2.898 |
| Variación 2023 a 2024 | +168,6 % | +168,6 % |
| Enero, todos los años | 7.676 (21,7 %) | 7.676 |
| Cundinamarca: 2023 a 2024 | 438 a 782 (+78,5 %) | 438 a 782 |
| Meses enero a marzo: 2023 / 2024 | 1.449 / 4.777 (+229,7 %) | 1.449 / 4.777 |
| Cundinamarca y enero: 2023 / 2024 | 22 / 169 (+668,2 %) | 22 / 169 |
| 2010: eventos enero a marzo | 2.269 de 2.322 | 2.269 de 2.322 (97,7 %) |

## Filtros y panel de conocimientos

- Segmentadores: `Dim_Departamento[DEPARTAMENTO_NORM]` (lista desplegable) y `Dim_Periodo[MES_NOMBRE]` (lista desplegable con selección múltiple).
- El segmentador de mes permite comparar periodos equivalentes: al elegir, por ejemplo, enero, febrero y marzo, el gráfico por año y las tarjetas comparan los mismos meses en todos los años.
- Los tres conocimientos evidentes están en un panel que se abre con el botón "Ver conocimientos" y se cierra con "Cerrar" (marcadores `Tablero P3` y `Conocimientos P3`, sin guardar el estado de los datos para no reiniciar los filtros).
