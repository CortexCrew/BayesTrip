"""Shared writer for BayesTrip_Data.xlsx: each pipeline step writes/replaces its own sheet."""

from pathlib import Path

import pandas as pd

WORKBOOK_PATH = Path(__file__).resolve().parents[2] / "data" / "BayesTrip_Data.xlsx"


def write_sheet(sheet_name: str, df: pd.DataFrame) -> None:
    WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if WORKBOOK_PATH.exists():
        with pd.ExcelWriter(WORKBOOK_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(WORKBOOK_PATH, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def read_sheet(sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(WORKBOOK_PATH, sheet_name=sheet_name)


def list_sheets() -> list[str]:
    if not WORKBOOK_PATH.exists():
        return []
    return pd.ExcelFile(WORKBOOK_PATH).sheet_names
