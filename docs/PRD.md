# Sales Intelligence Platform
## Product Requirements Document (PRD)

**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Product Type:** AI-Powered Sales Forecasting and Business Intelligence SaaS

---

## 1. Product Overview

The Sales Intelligence Platform is an enterprise-grade AI-powered business intelligence application that transforms historical transaction ledgers into forward demand trajectories, detects operational anomalies, monitors inventory risks, and generates commercial executive reports.

The platform directly integrates empirical ledger analysis, machine learning forecasts (Seasonal Naive and Auto-ARIMA), explainable Gemini Pro intelligence, and export capabilities through a unified Next.js dashboard and FastAPI backend.

All predictions, metrics, and recommendations are strictly grounded in verifiable source data. The system enforces non-fabrication principles, explicitly communicates forecast confidence bounds, and handles missing or zero data safely.

---

## 2. Problem Statement

Modern enterprise sales operations struggle with:

- Disconnected historical ledgers and unreliable manual forecasts.
- Difficulty isolating performance across specific target products, SKUs, and calendar horizons.
- Inflexible forecasting tools that fail to distinguish historical ledger actuals from forward projections.
- Inaccurate order-count reporting resulting from summing order lines across product categories.
- Basic, unstandardized CSV exports lacking essential commercial metrics (orders, quantities, sales, profit, margins).
- Siloed anomaly detection failing to alert teams to stockouts, demand surges, or data drift.
- LLM advisory tools that hallucinate advice without grounded telemetry from live ledgers.

---

## 3. Product Vision

Deliver a reliable, modular, and audit-ready Sales Intelligence SaaS platform that enables commercial executives, analysts, and inventory managers to inspect historical actuals, project future demand, and export professional compliance reports with zero data fabrication.

---

## 4. Target Users & Roles

### Business Owner / Executive
- Reviews consolidated store revenue, active SKU count, margin health, and high-level trends.
- Downloads audited Professional Sales Summary Reports for board and stakeholder reviews.

### Sales Manager & Merchandise Director
- Inspects category and sub-category commercial velocity, margin percentages, and product demand.
- Runs date-range cross-validation to assess promotion and seasonal performance.

### Business & Financial Analyst
- Selects specific Target Names (SKUs or product titles) to evaluate walk-forward forecast accuracy (MAE, RMSE, WAPE).
- Exports clean tabular CSV data for downstream BI tools (Tableau, PowerBI, Excel).

### Inventory & Supply Chain Manager
- Monitors days of supply, stockout risks, velocity metrics, and reorder triggers.

### Platform Administrator
- Manages tenant accounts, user roles (Admin, Analyst, Manager), and system health.

---

## 5. Implementation Status Matrix

| Capability | Module / Route | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Animated Welcome & Auth Flow** | `frontend/app/page.tsx`<br>`frontend/app/login/page.tsx` | **Implemented** | SalesMind AI landing page with 7-stage timed animation, SVG telemetry chart, floating cards, exit transition to auth, and clean AppShell segregation. |
| **Dashboard Overview & KPIs** | `frontend/app/dashboard/page.tsx`<br>`GET /api/v1/analytics/overview` | **Implemented** | Segregated to `/dashboard`; period filters (all, today, 7d, 30d, this_month, last_month, custom), 10 core KPIs, PoP comparisons, deterministic insights. |
| **Sales Analytics Suite** | `frontend/app/analytics/page.tsx`<br>`GET /api/v1/analytics/*` | **Implemented** | Time-series trends (daily/weekly/monthly), category/sub-category contributions, product rankings, and transaction explorer table. |
| **Dataset Ingestion & Preview** | `frontend/app/data/page.tsx`<br>`GET /api/v1/data/preview` | **Implemented** | CSV drag-and-drop, atomic replacement, schema types, date coverage span, missing value audit, and sample 10 rows. |
| **Forecast Lab & Model Selection** | `frontend/app/forecast/page.tsx`<br>`POST /api/v1/ml/analyze` | **Implemented** | Target Name selector, Option A (Selected Date) vs. Option B (Date Range), walk-forward validation (snaive vs ARIMA), 1-click report. |
| **Prediction History Audit** | `frontend/app/model-health/page.tsx`<br>`GET /api/v1/ml/history` | **Implemented** | Audit log of saved model runs, evaluation metrics (MAE, RMSE, WAPE), future horizons, and actuals vs. predictions variance. |
| **Professional Sales Reports** | `frontend/app/reports/page.tsx`<br>`GET /api/v1/analytics/report/csv` | **Implemented** | Category & sub-category breakdown with 7 required columns, `professional_sales_summary_YYYY-MM-DD.csv`, RFC 4180 compliance. |
| **Anomaly Detection Center** | `frontend/app/anomalies/page.tsx`<br>`GET /api/v1/analytics/anomalies` | **Implemented** | Rolling Z-score detection with severity, baseline expected demand, alert types (Spike/Drop), and investigation guidance. |
| **Gemini Pro AI Sales Advisor** | `frontend/app/gemini/page.tsx`<br>`POST /api/v1/analytics/gemini` | **Implemented** | Context-grounded in live revenue, distinct orders, profit, active SKUs, and transaction snapshots with rule-based fallback. |
| **User Profile & Workspace** | `frontend/app/profile/page.tsx`<br>`GET /api/v1/users/me` | **Implemented** | Account identity, UUID, RBAC role, active session status, tenant workspace isolation policies, and password complexity. |
| **Scenario Simulation Lab** | `frontend/app/scenarios/page.tsx`<br>`POST /api/v1/analytics/simulate` | **Implemented** | Interactive what-if pricing and discount elasticity simulation. |
| **Authentication & RBAC** | `POST /api/v1/auth/login` | **Implemented** | JWT Bearer authentication, password hashing (bcrypt), multi-tenant tenant isolation. |

