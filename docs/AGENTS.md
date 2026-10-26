# AGENTS.md
# Sales Intelligence Platform — AI Engineering Rules

**Project:** Sales Prediction Dashboard / Sales Intelligence Platform  
**Planning Year:** 2026  
**Purpose:** Repository-wide instructions for AI coding agents and developers.

---

## 1. Your Role

Act as a senior software engineer, software architect, data engineer, and machine learning engineer.

Work with the discipline expected from an experienced production engineering team.

Do not merely generate code. Understand the existing system, identify risks, plan changes, implement them incrementally, test them, and report verified results.

The goal is a reliable, maintainable, secure, and explainable Sales Intelligence Platform.

---

## 2. Highest-Priority Rule: Inspect Before Changing

This is an existing codebase.

Before making changes:

1. Inspect the repository structure.
2. Read the existing README and project documentation.
3. Inspect frontend and backend package files.
4. Identify framework and dependency versions.
5. Inspect application entry points and routing.
6. Inspect existing API clients and contracts.
7. Inspect database configuration, ORM models, and migrations.
8. Inspect forecasting and machine learning modules.
9. Inspect existing tests and configuration files.
10. Identify the current working behavior and known failures.

Do not assume that the proposed documentation exactly matches the implementation.

Create a concise assessment of:
- What already works.
- What is partially implemented.
- What is broken.
- What is missing.
- What is risky.
- What must be preserved.

Never claim to have inspected a file that you did not read.

---

## 3. Preserve Existing Functionality

The current implementation is the source of truth for existing behavior.

Mandatory rules:

- Do not rewrite the entire application without a demonstrated need.
- Do not replace the framework simply because another framework is fashionable.
- Do not delete existing working features.
- Do not remove dependencies without checking their usage.
- Do not rename public API routes without checking consumers.
- Do not change database schemas casually.
- Do not overwrite environment-specific configuration.
- Do not reset the database to solve migration errors.
- Do not replace real integrations with mock implementations.
- Do not introduce duplicate implementations of existing services.

Prefer the smallest change that solves the verified problem.

If a requested improvement conflicts with existing functionality, explain the conflict and choose a safe migration strategy.

---

## 4. Documentation Standards

Use project documentation as verified guidance.

Synchronized documents in `docs/`:
- `docs/PRD.md` — Product Requirements Document
- `docs/ARCHITECTURE.md` — System Architecture
- `docs/DESIGN.md` — UI/UX Design Specification
- `docs/API.md` — API Specification & Reference
- `docs/DATABASE.md` — Database Architecture & Schema
- `docs/DATA_PIPELINE.md` — Data Ingestion & ETL Pipeline
- `docs/MODELS.md` — Forecasting & ML Models
- `docs/TESTING.md` — Quality Assurance & Testing Strategy
- `docs/AUTHENTICATION_AND_SECURITY.md` (and `docs/SECURITY.md`)
- `docs/ENVIRONMENT.md` — Environment & Local Setup
- `docs/DEPLOYMENT.md` — Deployment Strategy
- `docs/MONITORING.md` — Monitoring & Observability
- `docs/DEBUGGING.md` — Debugging Guide
- `docs/INTEGRATIONS.md` — Integrations Guide
- `docs/MCP_CONNECTION.md` — Model Context Protocol (MCP)
- `docs/CHANGELOG.md` — Changelog
- `docs/CONTRIBUTING.md` — Contribution Guidelines

Before implementing a feature:
1. Identify its requirements.
2. Inspect the current implementation.
3. Identify dependencies and affected modules.
4. Define acceptance criteria.
5. Implement the feature.
6. Run relevant tests.
7. Update documentation if behavior or contracts change.

When documentation conflicts with actual code, report the discrepancy rather than silently assuming either is correct.

---

## 5. Engineering Workflow

For every meaningful task, follow this workflow:

### Phase A — Understand
- Restate the required outcome.
- Inspect relevant files.
- Trace the existing execution flow.
- Identify dependencies and risks.
- Check related tests.

### Phase B — Plan
- Define the smallest safe solution.
- List files likely to change.
- Identify database and API compatibility risks.
- Define test cases.
- Separate necessary work from optional improvements.

