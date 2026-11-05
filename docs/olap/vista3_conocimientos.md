# Vista 3: conocimientos multidimensionales

Vista: `/etapa-5/vista-3/` (Cobertura y territorio). Todas las cifras salen de consultas al modelo estrella (`incendios_dw.db`) y se pueden reproducir con los botones de ejemplo de la vista. Las consultas están en [vista3_consultas.md](vista3_consultas.md).

Recordatorio de lectura: las hectáreas de esta vista son el **área total del evento** asignada a su cobertura. No son comparables con las hectáreas por cobertura de la Etapa 4 (669.358 ha), que sumaban las columnas `COB_*`.

## Conocimiento 1. La región mejor informada cambia al comparar solo los años con registro de cobertura

1. **Pregunta:** ¿En qué regiones está mejor informada la cobertura y el orden se mantiene si se comparan solo los años en que la cobertura existe?
2. **Dimensiones y medidas:** cobertura (grupo), territorio (región) y tiempo (año); eventos con cobertura informada sobre el total de eventos de la región.
3. **Procedimiento:**
   - Primera lectura, sin filtros: botón "Ejemplo: grupos por región" y medida eventos (filas en grupo de cobertura, columnas en región). La segunda gráfica calcula 100 × (eventos − eventos "No informada") ÷ eventos de cada región.
   - Segunda lectura, periodos equivalentes: botón "Ejemplo: solo 2010-2020", que filtra `tiempo.anio` a los años 2010 a 2020 y vuelve a calcular el porcentaje.
   - Las dos lecturas usan el mismo nivel (región) y cambian solo el filtro de año. La gráfica no aplica filtros de cobertura, para que el denominador sea el total de eventos de la región.
4. **Evidencia:** matriz de grupo de cobertura × región y gráfica "Eventos con cobertura informada por región (%)" de la Vista 3, sin filtros y con el filtro de años.
5. **Hallazgo:**

   | Región | Todos los años | Años 2010-2020 |
   |---|---|---|
   | Amazonia | 56,3 % (513 de 912) | 82,1 % (513 de 625) |
   | Andina | 46,8 % (10.994 de 23.469) | 67,1 % (10.994 de 16.377) |
   | Orinoquia | 37,5 % (1.393 de 3.714) | 63,1 % (1.393 de 2.207) |
   | Caribe | 25,9 % (994 de 3.833) | 59,1 % (994 de 1.683) |
   | Pacifica | 29,8 % (998 de 3.347) | 56,0 % (998 de 1.782) |

   Insular (37 eventos) queda en 40,5 % con todos los años y en 75,0 % con 2010-2020; se omite del análisis por su tamaño.
6. **Interpretación:** los 12.621 eventos de las hojas 2021-2024 no registran cobertura y bajan el porcentaje de todas las regiones. Al compararlas en periodos equivalentes, Pacifica pasa a ser la región con menos cobertura informada (56,0 %) y Caribe deja de ser la última (59,1 %). Frente al conocimiento evidente, que daba un único 42,2 % de eventos con cobertura para todo el país, el aporte es medir ese vacío por región y en periodos comparables. El orden con todos los años describe en parte qué hojas pesan en cada región y no solo la calidad del registro.
7. **Utilidad:** indica en qué regiones el análisis por cobertura es más confiable (Amazonia, Andina) y dónde conviene mejorar el registro (Pacifica, Caribe y Orinoquia).
8. **Limitación:** "informada" no significa "bien clasificada": el 71,1 % de las hectáreas con cobertura queda en "Sin determinar". La región es una asignación simplificada por departamento, y los porcentajes de 2010-2020 no dicen por qué cambió el registro en cada región (sería una hipótesis).

## Conocimiento 2. En los bosques, Orinoquia tiene pocos eventos pero mucha más área por evento que Andina

1. **Pregunta:** ¿Los incendios en bosque tienen el mismo tamaño en Orinoquia y en Andina?
2. **Dimensiones y medidas:** cobertura (grupo Bosques y sus tipos), territorio (región) y tiempo (año); hectáreas, eventos y eventos con área.
3. **Procedimiento:** operación DICE con el botón "Ejemplo DICE: bosques en Orinoquia y Andina":
   - Filtros combinados: región en {Orinoquia, Andina}, grupo de cobertura = Bosques y año de 2010 a 2020.
   - Niveles: filas en tipo de cobertura (se bajó de grupo a tipo con drill-down) y columnas en región.
   - Cálculo: hectáreas por evento = hectáreas ÷ eventos con área de cada celda.
4. **Evidencia:** matriz tipo de bosque × región de la Vista 3 con la selección DICE activa, con la medida hectáreas y con la medida eventos (SQL y parámetros en "Ver consulta SQL").
5. **Hallazgo:** Orinoquia suma 23.763,2 ha en 105 eventos (226,3 ha por evento); Andina suma 28.763,1 ha en 1.246 eventos, 1.245 con área (23,1 ha por evento). Por tipo, el bosque natural denso registra 165,9 ha por evento en Orinoquia (12.611,5 ha en 76 eventos) y 28,2 ha en Andina (19.418,6 ha en 688 eventos); el bosque intervenido, 451,1 ha (10.375,2 ha en 23 eventos) y 17,1 ha (4.966,5 ha en 290 eventos).
6. **Interpretación:** Andina tiene unas 12 veces más eventos en bosque (1.246 frente a 105), pero las hectáreas son del mismo orden: los incendios en bosque de Orinoquia son mucho más extensos. Frente al conocimiento evidente, que ordenaba regiones por hectáreas y por eventos sin mirar la cobertura, el aporte es mostrar que el tamaño típico de un incendio en bosque depende de la región. La diferencia es una asociación: los datos no explican por qué.
7. **Utilidad:** sugiere preparar la respuesta ante pocos eventos extensos en los bosques de Orinoquia y ante muchos eventos pequeños en los de Andina.
8. **Limitación:** algunos tipos tienen muy pocos eventos (bosque plantado: 2 en Orinoquia; bosque seco: 4), así que sus promedios son inestables. El área es la total del evento y no solo la de bosque, y la selección cubre solo los eventos con cobertura informada en 2010-2020.
