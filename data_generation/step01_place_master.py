
import pandas as pd

from data_generation.common.places import CITY, PLACES, STATUS_ACTIVE
from data_generation.common.workbook import write_sheet


def build() -> pd.DataFrame:
    rows = [
        {
            "place_id": p["place_id"],
            "name": p["name"],
            "category": p["category"],
            "city": CITY,
            "status": STATUS_ACTIVE,
        }
        for p in PLACES
    ]
    return pd.DataFrame(rows)


def main() -> None:
    df = build()
    write_sheet("01_Place_Master", df)
    print(f"Wrote {len(df)} rows to 01_Place_Master")


if __name__ == "__main__":
    main()
