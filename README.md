# YieldWatch — Manufacturing Line Yield & Defect Root-Cause Analytics Platform

A simulated manufacturing analytics platform that identifies which production lines, machines, shifts, and materials drive defect rates, predicts high-defect production runs, and ranks the contributing factors behind quality issues.

## Business Problem

A manufacturing plant running multiple production lines, machines, shifts, and material batches needs to understand:

- Which lines, machines, shifts, and materials have the highest defect rates
- Which combinations of these factors compound into unusually high risk
- Which sensor/process variables are associated with defects
- Whether a production run is likely to result in high defects, before it happens

## Business Objective

Give plant management a data-driven way to prioritize maintenance, staffing, and material sourcing decisions by surfacing the specific, ranked factors most associated with defects — rather than relying on anecdote or intuition.

## Dataset

**The dataset is fully synthetic**, generated with Python (Pandas, NumPy, Faker) to simulate 12 months of manufacturing activity: 60,000 production runs across 20 machines, 5 production lines, 3 shifts, and 10 material types.

The data was not randomly generated — it was built with deliberate, realistic structure:

- **Multi-factor defect risk**: base defect probability increases with sensor readings (temperature, vibration, tool wear), specific high-risk machines, materials, and shifts, plus interaction effects (e.g., a risky machine on the night shift is worse than either factor alone)
- **Seasonality**: summer months run hotter, increasing defect risk
- **Machine drift**: older machines gradually develop higher vibration, temperature, and tool wear
- **Intentional data quality issues**: missing sensor readings, duplicate records, inconsistent category labels, and impossible sensor values were deliberately injected and then identified/corrected, to practice real-world data cleaning

This project was not used in a real factory — all findings reflect patterns in the synthetic dataset, not observed real-world manufacturing behavior.

## Architecture

Synthetic Data Generation (Python/Faker)

↓

Raw CSV Files

↓

Data Quality Checks & Cleaning

↓

SQLite Database (relational, 4 tables)

↓

SQL Analytics (20 queries)

↓

Python EDA (Matplotlib/Seaborn)

↓

Feature Engineering (leakage-safe)

↓

Machine Learning (Logistic Regression, Random Forest)

↓

Model Explainability (feature importance)

↓

Root-Cause Analysis (structured report)

↓

Power BI Dashboard (4 pages)

↓

GitHub Documentation

## Tech Stack

Python, Pandas, NumPy, Faker, SQLite, SQL, Scikit-learn, Matplotlib, Seaborn, Power BI, Git/GitHub

## Database Schema

**production_runs** — one row per production batch (run_id, timestamp, line_id, machine_id, shift_id, material_id, operator_id, planned/produced/good/defective units, yield_rate, defect_rate)

**sensor_readings** — one row per run (temperature, pressure, vibration, humidity, motor_current, rpm, cycle_time, tool_wear)

**defect_events** — one row per run that had defects (defect_type, defect_severity, defect_timestamp)

**machines** — one row per machine (machine_type, line_id, installation_date, manufacturer)

Relationships: `production_runs.run_id` → `sensor_readings.run_id` (1:1), `production_runs.run_id` → `defect_events.run_id` (1:1), `machines.machine_id` → `production_runs.machine_id` (1:many)

## Data Pipeline

1. **Generation** (`src/data_generation.py`): builds all 4 raw tables with realistic risk logic, seasonality, and machine drift
2. **Cleaning** (notebook `00_data_cleaning.ipynb`): detects and fixes missing values, duplicates, inconsistent categories, and impossible sensor values
3. **Loading** (notebook `01_database_setup.ipynb`): loads cleaned data into `database/yieldwatch.db`, verifies referential integrity (0 orphaned records)

## SQL Analysis

20 queries across 4 themed files in `sql/`, covering: overview metrics, breakdowns by line/machine/shift/material, defect type distribution, daily/weekly trends, rolling 7-day/30-day defect rates (window functions), and multi-dimension risk combinations with baseline comparison (CTEs, `CASE WHEN`, `HAVING`).

