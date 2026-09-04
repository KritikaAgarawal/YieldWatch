-- Overall production summary: total production, good/defective units, yield %, defect %
SELECT
    SUM(produced_units) AS total_production,
    SUM(good_units) AS total_good_units,
    SUM(defective_units) AS total_defective_units,
    ROUND(SUM(good_units) * 100.0 / SUM(produced_units), 2) AS overall_yield_pct,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS overall_defect_pct
FROM production_runs;
