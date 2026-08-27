# Tarea Camila — Calidad inicial y Limitaciones

Este documento es autosuficiente. El proyecto es la Etapa 1 (R1) de Mineria de Datos
sobre **incendios forestales**. Lee tambien `CLAUDE.md` en la raiz del repo.

## Punto de partida (ya resuelto)

`app/templates/etapa1/calidad.html` ya muestra, calculado automaticamente desde
`data/processed/calidad_resumen.json`:

- Registros totales, duplicados, departamentos distintos, rango de anios.
- % de valores vacios por columna (barra de progreso por campo).
- Una lista de "Hallazgos del diagnostico inicial" ya redactada con problemas reales
  encontrados durante la extraccion (formato de fecha inconsistente, columna nueva solo
  en 2024, coordenadas en formato no estandar, alta dispersión en variables de causa).

`app/templates/etapa1/limitaciones.html` ya trae una primera lista de limitaciones
razonada a partir de esos mismos hallazgos.

## Que debes producir

### 1. `app/templates/etapa1/calidad.html`

- Revisa que los hallazgos ya escritos sean precisos (abre
  `data/processed/incendios_ideam_2010_2024.csv` y confirma un par de casos si quieres
  verificarlo tu misma/o).
- Agrega el bloque `TODO` final: diagnostico de calidad de la(s) fuente(s) global(es) que
  Sara Vargas haya definido (¿tiene datos faltantes? ¿que tan actualizada esta? ¿que
  formato trae?).
- Si encuentras un problema de calidad adicional que el analisis automatico no capturo
  (por ejemplo revisando manualmente filas), agregalo a la lista.

### 2. `app/templates/etapa1/limitaciones.html`

- Revisa y amplia la lista ya redactada.
- Completa el bloque "Pendiente para completar esta pagina":
  - Limitaciones propias de la fuente global y de las fuentes nacional/regional
    adicionales (una vez Sara Vargas las tenga documentadas).
  - Como estas limitaciones podrian afectar las respuestas a la pregunta principal y
    secundarias de Sergio Gómez (leelas en `app/templates/etapa1/preguntas.html`
    despues de que el las complete).
  - Que decisiones de alcance tomo el grupo para mitigar cada limitacion.

## Archivos que SI puedes editar

- `app/templates/etapa1/calidad.html`
- `app/templates/etapa1/limitaciones.html`

## Archivos que NO debes tocar

Cualquier otro archivo del repo (rutas, layout compartido, otras plantillas,
`calidad_resumen.json` — ese es generado, no se edita a mano).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-1
git pull
git checkout -b feature/etapa-1-camila

# ... editas los 2 archivos ...

git add app/templates/etapa1/calidad.html app/templates/etapa1/limitaciones.html
git commit -m "docs(etapa1): diagnostico de calidad y limitaciones"
git push -u origin feature/etapa-1-camila
```

Abre un Pull Request de `feature/etapa-1-camila` hacia `feature/etapa-1` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] Los hallazgos de calidad describen problemas reales del dataset (no genericos).
- [ ] Incluiste el diagnostico de calidad de la(s) fuente(s) adicional(es) una vez el
      Sara Vargas las documente (coordina el orden con el/ella).
- [ ] Las limitaciones explican como afectan a las preguntas de investigacion.
- [ ] No quedo ningun `TODO` sin resolver en ninguna de las dos paginas.
- [ ] Corriste `python run.py` y viste `/etapa-1/calidad` y `/etapa-1/limitaciones` en el
      navegador sin errores.

## Prompt sugerido para tu sesion de Claude Code

> Estoy en la rama feature/etapa-1-camila del repo wildfire-data-mining. Lee
> CLAUDE.md y docs/tareas/camila.md completos. Tambien lee
> data/processed/calidad_resumen.json. Ayudame a revisar y completar
> app/templates/etapa1/calidad.html y app/templates/etapa1/limitaciones.html siguiendo
> exactamente las instrucciones de ese documento. No toques ningun otro archivo.