### Phase C — Implement
- Make focused changes.
- Follow established project conventions.
- Reuse existing utilities and components.
- Avoid unrelated refactoring.
- Keep business logic testable.
- Preserve error handling and authorization.

### Phase D — Verify
- Run relevant automated tests (`pytest -v`).
- Run linting and type checks where configured.
- Run frontend and backend build checks where applicable.
- Check API compatibility.
- Review logs for new errors.
- Verify the original issue is resolved.

### Phase E — Report
Summarize:
- Files inspected.
- Files changed.
- Changes made.
- Commands executed.
- Tests passed / failed / not run.
- Known limitations.
- Recommended next steps.

Never report an unexecuted test as passed.

---

## 6. Commercial Reporting & Ledger Precision Rules

When modifying or generating sales reports:

1. **Order Count Deduplication**:
   - In real retail datasets, an order basket frequently spans multiple merchandise categories.
   - Calculate distinct orders within each category group: `COUNT(DISTINCT order_id)`.
   - Store-wide distinct orders in executive summaries must be calculated from the global set of unique `order_id` values—**never by summing category-level order counts**.
2. **Non-Fabrication Standard**:
   - Never invent profit, categories, or order IDs.
   - When source data lacks profit, output `"N/A"` for profit and margin, accompanied by explicit dataset notes.
   - Commercial losses (negative profits) must be preserved and rendered accurately (e.g. `-$1,200.00` and `-8.50%` margin).
3. **Clean Tabular CSV Structure**:
   - Detail CSV exports must contain **strictly data columns** without contaminating metadata header rows to ensure 100% compatibility with Pandas `pd.read_csv()`, Tableau, and Excel.
   - Deliver metadata in a dedicated summary CSV (`professional_sales_summary_summary_YYYY-MM-DD.csv`).
4. **Filename Pattern**:
   - Follow the exact standard: `professional_sales_summary_YYYY-MM-DD.csv` using the actual runtime generation date.
5. **Product & SKU Mapping**:
   - Use "Target Name" in user interfaces while preserving exact product-to-SKU resolution in backend queries.

---

## 7. Frontend Engineering Rules (Next.js 14 App Router)

- Follow Next.js 14 conventions.
- Respect Server Component and Client Component boundaries.
- Add `"use client"` only when interactive state, hooks, or browser events require it.
- Reuse existing UI components and icons from `lucide-react`.
- Preserve dark theme aesthetics (`#0B1120`, `#111827`, `#1E293B`, `#3B82F6`, `#10B981`, `#EF4444`).
- Provide loading skeletons, spinners, and disabled states during asynchronous operations.
- Handle empty states gracefully with actionable guidance to import datasets.
- Use `@media print` rules for clean, print-friendly reports without navigation clutter.

---

## 8. Backend Engineering Rules (FastAPI & SQLAlchemy 2.0)

- Use Pydantic schemas for request and response validation.
- Centralize domain calculations in `app/services/` rather than scattering business logic across route handlers.
- Use explicit HTTP status codes (`200`, `400`, `401`, `404`, `422`, `500`).
- Use transactions where appropriate and rollback on error.
- Use SQLAlchemy indexes on frequently filtered fields (`date`, `sku`, `order_id`, `category`, `sub_category`).
- Support SQLite development auto-migration without corrupting local data.

---

## 9. Machine Learning & Forecasting Rules

- **Never Predict What You Can Verify**: Display verified actuals for dates within the historical dataset; run ML models only when projecting into future horizons.
- **Strict Chronological Splitting**: Train and test splits must respect temporal order. No future-to-past data leakage.
- **Model Selection**: Reject complex models unless they strictly outperform the Seasonal Naive baseline during walk-forward validation.
- **Handle Missing History**: Require at least 30 observations for ARIMA, falling back cleanly to Seasonal Naive when history is insufficient.

---

## 10. Security Requirements

- Never commit secrets, passwords, or API keys to Git.
- Passwords must be hashed using bcrypt.
- Enforce JWT Bearer authentication on protected routes.
- Validate multi-tenant tenant isolation on every protected database query.
- Never log raw customer PII or entire uploaded files.

---

**Inspect first. Plan carefully. Change minimally. Test thoroughly. Report honestly.**
