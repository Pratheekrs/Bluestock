"""
Bluestock Fintech - Mutual Fund Capstone
Day 1, Task 3/6/7: Load all 10 datasets, inspect them, explore fund_master,
and validate AMFI codes between fund_master and nav_history.

Run from the project root:
    python scripts/data_ingestion.py
(adjust RAW_DIR below if your script lives somewhere else)
"""

import pandas as pd
from pathlib import Path

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)

# ---------------------------------------------------------------------------
# 1. Paths & dataset list
# ---------------------------------------------------------------------------
RAW_DIR = Path("data/raw")

DATASETS = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_by_fund_house": "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "industry_folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings": "09_portfolio_holdings.csv",
    "benchmark_indices": "10_benchmark_indices.csv",
}


def load_all_datasets(raw_dir: Path) -> dict:
    """Load every CSV in DATASETS into a dict of DataFrames, printing
    shape/dtypes/head for each, and flagging anything missing."""
    frames = {}
    missing = []

    for name, filename in DATASETS.items():
        path = raw_dir / filename
        print("\n" + "=" * 80)
        print(f"DATASET: {name}  ({filename})")
        print("=" * 80)

        if not path.exists():
            print(f"  !! FILE NOT FOUND at {path} - skipping")
            missing.append(filename)
            continue

        df = pd.read_csv(path)
        frames[name] = df

        print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print("\nDtypes:")
        print(df.dtypes)
        print("\nHead:")
        print(df.head())

    if missing:
        print("\n" + "!" * 80)
        print(f"WARNING: {len(missing)} file(s) missing from {raw_dir}:")
        for m in missing:
            print(f"  - {m}")
        print("!" * 80)

    return frames


def explore_fund_master(frames: dict) -> None:
    """Day 1, Task 6: print unique fund houses, categories, sub-categories, risk grades."""
    if "fund_master" not in frames:
        print("\nfund_master not loaded - skipping exploration.")
        return

    fm = frames["fund_master"]
    print("\n" + "=" * 80)
    print("FUND MASTER EXPLORATION")
    print("=" * 80)

    for col in ["fund_house", "category", "sub_category", "risk_category"]:
        if col in fm.columns:
            uniques = fm[col].dropna().unique()
            print(f"\n{col} ({len(uniques)} unique values):")
            for val in sorted(uniques):
                print(f"  - {val}")
        else:
            print(f"\nColumn '{col}' not found in fund_master - check schema.")


def validate_amfi_codes(frames: dict) -> None:
    """Day 1, Task 7: confirm every amfi_code in fund_master exists in nav_history,
    and write a short data quality summary to reports/day1_data_quality.txt."""
    print("\n" + "=" * 80)
    print("AMFI CODE VALIDATION (fund_master vs nav_history)")
    print("=" * 80)

    lines = []

    if "fund_master" not in frames or "nav_history" not in frames:
        msg = "Cannot validate: fund_master and/or nav_history not loaded."
        print(msg)
        lines.append(msg)
    else:
        fm_codes = set(frames["fund_master"]["amfi_code"].astype(str))
        nav_codes = set(frames["nav_history"]["amfi_code"].astype(str))

        missing_in_nav = fm_codes - nav_codes
        extra_in_nav = nav_codes - fm_codes

        lines.append(f"fund_master schemes: {len(fm_codes)}")
        lines.append(f"nav_history unique schemes: {len(nav_codes)}")
        lines.append(f"Codes in fund_master missing from nav_history: {len(missing_in_nav)}")
        if missing_in_nav:
            lines.append(f"  -> {sorted(missing_in_nav)}")
        lines.append(f"Codes in nav_history not present in fund_master: {len(extra_in_nav)}")
        if extra_in_nav:
            lines.append(f"  -> {sorted(extra_in_nav)}")

        if not missing_in_nav and not extra_in_nav:
            lines.append("RESULT: All AMFI codes match cleanly between the two datasets.")
        else:
            lines.append("RESULT: Mismatches found - review before Day 2 SQL load.")

        # basic null / duplicate checks across all loaded frames, for the summary
        lines.append("\nNull counts per dataset (columns with any nulls):")
        for name, df in frames.items():
            null_cols = df.isnull().sum()
            null_cols = null_cols[null_cols > 0]
            if not null_cols.empty:
                lines.append(f"  {name}: {dict(null_cols)}")
            else:
                lines.append(f"  {name}: no nulls")

        lines.append("\nDuplicate row counts per dataset:")
        for name, df in frames.items():
            dup_count = df.duplicated().sum()
            lines.append(f"  {name}: {dup_count} duplicate rows")

    for line in lines:
        print(line)

    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "day1_data_quality.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nData quality summary written to: {report_path}")


if __name__ == "__main__":
    frames = load_all_datasets(RAW_DIR)
    explore_fund_master(frames)
    validate_amfi_codes(frames)
