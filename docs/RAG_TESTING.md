# SalesMind AI — RAG Testing & Quality Assurance Guide

This document describes the automated test suite and regression coverage implemented for the RAG Knowledge Assistant.

---

## 1. Automated Test Suite Overview

Test file: [`backend/tests/test_rag.py`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/backend/tests/test_rag.py)

The test suite covers 10 dedicated test cases across unit, integration, and security boundaries:

| Test Case | Scope | Description |
|---|---|---|
| `test_recursive_split_text` | Unit | Verifies structure-aware splitting on paragraph (`\n\n`), sentence, and word boundaries with overlap preservation. |
| `test_chunk_document_sections_preserves_metadata` | Unit | Verifies page numbers, section titles, and token counts are correctly attached to every chunk. |
| `test_csv_parser_structured_sections` | Unit | Tests tabular parsing into semantic records with column names and schema summary. |
| `test_json_parser_structured_sections` | Unit | Verifies structured JSON entity traversal and key-value serialization. |
| `test_deterministic_embedding_adapter` | Unit | Verifies 768-dimensional L2-normalized vector embedding generation, repeatability, and cosine similarity. |
| `test_hybrid_intent_classification` | Unit | Tests classification of user inquiries into `KNOWLEDGE`, `LEDGER_ANALYTICS`, and `HYBRID`. |
| `test_rag_document_upload_and_indexing` | API / E2E | Uploads Markdown document, verifies chunking, re-indexing, grounded chat query with citations, and safe deletion. |
| `test_rag_abstention_on_unrelated_query` | API | Verifies honest abstention (`has_sufficient_context: false`) when inquiry falls below similarity threshold. |
| `test_rag_multi_tenant_isolation` | Security | Ingests confidential document in Tenant 1 and verifies Tenant 2 cannot query, retrieve, read, or delete it (404/empty). |
| `test_rag_health_endpoint` | API | Verifies public health check returns vector store status without credential exposure. |

---

## 2. Executing RAG Tests

Run the dedicated RAG test suite in Windows PowerShell:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest tests/test_rag.py -v
```

Expected result:
```
tests/test_rag.py::test_recursive_split_text PASSED
tests/test_rag.py::test_chunk_document_sections_preserves_metadata PASSED
tests/test_rag.py::test_csv_parser_structured_sections PASSED
tests/test_rag.py::test_json_parser_structured_sections PASSED
tests/test_rag.py::test_deterministic_embedding_adapter PASSED
tests/test_rag.py::test_hybrid_intent_classification PASSED
tests/test_rag.py::test_rag_document_upload_and_indexing PASSED
tests/test_rag.py::test_rag_abstention_on_unrelated_query PASSED
tests/test_rag.py::test_rag_multi_tenant_isolation PASSED
tests/test_rag.py::test_rag_health_endpoint PASSED

======================= 10 passed in 35.80s =======================
```

---

## 3. Running the Entire System Test Suite

To verify zero regression across existing modules (Analytics, Forecasting, RBAC, Cleaning Studio):

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest tests/
```

Total expected: **98 passed out of 98 tests (100% pass rate)**.

