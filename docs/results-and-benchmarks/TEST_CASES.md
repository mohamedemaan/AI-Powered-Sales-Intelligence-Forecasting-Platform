# Enterprise Test Cases & Verification Matrix

This document provides the formal, structured test case verification matrix for **SalesMind AI (AI-Powered Sales Intelligence & Forecasting Platform)**. 

All test cases, scenarios, expected results, and statuses documented below are derived directly from the official **Enterprise System Functional Test & QA Audit Report** (October 30, 2026) conducted by the Senior QA Architect (10+ Years Experience).

---

## Standardized Status Key

- `PASS`: Test scenario executed and verified matching expected results with documented evidence.
- `FAIL`: Test scenario executed and resulted in unexpected behavior, regression, or calculation error.
- `PARTIAL`: Feature partially implemented or functional with known non-blocking constraints.
- `NOT TESTED`: Scope deferred to future audit phases (e.g., third-party competitor comparisons).
- `EVIDENCE PENDING`: Test executed in single-user environment; broad concurrency/load evidence pending.

---

## 1. Module-by-Module Functional Test Matrix

### 1.1 Overview (Dashboard & Global KPIs)
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-OV-001` | Overview | Aggregate store-wide gross sales across all transactions | Gross sales matches row-level transaction sums ($2,326,534.52) | Reconciled exactly to \$2,326,534.52 | `PASS` | QA Report Sec 2.1 |
| `SM-OV-002` | Overview | Calculate distinct store-wide unique orders | Strictly applies `COUNT(DISTINCT order_id)` avoiding category double-counting | Exactly 5,111 unique orders verified | `PASS` | QA Report Sec 2.1 & 3.0 |
| `SM-OV-003` | Overview | Compute Average Order Value (AOV) | Mathematical quotient of gross sales divided by unique orders ($455.20) | Reconciled to \$455.20 without variance | `PASS` | QA Report Sec 2.1 |
| `SM-OV-004` | Overview | Calculate total net commercial profit | Accurate profit sum retaining loss line items ($292,297.46) | Reconciled to \$292,297.46 with negative margins | `PASS` | QA Report Sec 2.1 & 3.0 |
| `SM-OV-005` | Overview | Compute global operating profit margin | Net profit divided by gross sales equals 12.56% | Reconciled to 12.56% | `PASS` | QA Report Sec 2.1 |

### 1.2 Data Ingestion & Preview
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-DI-001` | Data Ingestion | Drag-and-drop CSV upload and schema parsing | Multipart CSV parsed cleanly without column truncation | 10,194 records loaded across 1,862 SKUs | `PASS` | QA Report Sec 2.2 |
| `SM-DI-002` | Data Ingestion | Dataset temporal boundary verification | Transaction dates strictly index between 2023-01-03 and 2026-12-30 | Verified boundary dates indexed in database | `PASS` | QA Report Sec 2.2 |
| `SM-DI-003` | Data Ingestion | Memory leak & buffer stability under 10k rows | No process memory leak or server timeout during upload | Atomic database update executed cleanly | `PASS` | QA Report Sec 2.2 |
| `SM-DI-004` | Data Ingestion | Dataset reset and atomic re-upload | Re-upload cleanly updates dataset state | Clean atomic overwrite verified | `PASS` | QA Report Sec 2.2 |

