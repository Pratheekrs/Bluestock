"""
Bluestock Fintech - Mutual Fund Capstone
Day 2, Tasks 1-3: Clean nav_history, investor_transactions, and
scheme_performance. All other datasets are copied through to
data/processed with basic date parsing, since Day 1 found no
anomalies in them.

Run from the project root:
    python scripts/data_cleaning.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

log_lines = []


def log(msg: str):
    print(msg)
    log_lines.append(msg)


def clean_nav_history() -> pd.DataFrame:
    """Day 2, Task 1: parse dates, sort by amfi_code + date, forward-fill
    missing NAV (holidays/weekends), remove duplicates, validate NAV > 0."""
    log("\n" + "=" * 70)
    log("CLEANING: nav_history.csv")
    log("=" * 70)

    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    start_rows = len(df)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    dupes_removed = before_dedup - len(df)
    log(f"Duplicates removed: {dupes_removed}")

    # Reindex each scheme to a full daily calendar and forward-fill NAV
    # across weekends/holidays where the source has gaps.
    filled_frames = []
    for code, group in df.groupby("amfi_code"):
        group = group.set_index("date").sort_index()
        full_range = pd.date_range(group.index.min(), group.index.max(), freq="D")
        group = group.reindex(full_range)
        group["amfi_code"] = code
        group["nav"] = group["nav"].ffill()
        group = group.reset_index().rename(columns={"index": "date"})
        filled_frames.append(group)
    df = pd.concat(filled_frames, ignore_index=True)

    invalid_nav = (df["nav"] <= 0) | df["nav"].isna()
    log(f"Invalid NAV values (<=0 or null) after fill: {invalid_nav.sum()}")
    df = df[~invalid_nav].reset_index(drop=True)

    df["daily_return_pct"] = (
        df.groupby("amfi_code")["nav"].pct_change() * 100
    )

    log(f"Rows before cleaning: {start_rows} | after cleaning: {len(df)}")
    return df


def clean_investor_transactions() -> pd.DataFrame:
    """Day 2, Task 2: standardise transaction_type, validate amount > 0,
    check KYC status values, fix date formats."""
    log("\n" + "=" * 70)
    log("CLEANING: investor_transactions.csv")
    log("=" * 70)

    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    start_rows = len(df)

    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    valid_types = {"Sip", "Lumpsum", "Redemption"}
    type_map = {"Sip": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption"}
    bad_types = ~df["transaction_type"].isin(valid_types)
    log(f"Unrecognised transaction_type values: {bad_types.sum()}")
    df["transaction_type"] = df["transaction_type"].map(type_map)

    invalid_amount = df["amount_inr"] <= 0
    log(f"Invalid amounts (<=0): {invalid_amount.sum()}")
    df = df[~invalid_amount].reset_index(drop=True)

    valid_kyc = {"Verified", "Pending"}
    bad_kyc = ~df["kyc_status"].isin(valid_kyc)
    log(f"Unrecognised kyc_status values: {bad_kyc.sum()}")

    before_dedup = len(df)
    df = df.drop_duplicates()
    log(f"Duplicate rows removed: {before_dedup - len(df)}")

    log(f"Rows before cleaning: {start_rows} | after cleaning: {len(df)}")
    return df


def clean_scheme_performance() -> pd.DataFrame:
    """Day 2, Task 3: validate return values are numeric, flag negative
    Sharpe ratios, check expense_ratio range (0.1% - 2.5%)."""
    log("\n" + "=" * 70)
    log("CLEANING: scheme_performance.csv")
    log("=" * 70)

    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    start_rows = len(df)

    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
        "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
        "max_drawdown_pct", "expense_ratio_pct",
    ]
    for col in numeric_cols:
        non_numeric = pd.to_numeric(df[col], errors="coerce").isna() & df[col].notna()
        if non_numeric.any():
            log(f"  Non-numeric values found in {col}: {non_numeric.sum()}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    negative_sharpe = df["sharpe_ratio"] < 0
    log(f"Funds flagged with negative Sharpe ratio: {negative_sharpe.sum()}")
    if negative_sharpe.any():
        log(f"  -> {df.loc[negative_sharpe, 'scheme_name'].tolist()}")

    out_of_range_expense = ~df["expense_ratio_pct"].between(0.1, 2.5)
    log(f"Funds with expense_ratio outside 0.1%-2.5%: {out_of_range_expense.sum()}")
    if out_of_range_expense.any():
        log(f"  -> {df.loc[out_of_range_expense, 'scheme_name'].tolist()}")

    log(f"Rows before cleaning: {start_rows} | after cleaning: {len(df)}")
    return df


def passthrough_datasets():
    """Remaining 7 datasets had no anomalies on Day 1 - copy through to
    data/processed with basic date parsing where a date column exists."""
    log("\n" + "=" * 70)
    log("PASSTHROUGH: remaining datasets (no anomalies found on Day 1)")
    log("=" * 70)

    passthrough_files = {
        "fund_master": "01_fund_master.csv",
        "aum_by_fund_house": "03_aum_by_fund_house.csv",
        "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
        "category_inflows": "05_category_inflows.csv",
        "industry_folio_count": "06_industry_folio_count.csv",
        "portfolio_holdings": "09_portfolio_holdings.csv",
        "benchmark_indices": "10_benchmark_indices.csv",
    }

    date_like_cols = {"date", "month", "portfolio_date", "launch_date"}

    for name, filename in passthrough_files.items():
        df = pd.read_csv(RAW_DIR / filename)
        for col in df.columns:
            if col in date_like_cols:
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    pass
        out_path = PROCESSED_DIR / f"clean_{name}.csv"
        df.to_csv(out_path, index=False)
        log(f"  {name}: {len(df)} rows -> {out_path}")


def main():
    nav_df = clean_nav_history()
    nav_df.to_csv(PROCESSED_DIR / "clean_nav_history.csv", index=False)

    tx_df = clean_investor_transactions()
    tx_df.to_csv(PROCESSED_DIR / "clean_investor_transactions.csv", index=False)

    perf_df = clean_scheme_performance()
    perf_df.to_csv(PROCESSED_DIR / "clean_scheme_performance.csv", index=False)

    passthrough_datasets()

    log("\n" + "=" * 70)
    log("DONE - all 10 cleaned CSVs written to data/processed/")
    log("=" * 70)

    log_path = Path("reports") / "day2_cleaning_log.txt"
    log_path.parent.mkdir(exist_ok=True)
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\nCleaning log saved to: {log_path}")


if __name__ == "__main__":
    main()