---

## 6. Functional Requirements

### 6.1 Data Ingestion & Schema Preservation
- **CSV Ingestion**: Direct streaming upload via `POST /api/v1/data/upload`.
- **Column Normalization & Aliases**: Canonical mapping recognizing variants for `date`, `order_id`, `sku`, `product_name`, `category`, `sub_category`, `units_sold`, `price`, `total_sales`, `profit`, `discount_pct`, and `available_stock`.
- **Transaction Granularity Preservation**: Raw transaction line items are maintained in `RawSalesData` with full fidelity. The system does not collapse transactions prematurely on upload.
- **Fresh Upload Replacement**: When a new file is uploaded (`replace=True`), existing sales records, model runs, and forecasts are cleared to prevent duplicate data accumulation.
- **Deduplication Safeguards**: `POST /api/v1/data/clean-duplicates` checks `['date', 'sku', 'units_sold', 'order_id', 'product_name', 'total_sales']` ensuring legitimate line items from distinct orders are preserved.

### 6.2 Forecast Lab & Model Selection
- **Target Name Selector**:
  - Replaces legacy SKU-only inputs.
  - Supports searchable dropdown displaying product title, SKU code, and transaction counts.
  - Supports custom text input for ad-hoc SKU queries.
  - Global aggregation option: `"All Products (Global Aggregate)"` (`ALL`).
- **Product-to-SKU Mapping**:
  - Automatically resolves human-readable product names to backend SKUs.
  - Disambiguates duplicate product names with explicit SKU tags (e.g. `Logitech Wireless Mouse [SKU: LOGI-102]`).
- **Date Horizon Analysis Modes**:
  - **Option A: Selected Date**:
    - HTML5 calendar picker with presets (*Latest Recorded Date*, *Next Day +1d*, *Future +7d*).
    - If date is within historical dataset coverage: extracts verified actual transactions, total revenue, units sold, daily averages, and week-over-week deltas.
    - If date is in the future: triggers forward walk-forward ML models to project demand and confidence bounds.
  - **Option B: Date Range**:
    - Start Date and End Date inputs with presets (*Last 30 Days*, *Last 90 Days*, *Actuals + Next 14d Forecast*).
    - Client and server enforce `startDate <= endDate`.
- **Model Engine Selection**:
  - `auto`: Automatically evaluates candidate models over walk-forward rolling test splits and selects the model with lowest out-of-sample WAPE / RMSE.
  - `arima`: Auto-Regressive Integrated Moving Average for autoregressive and trend structures.
  - `baseline`: Seasonal Naive (`snaive`, 7-day cyclical lookback) or Simple Moving Average (`sma`).
- **Visualization & Insights**:
  - Interactive chart plotting actual ledger sales (solid emerald line), forecast projections (dashed blue line), and confidence bands (blue translucent fill).
  - Grounded business insights covering peak sales days, lowest demand periods, and inventory reorder actions.
- **Quick Report Action**: Integrated `"Generate Professional Sales Report"` button directly in Forecast Lab for immediate 1-click export of the selected product and date window.

### 6.3 Professional Sales Summary Report
- **Main Objective**: Replace unstandardized sales summaries with an audited, professional commercial report modeled after `Professional_Sales_Summary_Report.csv`.
- **Filename Convention**:
  - Detail CSV: `professional_sales_summary_YYYY-MM-DD.csv` where `YYYY-MM-DD` is the runtime generation date.
  - Summary CSV: `professional_sales_summary_summary_YYYY-MM-DD.csv`.
- **Clean Tabular Format**: Detail CSV strictly contains data columns without contaminating metadata header rows, guaranteeing 100% compatibility with Pandas `pd.read_csv()`, Tableau, PowerBI, and Excel.
- **Required Report Columns**:
  1. `Category`: Top-level commercial merchandise department. Defaults to `"General"` or `"Uncategorized"` if omitted in source data.
  2. `Sub-Category`: Second-tier merchandise classification. Defaults to product name or SKU if omitted.
  3. `Total_Orders`: Count of distinct orders (`COUNT(DISTINCT order_id)`) containing line items for that category/sub-category. If `order_id` is not present, falls back safely to transaction row count.
  4. `Total_Quantity_Sold`: Integer sum of all units sold (`SUM(units_sold)`).
  5. `Total_Sales_USD`: Dollar revenue formatted as raw decimal with 2 decimal places (`f"{val:.2f}"`) to avoid comma-separated CSV parse errors.
  6. `Total_Profit_USD`: Line-item profit sum. Supports negative numbers for commercial losses (e.g. `-1200.00`). Outputs `"N/A"` if profit data is not present in the dataset.
  7. `Profit_Margin_Percentage`: Ratio of \(\frac{\text{Total Profit}}{\text{Total Sales}} \times 100\) formatted to 2 decimal places. Defaults to `0.00` if sales = 0. Outputs `"N/A"` if profit is missing.
