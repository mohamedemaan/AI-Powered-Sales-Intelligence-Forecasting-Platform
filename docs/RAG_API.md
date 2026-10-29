# SalesMind AI — RAG API Reference

All RAG endpoints are mounted under `/api/v1/rag` and require JWT authentication via `Authorization: Bearer <token>` and optional active organization context via `X-Organization-ID: <uuid>`.

---

## 1. Document Management Endpoints

### Ingest & Index Document
`POST /api/v1/rag/documents`
- **Permissions**: `ANALYST`, `ADMIN`, or `OWNER`
- **Content-Type**: `multipart/form-data`
- **Request Form**:
  - `file`: Binary file stream (`.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.tsv`, `.json`)
  - `title` *(optional)*: Custom document display title
- **Response** (`201 Created`):
```json
{
  "id": "e5b8d234-a123-4567-8901-abcdef012345",
  "tenant_id": "c1f2e3d4-b5a6-7890-1234-567890abcdef",
  "title": "Corporate Hardware Return Policy 2026",
  "original_filename": "hardware_policy.pdf",
  "file_size": 184520,
  "mime_type": "application/pdf",
  "file_type": "pdf",
  "status": "INDEXED",
  "total_chunks": 8,
  "error_message": null,
  "created_at": "2026-10-29T22:30:00Z",
  "updated_at": null
}
```

---

### List Authorized Workspace Documents
`GET /api/v1/rag/documents`
- **Permissions**: `VIEWER` or higher
- **Response** (`200 OK`):
```json
{
  "total": 3,
  "documents": [
    {
      "id": "e5b8d234-a123-4567-8901-abcdef012345",
      "tenant_id": "c1f2e3d4-b5a6-7890-1234-567890abcdef",
      "title": "Corporate Hardware Return Policy 2026",
      "original_filename": "hardware_policy.pdf",
      "file_size": 184520,
      "mime_type": "application/pdf",
      "file_type": "pdf",
      "status": "INDEXED",
      "total_chunks": 8,
      "error_message": null,
      "created_at": "2026-10-29T22:30:00Z",
      "updated_at": null
    }
  ],
  "organization_id": "c1f2e3d4-b5a6-7890-1234-567890abcdef"
}
```

---

### Get Document Details & Chunk Previews
`GET /api/v1/rag/documents/{document_id}`
- **Permissions**: `VIEWER` or higher
- **Response** (`200 OK`):
```json
{
  "document": { ... },
  "chunks": [
    {
      "id": "chunk-uuid",
      "document_id": "e5b8d234-a123-4567-8901-abcdef012345",
      "chunk_index": 0,
      "chunk_text": "Section 1: General Warranty. All purchased hardware is covered for 12 calendar months...",
      "token_count": 85,
      "page_number": 1,
      "section_title": "General Warranty"
    }
  ]
}
```

---

### Reindex Document
`POST /api/v1/rag/documents/{document_id}/reindex`
- **Permissions**: `ANALYST` or higher
- Re-chunks and re-embeds the original file safely without creating duplicate records.

---

### Delete Document
`DELETE /api/v1/rag/documents/{document_id}`
- **Permissions**: `ADMIN` or `OWNER`
- Deletes document metadata, database chunks, physical file on disk, and synchronizes the FAISS vector index.

---

## 2. Knowledge Assistant Query & Chat Endpoint

### Ask RAG Assistant
`POST /api/v1/rag/chat`
- **Permissions**: `VIEWER` or higher
- **Request Body**:
```json
{
  "query": "What are the rules for bulk wholesale discounts on hardware?",
  "top_k": 4,
  "similarity_threshold": 0.60,
  "document_id": null,
  "sku": null
}
```
- **Response** (`200 OK`):
```json
{
  "query": "What are the rules for bulk wholesale discounts on hardware?",
  "answer": "According to the Sales Operating Procedure [cit_1], orders exceeding 100 units receive an automatic 15% wholesale discount. Any discount exceeding 25% requires formal approval from the Sales Director.",
  "intent": "KNOWLEDGE",
  "has_sufficient_context": true,
  "citations": [
    {
      "citation_id": "cit_1",
      "document_id": "e5b8d234-a123-4567-8901-abcdef012345",
      "document_title": "Sales Operating Procedure 2026",
      "filename": "sales_sop.md",
      "page_number": 1,
      "section_title": "Pricing and Bulk Discounts",
      "snippet": "Orders over 100 units qualify for an automatic 15 percent wholesale discount. Approval from the Sales Director is required for any commercial discount exceeding 25 percent...",
      "similarity_score": 0.8842
    }
  ],
  "model": "Google Gemini (gemini-1.5-pro)",
  "execution_time_ms": 342.15,
  "grounded_evidence": null,
  "error": null
}
```

---

## 3. System Health & Observability

### RAG System Health
`GET /api/v1/rag/health`
- **Permissions**: `VIEWER` or higher
- **Response** (`200 OK`):
```json
{
  "status": "HEALTHY",
  "vector_store": "Dual-Layer FAISS + SQLite/PostgreSQL",
  "embedding_model": "text-embedding-004",
  "total_documents": 3,
  "total_chunks": 42,
  "faiss_active": true
}
```

