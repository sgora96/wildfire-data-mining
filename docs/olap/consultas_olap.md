# Capa de consultas de la Etapa 5

## Componentes
- `app/static/olap/consultas.json`: dimensiones, niveles, jerarquias y medidas permitidas.
- `app/olap.py`: valida la especificacion, genera el SQL y lo ejecuta en solo lectura.
- `GET /api/olap/consulta?spec=<json>`: expone las consultas en Flask.

## Especificacion
```json
{
  "medida": "hectareas",
  "filas": "territorio.region",
  "columnas": "tiempo.trimestre",
  "filtros": { "tiempo.anio": ["2024"] },
  "orden": "valor_desc",
  "limite": 500
}
```

`columnas`, `filtros`, `orden` y `limite` son opcionales. La respuesta incluye `columnas`,
`filas`, `sql`, `parametros` y `ms`. Cada fila incluye `fila`, `col`, `valor`, `eventos` y
`eventos_con_area`, para mostrar los denominadores.

## Seguridad
- Medidas, niveles y orden se validan contra una lista blanca.
- Los valores de los filtros y el limite se envian como parametros `?`.
- La base se abre en modo de solo lectura.
- Una especificacion invalida responde con estado 400 y un mensaje en JSON.

## Verificacion de la API
| Consulta | Resultado | Valor de control |
|---|---|---|
| Hectareas de Orinoquia | 796.581,3 | 796.581 |
| Hectareas de Andina | 468.957,0 | 468.957 |
| Eventos de Andina | 23.469 | 23.469 |
| Eventos de Orinoquia | 3.714 | 3.714 |
| % de grandes en 2024-T1 | 2,8 % (base: 4.776) | 2,8 % (base: 4.776) |
| % de grandes en 2024-T3 | 5,5 % (base: 1.983) | 5,5 % (base: 1.983) |
| Medida no permitida | Estado 400 | Rechazada |