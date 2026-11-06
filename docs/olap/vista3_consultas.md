# Vista 3: consultas y operaciones

Pregunta: ¿Qué grupos y tipos de cobertura concentran las hectáreas en cada región y cuánta área queda sin cobertura informada?

- **Dimensiones:** cobertura (filas) y territorio (columnas, nivel región). Filtros: tiempo (año) y tamaño (clase).
- **Medidas:** hectáreas, eventos y participación de eventos (`pct_total`).
- **Jerarquías:** grupo → tipo de cobertura; región → departamento.
- **Archivos:** `app/templates/etapa5/vista3.html` y `app/static/js/olap_vista3.js`.

Todas las consultas se generan con `Olap.consultar(spec)`, que produce el mismo SQL en los dos modos: la API de Flask (`python run.py`) y sql.js en el sitio publicado. La vista no escribe SQL a mano y los valores de los filtros viajan como parámetros (`?`).

**Las hectáreas de esta vista** son el área total del evento asignada a su cobertura. No son las hectáreas por columna `COB_*` de la Etapa 4 (669.358 ha) y no deben compararse con ellas. La cobertura solo se registró en la hoja 2010-2020; los eventos de 2021-2024 aparecen como "No informada".

## 1. Consultas base

| Elemento de la vista | Especificación |
|---|---|
| Matriz inicial | `{ "medida": "hectareas", "filas": "cobertura.grupo", "columnas": "territorio.region", "filtros": {} }` |
| Indicadores | `{ "medida": "hectareas", "filas": "cobertura.grupo", "filtros": <filtros activos> }` |
| Gráfica 1: coberturas con mayor valor | `{ "medida": <medida elegida>, "filas": <nivel de filas>, "filtros": <filtros activos>, "orden": "valor_desc", "limite": 12 }` |
| Gráfica 2: % de eventos con cobertura informada por región | `{ "medida": "eventos", "filas": "territorio.region", "columnas": "cobertura.grupo", "filtros": <filtros activos sin los de cobertura> }` |

SQL de la matriz inicial (sin filtros):

```sql
SELECT b.grupo_cobertura AS fila, r.h_region AS col, SUM(f.area_total_ha) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_territorio r ON f.territorio_key = r.territorio_key
JOIN dim_cobertura b ON f.cobertura_key = b.cobertura_key
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
```

### Cómo se calculan los indicadores y sus denominadores

Los tres indicadores se obtienen de la consulta por grupo de cobertura con los filtros activos. El grupo "No informada" es el área o los eventos sin cobertura informada.

| Indicador | Cálculo | Denominador |
|---|---|---|
| Hectáreas con cobertura informada | hectáreas totales − hectáreas de "No informada" | Hectáreas totales de la selección |
| Eventos con cobertura informada | 100 × (eventos − eventos "No informada") ÷ eventos | Eventos de la selección (incluye los que no tienen área) |
| Hectáreas sin cobertura informada | hectáreas de "No informada" | Hectáreas totales de la selección |

La gráfica 2 no aplica los filtros de cobertura (`cobertura.grupo` y `cobertura.tipo`): su denominador es el total de eventos de cada región, y si se filtrara por un grupo el porcentaje sería siempre 100 %. Excluye "Sin region" (43 eventos sin departamento) del texto que compara regiones, porque no es una región.

### Valores de control (sin filtros)

La vista coincide con los valores de control calculados con pandas sobre el CSV tratado:

| Grupo de cobertura | Eventos | Hectáreas |
|---|---|---|
| No informada | 20.448 | 943.500 |
| Sin determinar | 8.495 | 475.905 |
| Vegetacion arbustiva y seca | 1.622 | 15.083 |
| Bosques | 1.533 | 62.590 |
| Pastos y sabanas | 1.531 | 55.063 |
| Varios tipos | 1.285 | 48.925 |
| Cultivos | 313 | 6.891 |
| Paramos | 128 | 4.962 |
| **Total** | **35.355** | **1.612.918** |

Eventos con cobertura informada por región (todos los años): Amazonia 56,3 % (513 de 912), Andina 46,8 % (10.994 de 23.469), Insular 40,5 % (15 de 37), Orinoquia 37,5 % (1.393 de 3.714), Pacifica 29,8 % (998 de 3.347) y Caribe 25,9 % (994 de 3.833).

## 2. Drill-down (grupo → tipo de cobertura)

- **Dimensiones y medida:** cobertura y territorio; hectáreas.
- **Nivel y filtros:** de grupo a tipo, con grupo de cobertura = Bosques.
- **Procedimiento:** con "Ejemplo: grupos por región", hacer clic en "Bosques" (o usar "Drill-down filas"). La vista agrupa por `cobertura.tipo`, agrega el filtro `cobertura.grupo = Bosques` y **vuelve a ejecutar** la consulta, de modo que las hectáreas, los eventos y los porcentajes se recalculan en el nuevo nivel.
- **Especificación:** `{ "medida": "hectareas", "filas": "cobertura.tipo", "columnas": "territorio.region", "filtros": { "cobertura.grupo": ["Bosques"] } }`

```sql
SELECT b.tipo_cobertura AS fila, r.h_region AS col, SUM(f.area_total_ha) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_territorio r ON f.territorio_key = r.territorio_key
JOIN dim_cobertura b ON f.cobertura_key = b.cobertura_key
WHERE b.grupo_cobertura IN (?)
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
-- parámetros: ['Bosques', 50000]
```

