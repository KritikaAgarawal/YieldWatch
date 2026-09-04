-- Defect type distribution
SELECT
    defect_type,
    COUNT(*) AS defect_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM defect_events), 2) AS pct_of_all_defects
FROM defect_events
GROUP BY defect_type
ORDER BY defect_count DESC;
-- Daily production and defect rate trend
SELECT
    DATE(timestamp) AS production_date,
    SUM(produced_units) AS daily_production,
    SUM(defective_units) AS daily_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS daily_defect_pct
FROM production_runs
GROUP BY DATE(timestamp)
ORDER BY production_date;
-- Weekly defect rate
SELECT
    strftime('%Y-%W', timestamp) AS year_week,
    SUM(produced_units) AS weekly_production,
    SUM(defective_units) AS weekly_defects,
    ROUND(SUM(defective_units) * 100.0 / SUM(produced_units), 2) AS weekly_defect_pct
FROM production_runs
GROUP BY year_week
ORDER BY year_week;

-- Rolling 7-day and 30-day defect rate (based on daily aggregates)
WITH daily AS (
    SELECT
        DATE(timestamp) AS production_date,
        SUM(produced_units) AS daily_production,
        SUM(defective_units) AS daily_defects
    FROM production_runs
    GROUP BY DATE(timestamp)
)
SELECT
    production_date,
    daily_production,
    daily_defects,
    ROUND(
        SUM(daily_defects) OVER (ORDER BY production_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) * 100.0 /
        SUM(daily_production) OVER (ORDER BY production_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
    , 2) AS rolling_7day_defect_pct,
    ROUND(
        SUM(daily_defects) OVER (ORDER BY production_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) * 100.0 /
        SUM(daily_production) OVER (ORDER BY production_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
    , 2) AS rolling_30day_defect_pct
FROM daily
ORDER BY production_date;