# Medidas DAX de la página 4 (análisis multivariado)

La página cruza tres variables: territorio (`DEPARTAMENTO_NORM`), época del año (`TEMPORADA`, derivada del mes) y tamaño del evento (`AREA_TOTAL_HA_NUM` y `CLASE_TAMANO`). Todas las medidas viven en la tabla `_Medidas` y usan las medidas base. Los segmentadores de año (`Dim_Periodo[ANIO]`) y de tamaño (`Eventos[CLASE_TAMANO_ORD]`) filtran todos los objetos de la página.

## Columna calculada `Dim_Periodo[TEMPORADA]`

```dax
TEMPORADA = SWITCH(TRUE(), Dim_Periodo[MES_NUM] IN {1, 2, 3}, "1. Ene-Mar", Dim_Periodo[MES_NUM] IN {7, 8, 9}, "2. Jul-Sep", "3. Abr-Jun y Oct-Dic")
```

Agrupa los meses en tres épocas. Los grupos se justifican con la página 3: enero a marzo y julio a septiembre reúnen cerca del 87 % de los eventos. El prefijo numérico hace que se ordenen cronológicamente. Los eventos sin año o mes válido (17) no pertenecen a ninguna temporada y se excluyen de los objetos con filtro de "(En blanco)". Sin filtros: 19.396, 11.292 y 4.650 eventos (suman 35.338).

## P4_Combinacion con mas Hectareas

```dax
P4_Combinacion con mas Hectareas =
VAR t =
    ADDCOLUMNS(
        SUMMARIZE(Eventos, Eventos[DEPARTAMENTO_NORM], Dim_Periodo[TEMPORADA]),
        "@ha", [Hectareas Totales]
    )
VAR m = MAXX(t, [@ha])
RETURN
    CONCATENATEX(
        FILTER(t, [@ha] = m),
        Eventos[DEPARTAMENTO_NORM] & " · " & MID(Dim_Periodo[TEMPORADA], 4, 50),
        "; "
    )
```

Combinación de departamento y temporada con más hectáreas en el contexto de filtro actual (en caso de empate muestra todas). `MID(..., 4, 50)` quita el prefijo numérico de la temporada. Sin filtros: Vichada · Ene-Mar (235.367 ha).

## P4_Evento Mas Grande (texto)

```dax
P4_Evento Mas Grande (texto) = FORMAT(MAX(Eventos[AREA_TOTAL_HA_NUM]), "#,0", "es-CO") & " ha"
```

Área del evento más grande del contexto actual, con punto de miles y la unidad. Es texto para que la tarjeta no abrevie el número como "41 mil". Sin filtros: 41.079 ha.

## P4_% Hectareas Ene-Mar

```dax
P4_% Hectareas Ene-Mar =
DIVIDE(
    CALCULATE([Hectareas Totales], Dim_Periodo[TEMPORADA] = "1. Ene-Mar"),
    CALCULATE([Hectareas Totales], REMOVEFILTERS(Dim_Periodo[TEMPORADA]))
)
```

Proporción de las hectáreas que cae en enero a marzo. Denominador: hectáreas totales del filtro actual, en todas las temporadas. Sin filtros: 65,2 %.

## P4_% Eventos por Tamano

```dax
P4_% Eventos por Tamano =
DIVIDE(
    [Total Eventos],
    CALCULATE([Eventos con Hectareas], REMOVEFILTERS(Eventos[CLASE_TAMANO]), REMOVEFILTERS(Eventos[CLASE_TAMANO_ORD]))
)
```

Porcentaje de los eventos de cada clase de tamaño dentro de la temporada del eje. Denominador: eventos con área informada de esa temporada (19.001, 11.012 y 4.553 sin filtros), de modo que cada columna del gráfico suma 100 %. Se quitan los filtros de las dos columnas de clase para que cada segmento se compare con el total de la temporada.

## Objetos de la página

| Objeto | Campos | Filtro del objeto |
|---|---|---|
| Matriz "Hectáreas por departamento y temporada" | filas `DEPARTAMENTO_NORM`, columnas `TEMPORADA`, valores `Hectareas Totales` | 8 departamentos con más hectáreas (N superiores por `Hectareas Totales`); se excluye "(En blanco)" de `TEMPORADA`; formato condicional de color en los valores |
| Gráfico "Tamaño de los eventos por temporada" | eje `TEMPORADA`, leyenda `CLASE_TAMANO_ORD`, valores `P4_% Eventos por Tamano` | se excluyen "5. Sin dato" y "(En blanco)" |
| Tabla "Los 10 eventos de mayor área" | `ID_EVENTO`, `DEPARTAMENTO_NORM`, `MUNICIPIO_NORM`, `ANIO`, `MES_NORM`, `AREA_TOTAL_HA_NUM`, `AREA_TOTAL_ATIPICO` | 10 mayores por `Hectareas Totales` sobre `ID_EVENTO`; hay un empate en el puesto 10 y por eso salen 11 filas |

## Indicadores de la página

| Indicador | Medida | Valor sin filtros |
|---|---|---|
| Combinación con más hectáreas | `P4_Combinacion con mas Hectareas` | Vichada · Ene-Mar |
| Evento de mayor área | `P4_Evento Mas Grande (texto)` | 41.079 ha |
| % de las hectáreas en enero-marzo | `P4_% Hectareas Ene-Mar` | 65,2 % |

## Comprobación contra pandas

Los valores del tablero se compararon con los calculados en pandas sobre `incendios_ideam_tratado_2010_2024.csv`:

| Comprobación | Power BI | pandas |
|---|---|---|
| Eventos por temporada | 19.396 / 11.292 / 4.650 | 19.396 / 11.292 / 4.650 |
| Vichada × enero-marzo (ha) | 235.367 | 235.367 |
| Casanare × enero-marzo (ha) | 222.521 | 222.521 |
| Tolima × julio-septiembre (ha) | 111.035 | 111.035 |
| Huila × julio-septiembre (ha) | 98.853 | 98.853 |
| Año 2024: combinación / mayor evento / % ene-mar | Huila · Jul-Sep / 30.000 ha / 44,0 % | Huila · Jul-Sep (39.109 ha) / 30.000 ha / 44,0 % |
| Tamaño > 100 ha: combinación / % ene-mar | Vichada · Ene-Mar / 67,2 % | Vichada · Ene-Mar (233.065 ha) / 67,2 % |
| % de eventos > 100 ha, enero-marzo | 5,5 % | 1.046 de 19.001 |
| Mayor evento | 41.079 ha (Cumaribo, Vichada, diciembre de 2021) | 41.079 ha |
| Cumaribo (5 eventos de la tabla) | 142.550 ha | 142.550 ha |

## Filtros y panel de conocimientos

- Segmentadores: `Dim_Periodo[ANIO]` (rango de años) y `Eventos[CLASE_TAMANO_ORD]` (lista desplegable con selección múltiple).
- Los tres conocimientos evidentes están en un panel que se abre con el botón "Ver conocimientos" y se cierra con "Cerrar" (marcadores `Tablero P4` y `Conocimientos P4`, sin guardar el estado de los datos para no reiniciar los filtros).