## Key Business Metrics

| Metric                     | Value                        |
| -------------------------- | ---------------------------- |
| Total Production           | 21,002,956 units             |
| Overall Yield Rate         | 94.89%                       |
| Overall Defect Rate        | 5.11%                        |
| Average Production per Run | ~350 units                   |
| Average Defects per Run    | ~17.9 units                  |
| Worst Line                 | L03 (5.82%)                  |
| Worst Machine              | M07 (7.92%)                  |
| Worst Shift                | Night (5.99%)                |
| Worst Material             | MAT09 (6.33%)                |
| Highest-Risk Combination   | M07 + Night + MAT09 (11.27%) |

## Machine Learning

**Target**: `defect_flag` — whether a run's defect rate exceeded the plant average (45%/55% balanced split)

**Approach**: time-aware train/test split (train on first 80% of the year chronologically, test on the last 20%) to realistically simulate predicting on future, unseen data. Note: this means the test set falls disproportionately within the summer high-defect period, a known limitation discussed below.

| Model               | Accuracy | Precision | Recall | F1    | ROC-AUC |
| ------------------- | -------- | --------- | ------ | ----- | ------- |
| Logistic Regression | 0.828    | 0.823     | 0.888  | 0.855 | 0.922   |
| Random Forest       | 0.833    | 0.822     | 0.902  | 0.860 | 0.924   |

Random Forest modestly outperformed Logistic Regression, particularly in recall — consistent with its ability to capture the non-linear threshold effects (e.g., temperature > 80°) and interaction effects (risky machine + night shift) built into the underlying defect-generation logic.

Random Forest confusion matrix (test set): 3,829 true negatives, 1,338 false positives, 672 false negatives, 6,161 true positives.

## Root-Cause Methodology

The root-cause report (`src/root_cause.py`) combines:

1. SQL-style group-level defect rate analysis (worst machine/shift/material)
2. Multi-dimension combination analysis with baseline comparison
3. Random Forest feature importance, grouped into interpretable sensor categories

**Top associated sensor factors**: Tool Wear (54.7%), Vibration (26.8%), Temperature (18.6%)

**Important**: these results describe statistical *association*, not proven *causation*. The correct, defensible interpretation is "tool wear is strongly associated with defect risk," not "tool wear causes defects" — establishing causation would require controlled experiments this dataset cannot provide.

## Power BI Dashboard

4 pages (`powerbi/YieldWatch_Dashboard.pbix`):

- **Manufacturing Overview**: plant-wide KPIs and trend charts
- **Line & Machine Analysis**: defect rate breakdowns, machine × shift and machine × material risk heatmaps, interactive slicers
- **Root Cause Analysis**: worst-performer KPIs, highest-risk combinations table, top contributing factors, sensor comparison, machine-specific trend
- **ML Model Performance**: model comparison table, feature importance chart

## Key Findings

- Machine M07 running the Night shift with material MAT09 shows an 11.27% defect rate — more than double the 5.11% plant average
- Tool wear is the strongest model-associated risk factor, followed by vibration and temperature
- Defect rate rises noticeably in summer months, driven by a temperature threshold effect (a large share of readings cross the 80° risk threshold once the underlying distribution shifts warmer)
- Night shift shows a defect rate roughly 28% higher (relative) than day shifts

## Limitations

- Dataset is synthetic; findings reflect the generation logic, not real factory behavior
- The `defect_flag` target had to be redefined from "any defect vs. none" (99.9% positive) to "above-average defect rate vs. not," since almost every run of ~300+ units contained at least one defective unit
- The time-based train/test split places the entire test set within the summer high-defect period, which may make model performance appear different than a full-year, multi-season holdout would show
- Several engineered sensor features (temperature, vibration, tool_wear) are correlated with each other (driven by the same underlying machine-age effect), which can make it harder for a model to isolate which one matters most in isolation
