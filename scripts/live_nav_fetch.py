"""
Bluestock Fintech - Mutual Fund Capstone
Day 1, Task 4/5: Fetch live NAV data from mfapi.in for HDFC Top 100
plus 5 key schemes, parse the JSON response, and save each as a raw CSV.

Run from the project root:
    python scripts/live_nav_fetch.py
"""

import time
import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Task 4 (HDFC Top 100 Direct) + Task 5 (5 key schemes)
SCHEMES = {
    "125497": "HDFC_Top_100",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip",
}

BASE_URL = "https://api.mfapi.in/mf/{code}"


def fetch_scheme_nav(code: str, label: str) -> pd.DataFrame | None:
    """Fetch NAV history for a single scheme code from mfapi.in and return
    it as a DataFrame, or None if the request/parsing fails."""
    url = BASE_URL.format(code=code)
    print(f"\nFetching {label} (AMFI code {code}) from {url} ...")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  !! Request failed for {label} ({code}): {e}")
        return None

    try:
        payload = response.json()
    except ValueError as e:
        print(f"  !! Could not parse JSON for {label} ({code}): {e}")
        return None

    if "data" not in payload or not payload["data"]:
        print(f"  !! No 'data' field found in response for {label} ({code}).")
        print(f"  Response keys: {list(payload.keys())}")
        return None

    df = pd.DataFrame(payload["data"])
    df["amfi_code"] = code
    df["scheme_name"] = payload.get("meta", {}).get("scheme_name", label)

    # mfapi.in returns dates as DD-MM-YYYY strings; keep as-is here,
    # Day 2 cleaning step will standardise formats.
    print(f"  OK - retrieved {len(df)} NAV records for {label}.")
    return df


def main():
    results = {}

    for code, label in SCHEMES.items():
        df = fetch_scheme_nav(code, label)
        if df is not None:
            out_path = RAW_DIR / f"live_nav_{label}_{code}.csv"
            df.to_csv(out_path, index=False)
            print(f"  Saved to {out_path}")
            results[label] = df
        # Be polite to the free public API - small delay between calls
        time.sleep(1)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for code, label in SCHEMES.items():
        status = "OK" if label in results else "FAILED"
        print(f"  {label} ({code}): {status}")

    succeeded = len(results)
    total = len(SCHEMES)
    print(f"\n{succeeded}/{total} schemes fetched successfully.")

    if succeeded < total:
        print("Some schemes failed - check your internet connection or "
              "whether mfapi.in is reachable, then re-run this script.")


if __name__ == "__main__":
    main()