### 1.3 Data Cleaning Studio
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-DC-001` | Data Cleaning | Missing profit field handling in uploaded rows | System outputs `"N/A"` per non-fabrication rule; no artificial zero-padding | `"N/A"` displayed with schema note | `PASS` | QA Report Sec 2.3 & 3.0 |
| `SM-DC-002` | Data Cleaning | Missing category attribute handling | System outputs `"N/A"` rather than inventing category | `"N/A"` preserved in data view | `PASS` | QA Report Sec 2.3 |
| `SM-DC-003` | Data Cleaning | Automated duplicate row detection & removal | Identical line items flagged and deduplicated cleanly | Deduplication confirmed without record loss | `PASS` | QA Report Sec 2.3 |
| `SM-DC-004` | Data Cleaning | Outlier hygiene and schema type standardization | Dates, numerics, and currencies cast into strict schema types | Schema standardized cleanly | `PASS` | QA Report Sec 2.3 |

### 1.4 Sales Analytics
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-SA-001` | Sales Analytics | Multi-dimensional time-series aggregation | Daily, weekly, monthly sales trends render accurate curves | Trends rendered with peak/trough analysis | `PASS` | QA Report Sec 2.4 |
| `SM-SA-002` | Sales Analytics | Category and sub-category contribution rankings | Breakdown accurately displays volume, revenue, and margin % | Full breakdown generated with loss preservation | `PASS` | QA Report Sec 2.4 |
| `SM-SA-003` | Sales Analytics | Transaction explorer table sorting and filtering | Sub-second table sorting by SKU, Order ID, Date, Amount | Multi-column sorting and filtering verified | `PASS` | QA Report Sec 2.4 |
| `SM-SA-004` | Sales Analytics | Pagination and high-volume table scrolling | Responsive page slicing without frontend lag | Pagination operates smoothly | `PASS` | QA Report Sec 2.4 |

### 1.5 Forecast Lab & Model Selection
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-FL-001` | Forecast Lab | Option A (Selected Date) within historical boundary | Displays verified transaction actuals and WoW deltas | Actual transactions displayed without ML inference | `PASS` | QA Report Sec 2.5 & AGENTS.md |
| `SM-FL-002` | Forecast Lab | Option A (Selected Date) targeting future date | Triggers forward walk-forward ML forecast projection | ML model executes forward projection | `PASS` | QA Report Sec 2.5 |
| `SM-FL-003` | Forecast Lab | Option B (Date Range) multi-period forecast execution | Generates projections across selected calendar horizon | Multi-period projections rendered | `PASS` | QA Report Sec 2.5 |
| `SM-FL-004` | Forecast Lab | Model competition (Auto-ARIMA vs. Seasonal Naive) | Walk-forward cross-validation selects best model dynamically | Best performing model dynamically selected | `PASS` | QA Report Sec 2.5 |
| `SM-FL-005` | Forecast Lab | Forecast telemetry accuracy logging | Correctly logs empirical WAPE (45.2%) and MAE (19.71) | WAPE 45.2%, MAE 19.71 recorded | `PASS` | QA Report Sec 2.5 |

### 1.6 Anomaly Detection Center
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-AD-001` | Anomaly Detection | Dynamic rolling Z-score detection ($|Z| \ge 2.0$) | Statistical demand spikes and contractions detected | 434 total anomalies successfully detected | `PASS` | QA Report Sec 2.6 |
| `SM-AD-002` | Anomaly Detection | Extreme surge identification | Flags extreme holiday spike (Dec 02 at +5.4 sigma) | Dec 02 surge identified at +5.4 sigma | `PASS` | QA Report Sec 2.6 |
| `SM-AD-003` | Anomaly Detection | Severity classification markers | Correctly tags events as High ($|Z| \ge 3$) or Medium | Severity badges rendered accurately | `PASS` | QA Report Sec 2.6 |
| `SM-AD-004` | Anomaly Detection | Root-cause operational investigation guidance | Generates contextual guidance for flagged anomalies | Actionable diagnostic guidance generated | `PASS` | QA Report Sec 2.6 |

