# Sales Intelligence Platform — Documentation Index

Welcome to the internal engineering and architectural documentation for the Sales Intelligence Platform (**SalesMind AI**).

All documents have been audited, synchronized, and verified against the production codebase as of **October 30, 2026**.

---

## Documentation Sitemap

| Document | File Path | Scope & Purpose |
| :--- | :--- | :--- |
| **Product Requirements** | [`PRD.md`](PRD.md) | Product scope, user personas, functional requirements, and acceptance criteria (v3.0). |
| **System Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) | High-level architecture, module breakdown, request sequence flows, and Mermaid diagrams (v3.0). |
| **API Specification** | [`API.md`](API.md) | Complete endpoint catalog, schemas, parameters, response codes, and examples (v3.0). |
| **Database Architecture** | [`DATABASE.md`](DATABASE.md) | SQLAlchemy models, table schemas, SQLite auto-migration, and multi-tenant schema (v3.0). |
| **UI/UX Design Specification**| [`DESIGN.md`](DESIGN.md) | Visual tokens, dark theme palette, component layouts, and print stylesheets. |
| **Data Pipeline & ETL** | [`DATA_PIPELINE.md`](DATA_PIPELINE.md) | Ingestion workflow, alias mapping, line-item preservation, and feature extraction. |
| **Forecasting & ML Models** | [`MODELS.md`](MODELS.md) | Baseline models, Auto-ARIMA, walk-forward cross-validation, and metric formulas. |
| **Testing Strategy** | [`TESTING.md`](TESTING.md) | QA standards, automated test commands, test suite layout, and comprehensive test matrix. |
| **Security & Authentication** | [`SECURITY.md`](SECURITY.md) | JWT Bearer authentication, bcrypt hashing, RBAC, and multi-tenant isolation. |
| **Environment Configuration** | [`ENVIRONMENT.md`](ENVIRONMENT.md) | Local development setup, virtual environments, Node prerequisites, and `.env` template. |
| **Deployment Strategy** | [`DEPLOYMENT.md`](DEPLOYMENT.md) | Multi-container Docker Compose, Render/Railway cloud blueprints, and Vercel hosting. |
| **Monitoring & Observability** | [`MONITORING.md`](MONITORING.md) | Health check endpoints, model drift monitoring, Prometheus, and Grafana. |
| **Debugging Guide** | [`DEBUGGING.md`](DEBUGGING.md) | Systematic troubleshooting for CSV parsing, date boundaries, and API integrations. |
| **Integrations Guide** | [`INTEGRATIONS.md`](INTEGRATIONS.md) | Google Gemini Pro AI, downstream BI tools (Tableau, PowerBI, Excel), and Celery. |
| **RAG Architecture** | [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md) | Dual-layer FAISS vector store, chunking pipelines, and citation grounding. |
| **RAG API Specification** | [`RAG_API.md`](RAG_API.md) | RAG endpoint schemas, vector parameters, and sample payloads. |
| **RAG Security & Isolation** | [`RAG_SECURITY.md`](RAG_SECURITY.md) | Multi-tenant knowledge vault isolation, quota boundaries, and threat model. |
| **RAG Testing & Verification** | [`RAG_TESTING.md`](RAG_TESTING.md) | Test suites, mock vector adapters, and citation grounding verification. |
| **Model Context Protocol** | [`MCP_CONNECTION.md`](MCP_CONNECTION.md) | MCP server architecture blueprint and tool definitions. |
| **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) | Version history and notable changes following Keep a Changelog (up to v3.0.0). |
| **Contribution Guidelines** | [`CONTRIBUTING.md`](CONTRIBUTING.md) | Standards for human contributors and AI coding agents. |
| **AI Engineering Rules** | [`AGENTS.md`](AGENTS.md) | Repository-wide guidelines and safety rules for AI coding assistants. |

---

## Core Platform Workflows

1. **Universal Data Cleaning Studio (`/cleaning`)**:
   - Upload any tabular, time-series, text, or semi-structured dataset.
   - Run the automated 20-step cleaning pipeline (backup, format detection, missing value imputation, type casting, deduplication, date normalization, outlier remediation, and quality scorecard).
   - Verify changes via side-by-side Before & After Data Explorer.
   - Export cleaned data in **CSV**, **Excel (.xlsx)**, **Apache Parquet**, **JSON**, or **TSV** format with on-disk caching (< 10ms repeat latency).
   - Download Executive Audit Reports in **PDF**, **Multi-Sheet Excel**, or **Machine-Readable JSON** format.
   - Promote verified cleaned datasets directly into the live sales ledger with 1 click.

2. **Knowledge Assistant & RAG Studio (`/knowledge`)**:
   - Ingest unstructured documents (PDF, DOCX, TXT, MD, CSV, JSON) into tenant-isolated vaults.
   - Auto-chunk with structure preservation (page numbers, section titles) and 768-D embeddings.
   - Accelerate similarity queries with an on-disk FAISS vector store.
   - Ask semantic questions in natural language; receive answers grounded in verified source documents with exact citation pills (`[cit_1]`, `[cit_2]`), cross-referenced with live SQL ledger metrics.
   - Seed default enterprise corporate playbooks and return policies with 1 click.

3. **Forecast Lab & Walk-Forward Model Selection (`/forecast`)**:
   - Select a Target Name (or custom SKU).
   - Choose Option A (Selected Date) or Option B (Date Range).
   - Click *"Analyse & Generate Report"* to inspect empirical ledger actuals or project future walk-forward demand trajectories using champion models (Seasonal Naive vs. Auto-ARIMA).

4. **Direct Gemini AI Sales Advisor (`/gemini`)**:
   - Query Google Gemini with live database KPIs (Revenue, Orders, Profit Margin, Active SKUs).
   - Generates tactical business recommendations and risk mitigation strategies with local empirical fallback.

5. **Multi-Tenant SaaS Workspaces & Billing (`/billing`, `/audit`)**:
   - Switch between customer organization workspaces from the sidebar.
   - Role-Based Access Control (`OWNER`, `ADMIN`, `ANALYST`, `VIEWER`).
   - Upgrade subscription tiers via Stripe Checkout and manage plans through Stripe Customer Portal.
   - Review immutable forensic audit logs tracking all workspace events.

6. **Professional Sales Summary Report (`/reports`)**:
   - Configure product scope and calendar date boundaries.
   - Compile verified category and sub-category commercial performance.
   - Download `professional_sales_summary_YYYY-MM-DD.csv`, summary metadata CSV, JSON, or browser Print-to-PDF.

---

**End of Documentation Index**
