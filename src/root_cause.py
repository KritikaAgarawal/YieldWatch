import pandas as pd
import sqlite3
import pickle

def load_data_and_model():
    conn = sqlite3.connect("database/yieldwatch.db")
    runs = pd.read_sql("SELECT * FROM production_runs", conn)
    conn.close()

    with open("models/defect_model.pkl", "rb") as f:
        rf = pickle.load(f)
    with open("models/feature_columns.pkl", "rb") as f:
        feature_columns = pickle.load(f)

    return runs, rf, feature_columns


def calculate_worst_performers(runs):
    plant_defect_rate = runs["defective_units"].sum() / runs["produced_units"].sum() * 100

    worst_machine = runs.groupby("machine_id").apply(
        lambda g: g["defective_units"].sum() / g["produced_units"].sum() * 100, include_groups=False
    ).sort_values(ascending=False)

    worst_shift = runs.groupby("shift_id").apply(
        lambda g: g["defective_units"].sum() / g["produced_units"].sum() * 100, include_groups=False
    ).sort_values(ascending=False)

    worst_material = runs.groupby("material_id").apply(
        lambda g: g["defective_units"].sum() / g["produced_units"].sum() * 100, include_groups=False
    ).sort_values(ascending=False)

    worst_combo = runs.groupby(["machine_id", "shift_id", "material_id"]).apply(
        lambda g: g["defective_units"].sum() / g["produced_units"].sum() * 100 if g["produced_units"].sum() > 1000 else None,
        include_groups=False
    ).dropna().sort_values(ascending=False)

    return plant_defect_rate, worst_machine, worst_shift, worst_material, worst_combo


def calculate_sensor_factors(rf, feature_columns):
    importances = pd.DataFrame({
        "feature": feature_columns,
        "importance": rf.feature_importances_
    }).sort_values("importance", ascending=False)

    sensor_groups = {
        "Tool Wear": ["tool_wear", "tool_wear_anomaly"],
        "Vibration": ["vibration", "vibration_deviation", "vibration_anomaly"],
        "Temperature": ["temperature", "temperature_deviation", "temp_anomaly"],
    }

    sensor_summary = {}
    for group_name, cols in sensor_groups.items():
        group_score = importances[importances["feature"].isin(cols)]["importance"].sum()
        sensor_summary[group_name] = group_score

    sensor_summary = dict(sorted(sensor_summary.items(), key=lambda x: x[1], reverse=True))
    total = sum(sensor_summary.values())

    return sensor_summary, total


def print_report(plant_defect_rate, worst_machine, worst_shift, worst_material, worst_combo, sensor_summary, total):
    print("=" * 55)
    print("YIELDWATCH ROOT-CAUSE ANALYSIS REPORT")
    print("=" * 55)

    print("\nPlant defect rate:")
    print(str(round(plant_defect_rate, 2)) + "%")

    print("\nHighest-risk machine:")
    print(worst_machine.index[0] + " (" + str(round(worst_machine.iloc[0], 2)) + "%)")

    print("\nHighest-risk shift:")
    print(worst_shift.index[0] + " (" + str(round(worst_shift.iloc[0], 2)) + "%)")

    print("\nHighest-risk material:")
    print(worst_material.index[0] + " (" + str(round(worst_material.iloc[0], 2)) + "%)")

    print("\nHighest-risk combination:")
    combo_name = worst_combo.index[0][0] + " + " + worst_combo.index[0][1] + " + " + worst_combo.index[0][2]
    print(combo_name + " (" + str(round(worst_combo.iloc[0], 2)) + "%)")

    print("\nTop associated sensor factors:")
    rank = 1
    for factor in sensor_summary:
        score = sensor_summary[factor]
        pct = round(score / total * 100, 1)
        print(str(rank) + ". " + factor + " (" + str(pct) + "%)")
        rank = rank + 1

    note = "Note: 'Associated with' reflects statistical patterns in historical data, not proven causation. Further engineering investigation is recommended before acting on these findings."

    print("\n" + "=" * 55)
    print(note)
    print("=" * 55)


if __name__ == "__main__":
    runs, rf, feature_columns = load_data_and_model()
    plant_defect_rate, worst_machine, worst_shift, worst_material, worst_combo = calculate_worst_performers(runs)
    sensor_summary, total = calculate_sensor_factors(rf, feature_columns)
    print_report(plant_defect_rate, worst_machine, worst_shift, worst_material, worst_combo, sensor_summary, total)