### 1.7 Scenario Simulation Lab (What-If Modeling)
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-SS-001` | Scenario Lab | Price adjustment slider parameter range (-50% to +50%) | Recalculates expected demand using elasticity $E_d = -0.75$ | Instant recalculation across slider range | `PASS` | QA Report Sec 2.7 |
| `SM-SS-002` | Scenario Lab | Promotional discount and macro demand multipliers | Dynamic multi-variable revenue simulation | Multi-parameter interaction computed cleanly | `PASS` | QA Report Sec 2.7 |
| `SM-SS-003` | Scenario Lab | 7-day projected revenue simulation run-rate | Projected revenue recalculates dynamically upon adjustment | Instant sub-second recalculation | `PASS` | QA Report Sec 2.7 |
| `SM-SS-004` | Scenario Lab | Stockout risk threshold warnings | Triggers operational alert if simulated demand exceeds stock | Stockout alerts rendered upon threshold breach | `PASS` | QA Report Sec 2.7 |

### 1.8 Inventory Intelligence & Velocity Tracking
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-II-001` | Inventory Intel | 30-day daily sales velocity tracking | Computes moving averages of unit consumption per SKU | Velocity tracking active across all 1,862 SKUs | `PASS` | QA Report Sec 2.8 |
| `SM-II-002` | Inventory Intel | 7-day demand runway and reorder estimation | Calculates runway days based on velocity trends | Reorder thresholds estimated dynamically | `PASS` | QA Report Sec 2.8 |
| `SM-II-003` | Inventory Intel | Schema degradation when physical stock column is omitted | Displays `"N/A (Omitted)"` without fabricating stock numbers | Cleanly displays `"N/A (Omitted)"` | `PASS` | QA Report Sec 2.8 & 3.0 |

### 1.9 Model Health & Prediction History
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-MH-001` | Model Health | Out-of-sample walk-forward cross-validation | Validates models on rolling historical test partitions | Walk-forward cross-validation active | `PASS` | QA Report Sec 2.9 |
| `SM-MH-002` | Model Health | Concept & data drift detection scoring | Drift score evaluates to 0 on active baseline partition | Drift score confirmed at 0 (stable) | `PASS` | QA Report Sec 2.9 |
| `SM-MH-003` | Model Health | Ground-truth prediction reconciliation audit | Audits forecasted volume against actual historical volume | Variance reconciliation logged accurately | `PASS` | QA Report Sec 2.9 |

### 1.10 Gemini Pro AI Advisor
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-AI-001` | Gemini Advisor | Live sales context prompt injection | Injects deterministic revenue, orders, margins, anomalies | Prompt payload strictly grounded in live metrics | `PASS` | QA Report Sec 2.10 |
| `SM-AI-002` | Gemini Advisor | Executive recommendation synthesis | Generates actionable business actions without hallucination | Executive narrative synthesized accurately | `PASS` | QA Report Sec 2.10 |
| `SM-AI-003` | Gemini Advisor | Graceful error handling on backend network failure | Clean error banner when API is unreachable | Defensive error handling verified | `PASS` | QA Report Sec 2.10 |

### 1.11 Knowledge Assistant & RAG Studio
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-KB-001` | Knowledge Assistant | Dual-layer FAISS vector store indexing (.md, .pdf) | Documents parsed, chunked, and embedded into index | Multi-format documents ingested cleanly | `PASS` | QA Report Sec 2.11 |
| `SM-KB-002` | Knowledge Assistant | Semantic retrieval of corporate return policies | Retrieves relevant chunks matching semantic query | Relevant policy clauses retrieved | `PASS` | QA Report Sec 2.11 |
| `SM-KB-003` | Knowledge Assistant | Grounded source citations and similarity scores | Outputs exact source document, page, and score | Grounded citations verified in chat response | `PASS` | QA Report Sec 2.11 |
| `SM-KB-004` | Knowledge Assistant | Query for missing/unindexed document information | Refuses hallucination; states information is not available | Grounding defense strictly verified | `PASS` | QA Report Sec 2.11 |

### 1.12 Reports & Exports Center
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-RE-001` | Reports Center | Filename pattern validation | Follows `professional_sales_summary_YYYY-MM-DD.csv` | Exact naming pattern verified | `PASS` | QA Report Sec 2.12 |
| `SM-RE-002` | Reports Center | Multi-format export generation (8 formats) | Generates XLSX, PDF, Parquet, Detail CSV, Summary CSV, TSV, JSON, Print | All 8 formats generated valid, compliant files | `PASS` | QA Report Sec 2.12 |
| `SM-RE-003` | Reports Center | RFC 4180 Detail CSV 7-column compliance | Detail CSV contains strictly the 7 data columns without header metadata | Schema-compliant 7-column structure verified | `PASS` | QA Report Sec 2.12 |
| `SM-RE-004` | Reports Center | Commercial loss retention in export | Negative margins (e.g., Furniture Tables at -8.53%) preserved | Negative margins exported without zero-padding | `PASS` | QA Report Sec 2.12 & 3.0 |

