# Verificaciones del modelo estrella

Resultado de `python scripts/etl/validar_dw.py` sobre `data/warehouse/incendios_dw.db`.
Las consultas están en `sql/validaciones.sql`; los valores esperados se calculan con
pandas sobre `data/processed/incendios_ideam_tratado_2010_2024.csv` (35.355 eventos).

**Resumen: 57 de 57 verificaciones en OK.**

Para reproducir:

```bash
python scripts/etl/build_dw.py
python scripts/etl/validar_dw.py
```

## 1. Integridad del modelo

Claves únicas, sin hechos huérfanos y sin duplicación de filas en la tabla de hechos.

| Verificación | Modelo | Esperado | Resultado | Nota |
|---|---|---|---|---|
| Filas de fact_incendio | 35.355 | 35.355 | OK |  |
| Suma de n_eventos | 35.355 | 35.355 | OK |  |
| id_evento repetidos | 0 | 0 | OK |  |
| JOIN de los hechos con las 6 dimensiones (filas) | 35.355 | 35.355 | OK | El JOIN no multiplica ni pierde filas. |
| PRAGMA foreign_key_check (claves foráneas huérfanas) | 0 | 0 | OK |  |
| Hechos sin miembro en dim_tiempo | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_tiempo | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_tiempo | 0 | 0 | OK |  |
| Hechos sin miembro en dim_territorio | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_territorio | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_territorio | 0 | 0 | OK |  |
| Hechos sin miembro en dim_tamano | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_tamano | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_tamano | 0 | 0 | OK |  |
| Hechos sin miembro en dim_causa | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_causa | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_causa | 0 | 0 | OK |  |
| Hechos sin miembro en dim_cobertura | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_cobertura | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_cobertura | 0 | 0 | OK |  |
| Hechos sin miembro en dim_fuente | 0 | 0 | OK |  |
| Claves primarias repetidas en dim_fuente | 0 | 0 | OK |  |
| Miembros repetidos (clave natural) en dim_fuente | 0 | 0 | OK |  |
| con_area coherente con area_total_ha | 0 | 0 | OK |  |

## 2. Tratamiento de faltantes y desconocidos

Un faltante no se convierte en cero: el área ausente queda `NULL` (y `con_area = 0`); la
causa ausente o sin información va al miembro "Sin causa registrada"; el territorio, el
tiempo y la fuente desconocidos van a miembros explícitos ("Sin departamento",
"Sin municipio", "Sin fecha", "Sin mes", "Sin dato").

| Verificación | Modelo | Esperado | Resultado | Nota |
|---|---|---|---|---|
| Eventos sin año (tiempo_key = 0) | 4 | 4 | OK |  |
| Eventos con año y sin mes válido | 13 | 13 | OK |  |
| Eventos con año y mes válidos | 35.338 | 35.338 | OK |  |
| Eventos sin departamento | 43 | 43 | OK |  |
| Eventos sin municipio | 49 | 49 | OK |  |
| Eventos sin área (tamano_key = 0) | 775 | 775 | OK |  |
| Eventos con área NULL (no convertida a 0) | 775 | 775 | OK |  |
| Eventos con área exactamente 0 (valor real, no faltante) | 1.889 | 1.889 | OK |  |
| Eventos sin causa registrada | 31.207 | 31.207 | OK |  |
| Eventos con más de una causa | 49 | 49 | OK |  |
| Eventos sin cobertura informada | 20.448 | 20.448 | OK |  |
| Eventos con más de un tipo de cobertura | 1.285 | 1.285 | OK |  |
| Eventos de hojas sin ENTIDAD_REPORTA ('No aplica') | 27.569 | 27.569 | OK |  |
| Eventos de 2024 sin entidad ('Sin dato') | 1 | 1 | OK |  |

## 3. Comparación del modelo con los datos tratados

| Verificación | Modelo | Esperado | Resultado | Nota |
|---|---|---|---|---|
| Suma de hectáreas (ha) | 1.612.917,95 | 1.612.917,95 | OK |  |
| Eventos con área | 34.580 | 34.580 | OK |  |
| Filas de dim_tiempo (15 años x 12 meses + 15 'año sin mes' + 1) | 196 | 196 | OK |  |
| Filas de dim_territorio (pares departamento-municipio normalizado) | 1.058 | 1.058 | OK |  |
| Filas de dim_fuente (hoja-entidad) | 23 | 23 | OK |  |
| Departamentos distintos | 33 | 33 | OK |  |
| Eventos por año (15 años) | 15 filas, suma 35.351 | 15 filas, suma 35.351 | OK |  |
| Eventos por departamento (33 departamentos) | 33 filas, suma 35.312 | 33 filas, suma 35.312 | OK |  |
| Top 5 departamentos por eventos | Cundinamarca 5.938, Huila 4.866, Antioquia 3.022, Boyacá 2.715, Tolima 2.695 | Cundinamarca 5.938, Huila 4.866, Antioquia 3.022, Boyacá 2.715, Tolima 2.695 | OK |  |
| Eventos por hoja de origen | 5 filas, suma 35.355 | 5 filas, suma 35.355 | OK |  |
| Hectáreas por región (ha, redondeadas) | 7 filas, suma 1.612.917 | 7 filas, suma 1.612.917 | OK | La región no existe en el CSV; se compara con la cifra de control del equipo. |
| Eventos por región | 7 filas, suma 35.355 | 7 filas, suma 35.355 | OK |  |
| Eventos por causa | 8 filas, suma 35.355 | 8 filas, suma 35.355 | OK |  |
| Eventos por grupo de cobertura | 8 filas, suma 35.355 | 8 filas, suma 35.355 | OK |  |
| Hectáreas por grupo de cobertura (ha, redondeadas) | 8 filas, suma 1.612.919 | 8 filas, suma 1.612.919 | OK | Área total del evento asignada a su cobertura; no es la de la Etapa 4. |
| Eventos con causa (4.099 con una + 49 con varias) | 4.148 | 4.148 | OK |  |
| Eventos con cobertura (13.622 con un tipo + 1.285 con varios) | 14.907 | 14.907 | OK |  |
| Filas evento-causa con las reglas de la Etapa 4 (dax_base.md) | 4.198 | 4.198 | OK |  |
| Eventos 'Intencional' en la Etapa 4 (A4) | 1.415 | 1.415 | OK |  |

