# Conocimientos evidentes: composición de la población

## Conocimiento 1: pocos incendios grandes concentran casi toda el área quemada

1. **Pregunta:** ¿Qué tan concentrada está el área quemada según el tamaño de los incendios?
2. **Variables:** `AREA_TOTAL_HA_NUM` y `CLASE_TAMANO` (≤ 1, 1–10, 10–100 y > 100 ha).
3. **Procedimiento:** Clasifiqué los 34.580 eventos con área informada en 4 clases y calculé el porcentaje de eventos (base: 34.580) y el porcentaje de hectáreas (base: 1.612.918 ha) de cada clase, con las medidas `P1_% Eventos por Clase` y `P1_% Hectareas por Clase`.
4. **Evidencia:** Gráfico "Tamaño del incendio: % de eventos y % de hectáreas" y tarjetas de mediana (2,0 ha) y promedio (46,6 ha).
5. **Hallazgo:** El 78,9 % de los eventos (27.280) tiene 10 ha o menos y aporta solo el 4,3 % de las hectáreas. Los 1.674 eventos de más de 100 ha (4,8 %) concentran el 83,4 % de las hectáreas (1.344.791 ha).
6. **Interpretación:** La distribución es muy asimétrica: el promedio (46,6 ha) no describe un incendio típico, la mediana (2,0 ha) sí.
7. **Utilidad:** Permite priorizar la detección temprana y la respuesta rápida para evitar que un incendio crezca, y reportar la mediana junto al promedio.
8. **Limitación:** 775 eventos (2,2 %) no tienen área y quedan fuera. El área es la reportada y los datos no explican por qué algunos incendios llegan a ser grandes.

## Conocimiento 2: la cobertura afectada se desconoce en la mayor parte del área

1. **Pregunta:** ¿Qué tipos de cobertura vegetal concentran las hectáreas afectadas?
2. **Variables:** `TIPO_COBERTURA` y `HECTAREAS` (tabla `Coberturas`, solo valores mayores que 0).
3. **Procedimiento:** Pasé las 11 columnas de cobertura a filas (evento y tipo), descarté nulos y ceros y calculé el porcentaje de hectáreas de cada tipo con `P1_% Hectareas por Cobertura`. Denominador: 669.358 ha de los 14.907 eventos que informan cobertura.
4. **Evidencia:** Gráfico "Hectáreas afectadas por tipo de cobertura" y tarjeta "Con cobertura registrada" (42,2 %).
5. **Hallazgo:** "Cobertura sin determinar" reúne el 71,2 % de las hectáreas (476.662 ha). Entre las identificadas están sabanas y pastizales (7,1 %), bosque natural denso (6,0 %) y pastos manejados (4,3 %). Rastrojo tiene más eventos (2.225) pero solo el 3,6 % de las hectáreas.
6. **Interpretación:** Para la mayor parte del área no se determinó la cobertura; las comparaciones entre tipos describen solo la parte identificada.
7. **Utilidad:** Reforzar el diligenciamiento de la cobertura en el reporte permitiría priorizar la protección por tipo de vegetación.
8. **Limitación:** Solo el 42,2 % de los eventos informa cobertura y todos son de 2010-2020. No se puede saber qué cobertura se quema más hoy ni qué parte de cada cobertura existente se afectó.

## Conocimiento 3: la intencionalidad es la causa más registrada, pero la causa casi no se informa

1. **Pregunta:** ¿Qué causas se registran con más frecuencia y qué parte de los eventos las informa?
2. **Variables:** `TIPO_CAUSA` (tabla `Causas`, solo marcas afirmativas).
3. **Procedimiento:** Pasé las 6 columnas de causa a filas, descarté nulos, ceros y valores no informativos ("Sin definir") y conté eventos distintos por causa con `P1_% Eventos por Causa`. Denominador: 4.148 eventos con causa; un evento puede tener varias.
4. **Evidencia:** Gráfico "Eventos por tipo de causa" y tarjeta "Con causa registrada" (11,7 %).
5. **Hallazgo:** Intencional 34,1 % (1.415 eventos), quema fuera de control 24,2 % (1.005), descuido o negligencia 14,6 % (605), accidental 14,6 % (605) y reactivación de focos 1,3 % (54). Solo 4.148 de 35.355 eventos (11,7 %) tienen causa. En Cundinamarca predomina el descuido o negligencia (41,6 %; base: 269 eventos).
6. **Interpretación:** Entre los eventos con causa informada pesan las causas asociadas a actividad humana (intencional, quemas fuera de control, descuido), y el patrón cambia según el departamento.
7. **Utilidad:** Orienta la prevención según el departamento (en Cundinamarca, al descuido) y justifica exigir la causa en el reporte.
8. **Limitación:** El 88,3 % de los eventos no tiene causa (ninguna en 2023 y 2024), las marcas no son homogéneas entre hojas y la causa reportada puede no ser la real. No se puede inferir causalidad.

## Limitación y decisión de la página

- **Limitación:** Causa y cobertura solo se registraron en las hojas 2010-2020 (17,7 % y 65,6 % de esos eventos); en 2023 y 2024 no hay ninguna. Por eso estas composiciones describen sobre todo 2010-2020, y el 71,2 % de las hectáreas con cobertura está "sin determinar". Son descripciones y no explican causas.
- **Posible decisión:** Concentrar la prevención y la capacidad de respuesta en evitar que los incendios superen las 100 ha (4,8 % de los eventos, 83,4 % del área), y hacer obligatorios la causa y la cobertura en el reporte, porque hoy solo se conoce la causa de 11,7 % de los eventos.
