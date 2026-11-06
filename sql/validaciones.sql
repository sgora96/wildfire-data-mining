-- Consultas de verificacion del modelo estrella (incendios_dw.db).
-- Las ejecuta scripts/etl/validar_dw.py, que compara cada resultado con el valor
-- esperado calculado con pandas sobre el CSV tratado. Cada bloque empieza con
-- "-- @identificador". Ademas de estas consultas, el validador ejecuta
-- PRAGMA foreign_key_check (debe devolver cero filas).

-- ======================================================================
-- 1. Tabla de hechos y totales
-- ======================================================================

-- @filas_hechos
SELECT COUNT(*) FROM fact_incendio;

-- @suma_eventos
SELECT SUM(n_eventos) FROM fact_incendio;

-- @ids_repetidos
SELECT COUNT(*) - COUNT(DISTINCT id_evento) FROM fact_incendio;

-- @suma_hectareas
SELECT SUM(area_total_ha) FROM fact_incendio;

-- @eventos_con_area
SELECT SUM(con_area) FROM fact_incendio;

-- @area_nula
SELECT COUNT(*) FROM fact_incendio WHERE area_total_ha IS NULL;

-- @area_cero
SELECT COUNT(*) FROM fact_incendio WHERE area_total_ha = 0;

-- @con_area_inconsistente
SELECT COUNT(*) FROM fact_incendio
WHERE (area_total_ha IS NULL AND con_area <> 0) OR (area_total_ha IS NOT NULL AND con_area <> 1);

-- @join_seis_dimensiones
SELECT COUNT(*)
FROM fact_incendio f
JOIN dim_tiempo     t ON t.tiempo_key     = f.tiempo_key
JOIN dim_territorio r ON r.territorio_key = f.territorio_key
JOIN dim_tamano     z ON z.tamano_key     = f.tamano_key
JOIN dim_causa      c ON c.causa_key      = f.causa_key
JOIN dim_cobertura  b ON b.cobertura_key  = f.cobertura_key
JOIN dim_fuente     u ON u.fuente_key     = f.fuente_key;

-- ======================================================================
-- 2. Unicidad de claves de las dimensiones (todas deben dar 0)
-- ======================================================================

-- @pk_repetidas_tiempo
SELECT COUNT(*) - COUNT(DISTINCT tiempo_key) FROM dim_tiempo;
-- @pk_repetidas_territorio
SELECT COUNT(*) - COUNT(DISTINCT territorio_key) FROM dim_territorio;
-- @pk_repetidas_tamano
SELECT COUNT(*) - COUNT(DISTINCT tamano_key) FROM dim_tamano;
-- @pk_repetidas_causa
SELECT COUNT(*) - COUNT(DISTINCT causa_key) FROM dim_causa;
-- @pk_repetidas_cobertura
SELECT COUNT(*) - COUNT(DISTINCT cobertura_key) FROM dim_cobertura;
-- @pk_repetidas_fuente
SELECT COUNT(*) - COUNT(DISTINCT fuente_key) FROM dim_fuente;

-- Claves naturales: dos filas de una dimension no pueden describir el mismo miembro.
-- @natural_repetida_tiempo
SELECT COUNT(*) - COUNT(DISTINCT h_mes) FROM dim_tiempo;
-- @natural_repetida_territorio
SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT departamento, municipio_clave FROM dim_territorio)) FROM dim_territorio;
-- @natural_repetida_tamano
SELECT COUNT(*) - COUNT(DISTINCT clase) FROM dim_tamano;
-- @natural_repetida_causa
SELECT COUNT(*) - COUNT(DISTINCT causa) FROM dim_causa;
-- @natural_repetida_cobertura
SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT grupo_cobertura, tipo_cobertura FROM dim_cobertura)) FROM dim_cobertura;
-- @natural_repetida_fuente
SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT hoja, entidad FROM dim_fuente)) FROM dim_fuente;

-- ======================================================================
-- 3. Hechos sin dimension (huerfanos; todas deben dar 0)
-- ======================================================================

-- @huerfanos_tiempo
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_tiempo d ON d.tiempo_key = f.tiempo_key WHERE d.tiempo_key IS NULL;
-- @huerfanos_territorio
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_territorio d ON d.territorio_key = f.territorio_key WHERE d.territorio_key IS NULL;
-- @huerfanos_tamano
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_tamano d ON d.tamano_key = f.tamano_key WHERE d.tamano_key IS NULL;
-- @huerfanos_causa
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_causa d ON d.causa_key = f.causa_key WHERE d.causa_key IS NULL;
-- @huerfanos_cobertura
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_cobertura d ON d.cobertura_key = f.cobertura_key WHERE d.cobertura_key IS NULL;
-- @huerfanos_fuente
SELECT COUNT(*) FROM fact_incendio f LEFT JOIN dim_fuente d ON d.fuente_key = f.fuente_key WHERE d.fuente_key IS NULL;