### Eventos por año (modelo y CSV)

| Año | Modelo | CSV |
|---|---|---|
| 2010 | 2.322 | 2.322 |
| 2011 | 816 | 816 |
| 2012 | 1.925 | 1.925 |
| 2013 | 2.615 | 2.615 |
| 2014 | 2.226 | 2.226 |
| 2015 | 2.199 | 2.199 |
| 2016 | 2.321 | 2.321 |
| 2017 | 1.088 | 1.088 |
| 2018 | 1.845 | 1.845 |
| 2019 | 3.180 | 3.180 |
| 2020 | 2.197 | 2.197 |
| 2021 | 931 | 931 |
| 2022 | 1.003 | 1.003 |
| 2023 | 2.898 | 2.898 |
| 2024 | 7.785 | 7.785 |

### Cinco departamentos con más eventos

| Departamento | Modelo | CSV |
|---|---|---|
| Cundinamarca | 5.938 | 5.938 |
| Huila | 4.866 | 4.866 |
| Antioquia | 3.022 | 3.022 |
| Boyacá | 2.715 | 2.715 |
| Tolima | 2.695 | 2.695 |

### Hectáreas y eventos por región

| Región | Eventos | Hectáreas |
|---|---|---|
| Orinoquia | 3.714 | 796.581,3 |
| Andina | 23.469 | 468.957,0 |
| Caribe | 3.833 | 179.877,4 |
| Pacifica | 3.347 | 133.028,4 |
| Amazonia | 912 | 34.361,1 |
| Insular | 37 | 112,8 |
| Sin region | 43 | 0,0 |

## 4. Diferencias frente a la Etapa 4 y su explicación

**Causas.** En la Etapa 4 un evento con varias causas contaba una vez en cada causa
(4.198 filas evento-causa para 4.148 eventos). En el modelo una fila de
hechos es un evento, así que los 49 eventos con dos o más causas
(48 con dos y 1 con tres) pasan al miembro "Mas de una causa"; así
ningún evento ni hectárea se cuenta dos veces. Por eso el modelo muestra menos eventos por
causa que la Etapa 4 (por ejemplo, Intencional 1.402 frente a 1.415):

| Causa | Etapa 4 (eventos con esa causa) | Modelo (solo esa causa) | Diferencia (pasan a 'Mas de una causa') |
|---|---|---|---|
| Intencional | 1.415 | 1.402 | 13 |
| Quema fuera de control | 1.005 | 974 | 31 |
| Descuido o negligencia | 605 | 583 | 22 |
| Accidental | 605 | 598 | 7 |
| Reactivacion de focos | 54 | 43 | 11 |
| Otra | 514 | 499 | 15 |

El total de eventos con causa no cambia: 4.148 en ambos.

**Hectáreas por cobertura.** La Etapa 4 sumó las columnas `COB_*` (hectáreas por tipo de
cobertura): 669.358,0 ha. El modelo asigna el área **total** del evento
a su cobertura: los eventos con cobertura informada suman 669.418,2 ha
(diferencia de 60,2 ha). La diferencia aparece
porque en 15 eventos la suma de coberturas supera el área total y en 75 es menor
(`docs/powerbi/dax_base.md`, sección 4). Además, en los eventos con varios tipos el modelo no
reparte el área entre tipos: la asigna a "Mas de un tipo de cobertura". Las dos cifras
responden preguntas distintas y no deben compararse entre sí.

**Calendario.** La Etapa 4 usaba un calendario de 180 meses y dejaba fuera 17 eventos sin
año o mes válido. El modelo tiene 196 miembros de tiempo: los
180 meses, 15 miembros "año sin mes" (13 eventos) y "Sin fecha" (4 eventos), de modo que
esos 17 eventos siguen en el total y solo se excluyen al filtrar por un mes concreto.

**Municipios.** Los nombres de municipio traen variantes de mayúsculas y tildes. Se
normalizan (mayúsculas, sin tildes, sin espacios sobrantes) y la clave de territorio es el par
(departamento, municipio), porque hay municipios homónimos en distintos departamentos.
El resultado son 1.058 miembros, que coinciden con los pares
calculados con pandas.

**Nombres de miembros.** Los nombres de dimensiones se escriben sin tildes (por ejemplo
"Pacifica", "Paramos", "Reactivacion de focos") para que todas las vistas usen
exactamente las mismas cadenas en filtros y consultas. Los departamentos conservan la
escritura del CSV.
