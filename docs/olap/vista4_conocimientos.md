# Vista 4: conocimientos multidimensionales

Vista: `/etapa-5/vista-4/` (Causa y tamaño). Todas las cifras salen de consultas al modelo estrella (`incendios_dw.db`) y se pueden reproducir con los botones de ejemplo de la vista. Las consultas están en [vista4_consultas.md](vista4_consultas.md).

Recordatorio de lectura: "Sin causa registrada" es un dato faltante (la causa solo se registró en las hojas 2010-2022), no una respuesta negativa; asociación no es causalidad.

## Conocimiento 1. Las causas más frecuentes no son las que más incendios grandes producen

1. **Pregunta:** ¿Las causas con más eventos registrados son también las que más se asocian con incendios de más de 100 ha?
2. **Dimensiones y medidas:** causa (registro → causa) y tamaño; % de eventos grandes con eventos con área como denominador.
3. **Procedimiento:**
   - Botón "Vista inicial: causa x tamaño" (filas = causa, columnas = clase de tamaño, medida = eventos).
   - Lectura de la gráfica "% de eventos grandes por causa", ordenada de mayor a menor.
   - Ambas lecturas usan el mismo nivel (causa) sin ningún filtro.
4. **Evidencia:** gráfica de % de eventos grandes por causa y matriz causa x tamaño de la Vista 4, sin filtros.
5. **Hallazgo:**

   | Causa | Eventos | Eventos con área | % de grandes |
   |---|---|---|---|
   | Mas de una causa | 49 | 48 | 16,7 % (8) |
   | Otra | 499 | 489 | 9,8 % (48) |
   | Reactivacion de focos | 43 | 40 | 5,0 % (2) |
   | Sin causa registrada | 31.207 | 30.606 | 4,9 % (1.509) |
   | Intencional | 1.402 | 1.303 | 3,6 % (47) |
   | Quema fuera de control | 974 | 945 | 3,6 % (34) |
   | Descuido o negligencia | 583 | 567 | 2,8 % (16) |
   | Accidental | 598 | 582 | 1,7 % (10) |

6. **Interpretación:** Intencional es la causa más frecuente (1.402 eventos) y Quema fuera de control la segunda (974), pero ambas quedan en 3,6 % de eventos grandes; "Otra" (499 eventos) llega a 9,8 % y "Mas de una causa" (49 eventos) a 16,7 %. Frente al conocimiento evidente, que solo contaba cuántas veces aparecía cada causa (Intencional 34,1 %, quema fuera de control 24,2 % de los eventos con causa), el aporte es cruzar la causa con el tamaño: la causa más frecuente no es la que más incendios grandes produce en proporción.
7. **Utilidad:** sugiere que la respuesta operativa no debe dimensionarse solo por la causa más frecuente; las causas poco comunes también merecen atención por su impacto en área.
8. **Limitación:** "Otra" agrupa causas distintas que el formulario no distingue entre sí, y "Mas de una causa" tiene solo 48 eventos con área, una base pequeña donde un solo incendio grande cambia mucho el porcentaje.

## Conocimiento 2. En Orinoquia, la causa "Otra" se asocia con incendios mucho más extensos que en el resto del país

1. **Pregunta:** ¿La asociación entre causa y tamaño es igual en todas las regiones?
2. **Dimensiones y medidas:** causa, territorio (región) y tamaño; hectáreas por evento y % de eventos grandes.
3. **Procedimiento:** operación DICE con el botón "Dice: Intencional y Otra, en Orinoquia y Andina":
   - Filtros combinados: causa en {Intencional, Otra} y región en {Orinoquia, Andina}.
   - Niveles: filas en causa, columnas en región.
   - Comparación adicional con el botón "Slice: región = Orinoquia" para ver el resto de causas de esa región.
4. **Evidencia:** matriz causa x región de la Vista 4 con la selección DICE activa (medidas hectáreas y ha por evento) y matriz causa x tamaño con el slice de Orinoquia (SQL y parámetros en "Ver consulta SQL").
5. **Hallazgo:** "Otra" en Orinoquia suma 120.217,5 ha en 83 eventos con área (1.448,4 ha por evento) y 47,0 % de eventos grandes (39 de 83); en Andina, la misma causa suma 3.750,6 ha en 349 eventos con área (10,7 ha por evento) y 2,0 % de grandes (7 de 349). Intencional cambia menos entre regiones: 209,3 ha por evento en Orinoquia (19 eventos con área) y 15,9 ha por evento en Andina (971 eventos con área).
6. **Interpretación:** frente al conocimiento evidente, que solo contaba causas a nivel nacional, el aporte es mostrar que la misma causa registrada tiene un efecto muy distinto según la región: en Orinoquia, "Otra" corresponde a pocos eventos pero extremadamente grandes, mientras que en Andina la misma causa corresponde a muchos eventos pequeños. Es una asociación observada en los datos, no una explicación de por qué ocurre.
7. **Utilidad:** advierte que un plan de prevención basado solo en la causa más frecuente a nivel nacional puede no ajustarse a lo que realmente ocurre en Orinoquia.
8. **Limitación:** dentro de Orinoquia, varias causas tienen muy pocos eventos con área (Accidental: 1; Reactivacion de focos: 4) y su porcentaje no es confiable; "Otra" en Orinoquia sí tiene 83 eventos, una base razonable, pero pequeña frente a los cientos o miles de eventos de las celdas de Andina.
