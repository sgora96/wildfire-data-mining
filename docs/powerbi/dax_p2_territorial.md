# Medidas DAX de la página 2 (comparación territorial)

Todas las medidas viven en la tabla `_Medidas` y usan `Total Eventos` de la base. Los segmentadores de año y mes filtran todas ellas.

## P2_Departamentos con Eventos
Cuenta los departamentos distintos con al menos un evento, excluyendo "Sin departamento". Resultado sin filtros: 33.

## P2_% Top 5 Deptos
Eventos de los 5 departamentos con más registros (TOPN sobre `Dim_Departamento[DEPARTAMENTO_NORM]` quitando el filtro de departamento) dividido entre el total de eventos del filtro actual. Denominador: 35.355 con los filtros en "Todos". Resultado: 54,4 %.

## P2_Eventos Cundinamarca
Eventos con departamento igual a Cundinamarca. Resultado sin filtros: 5.938 (16,8 % de 35.355).

## P2_% Participacion
Eventos del departamento divididos entre el total de eventos de los departamentos visibles (ALLSELECTED). Se usa en la información sobre herramientas del gráfico de departamentos.

## P2_Mediana Ha (min 100 eventos)
Devuelve la mediana de hectáreas por departamento solo si el departamento tiene 100 o más eventos con área registrada; si no, queda en blanco. Evita medianas poco confiables con pocos eventos.