# Sales Intelligence Platform
# External & System Integrations Guide

**Document:** INTEGRATIONS.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Integrations:** Google Gemini Pro AI, Downstream BI (Tableau / PowerBI / Excel), Redis & Celery, Prometheus

---

## 1. Google Gemini Pro AI Integration

Implemented in [`backend/app/services/gemini_service.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/services/gemini_service.py).

### 1.1 Configuration
- Set `GEMINI_API_KEY` in environment variables or `.env`.
- Set `GEMINI_MODEL=gemini-1.5-pro` (recommended) or compatible models.

### 1.2 Grounding & Privacy
- The integration never uploads raw customer PII or transaction lines.
- Only aggregated summary statistics (total revenue, active SKUs, 7-day ARIMA forecast, top anomaly flags) are provided as context to ground generative responses.

### 1.3 Fallback Diagnostic Behavior
- If `GEMINI_API_KEY` is not provided or the API is unreachable (e.g. rate limit or network failure), the system returns an informative diagnostic report containing verified ledger telemetry rather than failing silently.

---

## 2. Downstream Business Intelligence Integrations (Tableau, PowerBI, Excel)

The platform provides two standard integration pathways for commercial BI tools:

### 2.1 Direct CSV Ingestion
- Clean RFC 4180 Detail CSV (`professional_sales_summary_YYYY-MM-DD.csv`).
- 100% compliant with Pandas `pd.read_csv()`, Tableau Desktop/Server, and Microsoft PowerBI.
- Numbers formatted as clean decimals (`f"{val:.2f}"`) without thousand commas.

### 2.2 Streaming API Integration
- BI workflows can directly fetch reports via HTTP:
  ```bash
  GET /api/v1/analytics/report/csv?target_name=ALL&mode=range&start_date=2026-01-01&end_date=2026-12-30
  ```
  Returns `Content-Type: text/csv` with `Content-Disposition: attachment`.

---

## 3. Background Workers (Redis & Celery)

- Configured via [`docker-compose.yml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/docker-compose.yml) and `backend/Dockerfile.worker`.
- Message broker: `redis://redis:6379/0`.
- Task execution: Heavy model retraining or batch dataset processing.

---

**End of External & System Integrations Guide**