-- ======================================================================
-- 4. Tratamiento de faltantes y desconocidos (conteo por miembro)
-- ======================================================================

-- @tiempo_sin_fecha
SELECT COUNT(*) FROM fact_incendio WHERE tiempo_key = 0;

-- @tiempo_anio_sin_mes
SELECT COUNT(*) FROM fact_incendio f JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
WHERE t.anio IS NOT NULL AND t.mes_num IS NULL;

-- @tiempo_calendario_valido
SELECT COUNT(*) FROM fact_incendio f JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
WHERE t.anio IS NOT NULL AND t.mes_num IS NOT NULL;

-- @territorio_sin_departamento
SELECT COUNT(*) FROM fact_incendio f JOIN dim_territorio r ON r.territorio_key = f.territorio_key
WHERE r.departamento = 'Sin departamento';

-- @territorio_sin_municipio
SELECT COUNT(*) FROM fact_incendio f JOIN dim_territorio r ON r.territorio_key = f.territorio_key
WHERE r.municipio = 'Sin municipio';

-- @departamentos_distintos
SELECT COUNT(DISTINCT departamento) FROM dim_territorio WHERE departamento <> 'Sin departamento';

-- @tamano_sin_dato
SELECT COUNT(*) FROM fact_incendio WHERE tamano_key = 0;

-- @causa_sin_registro
SELECT COUNT(*) FROM fact_incendio WHERE causa_key = 0;

-- @causa_varias
SELECT COUNT(*) FROM fact_incendio WHERE causa_key = 7;

-- @cobertura_sin_informar
SELECT COUNT(*) FROM fact_incendio WHERE cobertura_key = 0;

-- @cobertura_varios_tipos
SELECT COUNT(*) FROM fact_incendio WHERE cobertura_key = 12;

-- @fuente_no_aplica
SELECT COUNT(*) FROM fact_incendio f JOIN dim_fuente u ON u.fuente_key = f.fuente_key
WHERE u.entidad = 'No aplica (hoja sin ese campo)';

-- @fuente_sin_dato
SELECT COUNT(*) FROM fact_incendio f JOIN dim_fuente u ON u.fuente_key = f.fuente_key
WHERE u.entidad = 'Sin dato';

-- ======================================================================
-- 5. Conteos por dimension (se comparan con pandas fila por fila)
-- ======================================================================

-- @filas_dim_tiempo
SELECT COUNT(*) FROM dim_tiempo;
-- @filas_dim_territorio
SELECT COUNT(*) FROM dim_territorio;
-- @filas_dim_fuente
SELECT COUNT(*) FROM dim_fuente;

-- @eventos_por_anio
SELECT t.anio, SUM(f.n_eventos) FROM fact_incendio f
JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
WHERE t.anio IS NOT NULL GROUP BY t.anio ORDER BY t.anio;

-- @eventos_por_departamento
SELECT r.departamento, SUM(f.n_eventos) FROM fact_incendio f
JOIN dim_territorio r ON r.territorio_key = f.territorio_key
WHERE r.departamento <> 'Sin departamento'
GROUP BY r.departamento ORDER BY SUM(f.n_eventos) DESC, r.departamento;

-- @eventos_por_hoja
SELECT u.hoja, SUM(f.n_eventos) FROM fact_incendio f
JOIN dim_fuente u ON u.fuente_key = f.fuente_key GROUP BY u.hoja ORDER BY u.hoja;

-- @hectareas_por_region
SELECT r.region, SUM(f.area_total_ha), SUM(f.n_eventos) FROM fact_incendio f
JOIN dim_territorio r ON r.territorio_key = f.territorio_key
GROUP BY r.region ORDER BY SUM(f.area_total_ha) DESC;

-- @eventos_por_causa
SELECT c.causa, SUM(f.n_eventos) FROM fact_incendio f
JOIN dim_causa c ON c.causa_key = f.causa_key
GROUP BY c.causa ORDER BY SUM(f.n_eventos) DESC, c.causa;

-- @eventos_por_grupo_cobertura
SELECT b.grupo_cobertura, SUM(f.n_eventos), SUM(f.area_total_ha) FROM fact_incendio f
JOIN dim_cobertura b ON b.cobertura_key = f.cobertura_key
GROUP BY b.grupo_cobertura ORDER BY SUM(f.n_eventos) DESC;

-- @hectareas_eventos_con_cobertura
SELECT SUM(area_total_ha) FROM fact_incendio WHERE cobertura_key <> 0;
