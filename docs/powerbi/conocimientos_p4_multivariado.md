# Conocimientos evidentes: análisis multivariado

## Conocimiento 1: cada región arde en su propia época, los llanos a inicio de año y Tolima y Huila a mitad

1. **Pregunta:** ¿Las hectáreas quemadas se reparten igual entre departamentos y épocas del año?
2. **Variables:** `DEPARTAMENTO_NORM`, `TEMPORADA` (derivada del mes: enero a marzo, julio a septiembre y resto) y `AREA_TOTAL_HA_NUM`.
3. **Procedimiento:** Crucé los 8 departamentos con más hectáreas con las 3 temporadas, sumando hectáreas con `Hectareas Totales`, con los filtros en "Todos".
4. **Evidencia:** Matriz "Hectáreas por departamento y temporada" y tarjeta "% de las hectáreas en enero-marzo" (65,2 %).
5. **Hallazgo:** Vichada (235.367 de 306.775 ha), Casanare (222.521 de 247.754), Meta (116.730 de 123.307) y Arauca (114.250 de 118.746) concentran su área en enero a marzo. Tolima (111.035 de 125.497) y Huila (98.853 de 118.601) la concentran en julio a septiembre. Enero a marzo reúne el 65,2 % de todas las hectáreas.
6. **Interpretación:** La época de mayor área quemada depende de la región: los llanos orientales arden a comienzos de año y Tolima y Huila a mitad de año (hipótesis: ciclos de sequía distintos por región).
7. **Utilidad:** Permite programar brigadas y alertas por región y por época, y no con un único calendario nacional.
8. **Limitación:** Son hectáreas absolutas (no consideran la extensión de cada departamento) y una asociación observada, no una causa. La matriz muestra solo los 8 departamentos con más hectáreas (73,8 % del área).

## Conocimiento 2: la temporada casi no cambia el tamaño de los incendios, salvo la proporción de los grandes

1. **Pregunta:** ¿Cambia el tamaño de los incendios según la época del año?
2. **Variables:** `TEMPORADA`, `CLASE_TAMANO_ORD` y conteo de eventos.
3. **Procedimiento:** Calculé, dentro de cada temporada, el porcentaje de eventos de cada clase de tamaño con `P4_% Eventos por Tamano` (base: eventos con área de esa temporada: 19.001, 11.012 y 4.553).
4. **Evidencia:** Gráfico "Tamaño de los eventos por temporada".
5. **Hallazgo:** En las tres temporadas entre 35,5 % y 38,8 % de los eventos tiene 1 ha o menos y cerca del 43 % tiene entre 1 y 10 ha. Los eventos de más de 100 ha son el 5,5 % en enero a marzo, el 4,3 % en julio a septiembre y el 3,3 % en el resto del año. En 2024 se invierte: 5,5 % en julio a septiembre y 2,8 % en enero a marzo.
6. **Interpretación:** La época del año casi no cambia el tamaño típico del incendio; solo varía la proporción de los grandes, y de forma distinta según el año.
7. **Utilidad:** La temporada ayuda a prever cuántos incendios habrá y dónde, pero no cuán grandes serán; para evitar los grandes hay que mirar otros factores.
8. **Limitación:** Diferencias de uno o dos puntos porcentuales pueden deberse a variaciones del reporte; no se hizo una prueba estadística. Los 775 eventos sin área quedan fuera.

## Conocimiento 3: unos pocos eventos inusuales pesan mucho en el total de hectáreas

1. **Pregunta:** ¿Qué eventos son inusuales por su tamaño y cuánto pesan?
2. **Variables:** `ID_EVENTO`, `DEPARTAMENTO_NORM`, `MUNICIPIO_NORM`, `ANIO`, `MES_NORM`, `AREA_TOTAL_HA_NUM` y `AREA_TOTAL_ATIPICO`.
3. **Procedimiento:** Listé los 10 eventos de mayor área (con el empate en el puesto 10 salen 11) y revisé su ubicación, su fecha y la bandera de atípico de la Etapa 2 antes de considerarlos errores.
4. **Evidencia:** Tabla "Los 10 eventos de mayor área".
5. **Hallazgo:** Los 11 eventos van de 12.000 a 41.079 ha y todos están marcados como atípicos. Cinco son de Cumaribo (Vichada) y suman 142.550 ha, el 8,8 % de todas las hectáreas; dos ocurren en febrero de 2017 y dos en enero de 2022.
6. **Interpretación:** Pocos eventos pesan mucho en el total. Que varios caigan en el mismo municipio y mes sugiere un mismo incendio grande reportado en partes, y las cifras redondas (30.000, 20.000, 15.000 y 12.000 ha) sugieren estimaciones (hipótesis, sin comprobar).
7. **Utilidad:** Antes de usar estas cifras en reportes oficiales conviene verificarlas con las entidades que reportan, y mostrar la mediana junto al total.
8. **Limitación:** Los datos no permiten saber si son errores, estimaciones o incendios reales de esa magnitud; por eso no se eliminaron.

## Limitación y decisión de la página

- **Limitación:** Son hectáreas reportadas y no medidas. Unos pocos eventos extremos mueven mucho los totales (los 5 de Cumaribo suman el 8,8 % del área), por eso se muestran con sus datos y no se descartan como errores. Los departamentos se comparan en hectáreas absolutas, sin considerar su extensión. La relación entre región y temporada es una asociación observada; la explicación climática es una hipótesis.
- **Posible decisión:** Programar la preparación por región y época: brigadas y alertas en los llanos orientales (Vichada, Casanare, Meta y Arauca) antes de enero, y en Tolima y Huila antes de julio. Además, verificar con las entidades que reportan los eventos de más de 10.000 ha antes de usarlos en cifras oficiales.
