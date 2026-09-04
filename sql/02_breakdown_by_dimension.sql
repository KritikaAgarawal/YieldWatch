-- Defect rate and yield by production line
SELECT
    line_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(good_units) * 100.0 / SUM(produced_units), 2) AS yield_pct,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY line_id
ORDER BY defect_pct DESC;

-- Defect rate by machine
SELECT
    machine_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY machine_id
ORDER BY defect_pct DESC;

-- Defect rate by shift
SELECT
    shift_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY shift_id
ORDER BY defect_pct DESC;

-- Defect rate by material
SELECT
    material_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY material_id
ORDER BY defect_pct DESC;
