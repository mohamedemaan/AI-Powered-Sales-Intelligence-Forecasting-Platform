# Sales Intelligence Platform
# Monitoring, Observability & Model Health Specification

**Document:** MONITORING.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Tools:** Application Health Checks, Model Health Drift Monitoring, Prometheus & Grafana (Docker)

---

## 1. Observability Architecture

Observability is divided into three tiers:

1. **Application Health & Liveness**: Light HTTP endpoints reporting process and database status.
2. **Model Health & Drift Detection**: Automated statistical telemetry tracking model accuracy degradation.
3. **Infrastructure Metrics (Production)**: Prometheus scraper and Grafana containerized dashboards configured in `docker-compose.yml`.

---

## 2. Health & Telemetry Endpoints

### 2.1 Process Liveness (`GET /health`)
- **Status Code**: `200 OK`
- **Payload**: `{"status": "ok"}`
- **Purpose**: Used by Docker, Kubernetes, and uptime monitors.

### 2.2 Ingestion Status (`GET /api/v1/data/status`)
- **Payload**:
  ```json
  {
    "status": "ok",
    "total_raw_records": 10194,
    "min_date": "2023-01-03",
    "max_date": "2026-12-30"
  }
  ```

### 2.3 Model Health & Drift Signals (`GET /api/v1/analytics/model-health`)
Implemented in [`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py).
- **Payload**:
  ```json
  {
    "active_model": "Hybrid (Seasonal Naive + Auto-ARIMA)",
    "model_status": "HEALTHY",
    "total_observations": 10194,
    "avg_wape": 8.8,
    "avg_mae": 12.4,
    "avg_rmse": 18.2,
    "drift_status": "Optimal",
    "drift_score": 0.042,
    "validation_strategy": "Walk-Forward Rolling Cross-Validation",
    "last_trained_runs": [
      {
        "id": "run-uuid-1",
        "sku": "ALL",
        "model_version": "v1.0",
        "mae": 12.4,
        "rmse": 18.2,
        "wape": 0.088,
        "status": "COMPLETED"
      }
    ]
  }
  ```
- **Drift Threshold**:
  - `avg_wape <= 12.0%`: Marked **Optimal** (Green).
  - `avg_wape > 12.0%`: Marked **Review Needed** (Amber/Red), indicating model retraining is recommended.

---

## 3. Prometheus & Grafana Integration (Docker Compose)

When launched via `docker-compose up`:
- **Prometheus**: Runs on internal port `9090`, configured via [`monitoring/prometheus.yml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/monitoring/prometheus.yml).
- **Grafana**: Exposed on host port `3001` (to prevent collision with Next.js port `3000`). Default login: `admin / admin`.

---

**End of Monitoring, Observability & Model Health Specification**
