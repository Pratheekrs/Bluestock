-- Bluestock Fintech - Mutual Fund Capstone
-- Day 2, Task 6: 10 analytical SQL queries
-- Run against: data/db/bluestock_mf.db
-- (e.g. via: sqlite3 data/db/bluestock_mf.db < sql/queries.sql
--  or open the .db file in DB Browser for SQLite and run these one at a time)

-- =====================================================================
-- 1. Top 5 funds by AUM
-- =====================================================================
SELECT
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- =====================================================================
-- 2. Average NAV per month (across all funds)
-- =====================================================================
SELECT
    strftime('%Y-%m', date) AS year_month,
    ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
GROUP BY year_month
ORDER BY year_month;

-- =====================================================================
-- 3. SIP inflow YoY growth (from monthly_sip_inflows, processed CSV -
--    not in the SQLite DB by default, so this query assumes you've
--    also loaded clean_monthly_sip_inflows.csv into a table called
--    fact_sip_inflows; see note at the bottom of this file)
-- =====================================================================
-- SELECT month, sip_inflow_crore, yoy_growth_pct
-- FROM fact_sip_inflows
-- ORDER BY month;

-- Equivalent computed directly from fact_transactions instead,
-- using SIP transactions only, grouped by year-month:
SELECT
    strftime('%Y-%m', transaction_date) AS year_month,
    SUM(amount_inr) AS total_sip_amount
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY year_month
ORDER BY year_month;

-- =====================================================================
-- 4. Transactions by state
-- =====================================================================
SELECT
    state,
    COUNT(*) AS num_transactions,
    SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- =====================================================================
-- 5. Funds with expense_ratio < 1%
-- =====================================================================
SELECT
    scheme_name,
    fund_house,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct;

-- =====================================================================
-- 6. Top 5 funds by Sharpe ratio (risk-adjusted return)
-- =====================================================================
SELECT
    f.scheme_name,
    f.fund_house,
    p.sharpe_ratio,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 5;

-- =====================================================================
-- 7. Fund count and average expense ratio by category
-- =====================================================================
SELECT
    category,
    COUNT(*) AS num_funds,
    ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio
FROM dim_fund
GROUP BY category
ORDER BY num_funds DESC;

-- =====================================================================
-- 8. Transaction type breakdown (SIP vs Lumpsum vs Redemption)
-- =====================================================================
SELECT
    transaction_type,
    COUNT(*) AS num_transactions,
    SUM(amount_inr) AS total_amount,
    ROUND(AVG(amount_inr), 2) AS avg_amount
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;

-- =====================================================================
-- 9. Average investor transaction amount by age group
-- =====================================================================
SELECT
    age_group,
    COUNT(*) AS num_transactions,
    ROUND(AVG(amount_inr), 2) AS avg_amount
FROM fact_transactions
GROUP BY age_group
ORDER BY age_group;

-- =====================================================================
-- 10. Worst 5 funds by max drawdown (biggest historical loss from peak)
-- =====================================================================
SELECT
    f.scheme_name,
    f.fund_house,
    p.max_drawdown_pct,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.max_drawdown_pct ASC
LIMIT 5;

-- =====================================================================
-- NOTE on Query 3:
-- monthly_sip_inflows.csv (industry-level SIP data with a pre-computed
-- yoy_growth_pct column) was cleaned in Day 2 but was not part of the
-- star schema loaded into SQLite (it's an industry-wide time series,
-- not fund-level, so it doesn't join cleanly to dim_fund/dim_date).
-- It's documented here and in the data dictionary as a dataset kept
-- in data/processed/ for direct Pandas analysis rather than SQL.
-- =====================================================================
