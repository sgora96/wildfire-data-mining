# Conclusiones integradas

Sección integradora de la Etapa 6 (Conocimiento Oculto). Se elabora con los resúmenes de las secciones 1 (YouTube), 2 (aprendizaje supervisado) y 3 (clustering), y con un cruce entre los resultados de las secciones 2 y 3 (`scripts/etapa6/cruce_resultados.py`). Toda cifra sale de esos informes o de ese cruce.

## 4.1 Nuevos conocimientos

1. **Los incendios más grandes no están donde hay más incendios.** Al cruzar los tres perfiles de departamentos (clustering) con la proporción de incendios grandes (más de 100 ha, supervisado), el grupo andino grande (A) reúne el 38,5 % de los eventos con área, pero solo el 14,6 % de los incendios grandes (1,84 % de sus eventos). El grupo de pico en enero-marzo con menos eventos (C) reúne el 27,4 % de los eventos y el **55,3 % de los incendios grandes** (9,77 % de sus eventos).

   | Grupo (clustering) | Eventos con área | Grandes | % grandes | % de los eventos | % de los grandes |
   |---|---|---|---|---|---|
   | A. Andinos grandes y extendidos | 13.301 | 245 | 1,84 % | 38,5 % | 14,6 % |
   | B. Pico en julio-septiembre | 11.759 | 504 | 4,29 % | 34,1 % | 30,1 % |
   | C. Pico en enero-marzo, menos eventos | 9.471 | 925 | 9,77 % | 27,4 % | 55,3 % |
   | **32 departamentos** | **34.531** | **1.674** | **4,85 %** | 100 % | 100 % |

2. **Dentro del grupo C, el tamaño se concentra en cinco departamentos, no en todo el grupo.** Vichada, Arauca, Casanare, Meta y Caquetá reúnen 663 de los 1.674 incendios grandes (39,6 %) con solo el 11,5 % de los eventos (3.988). El resto del grupo C tiene 4,78 % de incendios grandes (262 de 5.483), igual al promedio general (4,85 %). El grupo C incluye departamentos con casi ningún incendio grande (Risaralda 0,2 %, Bogotá 0,3 %, Atlántico 0,4 %, Guainía y Putumayo 0 %). Es decir, el calendario (enero-marzo) no basta para explicar el tamaño: el departamento pesa. Eso coincide con el modelo supervisado, donde el departamento es la variable más importante.
3. **El modelo supervisado sirve para priorizar, no para decidir.** Con año, mes, departamento y hoja de origen, la regresión logística balanceada detecta el 69,4 % de los incendios grandes (1.161 de 1.674; AUC 0,772), pero con una precisión de 11,1 % (9.274 falsas alarmas). Con datos de 2023-2024 el AUC baja a 0,70.
4. **Hay una brecha entre lo que se comenta y lo que se registra sobre las causas.** En 8 videos de YouTube, el 45 % de los comentarios (316 de 703; temas 2 y 3 de LDA) atribuye el incendio a una causa política o intencional, mientras el IDEAM solo registra la causa en el 11,7 % de los eventos (4.148 de 35.355) y no la registra en 2023-2024.
5. **Los videos analizados no tratan de los lugares donde se concentran los incendios grandes.** De los 8 videos, 4 se refieren a incendios en Tolima o en Jamundí (Valle del Cauca; grupo B), 2 a Villa de Leyva (Boyacá; grupo A) y 2 son generales. Ninguno trata de un departamento del grupo C (Llanos, Caribe y Amazonía).

## 4.2 Coincidencias y diferencias entre los análisis

| | Qué muestra | Con qué coincide o difiere |
|---|---|---|
| **Coincide** | El departamento es la señal más fuerte: en el modelo supervisado es la variable principal y las tasas más altas son Vichada (25,8 %), Arauca (21,1 %), Casanare (15,8 %), Meta (14,3 %) y Caquetá (14,1 %). | Esos cinco departamentos están todos en el grupo C del clustering, que además concentra el 55,3 % de los incendios grandes. |
| **Coincide** | La estacionalidad: el modelo supervisado da más peso a septiembre una vez descontado el departamento, y el clustering separa un grupo con pico en julio-septiembre (B) y otro con pico en enero-marzo (C). | Es el patrón que ya se veía en las Etapas 4 y 5 para Orinoquia (enero-marzo) y Andina (julio-septiembre). |
| **Difiere** | El grupo A (Cundinamarca, Antioquia, Boyacá y Santander) tiene la mayor cantidad de eventos y los más regulares entre años, pero la menor proporción de incendios grandes (1,84 %). | Frecuencia y tamaño no van juntos. |
| **Difiere** | Los comentarios de YouTube (8 videos) se centran en incendios de la zona andina; los datos del IDEAM sitúan más de la mitad de los incendios grandes (55,3 %) en el grupo C (Llanos, Caribe y Amazonía). | La conversación pública y el registro apuntan a lugares distintos. |
| **Difiere** | Los comentarios dan por hecha la intencionalidad con mucha seguridad. | El registro técnico desconoce la causa en casi nueve de cada diez eventos. |

