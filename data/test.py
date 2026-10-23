
import pandas as pd

# ============================================================
# 1. LOAD EVALUATION DATA
# ============================================================

file_path = "BayesTrip_Evaluation_Metrics.xlsx"

df = pd.read_excel(file_path)

# Remove summary rows
df = df[
    ~df["Sample"].astype(str).str.upper().str.contains("SUMMARY", na=False)
].copy()

# Remove rows missing essential evaluation data
required_columns = [
    "Sample",
    "Trial",
    "Baseline Distance (km)",
    "HMM Distance (km)"
]

df = df.dropna(subset=required_columns).copy()

# Convert distance columns to numeric
df["Baseline Distance (km)"] = pd.to_numeric(
    df["Baseline Distance (km)"], errors="coerce"
)

df["HMM Distance (km)"] = pd.to_numeric(
    df["HMM Distance (km)"], errors="coerce"
)

df = df.dropna(
    subset=["Baseline Distance (km)", "HMM Distance (km)"]
).copy()

# ============================================================
# 2. VALIDATE THE DATA
# ============================================================

print("=" * 60)
print("BAYESTRIP DATA VALIDATION")
print("=" * 60)

print("Unique scenarios:", sorted(df["Trial"].unique()))
print("Unique baseline samples:", sorted(df["Sample"].unique()))
print("Total baseline comparisons:", len(df))

# ============================================================
# 3. CALCULATE METRICS FOR EACH SCENARIO
# ============================================================

# Each Trial represents one test scenario.
# Each scenario should contain five baseline routes.

results = df.groupby("Trial").agg(
    Baseline_Average=("Baseline Distance (km)", "mean"),
    BayesTrip_Distance=("HMM Distance (km)", "first"),
    Baseline_Comparisons=("Baseline Distance (km)", "count"),
    HMM_Distance_Count=("HMM Distance (km)", "nunique")
)

# Check that each scenario has exactly one distinct HMM distance.
if (results["HMM_Distance_Count"] != 1).any():
    raise ValueError(
        "Some scenarios contain inconsistent HMM distances. "
        "Check the Excel data before calculating the metrics."
    )

# Distance saved in each scenario
results["Distance_Saved_km"] = (
    results["Baseline_Average"]
    - results["BayesTrip_Distance"]
)

# Percentage distance reduction in each scenario
results["Distance_Reduction_Percent"] = (
    results["Distance_Saved_km"]
    / results["Baseline_Average"]
    * 100
)

# Whether BayesTrip beats the average baseline distance
results["Improved"] = (
    results["Distance_Saved_km"] > 0
)

# Validate baseline counts
if not (results["Baseline_Comparisons"] == 5).all():
    print(
        "\nWARNING: Some scenarios do not contain exactly "
        "five baseline comparisons."
    )

# ============================================================
# 4. CALCULATE OVERALL DISTANCE METRICS
# ============================================================

# Give each scenario equal weight.
avg_baseline = results["Baseline_Average"].mean()

avg_bayestrip = results["BayesTrip_Distance"].mean()

# Absolute distance saved, in kilometres
distance_saved = avg_baseline - avg_bayestrip

# Relative reduction compared with the baseline
if avg_baseline > 0:
    reduction = (
        distance_saved / avg_baseline
    ) * 100
else:
    reduction = float("nan")

total_scenarios = len(results)

improved_scenarios = int(
    results["Improved"].sum()
)

scenario_improvement_rate = (
    improved_scenarios / total_scenarios * 100
    if total_scenarios > 0
    else float("nan")
)

# ============================================================
# 5. COMPARE BAYESTRIP WITH INDIVIDUAL BASELINE ROUTES
# ============================================================

df["HMM_Win"] = (
    df["HMM Distance (km)"]
    < df["Baseline Distance (km)"]
)

df["Baseline_Win"] = (
    df["Baseline Distance (km)"]
    < df["HMM Distance (km)"]
)

df["Tie"] = (
    df["Baseline Distance (km)"]
    == df["HMM Distance (km)"]
)

hmm_wins = int(df["HMM_Win"].sum())

baseline_wins = int(df["Baseline_Win"].sum())

ties = int(df["Tie"].sum())

total_comparisons = len(df)

hmm_win_rate = (
    hmm_wins / total_comparisons * 100
    if total_comparisons > 0
    else float("nan")
)

baseline_win_rate = (
    baseline_wins / total_comparisons * 100
    if total_comparisons > 0
    else float("nan")
)

# ============================================================
# 6. CALCULATE ONE-DAY FEASIBILITY
# ============================================================

# IMPORTANT:
# Update these column names to match your Excel file.
#
# The following section assumes your spreadsheet contains:
#   Travel Time (min)
#   Number of Destinations
#   Visit Time per Destination (min)
#   Available Time (min)
#
# If your file does not contain these columns, feasibility
# cannot be independently calculated from this spreadsheet.

