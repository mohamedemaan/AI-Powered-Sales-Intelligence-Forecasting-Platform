# Sales Intelligence Platform
# Contribution Guidelines

**Document:** CONTRIBUTING.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification

---

## 1. Welcome

Thank you for contributing to the Sales Intelligence Platform! We welcome contributions from both human engineers and AI coding assistants.

---

## 2. Core Contribution Principles

1. **Inspect Before Changing**: Inspect the actual codebase, package manifests, and database schema before making changes. Never assume or fabricate.
2. **Preserve Working Functionality**: Make focused, reviewable edits. Do not rewrite functioning modules.
3. **Ledger Precision & Non-Fabrication**:
   - Calculate distinct orders using `COUNT(DISTINCT order_id)`.
   - Never sum category distinct orders to claim store-wide unique orders.
   - Retain commercial losses (negative profit) and negative margins.
   - If profit or category is absent from source data, output `"N/A"` with documented schema notes rather than inventing zero.
   - Follow the exact filename pattern: `professional_sales_summary_YYYY-MM-DD.csv`.
4. **Never Commit Secrets**: Ensure `.env` and sensitive credentials remain excluded from Git.

---

## 3. Local Development Workflow

1. **Fork & Clone**:
   ```bash
   git clone https://github.com/your-username/sales-prediction-dashboards.git
   cd sales-prediction-dashboards
   ```
2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Run Tests**:
   ```bash
   cd backend
   pytest -v
   ```

---

## 4. Coding Standards

- **Python (Backend)**: Follow PEP 8 standards. Use type annotations (`typing.Optional`, `typing.List`, `typing.Dict`) and Pydantic v2 schemas for all API payloads.
- **TypeScript / React (Frontend)**: Follow React 18 and Next.js 14 App Router patterns. Keep Client Components marked with `"use client"` only when interactive state is required. Use Tailwind CSS utility classes and `lucide-react` icons.
- **SQLAlchemy 2.0**: Use declarative base with UUID primary keys. Always use parameterized queries.
- **Documentation**: Whenever changing an API endpoint, data model, or UI workflow, update the corresponding markdown documentation in `docs/` and add an entry in [`docs/CHANGELOG.md`](CHANGELOG.md).

---

**End of Contribution Guidelines**
