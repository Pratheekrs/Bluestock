-- Bluestock Fintech - Mutual Fund Capstone
-- Day 2, Task 4: SQLite star schema
-- 5+ tables: dim_fund, dim_date, fact_nav, fact_transactions, fact_performance, fact_aum

DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

-- ---------------------------------------------------------------------
-- DIMENSION: dim_fund
-- ---------------------------------------------------------------------
CREATE TABLE dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    fund_house          TEXT,
    scheme_name         TEXT,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct    REAL,
    exit_load_pct        REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ---------------------------------------------------------------------
-- DIMENSION: dim_date
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    date_id     TEXT PRIMARY KEY,   -- YYYY-MM-DD
    date        TEXT,
    year        INTEGER,
    month       INTEGER,
    quarter     INTEGER,
    is_weekday  INTEGER             -- 1 = weekday, 0 = weekend
);

-- ---------------------------------------------------------------------
-- FACT: fact_nav
-- ---------------------------------------------------------------------
CREATE TABLE fact_nav (
    amfi_code         TEXT,
    date              TEXT,
    nav               REAL,
    daily_return_pct  REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- ---------------------------------------------------------------------
-- FACT: fact_transactions
-- ---------------------------------------------------------------------
CREATE TABLE fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT,
    amfi_code           TEXT,
    transaction_date    TEXT,
    transaction_type    TEXT,
    amount_inr          INTEGER,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date_id)
);

-- ---------------------------------------------------------------------
-- FACT: fact_performance
-- ---------------------------------------------------------------------
CREATE TABLE fact_performance (
    amfi_code           TEXT,
    as_of_date          TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ---------------------------------------------------------------------
-- FACT: fact_aum
-- ---------------------------------------------------------------------
CREATE TABLE fact_aum (
    fund_house      TEXT,
    date            TEXT,
    aum_lakh_crore  REAL,
    aum_crore       INTEGER,
    num_schemes     INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- Indexes for fast lookups on the two foreign-key columns used everywhere
CREATE INDEX idx_fact_nav_code_date ON fact_nav(amfi_code, date);
CREATE INDEX idx_fact_tx_code_date ON fact_transactions(amfi_code, transaction_date);
