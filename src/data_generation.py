import pandas as pd
import numpy as np
from faker import Faker
import random

# Seed everything so results are repeatable every time we run this script
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

# ---- Configuration: the "knobs" for our factory ----
NUM_LINES = 5
NUM_MACHINES = 20
MACHINE_TYPES = ["CNC Mill", "Injection Molder", "Press Brake", "Laser Cutter", "Assembly Robot"]
MANUFACTURERS = ["Siemens", "Fanuc", "Bosch", "Mitsubishi Electric", "ABB"]

def generate_machines():
    machines = []
    for i in range(1, NUM_MACHINES + 1):
        machine_id = f"M{i:02d}"
        line_id = f"L{random.randint(1, NUM_LINES):02d}"
        machine_type = random.choice(MACHINE_TYPES)
        manufacturer = random.choice(MANUFACTURERS)
        installation_date = fake.date_between(start_date="-5y", end_date="-6m")
        machines.append({
            "machine_id": machine_id,
            "machine_type": machine_type,
            "line_id": line_id,
            "installation_date": installation_date,
            "manufacturer": manufacturer
        })
    return pd.DataFrame(machines)

# ---- More configuration ----
NUM_RUNS = 60000
SHIFTS = ["Morning", "Evening", "Night"]
MATERIALS = [f"MAT{i:02d}" for i in range(1, 11)]
START_DATE = pd.Timestamp("2025-09-01")
END_DATE = pd.Timestamp("2026-08-31")

def generate_production_runs(machines_df):
    runs = []
    total_days = (END_DATE - START_DATE).days
    for i in range(1, NUM_RUNS + 1):
        run_id = f"R{i:06d}"
        run_date = START_DATE + pd.Timedelta(days=random.randint(0, total_days))
        machine_row = machines_df.sample(1).iloc[0]
        machine_id = machine_row["machine_id"]
        line_id = machine_row["line_id"]
        shift_id = random.choice(SHIFTS)
        material_id = random.choice(MATERIALS)
        operator_id = f"OP{random.randint(1, 40):03d}"
        planned_units = random.randint(200, 500)
        produced_units = planned_units
        good_units = produced_units
        defective_units = 0
        runs.append({
            "run_id": run_id,
            "timestamp": run_date,
            "line_id": line_id,
            "machine_id": machine_id,
            "shift_id": shift_id,
            "material_id": material_id,
            "operator_id": operator_id,
            "planned_units": planned_units,
            "produced_units": produced_units,
            "good_units": good_units,
            "defective_units": defective_units
        })
    return pd.DataFrame(runs)

def generate_sensor_readings(runs_df, machines_df):
    runs = runs_df.merge(
        machines_df[["machine_id", "installation_date"]],
        on="machine_id", how="left"
    )
    runs["installation_date"] = pd.to_datetime(runs["installation_date"])

    sensors = []
    for idx, row in runs.iterrows():
        month = row["timestamp"].month
        if month in [5, 6, 7, 8]:
            season_temp_boost = 4
        elif month in [12, 1, 2]:
            season_temp_boost = -3
        else:
            season_temp_boost = 0

        machine_age_days = (row["timestamp"] - row["installation_date"]).days
        machine_age_years = max(machine_age_days / 365, 0)
        drift_factor = min(machine_age_years * 1.5, 10)

        temperature = np.random.normal(loc=70 + season_temp_boost + drift_factor, scale=4)
        vibration = np.random.normal(loc=3 + drift_factor * 0.3, scale=1)
        humidity = np.random.normal(loc=45, scale=8)
        motor_current = np.random.normal(loc=12, scale=2)
        rpm = np.random.normal(loc=1500, scale=100)
        cycle_time = np.random.normal(loc=30 + drift_factor * 0.5, scale=3)
        tool_wear = np.random.uniform(0, 100) + drift_factor * 2
        tool_wear = min(tool_wear, 100)

        sensors.append({
            "sensor_id": f"S{idx+1:06d}",
            "run_id": row["run_id"],
            "timestamp": row["timestamp"],
            "temperature": round(temperature, 2),
            "pressure": round(np.random.normal(loc=100, scale=10), 2),
            "vibration": round(max(vibration, 0), 2),
            "humidity": round(humidity, 2),
            "motor_current": round(motor_current, 2),
            "rpm": round(rpm, 1),
            "cycle_time": round(cycle_time, 2),
            "tool_wear": round(tool_wear, 2)
        })

    return pd.DataFrame(sensors)
# ---- Risk configuration: which machines/materials/shifts are riskier ----
# We deliberately make a few specific ones worse, to create realistic root-cause patterns
HIGH_RISK_MACHINES = ["M07", "M14", "M18"]
HIGH_RISK_MATERIALS = ["MAT03", "MAT09"]
HIGH_RISK_SHIFT = "Night"

