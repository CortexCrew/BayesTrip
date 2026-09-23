

import pandas as pd

from data_generation.common.evidence import read_all
from data_generation.common.workbook import write_sheet


def build() -> pd.DataFrame:
    records = read_all()
    df = pd.DataFrame(records, columns=["agent", "place_id", "variable", "evidence_text", "source", "source_url", "retrieved_at"])
    return df


def main() -> None:
    df = build()
    write_sheet("08_Evidence", df)
    print(f"Wrote {len(df)} rows to 08_Evidence from {df['agent'].nunique()} agents")


if __name__ == "__main__":
    main()
