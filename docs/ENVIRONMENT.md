# Sales Intelligence Platform
# Environment Configuration & Local Setup Guide

**Document:** ENVIRONMENT.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Platforms:** Windows, macOS, Linux, Docker

---

## 1. Prerequisites

Before setting up the project locally, verify the following runtimes:

- **Python**: Version 3.11 or 3.12 (`python --version`)
- **Node.js**: Version 18.x or 20.x LTS (`node --version`)
- **Package Managers**: `pip` (Python) and `npm` (Node)
- **Git**: (`git --version`)
- **Optional**: Docker Desktop for containerized deployment

---

## 2. Environment Variables Configuration

Create a `.env` file in the project root and in `backend/.env`.

### 2.1 Backend Environment Template (`backend/.env`)
```bash
# ==============================================================================
# Database Configuration
# ==============================================================================
# SQLite (Local Development):
DATABASE_URL=sqlite:///./sql_app.db
# PostgreSQL (Production / Docker):
# DATABASE_URL=postgresql://postgres:password@localhost:5432/sales_intel

# ==============================================================================
# Security & JWT Authentication
# ==============================================================================
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY_FOR_PRODUCTION
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ==============================================================================
# Google Gemini Pro AI Copilot (Optional)
# ==============================================================================
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_MODEL=gemini-1.5-pro

# ==============================================================================
# Background Processing & Redis (Optional)
# ==============================================================================
REDIS_URL=redis://localhost:6379/0

# ==============================================================================
# CORS Permitted Origins
# ==============================================================================
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 2.2 Frontend Environment Template (`frontend/.env.local`)
```bash
# Target backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 3. Step-by-Step Local Setup

### 3.1 Backend Installation & Startup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. (Optional) Populate database with sample sales records
python scripts/seed_data.py

# 6. Start FastAPI server
uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```
- Server endpoint: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### 3.2 Frontend Installation & Startup
```bash
# 1. Open a new terminal and navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Next.js development server
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 4. SQLite Development Auto-Migration

When running locally with SQLite (`DATABASE_URL=sqlite:///./sql_app.db`), the application automatically executes an internal schema auto-migration on server startup ([`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py)).

If the database is missing commercial reporting columns (`order_id`, `category`, `sub_category`, `total_sales`, `profit`), they are added dynamically via `ALTER TABLE` without wiping existing data.

---

## 5. Security Checklist
- [x] `.env` is listed in `.gitignore` to prevent committing secrets.
- [x] No production passwords or API tokens are hardcoded in application files.
- [x] CORS origins are restricted to configured client hosts.

---

**End of Environment Configuration & Local Setup Guide**
