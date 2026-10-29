# SalesMind AI — Retrieval-Augmented Generation (RAG) Implementation Plan

## 1. Executive Summary & Repository Audit

Following a comprehensive audit of the **SalesMind AI** repository, this document outlines the architecture, integration design, security boundaries, and test strategy for introducing an enterprise-grade, multi-tenant **Retrieval-Augmented Generation (RAG)** knowledge assistant.

### 1.1 Existing Architecture Discovered
- **Backend**: Python 3.12 with FastAPI (`0.103.2`), SQLAlchemy (`2.0.21`), Alembic (`1.20.0`), Pydantic V2 (`2.14.1`), and Pytest (`7.4.2`).
- **Database**: SQLite (`sql_app.db`) for zero-dependency local development and testing, with automatic fallback and schema migrations. Production supports PostgreSQL (`psycopg2-binary 2.9.13`) via `DATABASE_URL`.
- **Multi-Tenancy & RBAC**: Tenant workspace isolation enforced via `Tenant`, `TenantMember`, and `User` models. Active organization context resolved through `X-Organization-ID` header and JWT Bearer token in `app.api.deps.get_current_tenant_or_default`.
- **Existing AI & Analytics**:
  - `app/services/gemini_service.py`: Generative sales intelligence using the official `google-genai` SDK with fallback to deterministic local analytical intelligence.
  - `app/services/analytics_service.py` & `reporting_service.py`: Exact ledger aggregations (`COUNT(DISTINCT order_id)`), multi-sheet Excel generation, zero-dependency PDF rendering, Parquet streaming.
  - `app/services/cleaning/`: Universal 20-step multi-format data cleaning module supporting tabular, text, image, audio, and video containers.
- **Installed ML & Vector Packages**:
  - `faiss-cpu 1.15.0`: Installed and verified in `backend/.venv`.
  - `google-genai 2.30.1`, `google-generativeai 0.8.6`, `google-ai-generativelanguage 0.6.15`: Installed in `backend/.venv`.
  - `scikit-learn 1.9.0`, `torch 2.13.0`, `transformers 5.15.0`: Available.
- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide icons, React Query, and Axios HTTP client (`frontend/lib/api.ts`) configured with interceptors that automatically attach JWT tokens and `X-Organization-ID`.

### 1.2 Baseline Test Suite Results
- Ran full backend test suite: **88 passed out of 88 (100% pass rate)** across authentication, organizations, RBAC, analytics, forecasting, ML retraining, anomaly detection, audit logs, universal data cleaning, and multi-format reports.
- Ran frontend TypeScript typecheck: **0 errors**.

---

## 2. Identified Gaps

1. **Absence of Document Knowledge Retrieval**: The current system queries structured database tables (`raw_sales_data`) but cannot ingest unstructured enterprise knowledge (e.g., standard operating procedures, supplier contracts, return policies, regional sales playbooks, product technical specifications).
2. **Missing Document Chunking & Vector Schema**: No database tables currently exist to track uploaded knowledge documents, text chunks, chunk embeddings, and indexing status.
3. **Absence of Semantic Search API**: No dedicated vector retrieval endpoint with similarity scoring, top-K selection, or citation generation.
4. **Lack of RAG Grounding UI**: The existing `/gemini` advisor focuses strictly on structured SKU metrics without citation pills or document preview modals.

---

## 3. Recommended Integration Design

```
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    FastAPI RAG Pipeline                     │
                               └─────────────────────────────────────────────────────────────┘
                                                              │
 ┌───────────────────────┐         ┌─────────────────────────▼──────────────────────────┐
 │ User Document Upload  │ ──────► │ 1. Ingestion & Storage Service                     │
 │ (PDF, DOCX, TXT,      │         │    - SHA-256 Checksum, Multi-tenant Isolation      │
 │  MD, CSV, JSON)       │         │    - Saved to uploads/tenants/<tenant_id>/rag_docs │
 └───────────────────────┘         └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 2. Document Parser & Normalizer                    │
                                   │    - Page/Section preservation                     │
                                   │    - HTML/Whitespace sanitation                    │
                                   └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 3. Structure-Aware Chunking Engine                 │
                                   │    - Configurable chunk size (800) & overlap (150) │
                                   │    - Header & table preservation                   │
                                   └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 4. Vector Embedding Service                        │
                                   │    - Google Gemini text-embedding-004              │
                                   │    - Resilient offline/deterministic fallback      │
                                   └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 5. Dual-Layer Persistent Vector Store              │
                                   │    - ACID Storage: rag_documents & rag_chunks DB   │
                                   │    - Fast Retrieval: Persistent FAISS FlatIP Index │
                                   │      synced to uploads/tenants/<tenant_id>/index   │
                                   └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 6. Multi-Tenant Semantic Retrieval Engine          │
                                   │    - Strict tenant_id SQL isolation                │
                                   │    - Cosine similarity ranking & threshold filter  │
                                   │    - Honest abstention if context insufficient     │
                                   └─────────────────────────┬──────────────────────────┘
                                                             │
 ┌───────────────────────┐         ┌─────────────────────────▼──────────────────────────┐
 │ User Question / Query │ ──────► │ 7. Hybrid Business Intelligence Engine             │
 │ ("Explain revenue     │         │    - Routes: Knowledge vs Exact Sales vs Hybrid    │
 │  dip with policy")    │         │    - Fetches deterministic SQL analytics if needed │
 └───────────────────────┘         └─────────────────────────┬──────────────────────────┘
                                                             │
                                   ┌─────────────────────────▼──────────────────────────┐
                                   │ 8. Gemini Grounded Answer Generator                │
                                   │    - Untrusted evidence prompt protection          │
                                   │    - Source citations (doc_id, page, section)      │
                                   │    - JSON/Structured streaming output              │
                                   └────────────────────────────────────────────────────┘
```

