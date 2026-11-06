# Vista 2: conocimientos multidimensionales

## Conocimiento 1. La inversión de 2024 no es un caso aislado
1. **Pregunta:** al comparar la misma temporada entre años, ¿enero-marzo tiene siempre una proporción de incendios grandes mayor que julio-septiembre?
2. **Dimensiones y medidas:** tiempo (año y temporada; enero-marzo equivale al trimestre 1 y julio-septiembre al trimestre 3) y tamaño; % de eventos grandes (base: eventos con área de cada año y temporada).
3. **Procedimiento:** sin filtros; filas = `tiempo.anio`, columnas = `tiempo.temporada`, medida = `pct_grandes` (botón "Ejemplo: misma temporada entre años"). Después, slice año = 2024 con filas en trimestre.
4. **Evidencia:** matriz año x temporada y gráfica de líneas por temporada de la Vista 2.
5. **Hallazgo:** en 12 de los 15 años, enero-marzo tiene un % de grandes igual o mayor que julio-septiembre (por ejemplo, 2022: 12,1 %, 71 de 588, contra 5,1 %, 11 de 215). La relación se invierte en 2015 (3,4 % contra 4,0 %), 2023 (3,4 %, 49 de 1.448, contra 5,3 %, 54 de 1.028) y 2024 (2,8 %, 135 de 4.776, contra 5,5 %, 109 de 1.983).
6. **Interpretación:** la inversión que la Etapa 4 encontró en 2024 ya aparecía en 2023 y en 2015, así que no es un caso aislado. Frente al conocimiento evidente, lo nuevo es comparar periodos equivalentes año por año, con el porcentaje recalculado en cada celda en lugar de un agregado por temporada.
7. **Utilidad:** indica que la preparación para incendios grandes no puede concentrarse solo en enero-marzo; en los últimos años julio-septiembre también exige atención.
8. **Limitación:** 2010 tiene casi todo su reporte entre enero y marzo (2.269 de 2.322 eventos con área) y julio-septiembre de ese año solo tiene 13 eventos con área, por lo que su comparación es poco confiable. En grupos pequeños, pocos eventos cambian mucho el porcentaje.

## Conocimiento 2. Dentro de una misma entidad también se invierte la proporción
1. **Pregunta:** ¿la inversión de 2024 se explica por quién reporta?
2. **Dimensiones y medidas:** fuente (hoja → entidad que reporta) y tiempo (temporada); % de eventos grandes y eventos con área.
3. **Procedimiento:** slice año = 2024; filas = `fuente.entidad`, columnas = `tiempo.temporada`, medida = `pct_grandes` (botón "Ejemplo: entidad que reporta en 2024"). Se lee la fila de UNGRD, que reporta 7.031 de los 7.786 eventos de la hoja 2024. Se contrasta con la fila 2023 de la matriz año x temporada.
4. **Evidencia:** matriz entidad x temporada para 2024 y matriz año x temporada.
5. **Hallazgo:** solo dentro de UNGRD, el % de grandes es 3,0 % en enero-marzo (128 de 4.233 eventos con área) y 4,8 % en julio-septiembre (88 de 1.819). La hoja 2023, que no tiene campo de entidad, ya muestra la misma inversión (3,4 % contra 5,3 %).
6. **Interpretación:** si la inversión se debiera solo a una mezcla distinta de entidades, no aparecería dentro de una sola entidad. Por eso la hipótesis de la Etapa 4 (cambio en quién reporta) pierde fuerza como explicación única, aunque no se descarta, porque la entidad solo existe en 2024 y no se puede comparar con años anteriores. Es una asociación, no una causa.
7. **Utilidad:** evita atribuir el cambio solo a la fuente y sugiere revisar también factores propios del periodo, como hipótesis por comprobar con otros datos.
8. **Limitación:** las otras entidades tienen pocos eventos por temporada (por ejemplo, CAM tiene 68 eventos con área en julio-septiembre), así que sus porcentajes no son comparables con los de UNGRD.

## Limitación de la vista
La cantidad de eventos reportados cambia mucho entre años y hojas (1.003 eventos con área en 2022 contra 7.784 en 2024). Un reporte más amplio incluye más incendios pequeños y puede bajar el % de grandes sin que cambien los incendios. Por eso el promedio de hectáreas por evento de 2021 y 2022 (110,2 y 155,7 ha) no es directamente comparable con el de 2024 (39,7 ha). SQLite no calcula medianas, así que el promedio, muy sensible a unos pocos eventos enormes, no se complementa con la mediana.

## Posible decisión
Mantener la capacidad de respuesta a incendios grandes también en julio-septiembre, no solo en enero-marzo, porque en 2023 y 2024 ese trimestre tuvo la mayor proporción de eventos de más de 100 ha. Antes de comparar años, pedir a las entidades un criterio de reporte común para que el aumento de eventos pequeños no oculte la tendencia.
