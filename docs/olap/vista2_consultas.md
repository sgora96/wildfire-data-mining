# Vista 2: consultas y operaciones

Pregunta: ¿Cómo cambia, entre años y trimestres, la proporción de incendios grandes (más de 100 ha) y el área promedio por evento?

Las consultas se generan con `Olap.consultar(spec)` (API de Flask en local y sql.js en el sitio publicado; las dos dan las mismas cifras).

## Medidas y denominadores
- `pct_grandes` = 100 × eventos de más de 100 ha / eventos con área del grupo. Los 775 eventos sin área no entran en el denominador.
- `ha_por_evento` = hectáreas / eventos con área del grupo.
- Ninguna de las dos es aditiva: se recalculan con un nuevo `GROUP BY` en cada nivel. No se suman ni se promedian porcentajes de trimestres para obtener el del año.
- Los indicadores de la vista se calculan desde partes aditivas (eventos, eventos con área y hectáreas por clase de tamaño) de la selección activa.

## Consultas base
- Matriz inicial: `{ "medida": "eventos", "filas": "tiempo.anio", "columnas": "tamano.clase", "filtros": {} }`
- Indicadores: `{ "medida": "hectareas", "filas": "tamano.clase", "filtros": {} }`
- Gráfica 1 (sin filtro de tiempo): `{ "medida": "pct_grandes", "filas": "tiempo.anio", "columnas": "tiempo.temporada", "filtros": {} }`
- Gráfica 1 (con filtro de tiempo): `{ "medida": "pct_grandes", "filas": "tiempo.trimestre", "filtros": { "tiempo.anio": ["2024"] } }`
- Gráfica 2: `{ "medida": "ha_por_evento", "filas": "tiempo.anio", "filtros": {} }` (o `tiempo.trimestre` cuando hay filtro de tiempo)

## Slice
- Dimensiones y medidas: tiempo y tamaño; eventos y % de eventos grandes.
- Nivel y filtros: un solo valor de una dimensión, año = 2024; filas en trimestre y columnas en clase de tamaño.
- Procedimiento: botón "Slice: año = 2024". La consulta agrega `WHERE t.h_anio IN (?)` con el parámetro `"2024"`.
- Interpretación: 2024 tiene 7.785 eventos (7.784 con área) y 284 de más de 100 ha (3,6 %). Por trimestre: T1 2,8 % (135 de 4.776), T2 3,2 % (22 de 697), T3 5,5 % (109 de 1.983) y T4 5,5 % (18 de 328). La proporción de grandes es mayor en la segunda mitad del año, aunque la mayoría de eventos ocurre en T1.

## Roll-up
- Dimensiones y medidas: tiempo; % de eventos grandes.
- Nivel y filtros: de trimestre a año.
- Procedimiento: después del slice, usar "Roll-up filas". Las filas pasan de `tiempo.trimestre` a `tiempo.anio` y la medida se recalcula con un nuevo agrupamiento (el filtro del nivel al que se sube se retira para ver todos los años).
- Interpretación: el % de grandes de 2024 es 3,6 % (284 / 7.784). No coincide con el promedio simple de sus trimestres (4,2 %), porque T1 tiene muchos más eventos: por eso la medida se recalcula y no se promedian los porcentajes.

## Pivot
- Dimensiones y medidas: tiempo (año y temporada); % de eventos grandes.
- Nivel y filtros: año por temporada, sin filtros.
- Procedimiento: botón "Ejemplo: misma temporada entre años" y luego "Pivot". Se intercambian `filas` y `columnas` y la consulta se ejecuta de nuevo.
- Interpretación: con las temporadas como filas se lee cada temporada a lo largo de los años. La fila "1. Ene-Mar" muestra valores como 12,1 % en 2022 y 2,8 % en 2024; la fila "2. Jul-Sep" se mantiene entre 4,7 % y 5,5 % desde 2019.

## Dimensión fuente (contraste de la hipótesis de la Etapa 4)
- Consulta: `{ "medida": "pct_grandes", "filas": "fuente.entidad", "columnas": "tiempo.temporada", "filtros": { "tiempo.anio": ["2024"] } }` (botón "Ejemplo: entidad que reporta en 2024").
- La jerarquía hoja → entidad permite un drill-down desde `fuente.hoja` a `fuente.entidad` con los botones de la barra.

## Filtros de la vista
Territorio (`territorio.region`) y fuente (`fuente.hoja`). La selección activa se muestra en los chips, y el botón "Ver consulta SQL" muestra el SQL y sus parámetros.

## Comprobación contra los datos tratados
Valores calculados con pandas sobre `data/processed/incendios_ideam_tratado_2010_2024.csv` y comparados con las consultas al modelo:

| Periodo | % grandes (pandas) | % grandes (modelo) |
|---|---|---|
| 2022-T1 | 12,1 % (71 de 588) | 12,1 % (71 de 588) |
| 2023-T1 | 3,4 % (49 de 1.448) | 3,4 % (49 de 1.448) |
| 2024-T1 | 2,8 % (135 de 4.776) | 2,8 % (135 de 4.776) |
| 2023-T3 | 5,3 % (54 de 1.028) | 5,3 % (54 de 1.028) |
| 2024-T3 | 5,5 % (109 de 1.983) | 5,5 % (109 de 1.983) |
| 2024-T4 | 5,5 % (18 de 328) | 5,5 % (18 de 328) |

Hectáreas por evento: 2010 39,3; 2019 58,5; 2023 28,9; 2024 39,7 (iguales en pandas y en el modelo). Total: 46,6 ha por evento (1.612.918,0 ha / 34.580 eventos con área).