---

## 4. Database Models & Schema Design

### Table: `rag_documents`
- `id` (UUID, Primary Key)
- `tenant_id` (UUID, Foreign Key `tenants.id`, CASCADE, Indexed)
- `user_id` (UUID, Foreign Key `users.id`, SET NULL)
- `title` (VARCHAR 255)
- `original_filename` (VARCHAR 255)
- `file_path` (VARCHAR 500)
- `file_size` (INTEGER)
- `mime_type` (VARCHAR 100)
- `file_type` (VARCHAR 50) — `pdf`, `docx`, `txt`, `md`, `csv`, `json`
- `checksum_sha256` (VARCHAR 64, Indexed)
- `status` (VARCHAR 50) — `UPLOADED`, `PROCESSING`, `INDEXED`, `FAILED`, `DELETING`
- `error_message` (TEXT, Nullable)
- `total_chunks` (INTEGER, Default 0)
- `metadata_json` (TEXT, Nullable)
- `created_at`, `updated_at` (DATETIME)

### Table: `rag_chunks`
- `id` (UUID, Primary Key)
- `document_id` (UUID, Foreign Key `rag_documents.id`, CASCADE, Indexed)
- `tenant_id` (UUID, Foreign Key `tenants.id`, CASCADE, Indexed)
- `chunk_index` (INTEGER)
- `chunk_text` (TEXT)
- `token_count` (INTEGER)
- `embedding_json` (TEXT) — JSON serialized float array for ACID durability
- `page_number` (INTEGER, Nullable)
- `section_title` (VARCHAR 255, Nullable)
- `embedding_model` (VARCHAR 100)
- `indexing_version` (INTEGER, Default 1)
- `metadata_json` (TEXT, Nullable)
- `created_at` (DATETIME)

---

## 5. Security & Isolation Safeguards

1. **Tenant Isolation**: Every database query, vector search, and file retrieval requires explicit `tenant_id == current_tenant.id` match. Cross-tenant retrieval is architecturally prohibited.
2. **Untrusted Evidence Boundary**: Uploaded documents are treated as untrusted third-party inputs. The system prompt instructs Gemini to never execute commands or override system security instructions contained within document text.
3. **Zero Credential Exposure**: API keys are strictly read from backend environment variables (`GEMINI_API_KEY`). No secrets are passed to the frontend or saved in client-side storage.
4. **Path Traversal Protection**: Uploaded files are assigned random UUID filenames and sanitized base names. Absolute path access outside `uploads/` is rejected.
5. **Ledger Precision**: Exact numerical questions (revenue, orders, profit) route through verified backend SQL ledger calculations rather than allowing the LLM to hallucinate commercial figures.

---

## 6. Implementation Phasing

- [x] **Phase 1**: Repository Audit & Implementation Plan (`docs/RAG_IMPLEMENTATION_PLAN.md`).
- [ ] **Phase 2**: RAG Architecture Specification (`docs/RAG_ARCHITECTURE.md`).
- [ ] **Phase 3**: Document Ingestion Service & Parsers (PDF, DOCX, TXT, MD, CSV, JSON).
- [ ] **Phase 4**: Structure-Aware Chunking & Embedding Adapter.
- [ ] **Phase 5**: Persistent Vector Store & Multi-Tenant Retrieval Engine.
- [ ] **Phase 6**: Gemini Grounded Generation & Citation Construction.
- [ ] **Phase 7**: Hybrid Business Intelligence Router (Knowledge vs Ledger vs Hybrid).
- [ ] **Phase 8**: FastAPI Endpoints (`/api/v1/rag/*`).
- [ ] **Phase 9**: Frontend Knowledge Assistant UI (`/knowledge`).
- [ ] **Phase 10**: Database Model Registration & Auto-Migration.
- [ ] **Phase 11**: Security & Privacy Verification.
- [ ] **Phase 12**: Performance & Cache Optimization.
- [ ] **Phase 13**: Automated Testing Suite (`tests/test_rag.py`).
- [ ] **Phase 14**: Evaluation & Observability Telemetry.
- [ ] **Phase 15**: Configuration Updates (`.env.example`).
- [ ] **Phase 16**: Synchronized Documentation (`docs/RAG_*.md`).
- [ ] **Phase 17**: Final Verification & Clean Diff Review.

