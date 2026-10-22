# Conocimientos evidentes: comparación territorial

## Conocimiento 1: concentración por departamento

1. **Pregunta:** ¿Qué departamentos concentran más eventos?
2. **Variables:** `DEPARTAMENTO_NORM` y conteo de eventos (`ANIO` y `MES_NOMBRE` como filtros).
3. **Procedimiento:** Conté los eventos por departamento con la medida `Total Eventos`, los ordené de mayor a menor y tomé los 10 primeros. El porcentaje se calcula sobre los 35.355 eventos, con los filtros en "Todos".
4. **Evidencia:** Gráfico "Eventos por departamento, top 10" y tarjeta del porcentaje de eventos en los 5 departamentos con más registros.
5. **Hallazgo:** Cundinamarca tiene 5.938 eventos (16,8 %) y Huila 4.866 (13,8 %), seguidos de Antioquia (3.022), Boyacá (2.715) y Tolima (2.695). Los cinco suman 19.236, es decir, 54,4 % de 35.355. En total hay 33 departamentos con eventos.
6. **Interpretación:** Más de la mitad de los eventos reportados se concentra en 5 de 33 departamentos. Huila supera a Antioquia, aunque Antioquia es mucho más extenso.
7. **Utilidad:** Permite priorizar los departamentos donde conviene enfocar la revisión y la prevención.
8. **Limitación:** Son conteos absolutos, no tasas, y más eventos puede deberse a más reporte. Los 43 eventos sin departamento no se incluyen.

## Conocimiento 2: tamaño típico por departamento

1. **Pregunta:** ¿Los departamentos con más eventos son también los de incendios más grandes?
2. **Variables:** `DEPARTAMENTO_NORM` y `AREA_TOTAL_HA_NUM`.
3. **Procedimiento:** Calculé la mediana de hectáreas por departamento, solo con los que tienen 100 o más eventos con área registrada, y muestro los 10 con mayor mediana, incluidos los empates.
4. **Evidencia:** Gráfico "Mediana de hectáreas por evento, departamentos con 100 o más eventos con área".
5. **Hallazgo:** Meta tiene mediana de 10 ha (1.358 eventos con área), Arauca 8 (437), Vichada 7 (360) y Casanare 6 (1.485). Meta es octavo en cantidad (1.404 eventos), pero primero en mediana. Ninguno de los cinco departamentos con más eventos aparece entre los 12 de mayor mediana.
6. **Interpretación:** La cantidad de eventos y el tamaño típico no van de la mano: los departamentos de la Orinoquía tienen incendios típicos más grandes que los que más reportan.
7. **Utilidad:** Ayuda a distinguir dónde el problema es la frecuencia y dónde es el tamaño, para orientar acciones distintas.
8. **Limitación:** Solo cuenta eventos con área registrada; 775 registros de la base no la tienen. Además, se consideran departamentos con 100 o más eventos. La mediana no muestra los incendios muy grandes y varios departamentos empatan en 3 ha.

## Conocimiento 3: dispersión por municipio

1. **Pregunta:** ¿Los incendios se concentran en pocos municipios?
2. **Variables:** `MUNICIPIO_NORM` y conteo de eventos.
3. **Procedimiento:** Conté los eventos por municipio y tomé los 10 primeros. Power BI agrupa los nombres sin distinguir mayúsculas; por ejemplo, Neiva y NEIVA suman 654. El denominador es 35.355.
4. **Evidencia:** Gráfico "Eventos por municipio, top 10".
5. **Hallazgo:** Neiva lidera con 654 eventos (1,8 %), seguida de Yopal (406), Bello (396), Palermo (371) y Bogotá, D.C. (365). Los 10 municipios con más eventos suman 3.595, el 10,2 % de 35.355. Hay 1.173 nombres de municipio distintos.
6. **Interpretación:** A diferencia de los departamentos, los eventos están muy repartidos entre municipios: ninguno pasa del 2 % del total.
7. **Utilidad:** Indica que enfocarse en pocos municipios cubriría una parte pequeña del total, así que conviene mirar zonas más amplias.
8. **Limitación:** Un mismo municipio escrito con tildes distintas se cuenta por separado (979 nombres si se ignoran las tildes), y municipios con el mismo nombre en departamentos distintos se juntan en el gráfico.