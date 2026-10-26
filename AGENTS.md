# AGENTS.md
# Sales Intelligence Platform — AI Engineering Rules

This file provides root-level guidelines for AI coding assistants and developers.  
Full synchronized documentation is maintained in the [`docs/`](docs/) directory.

See [docs/AGENTS.md](docs/AGENTS.md) for complete engineering rules, architectural standards, and operational guidelines.

---

## Core Rules Summary

1. **Inspect Before Changing**: Inspect the actual codebase, package manifests, and database schema before making changes. Never assume or fabricate.
2. **Preserve Working Code**: Make minimal, focused, reviewable edits. Do not rewrite functioning modules.
3. **Ledger Precision & Non-Fabrication**:
   - Calculate distinct orders using `COUNT(DISTINCT order_id)`.
   - Never sum category distinct orders to claim store-wide unique orders.
   - Retain commercial losses (negative profit) and negative margins.
   - If profit or category is absent from source data, output `"N/A"` with documented schema notes rather than inventing zero.
   - Follow the exact filename pattern: `professional_sales_summary_YYYY-MM-DD.csv`.
4. **Temporal Grounding**: For dates within historical ledger coverage, display verified actuals and week-over-week deltas; run forward walk-forward ML models only when targeting future dates.
5. **Security & Secrets**: Never commit `.env` secrets, passwords, or production keys. Passwords must be hashed with bcrypt.

