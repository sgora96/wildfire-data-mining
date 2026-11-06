# Vista 1: consultas y operaciones

Pregunta: ¿Cómo se distribuyen las hectáreas quemadas entre regiones, departamentos y municipios, y cómo cambia esa distribución por trimestre y por año?

Las consultas se generan con `Olap.consultar(spec)`.

## Consultas base
- Matriz inicial: `{ "medida": "hectareas", "filas": "territorio.region", "columnas": "tiempo.trimestre", "filtros": {} }`
- Indicadores: `{ "medida": "hectareas", "filas": "territorio.region", "filtros": {} }`
- Gráfica de grupos: `{ "medida": "hectareas", "filas": "territorio.region", "filtros": {}, "orden": "valor_desc", "limite": 12 }`
- Gráfica de distribución: `{ "medida": "hectareas", "filas": "tiempo.trimestre", "filtros": {}, "orden": "etiqueta", "limite": 500 }`

## Drill-down
- Dimensiones y medida: territorio; hectáreas.
- Nivel y filtros: de región a departamento, con región = Orinoquia.
- Procedimiento: en "Ejemplo: regiones", clic en Orinoquia. La consulta agrupa por `territorio.departamento` y filtra `territorio.region`.
- Interpretación: las hectáreas de Orinoquia se recalculan por departamento y permiten bajar a municipio.

## Roll-up
- Dimensiones y medida: tiempo y territorio; hectáreas.
- Nivel y filtros: de trimestre a año, con región = Orinoquia.
- Procedimiento: en "Ejemplo: Orinoquia por trimestre", usar "Roll-up filas".
- Interpretación: 2022-T1 registra 129.677 ha y el año 2022 registra 135.266 ha. El total anual se recalcula con un nuevo agrupamiento.

## Pivot
- Dimensiones y medida: territorio y tiempo; hectáreas.
- Nivel y filtros: región por temporada, sin filtros.
- Procedimiento: en "Ejemplo: región x temporada", usar "Pivot". Se intercambian `filas` y `columnas`, y la consulta se ejecuta de nuevo.
- Interpretación: permite leer cada temporada como fila y comparar qué regiones aportan sus hectáreas.

## Filtros de la vista
Tamaño (`tamano.clase`) y fuente (`fuente.hoja`). La selección activa se muestra en los chips.