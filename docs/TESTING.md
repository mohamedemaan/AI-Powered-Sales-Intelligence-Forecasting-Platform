# Sales Intelligence Platform
# Quality Assurance & Testing Strategy

**Document:** TESTING.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Frameworks:** Pytest (Backend API & ML), Jest / React Testing Library (Frontend)

---

## 1. Testing Philosophy & Verification Standards

To guarantee enterprise data integrity and prevent regression:
1. **Never Fabricate Test Results**: Test cases must only be marked as *Passed* when supported by executed command output. In environments where tests have not been executed, they are strictly marked **Not Run**.
2. **Determinism**: Automated tests must run reproducibly against isolated SQLite or PostgreSQL test databases.
3. **Data Integrity Testing**: Calculations involving revenue, distinct orders, profit margins, and time-series boundaries must be tested with known numerical fixtures.
4. **Resilience to Missing Data**: The suite must explicitly test datasets lacking optional columns (such as `profit`, `order_id`, or `category`) to ensure the system falls back safely without crashing or fabricating numbers.

---

## 2. Test Suite Structure & Existing Test Files

```text
backend/tests/
├── test_api.py         # Integration tests for FastAPI endpoints (Overview, ML, Anomaly, Upload, Auth)
├── test_validation.py  # Validation & normalization rules (aliases, negative units, line-item preservation)
├── test_ml.py          # Time-series baseline models (snaive, sma), metric evaluation, model selection
├── test_anomaly.py     # Rolling Z-score anomaly detector edge cases
├── test_reporting.py   # Professional Sales Summary CSV/JSON generation, distinct orders, margins, downloads
└── test_analytics.py   # Overview 10 KPIs, time-series trends, categories, products, transactions, dataset preview, ML history
```

---

## 3. Test Execution Commands

### 3.1 Backend Test Execution (Pytest)
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Execute complete test suite
pytest -v

# Run specific test module
pytest tests/test_reporting.py -v
pytest tests/test_validation.py -v
pytest tests/test_ml.py -v

# Run with test coverage
pytest --cov=app tests/
```

### 3.2 Frontend Test Execution (Jest / Next.js)
```bash
# Navigate to frontend directory
cd frontend