## 4.3 Decisiones que podrían apoyarse

- **Priorizar la respuesta ante incendios extensos antes de enero** en Vichada, Arauca, Casanare, Meta y Caquetá, donde se concentra el 39,6 % de los incendios grandes del país con el 11,5 % de los eventos.
- **Preparar la zona andina por frecuencia y por temporada, no por tamaño:** antes de enero en el grupo A y antes de julio en el grupo B, sin dimensionarla como la zona de los incendios más extensos.
- **Usar el modelo como apoyo de priorización** (por ejemplo, ordenar departamentos y meses por riesgo), no como alarma automática: con una precisión de 11 %, el umbral debe ajustarse al costo real de una falsa alarma.
- **Mejorar el registro de la causa y de la cobertura.** Hoy faltan en la mayoría de los eventos y son justo lo que más se discute en la conversación pública.
- **Comunicar con cautela:** mientras no haya causa registrada, la atribución de intencionalidad que aparece en los comentarios no está respaldada por los datos.

## 4.4 Evidencia frente a hipótesis

| Respaldado por evidencia | Hipótesis que requiere validación |
|---|---|
| El grupo C concentra el 55,3 % de los incendios grandes con el 27,4 % de los eventos (cruce de los grupos con el archivo supervisado). | Que la concentración en esos departamentos se deba a vegetación de sabana abierta o a diferencias en la respuesta y el reporte: no se usaron datos de vegetación, clima ni capacidad de respuesta. |
| El departamento es la variable que más pesa para predecir un incendio grande (AUC 0,772; recall 0,694; precisión 0,111). | Que el modelo se sostenga en el tiempo: con 2023-2024 el AUC baja a 0,70-0,72. |
| Existen 3 perfiles de departamentos, estables frente al algoritmo (k = 3, silueta 0,429; índice de Rand ajustado 0,891 frente al jerárquico). | Que la estacionalidad de cada perfil se deba al régimen de lluvias: no se usaron datos climáticos. |
| El 45 % de los comentarios (316 de 703) atribuye el incendio a una causa política o intencional; el IDEAM registra la causa en el 11,7 % de los eventos. | Que los incendios sean realmente provocados: es una percepción de quienes comentaron, no un hecho verificado. |
| El tono de los comentarios varía mucho por video (sentimiento promedio de +5,66 a −6,01). | Que ese tono dependa del enfoque editorial de cada cobertura: con 8 videos, no se puede separar del evento ni del canal. |

## 4.5 Limitaciones del conjunto

- **Los datos del IDEAM describen eventos reportados**, y el reporte cambia entre hojas de origen y años; eso afecta a las secciones 2 y 3.
- **La muestra de YouTube es pequeña y sesgada:** 8 videos, uno de ellos (VANGUARDIA) con el 42,7 % de los comentarios, y son opiniones de quienes comentaron, no de toda la población.
- **Los periodos no coinciden:** los 8 videos se publicaron entre el 21 de agosto y el 20 de septiembre de 2026, y los datos del IDEAM llegan hasta 2024. El contraste entre comentarios y registro es de enfoque, no de los mismos incendios.
- **El cruce de las secciones 2 y 3 usa los 32 departamentos del clustering** (se excluye Vaupés, con 8 eventos, y los eventos sin departamento) y los eventos con área y año; es una asociación, no una causa.
- **Pocas variables:** causa y cobertura faltan en la mayoría de los eventos, y coordenadas y elevación son nulas en el 97 % de los casos.

## 4.6 Conclusión

El análisis de conocimiento oculto muestra que **el tamaño de un incendio se asocia más con dónde ocurre que con cuándo o con qué tan frecuentes sean los incendios**: cinco departamentos de Orinoquia y Amazonia (Vichada, Arauca, Casanare, Meta y Caquetá) concentran cerca del 40 % de los incendios grandes con una décima parte de los eventos, y los departamentos con más incendios (grupo andino) tienen la menor proporción de incendios grandes (1,84 %). Los comentarios de YouTube agregan algo que los datos no tienen, la narrativa pública sobre las causas, pero también muestran que esa narrativa se apoya en lugares y periodos distintos de los registrados. Las decisiones que se pueden respaldar con evidencia son de priorización territorial y de mejora del registro; las explicaciones climáticas o de intencionalidad siguen siendo hipótesis.

## 4.7 Cómo reproducir el cruce

```bash
python scripts/etapa6/cruce_resultados.py
```

Genera `data/etapa6/integracion/cruce_grupos_grandes.csv` y `cruce_departamentos.csv` a partir del archivo del ejercicio supervisado y de la pertenencia a los grupos del informe de clustering.