- **Order Count Deduplication Guardrail**:
  - Distinct orders are calculated per category group in the detail breakdown.
  - Store-wide distinct orders in the summary manifest are calculated from the global set of unique `order_id` values—**never by summing category-level order counts**, eliminating double-counting of multi-category customer baskets.
- **Report Delivery Center**:
  - Detail CSV download.
  - Summary CSV download.
  - Full structured JSON download.
  - Print / Save as PDF using `@media print` CSS layout.

### 6.4 Anomaly Detection Center
- Rolling 30-day Z-score analysis flagging demand surges, unexpected drops, and potential stockout events.
- Anomaly severity classification: `High` (|z| >= 3.0), `Medium` (|z| >= 2.5), `Low`, `None`.

### 6.5 Scenario Simulation Lab
- Interactive simulation engine testing demand elasticity under modified unit pricing, discount percentages, and demand multipliers.

### 6.6 Gemini Pro AI Sales Advisor
- Context-aware intelligence grounded in live sales metrics, stock levels, and forecasting models.
- Provides fallback diagnostics when API keys are unconfigured or upstream models return errors.

---

## 7. Supported Data Schema & Aliases

The data pipeline recognizes the following aliases during CSV upload:

| Canonical Field | Type | Recognized Aliases | Required |
| :--- | :--- | :--- | :--- |
| `date` | Date | `date`, `order date`, `order_date`, `transaction_date`, `sales_date`, `time` | **Yes** |
| `order_id` | String | `order id`, `order_id`, `orderid`, `transaction id`, `invoice id`, `invoice_no` | Optional |
| `sku` | String | `sku`, `product id`, `product_id`, `productid`, `item code`, `item_id` | **Yes** |
| `product_name` | String | `product name`, `product_name`, `item name`, `title`, `description` | Optional |
| `category` | String | `category`, `product category`, `department`, `dept` | Optional |
| `sub_category` | String | `sub-category`, `subcategory`, `sub category`, `product sub category` | Optional |
| `units_sold` | Integer | `units_sold`, `units sold`, `quantity`, `qty`, `volume`, `count` | **Yes** (defaults to 1) |
| `total_sales` | Decimal | `sales`, `sales_amount`, `total_sales`, `revenue`, `total revenue`, `amount` | Optional |
| `price` | Decimal | `price`, `unit price`, `unit_price`, `unit_cost` | Optional |
| `profit` | Decimal | `profit`, `total profit`, `net profit`, `margin`, `earnings` | Optional |
| `discount_pct` | Decimal | `discount_pct`, `discount`, `discount_rate`, `discount %` | Optional |
| `available_stock` | Integer | `available_stock`, `stock`, `inventory`, `on_hand`, `quantity_on_hand`| Optional |

---

## 8. Non-Functional Requirements

### 8.1 Data Integrity & Non-Fabrication
- No synthetic numbers, fake revenues, or mock accuracies are displayed when data is missing.
- When optional fields (such as `profit` or `category`) are absent from a dataset, the system explicitly reports `"N/A"` along with schema notes.
- Empty states are surfaced clearly whenever an analysis date or product returns zero matching records.

### 8.2 Performance & Scalability
- Sub-second analytical queries via SQLite / PostgreSQL indexes on `date`, `sku`, `order_id`, `category`, and `sub_category`.
- Large report downloads are streamed directly using RFC 4180 CSV serialization.

### 8.3 Security & Multi-Tenancy
- Passwords hashed using bcrypt.
- JWT Bearer tokens with 60-minute expiration.
- Tenant isolation enforced on protected database queries.
- No sensitive credentials, API keys, or customer PII are logged or exposed in client bundles.

---

## 9. Verification & Acceptance Criteria

A feature is considered verified only when supported by source code and execution evidence:
- **Verified**: Target Name selection with product-to-SKU resolution.
- **Verified**: Selected Date analysis and Date Range filtering.
- **Verified**: Walk-forward cross-validation model selection (Auto, ARIMA, snaive).
- **Verified**: Clean detail CSV matching `Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage`.
- **Verified**: Filename pattern `professional_sales_summary_YYYY-MM-DD.csv`.
- **Verified**: Store-wide distinct order deduplication avoiding category double-counting.
- **Verified**: Negative profit (commercial loss) and zero sales margin handling.
- **Verified**: Browser Print-to-PDF export.

---

**End of Product Requirements Document**
