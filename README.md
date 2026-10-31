# Sales Intel AI — Sales Prediction Dashboard & Analytics Platform

<div align="center">

[![Results & Benchmarks](https://img.shields.io/badge/📊_Results_&_Benchmarks-View_Master_Doc-007ACC?style=for-the-badge&logo=github)](RESULTS_AND_BENCHMARKS.md)
[![Comparison Report](https://img.shields.io/badge/⚖️_Comparison_Report-Power_BI_|_Tableau_|_Zoho-7928CA?style=for-the-badge)](docs/results-and-benchmarks/COMPARISON_TEST_REPORT.md)
[![QA Test Report](https://img.shields.io/badge/📋_QA_Test_Report-100%25_PASSED-success?style=for-the-badge)](docs/results-and-benchmarks/WEB_APPLICATION_TEST_REPORT.md)
[![Screenshots Gallery](https://img.shields.io/badge/🖼️_Screenshots_Gallery-14_Modules-blueviolet?style=for-the-badge)](docs/results-and-benchmarks/screenshots/README.md)
[![Verified Metrics](https://img.shields.io/badge/📈_Verified_Metrics-10k+_Records-orange?style=for-the-badge)](docs/results-and-benchmarks/TEST_METRICS.md)

| [📖 Overview](#sales-intel-ai--sales-prediction-dashboard--analytics-platform) | [📊 Results & Benchmarks](RESULTS_AND_BENCHMARKS.md) | [⚖️ Comparison Report](docs/results-and-benchmarks/COMPARISON_TEST_REPORT.md) | [📋 QA Test Report](docs/results-and-benchmarks/WEB_APPLICATION_TEST_REPORT.md) | [🖼️ Screenshots Gallery](docs/results-and-benchmarks/screenshots/README.md) | [📈 Verified Metrics](docs/results-and-benchmarks/TEST_METRICS.md) |
|:---:|:---:|:---:|:---:|:---:|:---:|
|:---:|:---:|:---:|:---:|:---:|:---:|

</div>

> [!TIP]
> **Quick Access to Test Evidence & Screenshots**:  
> View our certified Enterprise QA Audit, empirical metrics, and application screenshots in the [**Results & Benchmarks Master Document**](RESULTS_AND_BENCHMARKS.md) or open the [**Screenshots Gallery**](docs/results-and-benchmarks/screenshots/README.md).

[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.0.0-000000?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.3.0-38B2AC?logo=tailwind-css)](https://tailwindcss.com)

A production-grade, AI-powered Sales Intelligence and Prediction Platform. Integrates empirical transactional ledger analysis, time-series forecasting (Seasonal Naive, Auto-ARIMA), automated anomaly detection with dynamic z-scoring, business scenario simulation, LLM-based Gemini Pro advisory, audited Professional Sales Summary Reports, and multi-tenant SaaS architecture.

---

## Comparison Test Report

Explore the comparative evaluation of SalesMind AI against Microsoft Power BI, Tableau, and Zoho Analytics. The report covers application capabilities, feature-wise comparison, testing methodology, accuracy, efficiency, scalability, and overall findings.

📊 [View Complete Comparison Test Report](docs/results-and-benchmarks/COMPARISON_TEST_REPORT.md)

---

## Architecture & Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript | Dark enterprise SaaS dashboard, interactive Recharts graphs |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2 | High-performance asynchronous REST API |
| **Data & ML** | Pandas, Scikit-learn, Statsmodels | Walk-forward validation, Seasonal Naive & Auto-ARIMA |
| **Database** | PostgreSQL (Production) / SQLite (Dev) | Multi-tenant schema with UUID primary keys & startup auto-migration |
| **Reporting Engine** | Python CSV (RFC 4180), Pandas | Audited category & sub-category Professional Sales Summary Reports |
| **Auth & Security** | JWT (python-jose), Bcrypt (passlib) | Role-Based Access Control (Admin, Analyst, Manager) |
| **Deployment** | Docker, Docker Compose, Nginx | Multi-stage production containerization |

---

## Getting Started

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ or 20+
- (Optional) Docker & Docker Compose

---

### Running Locally

#### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows (Command Prompt / PowerShell):
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Seed sample transactions into SQLite database
python scripts/seed_data.py

# Run FastAPI server
uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000

# Run automated test suite
pytest -v
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```
- Dashboard UI: [http://localhost:3000](http://localhost:3000)

---

### Running via Docker Compose

To launch the full-stack containerized platform (PostgreSQL, Backend API, Frontend Dashboard, Prometheus, Grafana, and Nginx reverse proxy):
```bash
docker-compose up --build
```
Access the application at [http://localhost](http://localhost) (or Next.js direct at [http://localhost:3000](http://localhost:3000)).

---

## Core Capabilities & Workflows

### 1. Executive Intelligence Overview (`/`)
- Real-time revenue aggregation, active SKU count, distinct orders (`COUNT(DISTINCT order_id)`), total physical quantity, AOV, total profit, operating profit margin, 7-day forecasted revenue run-rate, detected anomalies, and model accuracy (WAPE).
- Flexible period filters (*All Time*, *Today*, *Last 7 Days*, *Last 30 Days*, *This Month*, *Previous Month*, *Custom Range*) with automated period-over-period delta comparisons (+/- %).
- Deterministic empirical business insights and diagnostics banner.
- Endpoint: `GET /api/v1/analytics/overview`.

### 2. Comprehensive Sales Analytics Suite (`/analytics`)
- **Time-Series Trends**: Aggregated daily, weekly, and monthly sales volume and revenue charts with peak/trough analysis and period delta changes.
- **Categories & Sub-Categories**: Visual contribution percentage bars, category rankings, and full commercial breakdown table.
- **Product Performance**: Top-selling and lowest-selling SKU rankings by volume and gross revenue with search filters.
- **Transaction Explorer**: Searchable, sortable, and paginated line-item transactions table supporting multi-column sorting and category filtering.
- Endpoints: `GET /api/v1/analytics/trends`, `/categories`, `/products`, `/transactions`.

### 3. Forecast Lab & Model Selection (`/forecast`)
- **Target Name Selector**: Searchable product combobox or custom SKU input. Disambiguates duplicate product names with explicit SKU codes. Global aggregation via `"All Products (Global Aggregate)"` (`ALL`).
- **Option A (Selected Date)**: Calendar picker targeting a single day. If within historical dataset coverage, displays verified transaction actuals, total sales, units, and week-over-week deltas; if in the future, projects forward demand via ML models.
- **Option B (Date Range)**: Dual start/end calendar pickers with quick range presets (*Last 30 Days*, *Last 90 Days*, *Full Dataset Coverage*).
- **Model Engine**: Walk-forward cross-validation auto-selecting the best model (Seasonal Naive vs. ARIMA) based on out-of-sample error (WAPE / RMSE).
- **Quick Action**: 1-click `"Generate Professional Sales Report"` button immediately exports audited CSVs for the active selection.

### 4. Reports & Export Center (`/reports`)
- **Professional Sales Summary Report**: Generates compliance-ready, audited commercial performance reports modeled after `Professional_Sales_Summary_Report.csv`.
- **Filename Convention**: `professional_sales_summary_YYYY-MM-DD.csv` using the actual runtime generation date.
- **Clean RFC 4180 Format**: Detail CSV strictly contains the 7 data columns without contaminating metadata header rows:
  ```
  Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage
  ```
- **Order Count Precision**: True distinct orders calculated via `COUNT(DISTINCT order_id)`. Avoids double-counting customer baskets spanning multiple categories.
- **Export Deliveries**: Detail CSV download, Summary metadata CSV download, JSON report, and Print / Save as PDF (`@media print`).

### 5. Anomaly Detection Center (`/anomalies`)
- Rolling dynamic Z-score algorithm (threshold 2.5–3.0) flagging demand surges, unexpected drops, and inventory stockouts.
- Provides alert types (Demand Surge Spike / Demand Contraction Drop), baseline expected units, and root-cause investigation guidance.
- Endpoint: `GET /api/v1/analytics/anomalies`.

### 6. Model Health & Prediction History Audit (`/model-health`)
- Production monitoring of forecasting accuracy, WAPE / MAE error bounds, and statistical drift signals.
- Prediction history audit log tracking saved forecast runs, target SKUs, model versions, and predicted vs. actual ground-truth variance.
- Endpoints: `GET /api/v1/analytics/model-health`, `GET /api/v1/ml/history`.

### 7. Gemini Pro AI Sales Advisor (`/gemini`)
- Context-aware sales intelligence powered by Google Gemini Pro, grounded in live sales revenue, distinct orders, profit margins, active SKUs, stock levels, and transaction snapshots.
- Endpoints: `POST /api/v1/analytics/gemini` (and `/copilot`).

### 8. Data Ingestion & Dataset Preview (`/data`)
- Multipart CSV upload with automatic alias mapping, line-item granularity preservation, and atomic overwrite protection (`replace=True`).
- Dataset preview telemetry displaying filename, total row and column counts, date coverage span, unique catalog scope, missing value audit, and sample 10 parsed rows.
- Endpoints: `POST /api/v1/data/upload`, `GET /api/v1/data/preview`, `GET /api/v1/data/products`, `POST /api/v1/data/clean-duplicates`, `POST /api/v1/data/reset`.

### 9. User Profile & Multi-Tenant Workspace (`/profile`)
- User account identity, assigned RBAC role (Admin / Analyst), active session verification, and multi-tenant workspace isolation policies.
- Endpoint: `GET /api/v1/users/me`.

### 10. Scenario Simulation Lab (`/scenarios`)
- Evaluates price elasticity, discount adjustments, and demand multipliers against historical baseline revenue.
- Endpoint: `POST /api/v1/analytics/simulate`.

### 11. Universal Data Cleaning Studio (`/cleaning`)
- Autonomous multi-format data profiling, schema casting, imputation, deduplication, and quality scoring across CSV, TSV, XLSX, Parquet, JSON, and media.
- Side-by-side raw vs. cleaned dataset explorer, multi-format export center, and 1-click promotion to live sales ledger.
- Endpoints: `POST /api/v1/cleaning/upload`, `POST /api/v1/cleaning/datasets/{id}/clean`, `GET /api/v1/cleaning/datasets/{id}/export`.

### 12. Knowledge Assistant & Hybrid RAG (`/knowledge`)
- Production-grade Retrieval-Augmented Generation (RAG) system grounded in internal sales playbooks, strategy memos, discount policies, and product catalogs.
- Multi-format document parser (PDF, DOCX, TXT, MD, CSV, TSV, JSON), structure-aware chunker, Google Gemini `text-embedding-004` (768-dim) with offline fallback adapter, and persistent vector store (FAISS `IndexFlatIP` with pure-NumPy fallback).
- Multi-tenant vector index isolation (`uploads/tenants/<tenant_id>/vector_index/`).
- Tri-mode hybrid router (`KNOWLEDGE`, `LEDGER_ANALYTICS`, `HYBRID`) combining semantic vector retrieval with exact SQL ledger execution.
- Grounding defense and strict honesty policy preventing hallucination when information is absent.
- Interactive Knowledge Chat with intent badges, source citation cards, chunk inspector modal, and document management ledger.
- Endpoints: `POST /api/v1/rag/documents`, `POST /api/v1/rag/chat`, `GET /api/v1/rag/health`.

---

## Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/          # Route endpoints (analytics, data, ml, auth)
│   │   ├── core/         # Settings, JWT security, password hashing
│   │   ├── db/           # Session management & declarative base
│   │   ├── ml/           # Time-series models (baseline, arima, evaluation, selection, anomaly)
│   │   ├── models/       # SQLAlchemy models (RawSalesData, User, Tenant, Forecast)
│   │   ├── pipelines/    # ETL data ingestion & feature extraction
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── services/     # Reporting engine, Gemini service, simulation
│   ├── tests/            # Test suite (API, validation, ML, anomalies, reporting)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js 14 App Router pages (forecast, reports, anomalies, data, etc.)
│   ├── components/       # Recharts visualizations, KPI cards, sidebar layout
│   ├── hooks/            # useAuth, useSalesData hooks
│   ├── lib/              # Axios API client with interceptors
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf        # Reverse proxy and rate limiter
├── docs/                 # In-depth architectural & API specifications
└── docker-compose.yml
```

---

## Results & Benchmarks

SalesMind AI has undergone exhaustive functional quality assurance and telemetry validation across all 13 core navigation modules, conducted by a Senior QA Architect (10+ Years Experience). The platform adheres strictly to non-fabrication rules, verified order uniqueness, and commercial loss preservation.

- **Verified Quality Gate**: **100% MODULES PASSED (APPROVED)** — Enterprise Release Grade
- **Documented Application Modules**: 13 Core Modules (Overview, Ingestion, Cleaning, Analytics, Forecasting, Anomalies, Simulation, Inventory, Model Health, Gemini AI, RAG Studio, Exports, Subscriptions/Audit)
- **Verified Dataset Scope**: 10,194 records, 1,862 distinct SKUs, 5,111 unique orders, $2.32M gross sales, 434 anomalies flagged

### Detailed Verification Reports:
- 🏆 [**Results & Benchmarks Master Document**](RESULTS_AND_BENCHMARKS.md) — Unified 14-topic evidence document containing screenshots, test reports, and verified metrics.
- ⚖️ [**Comparison Test Report (Power BI vs Tableau vs Zoho)**](docs/results-and-benchmarks/COMPARISON_TEST_REPORT.md) — Predictive comparative evaluation across 4 platforms.
- 📋 [**Web Application Testing Report**](docs/results-and-benchmarks/WEB_APPLICATION_TEST_REPORT.md) — Comprehensive functional assessment, boundary checks, and system testing.
- 📊 [**Verified Test Metrics**](docs/results-and-benchmarks/TEST_METRICS.md) — Empirical financial KPIs, forecasting error bounds (WAPE / MAE), and anomaly telemetry.
- 🧪 [**Test Cases & Verification Matrix**](docs/results-and-benchmarks/TEST_CASES.md) — Formal test case ledger (`SM-OV-001`, `SM-DI-001`, etc.) with execution results.
- 🖼️ [**Application Screenshots Gallery**](docs/results-and-benchmarks/screenshots/README.md) — Visual evidence directory and screenshot capture guide.
- 📁 [**Results & Benchmarks Suite Overview**](docs/results-and-benchmarks/README.md) — Landing page and QA certification overview.

---

## Documentation Directory

Full architectural and operational documentation is synchronized in the [`docs/`](docs/) directory:

- [Comparison Test Report (Power BI vs Tableau vs Zoho)](docs/results-and-benchmarks/COMPARISON_TEST_REPORT.md)
- [Results & Benchmarks Suite](docs/results-and-benchmarks/README.md)
- [Web Application Testing Report](docs/results-and-benchmarks/WEB_APPLICATION_TEST_REPORT.md)
- [Verified Test Metrics](docs/results-and-benchmarks/TEST_METRICS.md)
- [Test Cases & Verification Matrix](docs/results-and-benchmarks/TEST_CASES.md)
- [Product Requirements Document (PRD)](docs/PRD.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [UI/UX Design Specification](docs/DESIGN.md)
- [API Specification & Reference](docs/API.md)
- [Database Architecture & Schema](docs/DATABASE.md)
- [Data Pipeline & ETL](docs/DATA_PIPELINE.md)
- [Forecasting & ML Models](docs/MODELS.md)
- [Testing & Quality Assurance](docs/TESTING.md)
- [Authentication & Security](docs/SECURITY.md)
- [Environment & Local Setup](docs/ENVIRONMENT.md)
- [Deployment Strategy](docs/DEPLOYMENT.md)
- [Monitoring & Observability](docs/MONITORING.md)
- [Debugging Guide](docs/DEBUGGING.md)
- [Integrations Guide](docs/INTEGRATIONS.md)
- [Model Context Protocol (MCP)](docs/MCP_CONNECTION.md)
- [Changelog](docs/CHANGELOG.md)
- [Contribution Guidelines](docs/CONTRIBUTING.md)
- [AI Engineering Rules](docs/AGENTS.md)
- [RAG Architecture & System Design](docs/RAG_ARCHITECTURE.md)
- [RAG Implementation & Setup Guide](docs/RAG_SETUP.md)
- [RAG API Specification](docs/RAG_API.md)
- [RAG Security & Multi-Tenancy](docs/RAG_SECURITY.md)
- [RAG Test Plan & Verification](docs/RAG_TESTING.md)

---

## License

This project is licensed under the MIT License.