def calculate_defect_probability(row):
    base_risk = 0.02  # 2% baseline

    # Sensor-driven risk
    if row["temperature"] > 80:
        base_risk += 0.03
    if row["vibration"] > 5:
        base_risk += 0.025
    if row["tool_wear"] > 75:
        base_risk += 0.03

    # Machine / material / shift risk
    if row["machine_id"] in HIGH_RISK_MACHINES:
        base_risk += 0.02
    if row["material_id"] in HIGH_RISK_MATERIALS:
        base_risk += 0.015
    if row["shift_id"] == HIGH_RISK_SHIFT:
        base_risk += 0.01

    # Interaction effect: a risky machine on the risky shift is worse than either alone
    if row["machine_id"] in HIGH_RISK_MACHINES and row["shift_id"] == HIGH_RISK_SHIFT:
        base_risk += 0.02

    # Cap risk at 40% so it stays believable
    return min(base_risk, 0.40)


def apply_defects(runs_df, sensors_df):
    # Combine runs and sensors into one table so we can calculate risk per run
    merged = runs_df.merge(sensors_df, on="run_id", suffixes=("", "_sensor"))

    defective_units_list = []
    for _, row in merged.iterrows():
        defect_prob = calculate_defect_probability(row)
        # Each unit in the run independently has this chance of being defective
        defective = np.random.binomial(n=row["produced_units"], p=defect_prob)
        defective_units_list.append(defective)

    runs_df = runs_df.copy()
    runs_df["defective_units"] = defective_units_list
    runs_df["good_units"] = runs_df["produced_units"] - runs_df["defective_units"]

    return runs_df
DEFECT_TYPES = ["Surface Crack", "Dimension Error", "Overheating",
                 "Material Contamination", "Alignment Error", "Surface Damage"]
SEVERITIES = ["Low", "Medium", "High"]

def generate_defect_events(runs_df):
    events = []
    defect_id_counter = 1

    # Only runs that actually had defects get a defect_events row
    defective_runs = runs_df[runs_df["defective_units"] > 0]

    for _, row in defective_runs.iterrows():
        defect_type = random.choice(DEFECT_TYPES)
        # Higher severity is rarer than low severity — weighted choice
        severity = random.choices(SEVERITIES, weights=[0.5, 0.35, 0.15])[0]

        events.append({
            "defect_id": f"D{defect_id_counter:06d}",
            "run_id": row["run_id"],
            "defect_type": defect_type,
            "defect_severity": severity,
            "defect_timestamp": row["timestamp"]
        })
        defect_id_counter += 1

    return pd.DataFrame(events)
if __name__ == "__main__":
    machines_df = generate_machines()
    print(machines_df.head(10))
    print("\nTotal machines:", len(machines_df))
    print("\nMachines per line:")
    print(machines_df["line_id"].value_counts().sort_index())

    print("\n" + "="*50)
    print("Generating production runs...")
    runs_df = generate_production_runs(machines_df)
    print(runs_df.head(10))
    print("\nTotal runs:", len(runs_df))
    print("\nDate range:", runs_df["timestamp"].min(), "to", runs_df["timestamp"].max())

    print("\n" + "="*50)
    print("Generating sensor readings...")
    sensors_df = generate_sensor_readings(runs_df, machines_df)
    print(sensors_df.head(10))
    print("\nTotal sensor readings:", len(sensors_df))
    print("\nTemperature stats:")
    print(sensors_df["temperature"].describe())
    print("\n" + "="*50)
    print("Applying defect logic...")
    runs_df = apply_defects(runs_df, sensors_df)
    runs_df["yield_rate"] = runs_df["good_units"] / runs_df["produced_units"]
    runs_df["defect_rate"] = runs_df["defective_units"] / runs_df["produced_units"]

    print(runs_df[["run_id", "machine_id", "shift_id", "material_id", "produced_units", "good_units", "defective_units", "defect_rate"]].head(10))
    print("\nOverall defect rate:", round(runs_df["defective_units"].sum() / runs_df["produced_units"].sum() * 100, 2), "%")
    print("\nDefect rate by machine (top 5 worst):")
    print(runs_df.groupby("machine_id")["defect_rate"].mean().sort_values(ascending=False).head(5))

    print("\n" + "="*50)
    print("Generating defect events...")
    defects_df = generate_defect_events(runs_df)
    print(defects_df.head(10))
    print("\nTotal defect events:", len(defects_df))
    print("\nDefect type distribution:")
    print(defects_df["defect_type"].value_counts())

    print("\n" + "="*50)
    print("Saving to data/raw/ ...")
    machines_df.to_csv("data/raw/machines.csv", index=False)
    runs_df.to_csv("data/raw/production_runs.csv", index=False)
    sensors_df.to_csv("data/raw/sensor_readings.csv", index=False)
    defects_df.to_csv("data/raw/defect_events.csv", index=False)
    print("Done! All 4 CSV files saved to data/raw/")