-- Machine + Shift combinations
SELECT
    machine_id,
    shift_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY machine_id, shift_id
HAVING SUM(produced_units) > 5000   -- ignore combinations with too little data to trust
ORDER BY defect_pct DESC
LIMIT 15;

-- Machine + Material combinations
SELECT
    machine_id,
    material_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY machine_id, material_id
HAVING SUM(produced_units) > 3000
ORDER BY defect_pct DESC
LIMIT 15;

-- Machine + Shift + Material combinations (triple combo - the deepest cut)
SELECT
    machine_id,
    shift_id,
    material_id,
    SUM(produced_units) AS total_production,
    SUM(defective_units) AS total_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
FROM production_runs
GROUP BY machine_id, shift_id, material_id
HAVING SUM(produced_units) > 1000
ORDER BY defect_pct DESC
LIMIT 15;

-- Compare each combination against the plant baseline, flag high-risk ones
WITH baseline AS (
    SELECT SUM(defective_units) * 100.0 / SUM(produced_units) AS plant_defect_pct
    FROM production_runs
),
combo AS (
    SELECT
        machine_id,
        shift_id,
        material_id,
        SUM(produced_units) AS total_production,
        ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS defect_pct
    FROM production_runs
    GROUP BY machine_id, shift_id, material_id
    HAVING SUM(produced_units) > 1000
)
SELECT
    c.machine_id,
    c.shift_id,
    c.material_id,
    c.total_production,
    c.defect_pct,
    ROUND(b.plant_defect_pct, 2) AS plant_baseline_pct,
    ROUND(c.defect_pct - b.plant_defect_pct, 2) AS pct_points_above_baseline,
    CASE
        WHEN c.defect_pct > b.plant_defect_pct * 1.5 THEN 'High Risk'
        WHEN c.defect_pct > b.plant_defect_pct * 1.2 THEN 'Elevated Risk'
        ELSE 'Normal'
    END AS risk_flag
FROM combo c
CROSS JOIN baseline b
ORDER BY c.defect_pct DESC
LIMIT 15;