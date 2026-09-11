# Tarea Sergio Gómez — Descripción y requisitos de calidad (Etapa 2)

Este documento es autosuficiente. Es la Etapa 2 (R2) de Minería de Datos: "Calidad de
Datos" sobre el dataset de incendios forestales consolidado en la Etapa 1. Lee también
`CLAUDE.md` en la raíz del repo.

## Punto de partida (ya resuelto)

Ya existe un perfilamiento completo y real del dataset, calculado con
`scripts/data_quality_r2.py`:

- `data/processed/calidad_r2_resumen.json` — perfilamiento de las 36 variables, las 6
  dimensiones de calidad con su métrica y resultado, el inventario de problemas, el plan
  de tratamiento aplicado, y la comparación antes/después.
- `data/processed/incendios_ideam_tratado_2010_2024.csv` — dataset tratado (35.355
  registros, sin duplicados, con departamento/mes homologados, coordenadas convertidas
  donde fue posible, y columnas de apoyo `_NUM`/`_NORM`/`_FLAG`).

Ya está la página `app/templates/etapa2/descripcion.html` con la estructura lista y
marcadores `TODO` con instrucciones exactas de qué redactar.

## Qué debes producir

### `app/templates/etapa2/descripcion.html`

- **Variables principales y por qué este dataset**: retomar de la Etapa 1 (fecha,
  ubicación, área quemada, causa, cobertura) y explicar brevemente por qué se sigue
  usando este dataset para evaluar calidad.
- **Propósito y usuarios esperados**: para qué se van a usar estos datos en el proyecto
  (responder la pregunta principal y secundarias de la Etapa 1 — estacionalidad,
  geografía, causas, comparación con la tendencia global) y quiénes serían los usuarios
  de esa información.
- **Requisito de calidad adicional**: ya hay 4 requisitos redactados (completitud,
  validez, unicidad, exactitud); agregá 1-2 más si ves algo relevante propio del
  problema (por ejemplo, sobre las coordenadas para un futuro análisis geoespacial).

## Archivos que SÍ podés editar

- `app/templates/etapa2/descripcion.html`

## Archivos que NO debés tocar

Cualquier otro archivo (rutas, layout compartido, otras plantillas, el script de
calidad, el dataset tratado).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-2
git pull
git checkout -b feature/etapa-2-sergio

# ... editás el archivo ...

git add app/templates/etapa2/descripcion.html
git commit -m "docs(etapa2): descripcion del dataset y requisitos de calidad"
git push -u origin feature/etapa-2-sergio
```

Abrí un Pull Request de `feature/etapa-2-sergio` hacia `feature/etapa-2` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] Las variables principales están descritas con contexto (no solo listadas).
- [ ] El propósito y los usuarios esperados quedan claros.
- [ ] Hay al menos 1 requisito de calidad adicional bien justificado.
- [ ] No quedó ningún `TODO` sin resolver en el archivo.
- [ ] Corriste `python run.py` y viste `/etapa-2/descripcion/` en el navegador sin
      errores.

## Prompt sugerido para tu sesión de Claude Code

> Estoy en la rama feature/etapa-2-sergio del repo wildfire-data-mining. Lee CLAUDE.md
> y docs/tareas/sergio.md completos. Ayudame a completar
> app/templates/etapa2/descripcion.html siguiendo exactamente las instrucciones de ese
> documento, reemplazando los TODO. No toques ningún otro archivo.
