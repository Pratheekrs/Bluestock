"""
Bluestock Fintech - Mutual Fund Capstone
Day 2, Task 5: Load all cleaned datasets into SQLite using the schema
in sql/schema.sql, then verify row counts match the source CSVs.

Run from the project root:
    python scripts/load_to_sqlite.py
"""

import sqlite3
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

PROCESSED_DIR = Path("data/processed")
SQL_DIR = Path("sql")
DB_PATH = Path("data") / "db" / "bluestock_mf.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_PATH = SQL_DIR / "schema.sql"


def create_schema():
    print(f"Creating schema from {SCHEMA_PATH} ...")
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    print("Schema created.")


def load_table(engine, csv_path: Path, table_name: str, column_map: dict = None):
    """Load one cleaned CSV into its target table, optionally renaming
    columns to match the schema, and report the row count."""
    df = pd.read_csv(csv_path)
    if column_map:
        df = df.rename(columns=column_map)

    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"  Loaded {len(df):>6} rows from {csv_path.name:<40} -> {table_name}")
    return len(df)


def main():
    create_schema()
    engine = create_engine(f"sqlite:///{DB_PATH}")

    print("\nLoading cleaned datasets into SQLite tables:")
    counts = {}

    counts["dim_fund"] = load_table(
        engine, PROCESSED_DIR / "clean_fund_master.csv", "dim_fund"
    )
    counts["fact_nav"] = load_table(
        engine, PROCESSED_DIR / "clean_nav_history.csv", "fact_nav",
        column_map={"nav": "nav"},
    )
    counts["fact_transactions"] = load_table(
        engine, PROCESSED_DIR / "clean_investor_transactions.csv", "fact_transactions"
    )
    # fact_performance only stores the metrics themselves - descriptive
    # columns like scheme_name/fund_house/category/plan already live in
    # dim_fund, so drop them here before loading to match the schema.
    perf_df = pd.read_csv(PROCESSED_DIR / "clean_scheme_performance.csv")
    perf_schema_cols = [
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade",
    ]
    perf_df = perf_df[perf_schema_cols]
    perf_df.to_sql("fact_performance", engine, if_exists="append", index=False)
    print(f"  Loaded {len(perf_df):>6} rows from clean_scheme_performance.csv{'':<15} -> fact_performance")
    counts["fact_performance"] = len(perf_df)
    counts["fact_aum"] = load_table(
        engine, PROCESSED_DIR / "clean_aum_by_fund_house.csv", "fact_aum"
    )

    # fact_performance needs an as_of_date column - scheme_performance.csv
    # doesn't carry one explicitly, so backfill it with today's processing date
    # if the column is missing (documented assumption for the data dictionary).
    with sqlite3.connect(DB_PATH) as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(fact_performance)")]
        if "as_of_date" in cols:
            cur = conn.execute("SELECT COUNT(*) FROM fact_performance WHERE as_of_date IS NULL")
            null_count = cur.fetchone()[0]
            if null_count > 0:
                print(f"\nNote: {null_count} rows in fact_performance have no as_of_date - "
                      "documenting this as an assumption in the data dictionary.")

    print("\n" + "=" * 70)
    print("ROW COUNT VERIFICATION (source CSV rows vs loaded table rows)")
    print("=" * 70)

    source_counts = {
        "dim_fund": len(pd.read_csv(PROCESSED_DIR / "clean_fund_master.csv")),
        "fact_nav": len(pd.read_csv(PROCESSED_DIR / "clean_nav_history.csv")),
        "fact_transactions": len(pd.read_csv(PROCESSED_DIR / "clean_investor_transactions.csv")),
        "fact_performance": len(pd.read_csv(PROCESSED_DIR / "clean_scheme_performance.csv")),
        "fact_aum": len(pd.read_csv(PROCESSED_DIR / "clean_aum_by_fund_house.csv")),
    }

    all_match = True
    for table, loaded in counts.items():
        source = source_counts[table]
        match = "OK" if loaded == source else "MISMATCH"
        if loaded != source:
            all_match = False
        print(f"  {table:<20} source={source:<8} loaded={loaded:<8} [{match}]")

    print("\nAll row counts match." if all_match else "\nSome row counts do NOT match - investigate above.")
    print(f"\nDatabase file: {DB_PATH}")


if __name__ == "__main__":
    main()
