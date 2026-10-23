# Conocimientos evidentes: comportamiento temporal

## Conocimiento 1: 2024 rompe el patrón anual de los eventos reportados

1. **Pregunta:** ¿Cómo ha cambiado el número de eventos reportados por año entre 2010 y 2024?
2. **Variables:** `ANIO` (tabla `Dim_Periodo`) y conteo de eventos (`Total Eventos`).
3. **Procedimiento:** Conté los eventos por año con `Total Eventos` y calculé la variación de 2024 frente a 2023 con `P3_Variacion Interanual`, con los filtros en "Todos" (base: 35.338 eventos con año y mes válidos).
4. **Evidencia:** Gráfico "Eventos reportados por año" y tarjetas de último año, año anterior y variación.
5. **Hallazgo:** Hasta 2023 los eventos por año oscilan entre 816 (2011) y 3.180 (2019). 2024 registra 7.785, un 168,6 % más que 2023 (2.898) y el 22 % de todos los eventos del periodo. Con el filtro Cundinamarca la variación es +78,5 % (de 438 a 782).
6. **Interpretación:** 2024 rompe el patrón de los años anteriores. Como la hoja de 2024 es la única con la columna `ENTIDAD_REPORTA` (90 % UNGRD), el salto puede reflejar un cambio en quién y cómo se reporta y no solo más incendios (hipótesis).
7. **Utilidad:** Antes de afirmar que los incendios aumentan, conviene revisar el procedimiento de reporte de 2024; las cifras sirven para dimensionar la carga de eventos que deben atender las entidades.
8. **Limitación:** Eventos reportados no equivalen a incendios ocurridos; 17 eventos sin año o mes válido no se incluyen; los datos no permiten comprobar la causa del salto.

## Conocimiento 2: los eventos se concentran en dos temporadas, cada año

1. **Pregunta:** ¿Hay meses del año en que se concentran los eventos?
2. **Variables:** `MES_NOMBRE` (tabla `Dim_Periodo`) y conteo de eventos.
3. **Procedimiento:** Calculé el porcentaje de eventos de cada mes sobre el total de todos los años con `P3_% Eventos por Mes` (filtros en "Todos") y revisé en la matriz año y mes si el patrón se repite cada año.
4. **Evidencia:** Gráfico "Eventos por mes" y matriz "Eventos por año y mes".
5. **Hallazgo:** Enero (21,7 %), febrero (20,4 %) y marzo (12,7 %) reúnen alrededor del 55 % de los eventos; julio (6,1 %), agosto (12,5 %) y septiembre (13,4 %), alrededor del 32 %. Mayo (1,4 %), junio (1,7 %) y noviembre (0,6 %) son los meses con menos eventos. En los 15 años, los tres meses con más eventos siempre están dentro de enero a marzo o de julio a septiembre.
6. **Interpretación:** Hay dos temporadas de mayor reporte, separadas por un valle entre abril y junio; el patrón se repite año tras año y no depende de un año en particular.
7. **Utilidad:** Permite concentrar la preparación (brigadas, alertas, restricción de quemas) antes de enero y de julio.
8. **Limitación:** Describe cuándo se reportan los eventos, no por qué; la relación con la temporada seca es una hipótesis. No incluye los 17 eventos sin año o mes válido.

## Conocimiento 3: 2010 no es comparable como año completo

1. **Pregunta:** ¿Son comparables todos los años del periodo?
2. **Variables:** `ANIO`, `MES_NOMBRE` y conteo de eventos.
3. **Procedimiento:** Revisé en la matriz año y mes cuántos eventos tiene cada mes de cada año y comparé la distribución de 2010 con la de los demás años; con el segmentador de mes se comparan los mismos meses entre años.
4. **Evidencia:** Matriz "Eventos por año y mes" y gráfico por año con el segmentador de mes.
5. **Hallazgo:** En 2010, enero a marzo reúnen 2.269 de sus 2.322 eventos (97,7 %) y de abril a diciembre solo hay 53. De julio a septiembre 2010 tiene 13 eventos, mientras que ningún otro año baja de 215. Comparando solo enero a marzo, 2024 tiene 4.777 eventos y 2023, 1.449 (+229,7 %).
6. **Interpretación:** 2010 parece tener cobertura de reporte parcial (hipótesis), así que su total anual (2.322) no es comparable con el de años completos.
7. **Utilidad:** Al medir tendencias hay que comparar periodos equivalentes (los mismos meses) y marcar o excluir 2010, para no concluir que fue un año moderado cuando solo se observa un trimestre.
8. **Limitación:** No se sabe si abril a diciembre de 2010 casi no tiene eventos por reporte incompleto o por ausencia real; los datos no explican cómo se registró cada año.

## Limitación y decisión de la página

- **Limitación:** Eventos reportados no equivalen a incendios ocurridos. El salto de 2024 (7.785 frente a 2.898) coincide con una hoja de datos distinta, la única con la columna `ENTIDAD_REPORTA` (90 % UNGRD), por lo que puede reflejar un cambio en quién y cómo se reporta (hipótesis). 2010 parece tener cobertura parcial (casi todo entre enero y marzo) y no es comparable como año completo.
- **Posible decisión:** Concentrar la preparación (brigadas, alertas y restricción de quemas) en enero a marzo y julio a septiembre, que reúnen cerca del 87 % de los eventos, y estandarizar el procedimiento de reporte entre años antes de usar las cifras anuales para decidir si los incendios aumentan.