# Run test suite
npm test
```

---

## 4. Comprehensive Test Case Matrix

The following matrix documents the 16 core test specifications across the Forecast Lab, Model Selection, and Professional Sales Summary Report pipelines:

| Test ID | Test Category & Purpose | Prerequisites | Execution Steps | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | **Valid Target Name (Product / SKU)**: Verify user can query a valid product name or SKU. | Dataset loaded with products. | Call `POST /api/v1/ml/analyze` with `target_name="Logitech Mouse"`. | 200 OK. Resolves product name to SKU; returns valid `sales_performance` and chart data. | **Verified (Passed)** |
| **TC-02** | **Unknown Product Name**: Verify system handles queries for non-existent products. | Dataset loaded. | Call `POST /api/v1/ml/analyze` with `target_name="NonExistentSKU999"`. | 400 Bad Request or empty telemetry report with clear message indicating no transactions found. | **Verified (Passed)** |
| **TC-03** | **Product-to-SKU Mapping**: Verify catalog maps duplicate product names to unambiguous SKU codes. | Dataset contains identical product titles across distinct SKUs. | Call `GET /api/v1/data/products`. | 200 OK. Distinct items formatted with disambiguated labels: `"{p_name} [SKU: {sku}]"`. | **Verified (Passed)** |
| **TC-04** | **Selected Historical Date (Option A)**: Verify analysis for a date within ledger coverage. | Dataset covers 2024-01-01 to 2026-12-30. | Call `POST /api/v1/ml/analyze` with `mode="single"`, `selected_date="2026-12-15"`. | 200 OK. `is_forecast: false`, `status: "HISTORICAL ACTUALS"`. Returns verified transactions and WoW delta. | **Verified (Passed)** |
| **TC-05** | **Selected Future Date (Option A)**: Verify forecast trajectory for future dates. | Max ledger date is 2026-12-30. | Call `POST /api/v1/ml/analyze` with `mode="single"`, `selected_date="2027-01-15"`. | 200 OK. `is_forecast: true`, `status: "PROJECTED DEMAND"`. Returns projected units and confidence bounds. | **Verified (Passed)** |
| **TC-06** | **Valid Date Range (Option B)**: Verify inclusive range aggregation. | Dataset contains historical ledger. | Call `POST /api/v1/ml/analyze` with `mode="range"`, `start_date="2026-01-01"`, `end_date="2026-03-31"`. | 200 OK. Filters rows within bounds (inclusive); returns total revenue, daily velocity, peak/low days. | **Verified (Passed)** |
| **TC-07** | **Invalid Date Range**: Verify boundary validation rejects reversed dates. | System running. | Submit `start_date="2026-12-31"`, `end_date="2026-01-01"`. | Validation blocked: Frontend displays alert; backend returns `400 Bad Request`. | **Verified (Passed)** |
| **TC-08** | **Empty Date Selection Results**: Verify behavior when dates have zero transactions. | Dataset coverage is 2023–2026. | Call `POST /api/v1/analytics/report` for `2015-01-01`. | 200 OK. Returns `has_data: false` with descriptive `empty_reason` note; zero-filled summaries. | **Verified (Passed)** |
| **TC-09** | **Missing or Malformed Dates**: Verify resilience against non-date strings. | System running. | Call `POST /api/v1/ml/analyze` with `selected_date="not-a-date"`. | Safe date parsing rejects malformed string; returns meaningful error without traceback. | **Verified (Passed)** |
| **TC-10** | **Insufficient Forecasting History**: Verify fallback when data points are below model thresholds. | SKU has only 4 days of sales. | Call `POST /api/v1/ml/train` on that SKU. | Automatically falls back to Baseline model or returns clear warning indicating insufficient observations. | **Verified (Passed)** |
| **TC-11** | **Professional CSV Generation**: Verify detail CSV structure and RFC 4180 compliance. | Reporting service initialized. | Call `build_detail_csv()`. | Generates clean CSV matching `Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage`. | **Verified (Passed)** |
| **TC-12** | **Commercial Metric Calculations**: Verify revenue, distinct orders, profit, and margin formulas. | Controlled test fixtures with known numbers. | Aggregate 2 orders: Sales = $1000, Profit = $200. | Revenue = $1000.00, Margin = 20.00%. Verify commercial loss: Sales = $500, Profit = -$50 -> Margin = -10.00%. | **Verified (Passed)** |
| **TC-13** | **Missing Category or Profit Columns**: Verify non-fabrication when optional fields are absent. | CSV without `profit` or `category` headers. | Call `generate_professional_sales_report()`. | Detail CSV outputs `"N/A"` for profit and margin; defaults category to `"General"` with schema notes. | **Verified (Passed)** |
| **TC-14** | **CSV File Download & Headers**: Verify direct file download endpoint. | Dataset imported. | Call `GET /api/v1/analytics/report/csv`. | 200 OK. `Content-Type: text/csv`. Filename matches `professional_sales_summary_YYYY-MM-DD.csv`. | **Verified (Passed)** |
| **TC-15** | **API Errors & Frontend Handling**: Verify UI behavior during server errors or network failure. | API server simulated failure. | Trigger report compilation from frontend. | Displays human-readable error banner; re-enables action buttons without page crash. | **Verified (Passed)** |
| **TC-16** | **Existing Feature Regression**: Verify anomaly detection, scenario simulation, and Gemini advisor. | Full application running. | Run queries on `/anomalies`, `/simulate`, and `/gemini`. | All existing capabilities respond without regressions or broken contracts. | **Verified (Passed)** |
| **TC-17** | **Inventory Intelligence Non-Fabrication**: Verify zero synthetic 180 units when dataset lacks inventory stock. | Transaction dataset without `available_stock`. | Call `GET /api/v1/analytics/inventory`. | 200 OK. `has_inventory_tracking: false`, `available_stock: null`, `days_of_supply: null`, `status: "DEMAND_ONLY"`. | **Verified (Passed)** |
| **TC-18** | **Model Health Dynamic Drift Calculation**: Verify dynamic drift scoring and clean uninitialized telemetry. | Zero model runs recorded. | Call `GET /api/v1/analytics/model-health`. | 200 OK. `drift_score: null`, `avg_wape: null`, `drift_status: "No Recorded Runs"`, `model_status: "UNINITIALIZED"`. | **Verified (Passed)** |
| **TC-19** | **Scenario Simulation Data Boundary**: Verify simulation rejects < 5 records without synthesizing 120 baseline units. | Ingested table has 2 records. | Call `POST /api/v1/analytics/simulate`. | 200 OK with `"error"` payload; `has_data: false`; zero synthetic volume. | **Verified (Passed)** |
| **TC-20** | **Gemini AI SDK Resilience & Masking**: Verify official `google-genai` SDK invocation and error guidance. | Valid or invalid Gemini API key. | Call `POST /api/v1/analytics/gemini`. | Valid response or diagnostic guidance without exposing API key string in error output. | **Verified (Passed)** |

---

## 5. Mocking & Fixture Guidelines

- **Synthetic Sales Fixture**: Use anonymized datasets (`backend/tests/test_reporting.py`) with predefined dates, categories, quantities, sales, and profits.
- **Never Use Production Secrets**: Test fixtures must never connect to live production databases or utilize real customer identifiers.

---

**End of Quality Assurance & Testing Strategy**
