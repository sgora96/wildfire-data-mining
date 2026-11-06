# Vista 4: consultas y operaciones

Pregunta: ¿Qué causas registradas se asocian con incendios más grandes y cómo varía esa asociación entre regiones?

- **Dimensiones:** causa (filas) y tamaño (columnas), con territorio (región) como corte. Filtros: territorio (región) y tiempo (año).
- **Medidas:** % de eventos grandes (`pct_grandes`), hectáreas por evento (`ha_por_evento`), eventos y hectáreas.
- **Jerarquías:** registro de causa → causa; región → departamento.
- **Archivos:** `app/templates/etapa5/vista4.html` y `app/static/js/olap_vista4.js`.

Todas las consultas se generan con `Olap.consultar(spec)`, que produce el mismo SQL en los dos modos (API de Flask y sql.js en el sitio publicado). Los valores de los filtros viajan como parámetros (`?`).

**"Sin causa registrada"** (31.207 eventos) es un dato faltante, no una causa: la causa solo se registró en las hojas 2010-2022. Los eventos con dos o más causas distintas están en "Mas de una causa" (49), para que ninguna fila de hechos se duplique.

## 1. Consultas base

| Elemento de la vista | Especificación |
|---|---|
| Matriz inicial | `{ "medida": "eventos", "filas": "causa.causa", "columnas": "tamano.clase", "filtros": {} }` |
| Indicadores | `{ "medida": "hectareas", "filas": "tamano.clase", "filtros": <filtros activos> }` (se extrae el grupo "> 100 ha" para el % de grandes) |
| Gráfica 1: % de eventos grandes por causa | `{ "medida": "pct_grandes", "filas": "causa.causa", "filtros": <filtros activos>, "orden": "valor_desc" }` |
| Gráfica 2: hectáreas por evento por causa | `{ "medida": "ha_por_evento", "filas": "causa.causa", "filtros": <filtros activos>, "orden": "valor_desc" }` |

SQL de la matriz inicial (sin filtros):

```sql
SELECT c.causa AS fila, z.clase AS col, SUM(f.n_eventos) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_tamano z ON f.tamano_key = z.tamano_key
JOIN dim_causa c ON f.causa_key = c.causa_key
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
```

### Por qué el % de grandes no se calcula directamente en la matriz

Si `tamano.clase` queda en filas o en columnas, `pct_grandes` solo puede dar 0 % o 100 % en cada celda (la condición de la medida ya coincide con el grupo de la columna). Por eso la gráfica 1 consulta `pct_grandes` agrupando solo por causa, sin el cruce con tamaño, y la vista muestra un aviso si se elige esa medida con la clase de tamaño en la matriz.

### Valores de control (sin filtros)

La vista coincide con los valores de control calculados con pandas sobre el CSV tratado:

| Causa | Eventos | Eventos con área | % de grandes | Hectáreas por evento |
|---|---|---|---|---|
| Sin causa registrada | 31.207 | 30.606 | 4,9 % (1.509) | 45,1 |
| Intencional | 1.402 | 1.303 | 3,6 % (47) | 40,3 |
| Quema fuera de control | 974 | 945 | 3,6 % (34) | 23,7 |
| Accidental | 598 | 582 | 1,7 % (10) | 28,6 |
| Descuido o negligencia | 583 | 567 | 2,8 % (16) | 15,1 |
| Otra | 499 | 489 | 9,8 % (48) | 256,2 |
| Mas de una causa | 49 | 48 | 16,7 % (8) | 161,2 |
| Reactivacion de focos | 43 | 40 | 5,0 % (2) | 19,5 |
| **Total** | **35.355** | **34.580** | **4,8 % (1.674)** | **46,6** |

## 2. SLICE (un solo valor de una dimensión)

- **Dimensiones y medida:** territorio (región) como filtro; causa y tamaño en la matriz; eventos.
- **Nivel y filtro:** región = Orinoquia (un solo valor de una sola dimensión).
- **Procedimiento:** botón "Slice: región = Orinoquia". La matriz conserva causa x tamaño, pero ahora cuenta solo los 3.714 eventos de Orinoquia.
- **Especificación:** `{ "medida": "eventos", "filas": "causa.causa", "columnas": "tamano.clase", "filtros": { "territorio.region": ["Orinoquia"] } }`

