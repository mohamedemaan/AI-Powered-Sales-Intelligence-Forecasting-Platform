# Sales Intelligence Platform — Changelog

All notable changes to the Sales Intelligence Platform are documented in this file.  
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.9.0] - 2026-10-26

### Added & Enhanced
- **SalesMind AI Animated Welcome Flow** ([`frontend/app/page.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/app/page.tsx)):
  - Built enterprise-grade animated welcome page on root route (`/`) replacing direct dashboard drop.
  - Implemented 7-stage timed animation sequence: ambient cyber grid, connected data nodes, live SVG telemetry line chart with confidence bands, brand reveal, gradient heading, value proposition, and interactive CTAs.
  - Hardware-accelerated CSS animations (`pulseGlow`, `floatCard`, `drawPath`) with `@media (prefers-reduced-motion: reduce)` support and zero heavy external animation dependencies.
- **Route Segregation & Smart App Shell** ([`frontend/components/layout/AppShell.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/components/layout/AppShell.tsx), [`frontend/app/layout.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/app/layout.tsx)):
  - Moved full Overview dashboard from `/` to [`frontend/app/dashboard/page.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/app/dashboard/page.tsx).
  - Created `<AppShell>` client-side wrapper that conditionally isolates public routes (`/`, `/login`, `/landing`) from dashboard chrome, rendering the sidebar exclusively on protected routes.
  - Built-in route guard redirecting unauthenticated users visiting protected endpoints to `/login`.
- **Enhanced Authentication & Session UI** ([`frontend/app/login/page.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/app/login/page.tsx)):
  - Dedicated tabs for Sign In and Create Account supporting `?mode=login` and `?mode=register` query parameters.
  - Active session detection card displaying logged-in role, active status, tenant ID, and 1-click **Launch Dashboard** button.
  - Navigation links back to Welcome Page (`/`).
- **Production Build & Script Resilience** ([`frontend/package.json`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/package.json)):
  - Updated npm build and dev scripts to execute node binaries directly, eliminating Windows ampersand path-splitting errors on folders containing `&`.
  - Resolved TypeScript file transfer typing in [`frontend/app/data/page.tsx`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/frontend/app/data/page.tsx).
  - Verified 100% production build pass across all 19 static and dynamic routes.
  - Executed and verified all 43 backend Pytest tests with 100% pass rate.

---

## [2.8.0] - 2026-10-26

### Added & Integrated
- **Continuous Model Health Logging from Forecast Lab** ([`backend/app/api/v1/endpoints/ml.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/ml.py)):
  - Implemented `save_model_health_run_log` hook inside `POST /api/v1/ml/analyze`.
  - Every time an analysis or forecast is executed in Forecast Lab, the platform persists a `ModelRun` entry (`db.add` & `db.commit`) capturing `model_name`, `mae`, `rmse`, `wape`, `sku`, and `status`.
  - Future prediction intervals are stored in the `Forecast` table linked via `model_run_id`.
- **Root & V1 Model Health Endpoints** ([`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py), [`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py)):
  - Added `@app.get("/api/model-health/latest")` and `@app.get("/api/model-health")` root aliases.
  - Added `@router.get("/model-health/latest")` on `analytics.py`.
  - Added `@app.get("/api/forecast")` and `@app.post("/api/forecast")` root routing.
  - Query now orders chronologically by `ModelRun.created_at.desc()` (replacing UUID-based ordering).
  - WAPE error metrics are normalized across ratio and percentage representations.
- **Interactive Model Benchmark Trigger in Frontend** ([`frontend/app/model-health/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/model-health/page.tsx)):
  - Added `Run Walk-Forward Benchmark` button in the header and within empty state cards to allow 1-click evaluation of active sales data without needing to leave the page.
  - Live state transition from `UNINITIALIZED` to `HEALTHY` with real MAE, RMSE, and WAPE metrics upon run completion.
  - Direct navigation link from Forecast Lab report to Model Health Telemetry ([`frontend/app/forecast/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/forecast/page.tsx)).
- **Database Schema Auto-Migration for Model Runs** ([`backend/app/models/forecast.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/models/forecast.py), [`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py)):
  - Added canonical `model_name` attribute to `ModelRun` model with bi-directional sync to `model_version`.
  - Added canonical alias `ModelHealthLog = ModelRun`.
  - SQLite auto-migration ensures `model_name` column exists on startup.
- **Automated Verification Test** ([`backend/tests/test_audit_fixes.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/tests/test_audit_fixes.py)):
  - Added `test_model_health_persisted_from_forecast_and_root_endpoints` validating end-to-end telemetry persistence.

---

## [2.7.0] - 2026-10-26

### Added
- **Top-of-Overview Data Ingestion & Live Dataset Preview** ([`frontend/app/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/page.tsx), [`frontend/components/dashboard/DataIngestionOverviewCard.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/dashboard/DataIngestionOverviewCard.tsx)):
  - Placed an interactive Data Ingestion & Preview card directly at the top of the Global Overview dashboard.
  - Displays real-time dataset telemetry: loaded record count, active filename, calendar date coverage span, SKU & category totals.
  - Includes a quick drag-and-drop CSV uploader with instant overview cache invalidation and re-calculation upon ingest.
  - Includes a collapsible 10-row dataset preview drawer rendering canonical schema data types and parsed sample transactions.
- **Prominent Sidebar Positioning** ([`frontend/components/layout/Sidebar.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/layout/Sidebar.tsx)):
  - Renamed nav item to `Data Ingestion & Preview` and moved it to position #2 directly beneath `Overview` for immediate visibility.

### Fixed
- **Dataset Ingestion Schema Column Filtering** ([`backend/app/pipelines/etl.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/pipelines/etl.py), [`backend/app/data/validation.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/data/validation.py)):
  - Filtered ingested CSV records strictly to canonical `RawSalesData` attributes, resolving `'Row ID' is an invalid keyword argument for RawSalesData` when uploading Sample Superstore or Kaggle datasets containing unmapped columns like `Row ID`, `Ship Mode`, or `Customer Name`.
- **SQLite SQL Syntax Error in Categories & Products** ([`backend/app/services/analytics_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/analytics_service.py)):
  - Replaced invalid `func.null().label("profit")` with `literal(None).label("profit")`, resolving SQLite `near "(": syntax error`.
- **Forecast Endpoint Schema Consistency** ([`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py)):
  - Ensured `GET /api/v1/analytics/forecast` returns a structured 7-day initialized projection schema even when the database is initially empty.
- **Data Validation & Non-Fabrication Rules** ([`backend/app/data/validation.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/data/validation.py)):
  - Enforced required `units_sold` column validation and rejected negative quantities.
  - Eliminated hidden `df['available_stock'] = 150` synthetic stock fabrication.
- **Test Suite Synchronization** ([`backend/app/api/v1/endpoints/ml.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/ml.py), [`backend/tests/test_reporting.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/tests/test_reporting.py)):
  - Standardized `ml/train` 400 error message prefix (`"Insufficient data: "`).
  - Added `keep_default_na=False` in `test_reporting.py` when evaluating literal `"N/A"` profit strings.

---

## [2.6.0] - 2026-10-23

### Fixed & Audited
- **Inventory Intelligence Non-Fabrication** ([`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py), [`frontend/app/inventory/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/inventory/page.tsx)):
  - Eliminated synthetic `latest_stock = 180.0` default which previously triggered false "Critical Stockout Risk" alerts on retail datasets lacking on-hand stock columns.
  - Added `has_inventory_tracking` field; when stock is omitted from the dataset, the platform returns empirical 30-day velocity, sets `available_stock: null`, and shows an explicit "Empirical Sales Velocity Mode" disclosure banner.
- **Model Health Telemetry & Dynamic Drift Calculation** ([`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py), [`frontend/app/model-health/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/model-health/page.tsx)):
  - Removed hardcoded placeholder `drift_score = 0.042`.
  - Implemented dynamic drift scoring calculated across sequential model evaluation runs (percentage delta in out-of-sample WAPE).
  - Replaced frontend fallback placeholder values (`5.8%`, `12.4 units`, `16.2`, `0.042`) with clean uninitialized indicators (`--`, `No Recorded Runs`, `UNINITIALIZED`).
- **Scenario Simulation Non-Fabrication** ([`backend/app/services/simulation.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/simulation.py), [`frontend/app/scenarios/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/scenarios/page.tsx)):
  - Removed fallback synthetic trajectory (`base_val = 120.0`). The simulation engine now explicitly rejects datasets with < 5 historical observations with a descriptive validation error.
  - Removed synthetic mock option `<option value="SKU-1001">SKU-1001 (Sample)</option>` from the SKU dropdown.
- **Gemini AI Reliability & Official SDK Migration** ([`backend/app/services/gemini_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/gemini_service.py)):
  - Migrated to the official `google-genai` SDK (`from google import genai`) with structured JSON configuration (`GenerateContentConfig`).
  - Removed non-standard/unreachable `gemini-2.5-flash` model which returned HTTP 404; standardized candidate models to `gemini-2.0-flash`, `gemini-1.5-flash`, and `gemini-1.5-pro`.
  - Added resilient fallback to HTTP REST and error diagnostics that never leak secret API keys.
- **Strict Date Range Validation** ([`backend/app/services/reporting_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/reporting_service.py), [`backend/app/services/analytics_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/analytics_service.py)):
  - Added explicit validation raising HTTP 400 when `start_date > end_date` in `/api/v1/analytics/report`.
  - Added inverted date bound normalization in custom period date window resolution.
- **Audit Verification Test Suite** ([`backend/tests/test_audit_fixes.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/tests/test_audit_fixes.py)):
  - Added comprehensive automated test suite validating uninitialized model health null checks, inventory non-fabrication, date range 400 rejections, and simulation boundary conditions.

---

## [2.5.0] - 2026-10-23

### Added
- **Module 1: Dashboard Overview Upgrade** ([`frontend/app/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/page.tsx), [`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py)):
  - Added responsive period filter controls: *All Time*, *Today*, *Last 7 Days*, *Last 30 Days*, *This Month*, *Previous Month*, and *Custom Range*.
  - Added 10 core business KPIs: Total Revenue, Distinct Orders (`COUNT(DISTINCT order_id)`), Total Quantity Sold, Average Order Value (AOV), Total Profit (retaining commercial losses), Operating Profit Margin %, Period-over-period sales growth (+/- %), Forecasted Revenue (7d), Anomalies Detected count, and Active Catalog SKUs.
  - Added deterministic Business Insights banner grounded in historical ledger facts.
  - Upgraded [`KPICard.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/dashboard/KPICard.tsx) with directional percentage trend badges and contextual tooltips.
- **Module 2: Comprehensive Sales Analytics** ([`frontend/app/analytics/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/analytics/page.tsx)):
  - Built dedicated `/analytics` route with 4 interactive tabs:
    1. *Time-Series Trends*: Daily, weekly, and monthly aggregations with Recharts visualization ([`TrendsChart.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/charts/TrendsChart.tsx)), peak & trough highlights, and delta % change.
    2. *Categories & Sub-Categories*: Category revenue contribution % meters, best & lowest category highlights, and detailed sub-category ledger table.
    3. *Product Performance*: Top-selling vs. lowest-selling products, contribution to store sales, and instant search filter.
    4. *Transaction Explorer*: Paginated line-item transactions table with multi-column sorting (Date, Order ID, Revenue, Units, Profit), category filtering, and instant search.
  - Added backend endpoints in [`analytics_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/analytics_service.py): `GET /api/v1/analytics/trends`, `GET /api/v1/analytics/categories`, `GET /api/v1/analytics/products`, and `GET /api/v1/analytics/transactions`.
  - Added `Sales Analytics` navigation link to [`Sidebar.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/layout/Sidebar.tsx).
- **Module 7: Dataset Preview & Data Management** ([`frontend/app/data/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/data/page.tsx), [`backend/app/api/v1/endpoints/data.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/data.py)):
  - Added `GET /api/v1/data/preview` returning filename, row count, column count, schema types, date coverage span, product/category counts, missing-value audit, and sample 10 parsed rows.
  - Added Dataset Preview telemetry cards and sample data grid to the Data Ingestion UI.
- **Module 8: Prediction History Audit Log** ([`frontend/app/model-health/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/model-health/page.tsx), [`backend/app/api/v1/endpoints/ml.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/ml.py)):
  - Added `GET /api/v1/ml/history` to audit persisted model runs, evaluation metrics (MAE, RMSE, WAPE), future prediction horizons, and actuals vs. predictions ground-truth variance.
  - Added Prediction History tab to Model Health page.
- **Module 9: User Account & Workspace Settings** ([`frontend/app/profile/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/profile/page.tsx)):
  - Built dedicated user profile page displaying account identity, UUID, RBAC role, active session status, tenant workspace isolation policies, and password complexity requirements.
  - Added Profile & Workspace link to [`Sidebar.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/layout/Sidebar.tsx).
- **Module 5: Anomaly Investigation Guidance** ([`frontend/app/anomalies/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/anomalies/page.tsx), [`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py)):
  - Added baseline expected units, alert types (Spike / Drop), and root-cause investigation guidance to detected Z-score anomalies.

---

## [2.0.0] - 2026-10-22

### Added
- **Forecast Lab & Model Selection Suite** ([`frontend/app/forecast/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/forecast/page.tsx)):
  - Renamed "Target SKU" to "Target Name" with searchable combobox and custom input supporting both product titles and SKU codes.
  - Added product-to-SKU resolution mapping with unambiguous SKU labels for duplicate product names.
  - Added **Option A (Selected Date)** analysis mode with HTML5 calendar picker and presets (*Latest Recorded*, *Next Day +1d*, *Future +7d*).
  - Added **Option B (Date Range)** analysis mode with dual start/end calendar pickers and presets (*Last 30 Days*, *Last 90 Days*, *Actuals + Next 14d Forecast*).
  - Integrated walk-forward cross-validation engine (`/api/v1/ml/analyze`) auto-selecting champion models (ARIMA vs. Seasonal Naive) based on out-of-sample WAPE and RMSE.
  - Distinguishes historical ledger actuals (solid emerald trace) from forward ML predictions (dashed blue trace and confidence bounds).
- **Professional Sales Summary Report Engine** ([`backend/app/services/reporting_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/reporting_service.py)):
  - Modeled after `Professional_Sales_Summary_Report.csv`.
  - Strict filename standard: `professional_sales_summary_YYYY-MM-DD.csv` using the actual runtime generation date.
  - Clean RFC 4180 detail CSV containing strictly the 7 required columns:
    ```
    Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage
    ```
  - Separate dedicated metadata summary CSV (`professional_sales_summary_summary_YYYY-MM-DD.csv`) and nested structured JSON report.
  - Store-wide distinct order calculation via `COUNT(DISTINCT order_id)` avoiding multi-category order double-counting.
  - Safe commercial loss (negative profit) and negative margin handling.
  - Missing data safeguards: outputs `"N/A"` with documented schema notes rather than fabricating numbers.
- **Reports & Export Center UI** ([`frontend/app/reports/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/reports/page.tsx)):
  - Added interactive commercial performance data grid with sorting on all 7 columns and instant search.
  - Added visual badges for high margins (>= 20% emerald) and commercial losses (red).
  - Added one-click export center for Detail CSV, Summary CSV, JSON, and Print / Save as PDF (`@media print`).
  - Integrated quick export triggers into Forecast Lab for direct 1-click downloads.
- **Database Schema & Pipeline Expansion**:
  - Expanded `RawSalesData` model ([`backend/app/models/data.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/models/data.py)) with `order_id`, `category`, `sub_category`, `total_sales`, and `profit`.
  - Implemented SQLite development startup auto-migration in [`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py).
  - Preserved line-item transaction granularity in [`backend/app/data/validation.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/data/validation.py), eliminating premature table grouping.
  - Enforced atomic ledger overwrite on new uploads (`replace=True`) in [`backend/app/pipelines/etl.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/pipelines/etl.py).
- **New Unit & Integration Test Suite** ([`backend/tests/test_reporting.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/tests/test_reporting.py)):
  - Tests covering detail CSV structure, metadata CSV structure, missing profit `"N/A"` handling, negative margins, API endpoints (`GET/POST /api/v1/analytics/report`), and direct streaming file downloads (`/report/csv`).

### Changed
- Synchronized complete project documentation suite across `docs/` (`PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `API.md`, `DATABASE.md`, `DATA_PIPELINE.md`, `MODELS.md`, `TESTING.md`, `DEPLOYMENT.md`, `ENVIRONMENT.md`, `SECURITY.md`, `MONITORING.md`, `DEBUGGING.md`, `INTEGRATIONS.md`, `MCP_CONNECTION.md`).
- Updated `README.md` and root `AGENTS.md` with verified file links and accurate capabilities.
- Updated `backend/app/api/v1/endpoints/analytics.py` overview endpoint to calculate total sales revenue using `func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * RawSalesData.price)`.
- Updated deduplication logic in `backend/app/api/v1/endpoints/data.py` to preserve distinct orders across identical dates and SKUs.

---

## [1.0.0] - 2026-10-19

### Added
- Initial release of Sales Intel AI with Next.js 14 App Router and FastAPI backend.
- Time-series baseline forecasting (Seasonal Naive, ARIMA) and metric evaluation (MAE, RMSE, WAPE).
- Automated rolling Z-score anomaly detection center.
- Scenario simulation lab for price and discount elasticity.
- Context-aware sales assistant powered by Google Gemini Pro.
- JWT Bearer authentication, user registration, and multi-tenant organization models.
- Docker Compose containerization with PostgreSQL 15, Redis 7, Celery, Prometheus, Grafana, and Nginx.
