# Verified Test Metrics & Telemetry Baseline

This document consolidates and contextualizes the empirical test metrics, dataset boundaries, and telemetry figures established during the official Quality Assurance audit of **SalesMind AI (AI-Powered Sales Intelligence & Forecasting Platform)** conducted on **October 30, 2026**.

All figures documented below are sourced directly from the certified enterprise QA report (`Comprehensive_13_Module_QA_Report_10Yrs_Experience.docx`) authored by the Senior QA Architect (10+ Years Experience). In accordance with non-fabrication principles, metrics without empirical backing are marked as *"Not independently verified"* or *"Evidence pending"*.

---

## 1. Executive Metric Summary

| Metric Dimension | QA Reported Value | Verification Source | Status / Audit Notes |
| :--- | :--- | :--- | :--- |
| **Total Ingested Records** | `10,194` transactions | `Data Ingestion & Preview` | Verified from ledger parse without row truncation |
| **Distinct Active SKUs** | `1,862` SKUs | Transaction Catalog Scope | Atomic deduplication and SKU indexing confirmed |
| **Unique Distinct Orders** | `5,111` orders | Ledger Query (`COUNT(DISTINCT order_id)`) | Strict basket uniqueness; no category double-counting |
| **Store-Wide Gross Sales** | `$2,326,534.52` | Global KPI Aggregator | Direct reconciliation against row-level transaction amounts |
| **Net Commercial Profit** | `$292,297.46` | Financial Ledger Aggregation | True net profit retaining commercial loss line items |
| **Average Order Value (AOV)**| `$455.20` | Calculated (`Gross Sales / Distinct Orders`) | Exact mathematical match: `\$2,326,534.52 / 5,111` |
| **Operating Profit Margin** | `12.56%` | Calculated (`Net Profit / Gross Sales`) | Exact mathematical match: `\$292,297.46 / \$2,326,534.52` |
| **Dataset Date Boundaries** | `2023-01-03` to `2026-12-30` | Temporal Coverage Index | Multi-year transactional span validated |
| **Statistical Anomalies** | `434` events | Rolling Z-score ($|Z| \ge 2.0$) | Flagged demand spikes/contractions (e.g., +5.4 sigma) |
| **Forecast Model Error (WAPE)**| `45.2%` | Walk-Forward Cross-Validation | Weighted Absolute Percentage Error across test partition |
| **Forecast Absolute Error (MAE)**| `19.71` units | Walk-Forward Cross-Validation | Mean Absolute Error across test horizon |
| **Model Drift Score** | `0` | Model Health Telemetry | Zero drift detected on active baseline partition |
| **Price Elasticity Coefficient ($E_d$)** | `-0.75` | Scenario Simulation Lab | Calibrated price elasticity for what-if simulations |
| **Export Formats Supported** | `8` formats | Reports & Exports Center | Excel, PDF, Parquet, Detail CSV, Summary CSV, TSV, JSON, Print |
| **Filename Schema Standard** | `professional_sales_summary_YYYY-MM-DD.csv` | RFC 4180 Compliance | Exact runtime pattern validation |

---

## 2. Commercial Financial Metrics & Non-Fabrication Adherence

### 2.1 Distinct Order Count Rule
- **Verified Value**: `5,111`
- **Methodology**: Computed via `SELECT COUNT(DISTINCT order_id) FROM raw_sales_data`.
- **Integrity Rule**: Individual transaction baskets frequently span multiple categories (e.g., *Technology* and *Office Supplies* in the same cart). Under zero-fabrication rules, summing distinct orders across category breakdowns produces an inflated total. The platform enforces single store-wide distinct counting.

### 2.2 Commercial Loss & Negative Margin Preservation
- **Net Profit**: `$292,297.46`
- **Operating Margin**: `12.56%`
- **Integrity Rule**: Commercial losses are never zero-padded or hidden. For example, lines within sub-categories running at a loss (such as *Furniture Tables* at `-8.53%` margin) are preserved in both the database ledger and exported reports.

### 2.3 Handling Missing Schema Attributes
- When raw datasets lack optional columns such as physical warehouse inventory counts or margin sub-allocations, the platform avoids generating artificial placeholders.
- Missing profit/category values: Displayed as `"N/A"`.
- Missing warehouse physical stock: Displayed as `"N/A (Omitted)"` while retaining 30-day demand velocity calculations.

---

## 3. Forecasting Telemetry & Error Context

### 3.1 Model Evaluation Architecture
- **Evaluation Mechanism**: Walk-Forward Cross-Validation on out-of-sample test splits (Auto-ARIMA vs. Seasonal Naive).
- **Anti-Lookahead Boundary**: Historical actuals (`2023-01-03` to `2026-12-30`) display verified transaction data; forward ML models only generate projections when targeting post-coverage or future dates.

### 3.2 Error Metrics In Context
- **Weighted Absolute Percentage Error (WAPE)**: `45.2%`
- **Mean Absolute Error (MAE)**: `19.71` units
- **Technical Context**:
  > [!NOTE]
  > In retail and catalog sales intelligence spanning 1,862 distinct SKUs with intermittent demand, a WAPE of `45.2%` represents an unconstrained multi-SKU walk-forward baseline across volatile demand profiles. It is **not** claimed as an idealized benchmark, but rather as an audited, empirical baseline reflecting real-world transactional variance and seasonal surges without lookahead leakage.

---

## 4. Anomaly Detection Telemetry

- **Detection Algorithm**: Dynamic rolling Z-score with a severity threshold of $|Z| \ge 2.0$.
- **Total Flagged Anomalies**: `434` statistical events.
- **Severity Classifications**:
  - **High Severity ($|Z| \ge 3.0$)**: Severe surges (e.g., peak holiday spike on Dec 02 at `+5.4 sigma`) and structural stockouts.
  - **Medium Severity ($2.0 \le |Z| < 3.0$)**: Transient promotional fluctuations and localized velocity shifts.
- **Root-Cause Telemetry**: Every anomaly event generates baseline expected unit volumes and actionable operational diagnostic notes.

---

## 5. Unverified Claims & Deliberate Exclusions

In alignment with Phase 4 guidelines, the following metrics were **not** independently audited or benchmarked in the source QA report and are strictly recorded as unverified:

| Metric Category | Claimed Status | Audit Observation |
| :--- | :--- | :--- |
| **API Response Latency Under High Concurrency** | *Evidence pending* | Sub-second response observed in single-analyst session; formal multi-user load testing pending |
| **Platform Uptime & SLA Percentage** | *Not independently verified* | 100% availability observed during audit window; long-term SLA monitoring active |
| **External Competitor Benchmark Scores** | *Postponed* | Comparison testing against Power BI, Tableau, and Zoho Analytics deferred per project scope |
| **Model Accuracy Over 100% of SKUs** | *Not claimed* | Forecast telemetry evaluated on global aggregate and primary high-volume series |

---

## 6. Audit Certification Sign-Off

- **Lead QA Author**: Senior QA Architect (10+ Years Enterprise Experience)
- **Certification Date**: October 30, 2026
- **Quality Gate Status**: **100% MODULES PASSED (APPROVED)**
- **Audit Grade**: Enterprise Release Grade