feasibility_columns = [
    "Travel Time (min)",
    "Number of Destinations",
    "Visit Time per Destination (min)",
    "Available Time (min)"
]

if all(col in df.columns for col in feasibility_columns):

    # Extract one record per scenario.
    # The HMM itinerary is assumed to be identical across
    # the five baseline comparison rows for each scenario.
    feasibility_data = df.groupby("Trial").first()

    feasibility_data["Total_Visit_Time_min"] = (
        feasibility_data["Number of Destinations"]
        * feasibility_data["Visit Time per Destination (min)"]
    )

    feasibility_data["Total_Required_Time_min"] = (
        feasibility_data["Travel Time (min)"]
        + feasibility_data["Total_Visit_Time_min"]
    )

    feasibility_data["Feasible"] = (
        feasibility_data["Total_Required_Time_min"]
        <= feasibility_data["Available Time (min)"]
    )

    feasible_count = int(
        feasibility_data["Feasible"].sum()
    )

    total_feasibility_scenarios = len(feasibility_data)

    one_day_feasibility = (
        feasible_count / total_feasibility_scenarios * 100
        if total_feasibility_scenarios > 0
        else float("nan")
    )

else:
    feasible_count = None
    total_feasibility_scenarios = None
    one_day_feasibility = None

# ============================================================
# 7. DISPLAY OVERALL RESULTS
# ============================================================

print("\n" + "=" * 60)
print("BAYESTRIP RESULTS AND PERFORMANCE EVALUATION")
print("=" * 60)

print(f"Total test scenarios: {total_scenarios}")
print(f"Total baseline comparisons: {total_comparisons}")

print("\n--- Distance Metrics ---")

print(
    f"Average baseline distance: "
    f"{avg_baseline:.2f} km"
)

print(
    f"Average BayesTrip distance: "
    f"{avg_bayestrip:.2f} km"
)

print(
    f"Average distance saved: "
    f"{distance_saved:.2f} km"
)

print(
    f"Distance reduction: "
    f"{reduction:.2f}%"
)

print("\n--- Baseline Comparison Metrics ---")

print(
    f"BayesTrip wins: "
    f"{hmm_wins}/{total_comparisons}"
)

print(
    f"BayesTrip win rate: "
    f"{hmm_win_rate:.2f}%"
)

print(
    f"Random baseline wins: "
    f"{baseline_wins}/{total_comparisons}"
)

print(
    f"Random baseline win rate: "
    f"{baseline_win_rate:.2f}%"
)

print(f"Tied comparisons: {ties}")

print("\n--- Scenario Improvement ---")

print(
    f"Scenarios improved: "
    f"{improved_scenarios}/{total_scenarios}"
)

print(
    f"Scenario improvement rate: "
    f"{scenario_improvement_rate:.2f}%"
)

print("\n--- One-Day Feasibility ---")

if one_day_feasibility is not None:
    print(
        f"Feasible itineraries: "
        f"{feasible_count}/{total_feasibility_scenarios}"
    )

    print(
        f"One-day feasibility: "
        f"{one_day_feasibility:.2f}%"
    )
else:
    print(
        "Not calculated: the required time columns were "
        "not found in the Excel file."
    )

# ============================================================
# 8. DISPLAY RESULTS FOR ALL SCENARIOS
# ============================================================

print("\n" + "=" * 60)
print("INDIVIDUAL SCENARIO RESULTS")
print("=" * 60)

display_columns = [
    "Baseline_Average",
    "BayesTrip_Distance",
    "Distance_Saved_km",
    "Distance_Reduction_Percent",
    "Baseline_Comparisons",
    "Improved"
]

print(results[display_columns].round(2).to_string())

# ============================================================
# 9. EXPORT RESULTS TO EXCEL
# ============================================================

output_file = "BayesTrip_Corrected_Results.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

    results[display_columns].round(4).to_excel(
        writer,
        sheet_name="Scenario Results"
    )

    overall = pd.DataFrame({
        "Metric": [
            "Total Scenarios",
            "Total Baseline Comparisons",
            "Average Baseline Distance (km)",
            "Average BayesTrip Distance (km)",
            "Average Distance Saved (km)",
            "Distance Reduction (%)",
            "BayesTrip Wins",
            "BayesTrip Win Rate (%)",
            "Random Baseline Wins",
            "Random Baseline Win Rate (%)",
            "Tied Comparisons",
            "Scenarios Improved",
            "Scenario Improvement Rate (%)",
            "One-Day Feasibility (%)"
        ],
        "Value": [
            total_scenarios,
            total_comparisons,
            avg_baseline,
            avg_bayestrip,
            distance_saved,
            reduction,
            hmm_wins,
            hmm_win_rate,
            baseline_wins,
            baseline_win_rate,
            ties,
            improved_scenarios,
            scenario_improvement_rate,
            one_day_feasibility
        ]
    })

    overall.to_excel(
        writer,
        sheet_name="Overall Summary",
        index=False
    )

print(f"\nResults exported to: {output_file}")

