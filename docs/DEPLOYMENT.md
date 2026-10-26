# Sales Intelligence Platform
# Deployment Strategy & Operations Guide

**Document:** DEPLOYMENT.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Deployment Modes:** Local Dev, Multi-Container Docker Compose, Cloud (Render / Railway / Vercel)

---

## 1. Deployment Architecture Overview

The platform supports three distinct deployment topologies:

1. **Local Bare-Metal Development**:
   - Backend: Uvicorn (`127.0.0.1:8000`) with SQLite database (`backend/sql_app.db`).
   - Frontend: Next.js dev server (`localhost:3000`).
2. **Multi-Container Production Stack (Docker Compose)**:
   - Orchestrated via [`docker-compose.yml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/docker-compose.yml) with Nginx reverse proxy, PostgreSQL 15, Redis 7, Celery background worker, Prometheus, and Grafana.
3. **Cloud SaaS Platform**:
   - Automated deployment via [`render.yaml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/render.yaml) (managed PostgreSQL, FastAPI web service) and Vercel ([`frontend/vercel.json`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/vercel.json)).

```mermaid
flowchart TD
    Internet["Internet Traffic (HTTPS 443 / HTTP 80)"] --> Nginx["Nginx Reverse Proxy & Rate Limiter (nginx/nginx.conf)"]
    Nginx -- "/api/*" --> FastAPI["FastAPI Backend (backend: Dockerfile)"]
    Nginx -- "/*" --> NextJS["Next.js Frontend (frontend: Dockerfile)"]
    FastAPI --> Postgres[("PostgreSQL 15 (postgres:15-alpine)")]
    FastAPI --> Redis[("Redis 7 (redis:7-alpine)")]
    Worker["Celery Worker (backend: Dockerfile.worker)"] --> Redis
    Worker --> Postgres
    Prometheus["Prometheus Monitoring"] --> FastAPI
    Grafana["Grafana Visualizer (Port 3001)"] --> Prometheus
```

---

## 2. Docker Compose Multi-Container Stack

The repository includes a complete production configuration in [`docker-compose.yml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/docker-compose.yml):

### 2.1 Service Catalog

| Service Name | Image / Build Context | Internal Port | Host Port | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `db` | `postgres:15-alpine` | `5432` | `5432` | Primary transactional relational database. |
| `redis` | `redis:7-alpine` | `6379` | `6379` | Message broker and caching backend. |
| `backend` | `./backend` | `8000` | Internal | FastAPI REST API engine. |
| `worker` | `./backend` (`Dockerfile.worker`) | N/A | N/A | Celery background job worker. |
| `frontend` | `./frontend` | `3000` | `3000` | Next.js 14 App Router dashboard. |
| `nginx` | `nginx:alpine` | `80`, `443` | `80`, `443` | Public reverse proxy, SSL termination, rate limiting. |
| `prometheus`| `prom/prometheus` | `9090` | Internal | Metrics scraper. |
| `grafana` | `grafana/grafana` | `3000` | `3001` | Operational metrics visualization dashboard. |

### 2.2 Execution Command
```bash
# Build and run the entire stack in the background
docker-compose up --build -d

# View logs from all services
docker-compose logs -f

# Check container status
docker-compose ps

# Graceful shutdown
docker-compose down
```

---

## 3. Cloud Deployment (Render, Railway & Vercel)

### 3.1 Render / Railway Blueprint (`render.yaml`)
Defined in [`render.yaml`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/render.yaml):
- **Database**: Managed PostgreSQL instance named `sales-intel-db` (plan: starter).
- **Backend API**:
  - Environment: `python`
  - Build Command: `pip install -r backend/requirements.txt`
  - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Auto-linked to `DATABASE_URL` from `sales-intel-db`.
- **Frontend Web Service**:
  - Environment: `node`
  - Build Command: `cd frontend && npm install && npm run build`
  - Start Command: `cd frontend && npm run start`

### 3.2 Vercel Deployment (`frontend/vercel.json`)
The Next.js frontend can be deployed independently to Vercel with output directory configured for standalone Next.js builds.

---

## 4. Environment Variables Reference

A verified `.env` file should be maintained in the root and `/backend`:

| Variable Name | Required | Default (Dev) | Production Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** | `sqlite:///./sql_app.db` | PostgreSQL connection URI (`postgresql://user:pass@host:5432/dbname`). |
| `SECRET_KEY` | **Yes** | `dev_secret_key` | Cryptographic secret for signing JWT access tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `60` | Token validity duration in minutes. |
| `GEMINI_API_KEY` | Optional| None | Google Gemini API key for natural language sales copilot. |
| `GEMINI_MODEL` | No | `gemini-1.5-pro` | Gemini model identifier. |
| `REDIS_URL` | Optional| `redis://localhost:6379/0`| Connection string for Celery task broker. |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of permitted frontend origins. |
| `NEXT_PUBLIC_API_URL` | **Yes** | `http://localhost:8000` | Frontend backend API target URL. |

---

## 5. Post-Deployment Verification & Health Checks

Verify system availability after deployment:

1. **Process Liveness**:
   ```bash
   curl -s http://localhost:8000/health
   # Expected response: {"status": "ok"}
   ```
2. **Database Status**:
   ```bash
   curl -s http://localhost:8000/api/v1/data/status
   # Expected response: {"status": "ok", "total_raw_records": N}
   ```
3. **Frontend Dashboard**:
   Open browser to `http://localhost:3000` and confirm navigation, overview cards, and Forecast Lab render without errors.
4. **Reports Verification**:
   Navigate to `/reports`, select a target date range, and click **"Generate Professional Sales Report"** to verify RFC 4180 CSV export.

---

**End of Deployment Strategy & Operations Guide**
