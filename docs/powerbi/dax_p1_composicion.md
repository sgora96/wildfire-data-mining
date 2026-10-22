# Medidas DAX de la página 1 (composición de la población)

Todas las medidas viven en la tabla `_Medidas` y usan las medidas base (`Total Eventos`, `Eventos con Hectareas`, `Hectareas Totales`, `Hectareas por Cobertura`, `Eventos con Causa`). Los segmentadores de año (`Dim_Periodo[ANIO]`) y de departamento (`Dim_Departamento[DEPARTAMENTO_NORM]`) filtran todas ellas y también las tarjetas de la página.

## P1_% Eventos por Clase

```dax
P1_% Eventos por Clase =
DIVIDE(
    [Total Eventos],
    CALCULATE([Eventos con Hectareas], REMOVEFILTERS(Eventos[CLASE_TAMANO]), REMOVEFILTERS(Eventos[CLASE_TAMANO_ORD]))
)
```

Porcentaje de eventos de cada clase de tamaño (≤ 1, 1–10, 10–100 y > 100 ha). Denominador: eventos con área informada (34.580 sin filtros); los 775 eventos sin área no entran en el gráfico. Se quitan los filtros de las dos columnas de clase para que cada barra se compare con el total y no consigo misma.

## P1_% Hectareas por Clase

```dax
P1_% Hectareas por Clase =
DIVIDE(
    [Hectareas Totales],
    CALCULATE([Hectareas Totales], REMOVEFILTERS(Eventos[CLASE_TAMANO]), REMOVEFILTERS(Eventos[CLASE_TAMANO_ORD]))
)
```

Porcentaje de las hectáreas que aporta cada clase de tamaño. Denominador: hectáreas totales del filtro actual (1.612.918 ha sin filtros). Junto con la medida anterior permite comparar cuántos eventos y cuánta área hay en cada clase.

## P1_% Hectareas por Cobertura

```dax
P1_% Hectareas por Cobertura =
DIVIDE(
    [Hectareas por Cobertura],
    CALCULATE([Hectareas por Cobertura], REMOVEFILTERS(Coberturas[TIPO_COBERTURA]))
)
```

Porcentaje de las hectáreas con cobertura informada que corresponde a cada tipo de cobertura. Denominador: hectáreas de los eventos que informan cobertura (669.358 ha sin filtros, en 14.907 eventos), no las 1.612.918 ha totales.

## P1_% Eventos por Causa

```dax
P1_% Eventos por Causa =
DIVIDE(
    [Eventos con Causa],
    CALCULATE([Eventos con Causa], REMOVEFILTERS(Causas[TIPO_CAUSA]))
)
```

Porcentaje de los eventos con causa registrada que tienen cada tipo de causa. Denominador: eventos distintos con al menos una causa afirmativa (4.148 sin filtros). Un evento puede tener varias causas, por eso los porcentajes suman más de 100 % (101,2 % sin filtros).

## Columna calculada `Eventos[CLASE_TAMANO_ORD]`

```dax
CLASE_TAMANO_ORD = Eventos[ORDEN_TAMANO] & ". " & Eventos[CLASE_TAMANO]
```

Es una columna calculada (no una medida) que antepone el número de orden a la clase de tamaño: `1. ≤ 1 ha`, `2. 1–10 ha`, `3. 10–100 ha`, `4. > 100 ha` y `5. Sin dato`. Se usa como eje del gráfico de tamaño para que las clases salgan en orden creciente. En el gráfico se excluye `5. Sin dato` con un filtro del objeto visual.

## Indicadores de la página

| Indicador | Medida | Valor sin filtros |
|---|---|---|
| Eventos reportados | `Total Eventos` | 35.355 |
| Hectáreas por evento | `Hectareas Mediana` y `Hectareas Promedio` | 2,0 y 46,6 |
| Eventos con información registrada | `% Eventos con Causa` y `% Eventos con Cobertura` | 11,7 % y 42,2 % |

## Comprobación contra pandas

Los valores del tablero se compararon con los calculados en pandas sobre `incendios_ideam_tratado_2010_2024.csv`:

| Comprobación | Power BI | pandas |
|---|---|---|
| Eventos con área informada | 34.580 | 34.580 |
| ≤ 1 ha: eventos / hectáreas | 35,9 % / 0,5 % | 12.428 eventos (35,9 %) / 8.228,5 ha (0,5 %) |
| 1–10 ha | 42,9 % / 3,8 % | 14.852 eventos / 61.178,5 ha |
| 10–100 ha | 16,3 % / 12,3 % | 5.626 eventos / 198.720,2 ha |
| > 100 ha | 4,8 % / 83,4 % | 1.674 eventos / 1.344.790,7 ha |
| Cobertura sin determinar | 71,2 % | 476.662,1 ha de 669.358,0 ha |
| Causa intencional | 34,1 % | 1.415 de 4.148 eventos |
| Con filtro Cundinamarca, ≤ 1 ha | 39,7 % de los eventos | 2.330 de 5.867 eventos con área |

## Filtros y panel de conocimientos

- Segmentadores: `Dim_Periodo[ANIO]` (rango de años) y `Dim_Departamento[DEPARTAMENTO_NORM]` (lista desplegable).
- Con los años 2021 a 2024 los gráficos de causa y de cobertura quedan vacíos y las tarjetas de causa y cobertura muestran "--": las hojas recientes del IDEAM no traen esos campos. Es un valor faltante, no un cero.
- Los tres conocimientos evidentes están en un panel que se abre con el botón "Ver conocimientos" y se cierra con "Cerrar" (marcadores `Tablero` y `Conocimientos`, sin guardar el estado de los datos para no reiniciar los filtros).
