# Sales Intelligence Platform
# Systematic Debugging & Troubleshooting Guide

**Document:** DEBUGGING.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Scope:** Frontend, Backend API, Database, ML Engine, CSV Processing, and AI Integrations

---

## 1. Troubleshooting Principles

1. **Identify the Failing Layer**: Determine whether the failure originates in the client UI, API route, database query, or ML pipeline.
2. **Examine Exact Tracebacks**: Never swallow errors with empty `catch` blocks; capture the status code and JSON error details.
3. **Preserve Valid Data**: Never delete the database or alter schemas casually during troubleshooting.

---

## 2. Common Scenarios & Verified Solutions

### Scenario 1: CSV Tokenizer Parsing Error (`Expected 2 fields, saw 4`)
- **Symptom**: Pandas `read_csv` throws a C-tokenization error when reading generated sales summary CSVs.
- **Root Cause**: Dollar amounts formatted with thousand commas (e.g., `"$2,326,534.35"`) or unescaped commas inside category descriptions.
- **Resolution**:
  - The reporting service outputs raw numerical floats (`2326534.35`) in `professional_sales_summary_YYYY-MM-DD.csv`.
  - RFC 4180 standard escaping is applied via Python's `csv.writer(quoting=csv.QUOTE_MINIMAL)`.

### Scenario 2: Forecast Lab Analysis Blocked
- **Symptom**: User clicks *"Analyse & Generate Report"* or *"Generate Professional Sales Report"* and receives an error alert banner.
- **Root Causes**:
  - `Start Date > End Date`: Inverted date boundary.
  - Missing date inputs: Unselected date in single-date mode or unselected start/end in range mode.
  - Zero dataset records: No CSV has been uploaded yet.
- **Resolution**: Ensure dataset is uploaded via `/data`, and verify that Start Date is before or equal to End Date.

### Scenario 3: Gemini Pro HTTP 404 (`models/gemini-pro is not found`)
- **Symptom**: Copilot queries return: `Model gemini-pro returned HTTP 404`.
- **Root Cause**: Upstream Google Gemini API deprecation of legacy `gemini-pro` endpoint on version `v1beta`.
- **Resolution**: Configure `GEMINI_MODEL=gemini-1.5-pro` in `.env`.

### Scenario 4: Missing Database Columns on Local SQLite
- **Symptom**: `sqlite3.OperationalError: no such column: raw_sales_data.order_id`.
- **Root Cause**: Local SQLite database (`sql_app.db`) was created prior to schema enhancements.
- **Resolution**: Restart the backend server. The startup auto-migration in [`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py) dynamically executes `ALTER TABLE raw_sales_data ADD COLUMN ...` for missing columns.

### Scenario 5: Data Appending on New Uploads
- **Symptom**: Re-uploading a dataset increases record counts rather than replacing them.
- **Resolution**: Ensure `POST /api/v1/data/upload` uses `replace=true` (the default). The pipeline atomically clears `raw_sales_data`, `model_runs`, and `forecasts` before writing fresh records.

### Scenario 6: Port 3000 Collision in Docker
- **Symptom**: Grafana fails to bind to port 3000 because Next.js uses port 3000.
- **Resolution**: In [`docker-compose.yml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/docker-compose.yml), Grafana is mapped to host port `3001` (`"3001:3000"`).

---

**End of Systematic Debugging & Troubleshooting Guide**