### 1.13 Subscription, Plans & Audit Logs
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-SB-001` | Subscriptions | Enterprise plan tier feature gating | Enforces access restrictions based on subscription tier | Plan tiers gated appropriately | `PASS` | QA Report Sec 2.13 |
| `SM-SB-002` | Subscriptions | Role-Based Access Control (Admin vs. Analyst) | Admin permissions required for privileged actions | RBAC boundaries verified | `PASS` | QA Report Sec 2.13 |
| `SM-SB-003` | Audit Logs | Immutable security event trail logging | Records user logins, exports, and data modifications | Complete event traceability verified | `PASS` | QA Report Sec 2.13 |

### 1.14 User Profile & Account Settings
| Test ID | Module | Test Scenario | Expected Result | Actual Result | Status | Evidence Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SM-PF-001` | User Profile | Authenticated user session profile retrieval | `GET /api/v1/users/me` returns current user identity & role | Profile data returned without credentials leakage | `PASS` | PRD & Architecture |
| `SM-PF-002` | User Profile | Role badge & tenant workspace display | Displays correct RBAC role badge (Admin / Analyst) | Verified role badge displayed | `PASS` | PRD & Design Specs |
| `SM-PF-003` | User Profile | Account credentials & password security policy | Enforces 12-char minimum with uppercase, number, symbol | Policy verified on account creation | `PASS` | Security Spec Sec 2.0 |

---

## 2. Broader Architectural Testing Categories

| Category | Scope | Result / Audit Observation | Status |
| :--- | :--- | :--- | :--- |
| **Installation & Environment** | Python 3.11+, Node 18+, Docker containerization | Verified clean dependencies and build across backend & frontend | `PASS` |
| **UI & Visual Layout** | Dark enterprise theme, Recharts responsive rendering | Verified responsive navigation across desktop and tablet | `PASS` |
| **Functional Testing** | All 13 core navigation modules | 100% of functional audit checkpoints certified | `PASS` |
| **API Testing** | REST endpoints (`/api/v1/...`), OpenAPI contracts | Schema validation via Pydantic v2 verified | `PASS` |
| **Database Testing** | PostgreSQL multi-tenant isolation, UUID PKs | Atomic transaction commit, grouping integrity, clean indices | `PASS` |
| **Data Upload Testing** | CSV ingestion with alias mapping, atomic replaces | Handled 10,194 records without data loss or truncation | `PASS` |
| **AI / ML Testing** | Time-series forecasting, Z-score anomalies, Gemini RAG | Anti-lookahead boundaries, walk-forward CV, grounded citations | `PASS` |
| **Security Testing** | JWT token authentication, Bcrypt password hashing | Passwords hashed with bcrypt; protected routes enforced | `PASS` |
| **Performance Testing** | High-concurrency load testing & stress testing | Sub-second response verified in single session; multi-user stress test pending | `EVIDENCE PENDING` |
| **Deployment Testing** | Cloud containerization (Render Backend, Vercel Frontend, Neon DB) | Cloud database connection and server-side deployment verified | `PASS` |
| **Competitor Benchmarking** | Comparison vs. Power BI, Tableau, Zoho Analytics | Explicitly postponed per project scope instructions | `NOT TESTED` |

