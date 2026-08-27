# Tarea Sara Vargas — Necesidades de informacion y Fuentes de datos

Este documento es autosuficiente. El proyecto es la Etapa 1 (R1) de Mineria de Datos
sobre **incendios forestales** (escalas global, nacional-Colombia, regional-
Cundinamarca). Lee tambien `CLAUDE.md` en la raiz del repo (contexto general).

**Tu tarea es la mas critica del grupo esta semana**: sin las fuentes, no se puede cerrar
la entrega. El resto del equipo depende de que definas la(s) fuente(s) global(es).

## Punto de partida (ya resuelto)

Ya existe un dataset real y consolidado del **IDEAM** (Colombia) que cubre nacional y
regional (Cundinamarca) de sobra: 40.010 registros nacionales, 6.027 regionales,
2010-2024, 35 variables. Esta documentado como fuente #1 de nivel nacional y #1 de nivel
regional en `app/templates/etapa1/fuentes.html` (ya prellenado, no lo borres).

**Lo que falta y es tu prioridad:**

1. **2 fuentes de nivel GLOBAL** (ninguna fuente actual cubre el mundo). Candidatas
   reales conocidas — verifica tu misma/o la URL exacta y las condiciones de uso antes de
   citarlas, no copies la URL de aqui sin confirmarla:
   - NASA FIRMS (Fire Information for Resource Management System) — incendios activos
     detectados por satelite (MODIS/VIIRS), cobertura mundial, actualizacion casi diaria.
   - Global Forest Watch Fires (World Resources Institute) — alertas de incendio y
     perdida de cobertura forestal a nivel mundial.
   - Alternativas: Copernicus EFFIS (Europa, pero publica series globales tambien), FAO
     (estadisticas forestales), EM-DAT (base de desastres, incluye incendios forestales
     como categoria).
2. **1 fuente NACIONAL adicional** (independiente de IDEAM) — ej. UNGRD (Unidad Nacional
   para la Gestion del Riesgo de Desastres), Datos Abiertos Colombia (datos.gov.co), SIAC
   (Sistema de Informacion Ambiental de Colombia).
3. **1 fuente REGIONAL adicional** (Cundinamarca, independiente de IDEAM) — ej. CAR
   Cundinamarca (Corporacion Autonoma Regional), boletines de la Gobernacion de
   Cundinamarca, alcaldias municipales.

Si el grupo decide levantar datos propios (encuesta, entrevista a bomberos forestales,
etc.), esa seria una fuente **primaria** valida para regional o nacional.

## Que debes producir

### `app/templates/etapa1/fuentes.html`

Reemplaza cada bloque `TODO` (hay 4: global x2, nacional x1, regional x1) con, para
cada fuente:
- Nombre de la fuente
- Institucion responsable
- URL (verificada, que abra de verdad)
- Tipo: primaria / secundaria / terciaria
- Cobertura geografica y periodo disponible
- Formato (CSV, API, xlsx, shapefile...)
- Metodo de adquisicion (descarga directa, API, formulario...)
- Numero aproximado de registros
- Variables disponibles (lista breve)
- Fecha de consulta (hoy)
- Restricciones/licencia de uso
- Justificacion de pertinencia, confiabilidad, actualidad y cobertura (por que sirve
  para responder las preguntas de investigacion de Sergio Gómez)

### `app/templates/etapa1/necesidades.html`

- Tabla de entidades y atributos: agrega filas para las entidades que traigan tus nuevas
  fuentes (ej. "estacion satelital de deteccion", "pais", "region climatica") ademas de
  la fila ya prellenada de "Evento de incendio forestal".
- Cobertura requerida: completa el periodo y la cobertura geografica de las fuentes
  globales que elijas.
- Variables para comparar escalas: explica con que variables se podra comparar global vs
  nacional vs regional (ej. tasa de incendios normalizada por area de bosque, no solo
  conteo absoluto, porque los paises/regiones tienen tamanos distintos).

## Archivos que SI puedes editar

- `app/templates/etapa1/fuentes.html`
- `app/templates/etapa1/necesidades.html`

## Archivos que NO debes tocar

Cualquier otro. Si tu fuente global trae variables que valdria la pena sumar al
diccionario de datos (`app/etapa1.py`, lista `DICCIONARIO`), coordina con Laura Bautista
antes de tocar ese archivo (es compartido).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-1
git pull
git checkout -b feature/etapa-1-sara

# ... editas los 2 archivos ...

git add app/templates/etapa1/fuentes.html app/templates/etapa1/necesidades.html
git commit -m "docs(etapa1): fuentes global/nacional/regional y necesidades de informacion"
git push -u origin feature/etapa-1-sara
```

Abre un Pull Request de `feature/etapa-1-sara` hacia `feature/etapa-1` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] Hay al menos 2 fuentes por cada nivel (global, nacional, regional) — 6 en total,
      todas con URL verificada (que abre y muestra lo que dice).
- [ ] Cada fuente tiene su tipo (primaria/secundaria/terciaria) correcto.
- [ ] Cada fuente tiene los 11 campos pedidos completos (no dejaste ningun `TODO`).
- [ ] La justificacion de pertinencia/confiabilidad/actualidad/cobertura es especifica
      (no generica) para cada fuente.
- [ ] `necesidades.html` explica como se van a poder comparar las tres escalas.
- [ ] Corriste `python run.py` y viste `/etapa-1/fuentes` y `/etapa-1/necesidades` en el
      navegador sin errores.

## Prompt sugerido para tu sesion de Claude Code

> Estoy en la rama feature/etapa-1-sara del repo wildfire-data-mining. Lee
> CLAUDE.md y docs/tareas/sara.md completos. Ayudame a investigar y documentar
> fuentes reales de datos de incendios forestales a nivel global (ej. NASA FIRMS, Global
> Forest Watch Fires), y a completar app/templates/etapa1/fuentes.html y
> app/templates/etapa1/necesidades.html siguiendo exactamente el formato que ya tienen
> esos archivos. No inventes URLs: si no puedes verificar un dato, dejalo marcado como
> pendiente de verificar. No toques ningun otro archivo del repo.