```sql
SELECT c.causa AS fila, z.clase AS col, SUM(f.n_eventos) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_territorio r ON f.territorio_key = r.territorio_key
JOIN dim_tamano z ON f.tamano_key = z.tamano_key
JOIN dim_causa c ON f.causa_key = c.causa_key
WHERE r.h_region IN (?)
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
-- parámetros: ['Orinoquia', 50000]
```

Eventos con área por causa dentro de Orinoquia: Sin causa registrada 3.484, Otra 83, Quema fuera de control 25, Descuido o negligencia 20, Intencional 19, Mas de una causa 4, Reactivacion de focos 4, Accidental 1.

- **Interpretación:** dentro de Orinoquia, "Otra" llega a 47,0 % de eventos grandes (39 de 83) frente a 9,8 % a nivel nacional. Casi todas las demás causas de Orinoquia tienen muy pocos eventos con área (Accidental: 1; Reactivacion de focos: 4), así que su porcentaje no es confiable.

## 3. DICE (varias dimensiones a la vez)

- **Dimensiones y medida:** causa y territorio (región); hectáreas, con eventos y eventos con área como denominadores.
- **Nivel y filtros:** filas en causa y columnas en región, con dos filtros combinados: causa en {Intencional, Otra} y región en {Orinoquia, Andina}.
- **Procedimiento:** botón "Dice: Intencional y Otra, en Orinoquia y Andina". Las hectáreas por evento se calculan como hectáreas ÷ eventos con área de cada celda.
- **Especificación:**

```json
{
  "medida": "hectareas",
  "filas": "causa.causa",
  "columnas": "territorio.region",
  "filtros": {
    "causa.causa": ["Intencional", "Otra"],
    "territorio.region": ["Orinoquia", "Andina"]
  }
}
```

```sql
SELECT c.causa AS fila, r.h_region AS col, SUM(f.area_total_ha) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_territorio r ON f.territorio_key = r.territorio_key
JOIN dim_causa c ON f.causa_key = c.causa_key
WHERE c.causa IN (?, ?) AND r.h_region IN (?, ?)
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
-- parámetros: ['Intencional', 'Otra', 'Orinoquia', 'Andina', 50000]
```

Resultado:

| Causa | Región | Hectáreas | Eventos | Con área | Ha por evento | % grandes |
|---|---|---|---|---|---|---|
| Intencional | Andina | 15.456,1 | 1.070 | 971 | 15,9 | 1,8 % (17) |
| Intencional | Orinoquia | 3.976,1 | 19 | 19 | 209,3 | 10,5 % (2) |
| Otra | Andina | 3.750,6 | 358 | 349 | 10,7 | 2,0 % (7) |
| Otra | Orinoquia | 120.217,5 | 83 | 83 | 1.448,4 | 47,0 % (39) |

- **Interpretación:** con el corte combinado, "Otra" en Orinoquia concentra 120.217,5 ha en solo 83 eventos (1.448,4 ha por evento), muy por encima de "Otra" en Andina (10,7 ha por evento) e incluso de "Intencional" en la misma Orinoquia (209,3 ha por evento). Las ha por evento son razones: se recalculan en cada celda y no se suman. 83 eventos con área es una base razonable para esta causa en esta región, aunque pequeña frente a los cientos o miles de eventos de las otras celdas.

## 4. Roll-up, drill-down y pivot

La barra de controles también permite:

- **Roll-up / drill-down:** entre registro de causa y causa (por ejemplo, de "Con causa registrada" a cada causa concreta), o entre región y departamento si se usan como filas o columnas.
- **Pivot:** intercambiar filas y columnas (por ejemplo, causa x región pasa a región x causa). Se ejecuta de nuevo la consulta con los dos niveles intercambiados.

## 5. Filtros de la vista

Región (`territorio.region`) y año (`tiempo.anio`): son de dimensiones diferentes. La selección activa se muestra como chips, y el botón "Ver consulta SQL" muestra el SQL y los parámetros de la matriz.

## 6. Paridad entre los dos modos

Las mismas especificaciones (matriz inicial, slice de Orinoquia y dice de causa x región) se ejecutaron en modo API (`python run.py`) y en el sitio estático con sql.js (`python freeze.py` y un servidor local sobre `build/`). Los indicadores y las matrices dieron los mismos valores en ambos modos.
