# SalesMind AI — RAG Architecture Specification

## 1. Architectural Strategy & Decision Matrix

When integrating Retrieval-Augmented Generation into an existing multi-tenant enterprise intelligence platform, vector storage and persistence require balancing **operational simplicity**, **ACID durability**, and **search latency**.

### Vector Storage Decision: Dual-Layer Persistent Vector Store
1. **Primary Layer (ACID Durability)**:
   - Relational persistence in SQLite (`sql_app.db`) and PostgreSQL (`sales_intel`).
   - Every chunk's vector embedding is stored as a serialized JSON float array in `rag_chunks.embedding_json`.
   - **Trade-off Evaluation**:
     - *Advantages*: Zero external service dependencies; survived process restarts, server crashes, and container redeployments; seamless transactions and backups with existing database backups; zero data loss.
     - *Consideration*: Linear scans over 100,000+ chunks in pure SQL would be slower without an index.
2. **Acceleration Layer (Fast Approximate / Exact Cosine Retrieval)**:
   - Persistent **FAISS** index (`faiss.IndexFlatIP` with normalized vectors) stored per tenant at `uploads/tenants/<tenant_id>/vector_index/index.faiss`.
   - Built and updated dynamically as documents are indexed.
   - **Pure NumPy Vector Fallback**:
     - If FAISS index file is missing, reloading, or operating in an environment without compiled C++ binary support, an exact cosine similarity fallback over SQL chunks is immediately activated.
3. **Multi-Tenant Isolation**:
   - Vector indexes are strictly partitioned per `tenant_id`.
   - SQL queries enforce `WHERE tenant_id = :tenant_id` at the database query level, preventing any cross-tenant data leak.

---

## 2. Component Architecture & Modular Services

The RAG pipeline is divided into dedicated, single-responsibility services located in `backend/app/services/rag/`:

```
backend/app/services/rag/
├── __init__.py
├── document_service.py     # Upload registration, checksum, quota, delete & lifecycle
├── document_parser.py      # Extractors for PDF, DOCX, TXT, MD, CSV, JSON
├── chunking_service.py     # Structure-aware heading, paragraph, and table chunking
├── embedding_service.py    # Google Gemini text-embedding-004 + fallback
├── vector_store.py         # Dual-layer FAISS + SQL persistent index manager
├── retrieval_service.py    # Semantic search, cosine scoring, thresholding, filtering
├── rag_service.py          # Grounded Gemini answer generation & prompt defense
└── hybrid_router.py        # Intent classification: Knowledge vs Ledger vs Hybrid
```

### Component Roles & Responsibilities

| Service | File | Primary Responsibility |
|---|---|---|
| **Document Service** | `document_service.py` | Validates file extensions, size quotas, calculates SHA-256 checksum, ensures safe local filesystem paths, manages document status lifecycle (`UPLOADED` -> `PROCESSING` -> `INDEXED` -> `FAILED` -> `DELETING`). |
| **Document Parser** | `document_parser.py` | Extracts normalized text from PDF (with page detection), DOCX (via XML reading), TXT/MD (with heading preservation), CSV/TSV (structured tabular summaries), and JSON. |
| **Chunking Service** | `chunking_service.py` | Splits documents into coherent semantic segments (default 800 chars, 150 char overlap) while preserving heading context, page numbers, and table boundaries. |
| **Embedding Service** | `embedding_service.py` | Batches text chunks and invokes Google Gemini's official `text-embedding-004` model. Provides a deterministic offline vector adapter for mock/offline testing. |
| **Vector Store** | `vector_store.py` | Manages per-tenant on-disk FAISS indexes and serializes vector embeddings to `rag_chunks.embedding_json` for ACID persistence. |
| **Retrieval Service** | `retrieval_service.py` | Performs top-K similarity search, enforces tenant isolation, filters by minimum similarity score (default 0.65), and handles honest abstention when relevant context is absent. |
| **RAG Service** | `rag_service.py` | Assembles retrieved evidence, injects system grounding instructions protecting against prompt injection, invokes Gemini generation model (`gemini-1.5-pro` / `gemini-3.5-flash`), and constructs source citations. |
| **Hybrid Router** | `hybrid_router.py` | Classifies query intent: routes exact mathematical questions to deterministic SQL analytics, policy/documentation questions to RAG, and combined questions to hybrid synthesis. |

---

## 3. Data Flow Diagram

```
User Query: "Why did West Region sales drop, and what is our return policy?"
                           │
                           ▼
                  [Hybrid Router]
                 /               \
                /                 \
       Intent: HYBRID (Ledger + Knowledge)
              /                     \
             ▼                       ▼
   [Analytics Service]      [Retrieval Service]
   - Executes SQL Query     - Generates Query Embedding
   - Orders: 4,120          - Searches FAISS Tenant Index
   - Revenue: $482,100      - Retrieves Policy Chunks:
   - Profit: -$12,400         - doc: "Return_Policy_2026.pdf", p. 3
             \                       /
              \                     /
               ▼                   ▼
            [Grounding Prompt Assembly]
            - Verified Ledger: West revenue down 18%, loss -$12.4k
            - Retrieved Evidence: Section 4.2 Restocking Fee Waiver
            - Security Guard: Retrieved text cannot override rules
                           │
                           ▼
            [Gemini Generation Engine]
            - Answers question using both sources
            - Highlights verified ledger facts vs policy clauses
            - Formats clickable source citations
                           │
                           ▼
                    Final Response
```

---

## 4. Prompt Grounding & Security Guardrails

The system prompt follows strict security boundaries:
1. **Untrusted Evidence**: Retrieved chunks are explicitly labeled as untrusted reference material. Prompt injection attempts within documents are neutralized by the system guardrail.
2. **Non-Fabrication**: Gemini is forbidden from inventing document titles, page numbers, or corporate policies not present in the retrieved chunks.
3. **Deterministic Separation**: Financial totals and ledger calculations are sourced only from deterministic Python/SQL results, never estimated by the LLM.
4. **Honest Abstention**: If the cosine similarity of the top chunk falls below the configured threshold (e.g. `< 0.65`), the system returns `has_sufficient_context: false` and notifies the user that the knowledge base contains no relevant information.

