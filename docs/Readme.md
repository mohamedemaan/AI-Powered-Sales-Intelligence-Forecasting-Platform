# Sales Intelligence Platform — Documentation Index

Welcome to the internal engineering and architectural documentation for the Sales Intelligence Platform.

All documents have been audited, synchronized, and verified against the production codebase as of October 2026.

---

## Documentation Sitemap

| Document | File Path | Scope & Purpose |
| :--- | :--- | :--- |
| **Product Requirements** | [`PRD.md`](PRD.md) | Product scope, user personas, functional requirements, and acceptance criteria. |
| **System Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) | High-level architecture, module breakdown, request sequence flows, and Mermaid diagrams. |
| **UI/UX Design Specification**| [`DESIGN.md`](DESIGN.md) | Visual tokens, dark theme palette, component layouts, and print stylesheets. |
| **API Specification** | [`API.md`](API.md) | Complete endpoint catalog, schemas, parameters, response codes, and examples. |
| **Database Architecture** | [`DATABASE.md`](DATABASE.md) | SQLAlchemy models, table schemas, SQLite auto-migration, and Alembic setup. |
| **Data Pipeline & ETL** | [`DATA_PIPELINE.md`](DATA_PIPELINE.md) | Ingestion workflow, alias mapping, line-item preservation, and feature extraction. |
| **Forecasting & ML Models** | [`MODELS.md`](MODELS.md) | Baseline models, Auto-ARIMA, walk-forward cross-validation, and metric formulas. |
| **Testing Strategy** | [`TESTING.md`](TESTING.md) | QA standards, automated test commands, test suite layout, and comprehensive test matrix. |
| **Security & Authentication** | [`SECURITY.md`](SECURITY.md) | JWT Bearer authentication, bcrypt hashing, RBAC, and multi-tenant isolation. |
| **Environment Configuration** | [`ENVIRONMENT.md`](ENVIRONMENT.md) | Local development setup, virtual environments, Node prerequisites, and `.env` template. |
| **Deployment Strategy** | [`DEPLOYMENT.md`](DEPLOYMENT.md) | Multi-container Docker Compose, Render/Railway cloud blueprints, and Vercel hosting. |
| **Monitoring & Observability** | [`MONITORING.md`](MONITORING.md) | Health check endpoints, model drift monitoring, Prometheus, and Grafana. |
| **Debugging Guide** | [`DEBUGGING.md`](DEBUGGING.md) | Systematic troubleshooting for CSV parsing, date boundaries, and API integrations. |
| **Integrations Guide** | [`INTEGRATIONS.md`](INTEGRATIONS.md) | Google Gemini Pro AI, downstream BI tools (Tableau, PowerBI, Excel), and Celery. |
| **Model Context Protocol** | [`MCP_CONNECTION.md`](MCP_CONNECTION.md) | MCP server architecture blueprint and tool definitions. |
| **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) | Version history and notable changes following Keep a Changelog. |
| **Contribution Guidelines** | [`CONTRIBUTING.md`](CONTRIBUTING.md) | Standards for human contributors and AI coding agents. |
| **AI Engineering Rules** | [`AGENTS.md`](AGENTS.md) | Repository-wide guidelines and safety rules for AI coding assistants. |

---

## Core Platform Workflows

1. **Forecast Lab & Model Selection**:
   - Navigate to `/forecast`.
   - Select a Target Name (or custom SKU).
   - Choose Option A (Selected Date) or Option B (Date Range).
   - Click *"Analyse & Generate Report"* to inspect empirical ledger actuals or project future walk-forward demand trajectories.
2. **Professional Sales Summary Report**:
   - Navigate to `/reports` (or click *"Generate Professional Sales Report"* in Forecast Lab).
   - Configure product scope and calendar date boundaries.
   - Click *"Generate Professional Sales Report"* to compile verified category and sub-category performance data.
   - Download `professional_sales_summary_YYYY-MM-DD.csv`, summary metadata CSV, JSON, or print to PDF.
3. **Data Ingestion**:
   - Navigate to `/data`.
   - Upload any retail transaction CSV (e.g. Superstore).
   - The platform auto-maps aliases and atomically updates the ledger without accumulating duplicate records.
