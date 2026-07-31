# Bluestock MF Capstone - Data Dictionary

Documents every table loaded into `data/db/bluestock_mf.db`, plus the
datasets kept in `data/processed/` that weren't loaded into SQLite.
Source: AMFI India, mfapi.in, NSE/BSE public data (see original capstone
brief for full source list).

---

## dim_fund
Master list of all 40 mutual fund schemes.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (PK) | AMFI's unique scheme identifier code |
| fund_house | TEXT | Asset Management Company (AMC) name, e.g. SBI Mutual Fund |
| scheme_name | TEXT | Full official AMFI scheme name |
| category | TEXT | Equity / Debt |
| sub_category | TEXT | Large Cap / Mid Cap / Small Cap / Liquid / Gilt / etc. |
| plan | TEXT | Regular or Direct |
| launch_date | TEXT | Scheme launch date (YYYY-MM-DD) |
| benchmark | TEXT | Official benchmark index for the scheme |
| expense_ratio_pct | REAL | Annual expense ratio as a percentage |
| exit_load_pct | REAL | Exit load percentage (0 for liquid/index funds) |
| min_sip_amount | INTEGER | Minimum SIP investment amount in INR |
| min_lumpsum_amount | INTEGER | Minimum lumpsum investment amount in INR |
| fund_manager | TEXT | Name of the fund's primary manager |
| risk_category | TEXT | SEBI risk category: Low / Moderate / High / Very High |
| sebi_category_code | TEXT | Internal SEBI code, e.g. EC01 = Large Cap Equity |

---

## fact_nav
Daily NAV history for all 40 schemes, Jan 2022 - May 2026.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK -> dim_fund) | Scheme identifier |
| date | TEXT | NAV date (YYYY-MM-DD) |
| nav | REAL | Net Asset Value in INR |
| daily_return_pct | REAL | Day-over-day % change in NAV; NULL on each scheme's first day |

**Cleaning notes:** dates parsed to datetime, sorted by amfi_code + date,
missing NAV on weekends/holidays forward-filled from the prior available
value, duplicate (amfi_code, date) rows removed, all NAV values validated > 0.

---

## fact_transactions
Investor-level SIP/Lumpsum/Redemption transactions.

| Column | Type | Description |
|---|---|---|
| tx_id | INTEGER (PK, autoincrement) | Internal transaction ID (not from source data) |
| investor_id | TEXT | Unique investor identifier, e.g. INV003054 |
| amfi_code | TEXT (FK -> dim_fund) | Scheme the transaction was made in |
| transaction_date | TEXT | Date of transaction |
| transaction_type | TEXT | SIP / Lumpsum / Redemption (standardised casing) |
| amount_inr | INTEGER | Transaction amount in INR; validated > 0 |
| state | TEXT | Investor's state (12 Indian states covered) |
| city | TEXT | Investor's city |
| city_tier | TEXT | T30 (Top 30 cities) or B30 (Beyond Top 30), per AMFI classification |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ |
| gender | TEXT | Male / Female |
| annual_income_lakh | REAL | Annual income in INR lakh |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque |
| kyc_status | TEXT | Verified / Pending |

**Cleaning notes:** transaction_type values standardised to title case then
mapped to SIP/Lumpsum/Redemption; rows with amount_inr <= 0 removed;
duplicate rows dropped. kyc_status values checked against {Verified, Pending}.

---

## fact_performance
Point-in-time performance and risk metrics per scheme.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK -> dim_fund) | Scheme identifier |
| as_of_date | TEXT | **Assumption:** source CSV does not carry an explicit as-of date column; this field is currently NULL for all rows. Treat all metrics in this table as reflecting the same snapshot date as when the original dataset was generated (see capstone brief: figures anchored to Dec 2025 / May 2026 market data). Flagged here rather than silently guessing a date. |
| return_1yr_pct | REAL | 1-year absolute return % |
| return_3yr_pct | REAL | 3-year CAGR % |
| return_5yr_pct | REAL | 5-year CAGR % |
| benchmark_3yr_pct | REAL | Benchmark index 3yr CAGR, for comparison |
| alpha | REAL | Return above benchmark (return_3yr - benchmark_3yr) |
| beta | REAL | Sensitivity to market movement (1.0 = moves with market) |
| sharpe_ratio | REAL | Risk-adjusted return; higher is better, >1 considered good |
| sortino_ratio | REAL | Like Sharpe, but penalises only downside volatility |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns |
| max_drawdown_pct | REAL | Worst peak-to-trough decline (negative value) |
| aum_crore | INTEGER | Assets Under Management for this scheme, in INR crore |
| expense_ratio_pct | REAL | Annual expense ratio %; validated in range 0.1%-2.5% |
| morningstar_rating | INTEGER | 1-5 star rating (simulated, based on Sharpe ratio) |
| risk_grade | TEXT | Risk grade label matching dim_fund.risk_category |

**Cleaning notes:** all numeric columns coerced to numeric type (non-numeric
values would become NULL, none found); rows flagged (not removed) if
sharpe_ratio < 0 or expense_ratio_pct outside 0.1%-2.5% - none were flagged
in this dataset. Descriptive columns (scheme_name, fund_house, category,
plan) intentionally excluded from this table since they already live in
dim_fund - join on amfi_code to get them.

---

## fact_aum
Quarterly AUM by fund house.

| Column | Type | Description |
|---|---|---|
| fund_house | TEXT | AMC name |
| date | TEXT | Quarter-end date |
| aum_lakh_crore | REAL | AUM in INR lakh crore |
| aum_crore | INTEGER | AUM in INR crore |
| num_schemes | INTEGER | Number of schemes run by this fund house at this date |

---

## Datasets kept in data/processed/ but NOT loaded into SQLite

These were cleaned on Day 2 but don't fit the fund-level/date-level star
schema cleanly (they're industry-wide time series or reference tables), so
they're kept as CSVs for direct Pandas analysis instead:

| File | Description |
|---|---|
| clean_monthly_sip_inflows.csv | Industry-wide monthly SIP inflow, active/new SIP accounts, and pre-computed YoY growth %. Not fund-level, so no natural join key to dim_fund. |
| clean_category_inflows.csv | Net inflow by fund category per month (Large Cap, Mid Cap, etc.) |
| clean_industry_folio_count.csv | Total MF folio counts (crore) split by Equity/Debt/Hybrid/Others |
| clean_portfolio_holdings.csv | Top equity holdings (stock, weight %, sector) per fund, as of Dec 2025 |
| clean_benchmark_indices.csv | Daily closing values for Nifty 50, Nifty 100, Nifty Midcap 150, BSE SmallCap, CRISIL Liquid & Gilt indices |

---

## Known assumptions / limitations

1. **fact_performance.as_of_date is NULL for all rows** - the source
   dataset doesn't provide this explicitly. Documented above rather than
   fabricating a date.
2. **SIP YoY growth (Query 3)** is computed two ways: the "true" industry
   figure lives in clean_monthly_sip_inflows.csv (not in SQLite); a
   fund-level proxy is computed directly from fact_transactions instead,
   summing SIP transaction amounts by month. These are not the same
   number and shouldn't be confused - see the note in queries.sql.
3. **nav_history forward-fill**: any date range where a scheme's very
   first NAV record starts after 2022-01-01 will not be backfilled prior
   to that scheme's actual first NAV date - forward-fill only applies
   within each scheme's own observed date range, not before it.