Resultado (todas las regiones, todos los años):

| Tipo de cobertura | Hectáreas | Eventos | Eventos con área |
|---|---|---|---|
| Bosque natural denso | 36.436,1 | 841 | 841 |
| Bosque intervenido | 19.838,1 | 342 | 342 |
| Bosque plantado | 3.882,9 | 218 | 217 |
| Bosque seco | 2.432,8 | 132 | 132 |
| **Bosques (grupo)** | **62.589,9** | **1.533** | **1.532** |

- **Interpretación:** el grupo Bosques (62.590 ha) se descompone en cuatro tipos; el bosque natural denso aporta el 58 % de sus hectáreas. Las medidas son aditivas, por eso los tipos suman el grupo. El mismo control permite bajar de región a departamento con "Drill-down columnas".

## 3. DICE (varias dimensiones a la vez)

- **Dimensiones y medida:** cobertura, territorio y tiempo; hectáreas, con eventos y eventos con área como denominadores.
- **Nivel y filtros:** filas en tipo de cobertura y columnas en región, con tres filtros combinados: región en {Orinoquia, Andina}, grupo de cobertura = Bosques y año de 2010 a 2020.
- **Procedimiento:** botón "Ejemplo DICE: bosques en Orinoquia y Andina". El filtro de año lista los 11 años (2010 a 2020) porque el catálogo acepta listas de valores y no rangos. Las hectáreas por evento se calculan como hectáreas ÷ eventos con área de cada celda.
- **Especificación:**

```json
{
  "medida": "hectareas",
  "filas": "cobertura.tipo",
  "columnas": "territorio.region",
  "filtros": {
    "territorio.region": ["Orinoquia", "Andina"],
    "cobertura.grupo": ["Bosques"],
    "tiempo.anio": ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"]
  }
}
```

```sql
SELECT b.tipo_cobertura AS fila, r.h_region AS col, SUM(f.area_total_ha) AS valor, SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area
FROM fact_incendio f
JOIN dim_tiempo t ON f.tiempo_key = t.tiempo_key
JOIN dim_territorio r ON f.territorio_key = r.territorio_key
JOIN dim_cobertura b ON f.cobertura_key = b.cobertura_key
WHERE r.h_region IN (?, ?) AND b.grupo_cobertura IN (?) AND t.h_anio IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
GROUP BY fila, col
ORDER BY fila, col
LIMIT ?
-- parámetros: ['Orinoquia', 'Andina', 'Bosques', '2010', ..., '2020', 50000]
```

Resultado:

| Tipo de bosque | Región | Hectáreas | Eventos | Con área | Ha por evento |
|---|---|---|---|---|---|
| Bosque intervenido | Andina | 4.966,5 | 290 | 290 | 17,1 |
| Bosque intervenido | Orinoquia | 10.375,2 | 23 | 23 | 451,1 |
| Bosque natural denso | Andina | 19.418,6 | 688 | 688 | 28,2 |
| Bosque natural denso | Orinoquia | 12.611,5 | 76 | 76 | 165,9 |
| Bosque plantado | Andina | 2.722,7 | 187 | 186 | 14,6 |
| Bosque plantado | Orinoquia | 444,0 | 2 | 2 | 222,0 |
| Bosque seco | Andina | 1.655,2 | 81 | 81 | 20,4 |
| Bosque seco | Orinoquia | 332,5 | 4 | 4 | 83,1 |
| **Bosques, Andina** | | **28.763,1** | **1.246** | **1.245** | **23,1** |
| **Bosques, Orinoquia** | | **23.763,2** | **105** | **105** | **226,3** |

- **Interpretación:** con el corte combinado, Andina tiene unas 12 veces más eventos en bosque (1.246 frente a 105), pero las hectáreas son del mismo orden (28.763 ha y 23.763 ha); por eso el área promedio por evento es mucho mayor en Orinoquia. Las ha por evento son razones: se recalculan en cada celda y no se suman. Los tipos con pocos eventos (bosque plantado en Orinoquia, 2; bosque seco, 4) tienen promedios inestables.

## 4. Roll-up y pivot

La barra de controles también permite:

- **Roll-up:** subir de tipo a grupo (`cobertura.tipo` → `cobertura.grupo`) o de departamento a región. Es la operación inversa al drill-down y vuelve a agrupar y a calcular.
- **Pivot:** intercambiar filas y columnas (región en filas y grupo de cobertura en columnas). Se ejecuta de nuevo la consulta con los dos niveles intercambiados.

## 5. Filtros de la vista

Año (`tiempo.anio`) y clase de tamaño (`tamano.clase`): son de dimensiones diferentes. La selección activa (nivel de filas, nivel de columnas y filtros) se muestra como chips, y el botón "Ver consulta SQL" muestra el SQL y los parámetros de la matriz.

Ejemplo "Solo 2010-2020": filtra `tiempo.anio` a los años 2010-2020 para comparar periodos equivalentes. Con ese filtro, la cobertura está informada en 14.907 de 22.734 eventos (65,6 %) y en 69,2 % de las hectáreas, frente a 42,2 % de los eventos sin filtro.

## 6. Paridad entre los dos modos

Las mismas especificaciones se ejecutaron en modo API (`python run.py`) y en el sitio estático con sql.js (`python freeze.py` y un servidor local sobre `build/`). Los indicadores, la matriz inicial y la consulta DICE dieron los mismos valores en ambos modos.
