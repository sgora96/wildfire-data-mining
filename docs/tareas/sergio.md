# Tarea Sergio Gómez — Problema y preguntas

Bienvenido/a. Este documento es autosuficiente: leelo completo antes de escribir nada.
El proyecto es la Etapa 1 (R1) de Mineria de Datos sobre **incendios forestales**
(escalas global, nacional-Colombia, regional-Cundinamarca). El repo ya tiene:

- Un dataset real de 40.010 registros nacionales + 6.027 regionales (IDEAM, 2010-2024),
  ya consolidado en `data/processed/`.
- La app Flask con el menu "Etapa 1" y sus 8 submenus ya armados (rutas + plantillas).
- Contexto completo del proyecto en `CLAUDE.md` (leelo tambien, es corto).

Tu trabajo NO es tecnico/codigo: es **redactar contenido** en dos plantillas HTML que ya
existen con la estructura lista y marcadores `TODO`.

## Que debes producir

### 1. `app/templates/etapa1/problema.html`

- Contexto del problema en las 3 escalas (reemplaza los 3 bloques TODO: global, nacional,
  regional). 3-5 lineas cada uno, con datos/cifras si las consigues (cita de donde salen
  informalmente, la fuente formal se documenta en la pagina de Fuentes que hace el
  Sara Vargas).
- Un parrafo delimitando el **problema especifico** de investigacion (no solo "hay
  incendios forestales" — que aspecto puntual van a estudiar: frecuencia, severidad,
  causas, estacionalidad, relacion con clima, etc.)
- Un parrafo de que **conocimiento esperan obtener** de los datos.

### 2. `app/templates/etapa1/preguntas.html`

- **1 pregunta principal**: clara, delimitada, respondible con datos (no una opinion).
- **Minimo 3 preguntas secundarias** que descompongan la principal.
- Evitar: preguntas demasiado generales, opiniones sin datos, preguntas cuya respuesta ya
  esta en el enunciado del tema.
- Llenar la tabla "Que orienta cada pregunta" (variables involucradas, periodo/poblacion)
  para la principal y cada secundaria.

**Tip:** ya sabes que el dataset disponible tiene: fecha, departamento, municipio,
vereda, area afectada (total y por tipo: copa/superficial/subterraneo/mixto), causa
(quema fuera de control, descuido, intencional, accidental, reactivacion), tipo de
cobertura vegetal afectada (bosque denso, bosque intervenido, paramo, cultivos, etc.),
elevacion, y coordenadas. Formula preguntas que este tipo de datos SI pueda responder
(ej. estacionalidad, relacion causa-severidad, comparacion de departamentos), no
preguntas que necesiten datos que no vas a tener (ej. "por que la gente no reporta los
incendios" no es respondible con este dataset).

## Archivos que SI puedes editar

- `app/templates/etapa1/problema.html`
- `app/templates/etapa1/preguntas.html`

## Archivos que NO debes tocar

Cualquier otro archivo (rutas, layout compartido, otras plantillas) — son de otros
integrantes o compartidos. Si necesitas algo distinto ahi, avisa en el chat del grupo.

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-1
git pull
git checkout -b feature/etapa-1-sergio

# ... editas los 2 archivos ...

git add app/templates/etapa1/problema.html app/templates/etapa1/preguntas.html
git commit -m "docs(etapa1): problema, contexto y preguntas de investigacion"
git push -u origin feature/etapa-1-sergio
```

Luego abre un Pull Request de `feature/etapa-1-sergio` hacia `feature/etapa-1`
(NO hacia `main`).

## Checklist antes de dar por terminada tu parte

- [ ] Los 3 bloques de contexto (global/nacional/regional) estan escritos, sin `TODO`.
- [ ] El problema especifico esta delimitado en un parrafo claro.
- [ ] Hay exactamente 1 pregunta principal, bien formulada.
- [ ] Hay minimo 3 preguntas secundarias.
- [ ] Cada pregunta es respondible con las variables que el dataset realmente tiene.
- [ ] Corriste `python run.py` y viste `/etapa-1/problema` y `/etapa-1/preguntas` en el
      navegador sin errores.

## Prompt sugerido para tu sesion de Claude Code

> Estoy en la rama feature/etapa-1-sergio del repo wildfire-data-mining. Lee
> CLAUDE.md y docs/tareas/sergio.md completos. Ayudame a redactar el contenido de
> app/templates/etapa1/problema.html y app/templates/etapa1/preguntas.html siguiendo
> exactamente las instrucciones de ese documento, reemplazando los TODO. El tema es
> incendios forestales (global / Colombia / Cundinamarca). No toques ningun otro archivo.
