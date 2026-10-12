"""
BayesTrip Evaluation Metrics
=============================
Runs 10-15 different evidence combinations through the full BayesTrip pipeline
and evaluates each trial using three metrics:

  1. Route Distance Reduction (%)
  2. Travel-Time Reduction (%)
  3. One-Day Itinerary Feasibility

The HMM-generated itinerary (Viterbi-ordered) is compared with a naive
BASELINE that visits the same five destinations in the order they were ranked
by the Bayesian posterior (highest -> lowest).

OSRM is called to get pairwise road distances and travel times for both
orderings.  The tour distance/time is the sum of consecutive-leg values
(open-path comparison, no return-to-origin leg).

Results are saved to:
  data/BayesTrip_Evaluation_Metrics.xlsx
  Sheets: All_Trials | Sample_Review_5 | Summary_Statistics
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so local imports work
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommendation_engine.bayesian_inference import Evidence, top_n
from recommendation_engine.hmm_viterbi import decode_sequence
from recommendation_engine.itinerary import build_itinerary
from data_generation.common.workbook import read_sheet

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving/{coords}"

DAY_START_STR = "09:00"
DAY_END_STR   = "20:30"
VISIT_DURATION_MIN = 60   # assumed visit time per stop (minutes)

# ---------------------------------------------------------------------------
# 15 Diverse Evidence Trial Combinations
# Valid states discovered from CPT:
#   Age          : Student, Adult
#   Budget       : Low, Medium, High
#   Interest     : Entertainment, History, Nature, Shopping, Spiritual
#   Travel Type  : Family, Friends, Solo
#   Weather      : Sunny, Rainy
# ---------------------------------------------------------------------------
TRIALS: list[dict] = [
    # T01 - Student history seeker, low budget, friends, sunny
    {"trial_id": "T01", "age": "Student", "budget": "Low",    "interest": "History",       "travel_type": "Friends", "weather": "Sunny"},
    # T02 - Adult nature lover, medium budget, family, sunny
    {"trial_id": "T02", "age": "Adult",   "budget": "Medium", "interest": "Nature",        "travel_type": "Family",  "weather": "Sunny"},
    # T03 - Adult spiritual, high budget, solo, sunny
    {"trial_id": "T03", "age": "Adult",   "budget": "High",   "interest": "Spiritual",     "travel_type": "Solo",    "weather": "Sunny"},
    # T04 - Student shopping, medium budget, friends, rainy
    {"trial_id": "T04", "age": "Student", "budget": "Medium", "interest": "Shopping",      "travel_type": "Friends", "weather": "Rainy"},
    # T05 - Adult entertainment, low budget, family, sunny
    {"trial_id": "T05", "age": "Adult",   "budget": "Low",    "interest": "Entertainment", "travel_type": "Family",  "weather": "Sunny"},
    # T06 - Adult history, low budget, solo, rainy
    {"trial_id": "T06", "age": "Adult",   "budget": "Low",    "interest": "History",       "travel_type": "Solo",    "weather": "Rainy"},
    # T07 - Student nature, high budget, friends, rainy
    {"trial_id": "T07", "age": "Student", "budget": "High",   "interest": "Nature",        "travel_type": "Friends", "weather": "Rainy"},
    # T08 - Adult spiritual, high budget, family, sunny
    {"trial_id": "T08", "age": "Adult",   "budget": "High",   "interest": "Spiritual",     "travel_type": "Family",  "weather": "Sunny"},
    # T09 - Adult nature, medium budget, solo, rainy
    {"trial_id": "T09", "age": "Adult",   "budget": "Medium", "interest": "Nature",        "travel_type": "Solo",    "weather": "Rainy"},
    # T10 - Adult entertainment, high budget, family, sunny
    {"trial_id": "T10", "age": "Adult",   "budget": "High",   "interest": "Entertainment", "travel_type": "Family",  "weather": "Sunny"},
    # T11 - Student spiritual, low budget, friends, rainy
    {"trial_id": "T11", "age": "Student", "budget": "Low",    "interest": "Spiritual",     "travel_type": "Friends", "weather": "Rainy"},
    # T12 - Adult history, low budget, solo, rainy
    {"trial_id": "T12", "age": "Adult",   "budget": "Low",    "interest": "History",       "travel_type": "Solo",    "weather": "Rainy"},
    # T13 - Student shopping, medium budget, family, sunny
    {"trial_id": "T13", "age": "Student", "budget": "Medium", "interest": "Shopping",      "travel_type": "Family",  "weather": "Sunny"},
    # T14 - Student entertainment, medium budget, friends, sunny
    {"trial_id": "T14", "age": "Student", "budget": "Medium", "interest": "Entertainment", "travel_type": "Friends", "weather": "Sunny"},
    # T15 - Adult nature, high budget, friends, rainy
    {"trial_id": "T15", "age": "Adult",   "budget": "High",   "interest": "Nature",        "travel_type": "Friends", "weather": "Rainy"},
]

# 5 samples to review in depth
SAMPLE_REVIEW_IDS = ["T01", "T03", "T05", "T09", "T12"]

# ---------------------------------------------------------------------------
# OSRM helpers
# ---------------------------------------------------------------------------

def _osrm_matrix(coords: list[dict]) -> tuple[list[list[float]], list[list[float]]]:
    """Returns (distances_m, durations_s) matrices via OSRM table service."""
    coord_str = ";".join(f"{c['lng']},{c['lat']}" for c in coords)
    url = OSRM_TABLE_URL.format(coords=coord_str)
    resp = requests.get(url, params={"annotations": "duration,distance"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok":
        raise ValueError(f"OSRM error: {data}")
    return data["distances"], data["durations"]


def _tour_distance_and_time(
    sequence: list[str],
    coord_lookup: dict[str, dict],
) -> tuple[float, float]:
    """
    Sum of consecutive-leg road distances (km) and travel times (min)
    for an OPEN path (no return-to-origin leg).
    """
    pts = [{"lat": coord_lookup[pid]["lat"], "lng": coord_lookup[pid]["lng"]}
           for pid in sequence]
    dist_m, dur_s = _osrm_matrix(pts)

    total_dist_km  = 0.0
    total_time_min = 0.0
    for i in range(len(sequence) - 1):
        d = dist_m[i][i + 1]
        t = dur_s[i][i + 1]
        if d is None or t is None:
            raise ValueError(
                f"OSRM returned None for leg {sequence[i]} -> {sequence[i + 1]}"
            )
        total_dist_km  += d / 1000.0
        total_time_min += t / 60.0

    return round(total_dist_km, 3), round(total_time_min, 3)


# ---------------------------------------------------------------------------
# Feasibility check
# ---------------------------------------------------------------------------

def _check_feasibility(total_travel_min: float, n_stops: int) -> tuple[bool, str]:
    """
    Returns (is_feasible, detail_string).
    Available window: 09:00-20:30 = 690 minutes.
    Required = total_travel_min + n_stops * VISIT_DURATION_MIN.
    """
    fmt = "%H:%M"
    day_start    = datetime.strptime(DAY_START_STR, fmt)
    day_end      = datetime.strptime(DAY_END_STR,   fmt)
    available    = (day_end - day_start).seconds / 60  # 690
    total_visit  = n_stops * VISIT_DURATION_MIN
    total_req    = total_travel_min + total_visit
    feasible     = total_req <= available
    detail = (
        f"Travel={total_travel_min:.1f} min + "
        f"Visits={total_visit} min ({n_stops}x{VISIT_DURATION_MIN}) "
        f"= {total_req:.1f} min | Available={available:.0f} min "
        f"({'FEASIBLE' if feasible else 'NOT FEASIBLE'})"
    )
    return feasible, detail


# ---------------------------------------------------------------------------
# Per-trial runner
# ---------------------------------------------------------------------------

def run_trial(trial: dict, coord_lookup: dict[str, dict]) -> dict:
    tid = trial["trial_id"]
    ev  = Evidence(
        age=trial["age"],
        budget=trial["budget"],
        interest=trial["interest"],
        travel_type=trial["travel_type"],
        weather=trial["weather"],
    )

    # Bayesian top-5
    top5        = top_n(ev, n=5)
    place_ids   = top5["place_id"].tolist()
    place_names = top5["name"].tolist()
    posteriors  = top5["posterior"].tolist()

    # HMM-Viterbi sequence
    hmm_seq      = decode_sequence(place_ids)
    # Baseline = Bayesian rank order (highest posterior first)
    baseline_seq = place_ids[:]

    # OSRM road distances & times
    hmm_dist_km,      hmm_time_min      = _tour_distance_and_time(hmm_seq,      coord_lookup)
    baseline_dist_km, baseline_time_min = _tour_distance_and_time(baseline_seq, coord_lookup)

    # Metric 1: Distance Reduction
    if baseline_dist_km > 0:
        dist_red = round((baseline_dist_km - hmm_dist_km) / baseline_dist_km * 100, 2)
    else:
        dist_red = 0.0

    # Metric 2: Travel-Time Reduction
    if baseline_time_min > 0:
        time_red = round((baseline_time_min - hmm_time_min) / baseline_time_min * 100, 2)
    else:
        time_red = 0.0

    # Metric 3: One-Day Feasibility (using HMM itinerary)
    feasible, feas_detail = _check_feasibility(hmm_time_min, len(hmm_seq))

    # Itinerary strings (human-readable)
    def seq_str(seq):
        return " -> ".join(
            f"{coord_lookup[pid]['name']}"
            for pid in seq
        )

    top5_str = "; ".join(
        f"{pid}:{name}({post:.4f})"
        for pid, name, post in zip(place_ids, place_names, posteriors)
    )

    return {
        "Trial ID":                          tid,
        "Age":                               trial["age"],
        "Budget":                            trial["budget"],
        "Interest":                          trial["interest"],
        "Travel Type":                       trial["travel_type"],
        "Weather":                           trial["weather"],
        "Top-5 Bayesian (id:name:posterior)": top5_str,
        "Baseline Itinerary":                seq_str(baseline_seq),
        "HMM Itinerary":                     seq_str(hmm_seq),
        "Baseline Distance (km)":            baseline_dist_km,
        "HMM Distance (km)":                 hmm_dist_km,
        "Distance Reduction (%)":            dist_red,
        "Baseline Travel Time (min)":        baseline_time_min,
        "HMM Travel Time (min)":             hmm_time_min,
        "Travel-Time Reduction (%)":         time_red,
        "One-Day Feasible?":                 "Yes" if feasible else "No",
        "Feasibility Detail":                feas_detail,
    }


# ---------------------------------------------------------------------------
# Sample review logic
# ---------------------------------------------------------------------------

def _review_sample(row: dict) -> dict:
    dist_red = row["Distance Reduction (%)"]
    time_red = row["Travel-Time Reduction (%)"]
    feasible = row["One-Day Feasible?"]
    hmm_dist = row["HMM Distance (km)"]
    hmm_time = row["HMM Travel Time (min)"]

    positives, issues = [], []

    # Distance
    if dist_red >= 20:
        positives.append(f"Excellent distance reduction ({dist_red:.1f}%).")
    elif 10 <= dist_red < 20:
        positives.append(f"Good distance reduction ({dist_red:.1f}%).")
    elif 0 <= dist_red < 10:
        issues.append(f"Low distance reduction ({dist_red:.1f}%) — marginal routing gain.")
    else:
        issues.append(f"Negative distance reduction ({dist_red:.1f}%) — HMM route is longer than baseline!")

    # Time
    if time_red >= 20:
        positives.append(f"Excellent time reduction ({time_red:.1f}%).")
    elif 10 <= time_red < 20:
        positives.append(f"Good time reduction ({time_red:.1f}%).")
    elif 0 <= time_red < 10:
        issues.append(f"Low time reduction ({time_red:.1f}%) — minimal gain.")
    else:
        issues.append(f"Negative time reduction ({time_red:.1f}%) — HMM takes longer than baseline!")

    # Feasibility
    if feasible == "Yes":
        positives.append("Fits within one day (09:00-20:30). Schedule is practical.")
    else:
        issues.append("Does NOT fit within one day. Itinerary is over-packed.")

    # Absolute sanity
    if hmm_dist < 3:
        issues.append(f"Very short tour ({hmm_dist:.2f} km) — all destinations may be very close or a data issue.")
    if hmm_time > 150:
        issues.append(f"Long driving time ({hmm_time:.1f} min total) — consider if this is practical for tourists.")

    # Verdict
    n_neg  = sum(1 for x in [dist_red, time_red] if x < 0)
    if not issues:
        verdict = "GOOD - All metrics pass; output is correct and efficient."
    elif n_neg > 0:
        verdict = "REVIEW NEEDED - HMM performs worse than baseline on at least one metric."
    elif feasible == "No":
        verdict = "NEEDS ATTENTION - Schedule infeasible; itinerary is too aggressive for one day."
    else:
        verdict = "ACCEPTABLE - Minor concerns but overall output is reasonable."

    return {
        "Trial ID":               row["Trial ID"],
        "Profile":                f"{row['Age']}/{row['Interest']}/{row['Travel Type']}",
        "HMM Itinerary":          row["HMM Itinerary"],
        "Distance Reduction (%)": dist_red,
        "Time Reduction (%)":     time_red,
        "One-Day Feasible?":      feasible,
        "Positives":              " | ".join(positives) if positives else "—",
        "Issues":                 " | ".join(issues)    if issues    else "None",
        "Review Verdict":         verdict,
        "Is Sample OK?":          "YES" if "GOOD" in verdict or "ACCEPTABLE" in verdict else "NO",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("BayesTrip — Evaluation Metrics  (15 Trials | 3 Metrics | 5 Reviews)")
    print("=" * 72)

    # Load coordinates
    print("\n[1/4] Loading coordinate data …")
    coords_df = read_sheet("07_Coordinates")
    coord_lookup: dict[str, dict] = {
        row.place_id: {"lat": float(row.latitude), "lng": float(row.longitude), "name": row.place_name}
        for row in coords_df.itertuples()
    }
    print(f"      {len(coord_lookup)} places loaded.")

    # Run all trials
    print(f"\n[2/4] Running {len(TRIALS)} trial combinations …\n")
    results = []
    for trial in TRIALS:
        tid = trial["trial_id"]
        print(f"  {tid}: {trial['age']} | {trial['budget']} | {trial['interest']} "
              f"| {trial['travel_type']} | {trial['weather']} … ", end="", flush=True)
        try:
            row = run_trial(trial, coord_lookup)
            results.append(row)
            print(
                f"DistRed={row['Distance Reduction (%)']:+.1f}%  "
                f"TimeRed={row['Travel-Time Reduction (%)']:+.1f}%  "
                f"Feasible={row['One-Day Feasible?']}"
            )
        except Exception as exc:
            print(f"FAILED — {exc}")
            results.append({
                "Trial ID":   tid,
                "Age":        trial["age"],
                "Budget":     trial["budget"],
                "Interest":   trial["interest"],
                "Travel Type": trial["travel_type"],
                "Weather":    trial["weather"],
                "Error":      str(exc),
            })

    results_df = pd.DataFrame(results)

    # Sample review
    print(f"\n[3/4] Reviewing 5 samples: {SAMPLE_REVIEW_IDS} …\n")
    review_rows = []
    for sid in SAMPLE_REVIEW_IDS:
        match = next((r for r in results if r.get("Trial ID") == sid and "Error" not in r), None)
        if match:
            rev = _review_sample(match)
        else:
            rev = {"Trial ID": sid, "Review Verdict": "FAILED — trial did not complete.", "Is Sample OK?": "NO"}
        review_rows.append(rev)
        print(f"  [{sid}]  Verdict: {rev.get('Review Verdict', 'N/A')}")
        print(f"         OK? {rev.get('Is Sample OK?', 'N/A')}")
        print(f"         Positives: {rev.get('Positives', '—')}")
        print(f"         Issues:    {rev.get('Issues', '—')}\n")

    review_df = pd.DataFrame(review_rows)

    # Summary statistics
    valid = results_df[results_df.get("Distance Reduction (%)") is not None
                       if "Distance Reduction (%)" not in results_df.columns
                       else results_df["Distance Reduction (%)"].notna()].copy()
    if "Distance Reduction (%)" in valid.columns:
        summary_data = {
            "Metric": [
                "Trials Run",
                "Successful Trials",
                "Mean Distance Reduction (%)",
                "Max Distance Reduction (%)",
                "Min Distance Reduction (%)",
                "Mean Travel-Time Reduction (%)",
                "Max Travel-Time Reduction (%)",
                "Min Travel-Time Reduction (%)",
                "One-Day Feasible Count",
                "One-Day Feasibility Rate (%)",
                "Mean HMM Distance (km)",
                "Mean Baseline Distance (km)",
                "Mean HMM Travel Time (min)",
                "Mean Baseline Travel Time (min)",
            ],
            "Value": [
                len(results),
                len(valid),
                round(valid["Distance Reduction (%)"].mean(), 2),
                round(valid["Distance Reduction (%)"].max(),  2),
                round(valid["Distance Reduction (%)"].min(),  2),
                round(valid["Travel-Time Reduction (%)"].mean(), 2),
                round(valid["Travel-Time Reduction (%)"].max(),  2),
                round(valid["Travel-Time Reduction (%)"].min(),  2),
                int((valid["One-Day Feasible?"] == "Yes").sum()),
                round((valid["One-Day Feasible?"] == "Yes").mean() * 100, 1),
                round(valid["HMM Distance (km)"].mean(), 2),
                round(valid["Baseline Distance (km)"].mean(), 2),
                round(valid["HMM Travel Time (min)"].mean(), 2),
                round(valid["Baseline Travel Time (min)"].mean(), 2),
            ],
            "Formula / Notes": [
                "Total trials attempted",
                "Trials without errors",
                "Mean((D_baseline - D_HMM) / D_baseline * 100)",
                "Best-case distance reduction across all trials",
                "Worst-case distance reduction across all trials",
                "Mean((T_baseline - T_HMM) / T_baseline * 100)",
                "Best-case time reduction",
                "Worst-case time reduction",
                "Count of trials where HMM itinerary fits in one day",
                "Feasible trials / Successful trials * 100",
                "Average total road distance of HMM routes",
                "Average total road distance of baseline routes",
                "Average total driving time of HMM routes",
                "Average total driving time of baseline routes",
            ],
        }
    else:
        summary_data = {"Metric": ["All trials failed"], "Value": ["N/A"], "Formula / Notes": [""]}

    summary_df = pd.DataFrame(summary_data)

    # Write Excel
    print("[4/4] Writing Excel file …")
    out_path = PROJECT_ROOT / "data" / "BayesTrip_Evaluation_Metrics.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        results_df.to_excel(writer, sheet_name="All_Trials",          index=False)
        review_df.to_excel( writer, sheet_name="Sample_Review_5",     index=False)
        summary_df.to_excel(writer, sheet_name="Summary_Statistics",  index=False)

    print(f"\n  Saved -> {out_path}")
    print("  Sheets: All_Trials | Sample_Review_5 | Summary_Statistics")
    print("\n" + "=" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
