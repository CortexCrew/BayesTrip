"""Runs automated PASS/FAIL checks on every table in BayesTrip_Data.xlsx.

This step re-derives every sum itself rather than trusting the assertions each
generating script already made -- it is the final, independent check across the
whole workbook.
"""

import sys

import pandas as pd

from data_generation.common.workbook import list_sheets, read_sheet, write_sheet

TOLERANCE = 1e-6


def _check(name: str, condition: bool, detail: str) -> dict:
    return {"check": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def build() -> list[dict]:
    sheets = set(list_sheets())
    results = []

    # 1. Exactly 20 places
    if "01_Place_Master" in sheets:
        places = read_sheet("01_Place_Master")
        results.append(_check("01_Place_Master has exactly 20 places", len(places) == 20, f"found {len(places)} rows"))
    else:
        results.append(_check("01_Place_Master has exactly 20 places", False, "sheet not found"))

    # 2. BN prior sums to 1
    if "02_BN_Prior" in sheets:
        prior = read_sheet("02_BN_Prior")
        total = prior["prior_probability"].sum()
        results.append(_check("02_BN_Prior sums to 1", abs(total - 1.0) < TOLERANCE, f"sum={total:.6f}"))
    else:
        results.append(_check("02_BN_Prior sums to 1", False, "sheet not found"))

    # 3. Each CPT variable sums to 1 per place
    if "03_BN_CPT" in sheets:
        cpt = read_sheet("03_BN_CPT")
        sums = cpt.groupby(["place_id", "variable"])["probability"].sum()
        bad = sums[(sums - 1.0).abs() >= TOLERANCE]
        results.append(
            _check(
                "03_BN_CPT: each (place, variable) sums to 1",
                len(bad) == 0,
                "all groups OK" if len(bad) == 0 else f"{len(bad)} groups off, worst error {(bad - 1.0).abs().max():.2e}",
            )
        )
    else:
        results.append(_check("03_BN_CPT: each (place, variable) sums to 1", False, "sheet not found"))

    # 4. Each from_id's transition_probability sums to 1
    if "05_HMM_Transition" in sheets:
        trans = read_sheet("05_HMM_Transition")
        row_sums = trans.groupby("from_id")["transition_probability"].sum(min_count=1)
        max_err = (row_sums - 1.0).abs().max()
        results.append(_check("05_HMM_Transition: each from_id sums to 1", max_err < TOLERANCE, f"max error={max_err:.2e}"))
    else:
        results.append(_check("05_HMM_Transition: each from_id sums to 1", False, "sheet not found"))

    # 5. Each place's emission sums to 1
    if "06_HMM_Emission" in sheets:
        emission = read_sheet("06_HMM_Emission")
        sums = emission.groupby("place_id")["probability"].sum()
        max_err = (sums - 1.0).abs().max()
        results.append(_check("06_HMM_Emission: each place sums to 1", max_err < TOLERANCE, f"max error={max_err:.2e}"))
    else:
        results.append(_check("06_HMM_Emission: each place sums to 1", False, "sheet not found"))

    # 6. pi (initial_probability) sums to 1
    if "04_HMM_Initial" in sheets:
        initial = read_sheet("04_HMM_Initial")
        total = initial["initial_probability"].sum()
        results.append(_check("04_HMM_Initial: initial_probability sums to 1", abs(total - 1.0) < TOLERANCE, f"sum={total:.6f}"))
    else:
        results.append(_check("04_HMM_Initial: initial_probability sums to 1", False, "sheet not found"))

    return results


def main() -> None:
    results = build()
    df = pd.DataFrame(results)
    write_sheet("09_Validation", df)

    for r in results:
        print(f"[{r['status']}] {r['check']} -- {r['detail']}")

    if any(r["status"] == "FAIL" for r in results):
        print("\nOne or more checks FAILED.")
        sys.exit(1)
    print("\nAll checks PASSED.")


if __name__ == "__main__":
    main()
