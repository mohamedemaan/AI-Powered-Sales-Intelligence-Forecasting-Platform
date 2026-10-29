# SalesMind AI — RAG Knowledge Assistant Setup Guide

This guide details how to configure, run, and verify the multi-tenant Retrieval-Augmented Generation (RAG) knowledge engine in your local Windows environment or production deployment.

---

## 1. Prerequisites & Environment

- **Operating System**: Windows 11, macOS, or Linux
- **Python**: 3.10+ (Current runtime: Python 3.12)
- **Node.js**: v18+ with npm
- **Database**: SQLite (default zero-config local development in `backend/sql_app.db`) or PostgreSQL for production

---

## 2. Environment Variables Configuration

Copy `.env.example` to `backend/.env` (or configure root `.env`):

```bash
# In Windows PowerShell:
Copy-Item backend\.env.example backend\.env
```

Open `backend/.env` and configure your settings:

```ini
# Google Gemini API (Get a free key from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY="AIzaSyYourActualKeyFromAIStudio"
GEMINI_MODEL="gemini-1.5-pro"
GEMINI_EMBEDDING_MODEL="text-embedding-004"

# RAG Engine Parameters
RAG_TOP_K=4
RAG_SIMILARITY_THRESHOLD=0.60
RAG_MAX_CONTEXT_CHARS=4000
RAG_MAX_UPLOAD_MB=25
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=150
```

> [!NOTE]
> **Offline / Resilient Fallback Mode**:
> If `GEMINI_API_KEY` is not yet configured or Google AI Studio encounters transient quotas, SalesMind AI automatically activates its high-speed deterministic offline vector adapter. The platform remains 100% testable and operational without external cloud dependencies.

---

## 3. Starting the Backend Service

In Windows PowerShell from the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify backend health at:
- Documentation: `http://127.0.0.1:8000/docs`
- RAG Health Endpoint: `http://127.0.0.1:8000/api/v1/rag/health`

---

## 4. Starting the Next.js Frontend

In a separate terminal from the repository root:

```powershell
Set-Location frontend
npm run dev
```

Navigate your browser to:
- **Knowledge Assistant (RAG)**: `http://localhost:3000/knowledge`
- **Sales Analytics Dashboard**: `http://localhost:3000/dashboard`

---

## 5. First-Time Verification Smoke Test

1. Open `http://localhost:3000/knowledge` in your browser.
2. Click **Document Ingestion & Index**.
3. Drag and drop any test file (`.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.tsv`, or `.json`).
4. Watch the instant progress status transition to `INDEXED`.
5. Switch to **Knowledge Assistant Chat** and ask a question grounded in your document.
6. Observe the answer, citation tags `[cit_1]`, similarity percentage, and clickable preview popovers.

