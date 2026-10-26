# Sales Intelligence Platform
# UI/UX Design Specification

**Document:** DESIGN.md  
**Version:** 2.0  
**Planning Year:** 2026  
**Status:** Verified & Synchronized Specification  
**Design System:** Enterprise Dark SaaS (Next.js 14 + Tailwind CSS + Recharts)

---

## 1. Design Vision & Philosophy

The Sales Intelligence Platform interface is engineered for commercial executives, financial analysts, and supply-chain planners. It delivers dense, high-contrast, data-driven telemetry while strictly adhering to non-fabrication principles.

### Core Principles
1. **Data-Grounded Authenticity**: Every KPI, chart series, and badge is connected directly to verifiable ledger data. No fake mock values or artificial approximations.
2. **Clear Temporal Demarcation**: Solid emerald traces (`#10B981`) indicate historical actual ledger transactions; dashed blue lines (`#3B82F6`) and blue translucent bands (`rgba(59, 130, 246, 0.2)`) represent statistical model projections and confidence intervals.
3. **Progressive Disclosure**: High-level KPIs and summaries appear at the top, followed by sortable category grids, time-series visualizations, and granular schema notes.
4. **Resilient Feedback**: Loading states utilize spinning indicators with disabled buttons, empty states guide users toward dataset ingestion, and validation errors display explicit boundary alerts.

---

## 2. Design Tokens & Theme System

The application employs a dark enterprise palette built on Tailwind CSS:

| Token | Hex / Class | Semantic Usage |
| :--- | :--- | :--- |
| **Canvas Background** | `#0B1120` (`bg-background`) | Full-page background. |
| **Card Surface** | `#111827` (`bg-surface`) | Metric cards, section panels, table containers. |
| **Elevated Surface** | `#1E293B` (`bg-slate-800`) | Input fields, active button states, dropdown items. |
| **Border / Divider** | `#334155` (`border-slate-700`) | Card borders, table row dividers, control separators. |
| **Text Primary** | `#FFFFFF` (`text-white`) | Headings, primary KPI values, table headers. |
| **Text Muted** | `#94A3B8` (`text-slate-400`) | Labels, captions, metadata timestamps. |
| **Brand Primary** | `#3B82F6` (`text-primary`) | Action buttons, active navigation, focus rings. |
| **Success / Actuals**| `#10B981` (`text-emerald-400`) | Actual sales line, positive margins, healthy models. |
| **Warning / Caution**| `#F59E0B` (`text-amber-400`) | Medium anomalies, data notices, missing profit alerts. |
| **Danger / Loss** | `#EF4444` (`text-danger`) | Commercial losses, negative margins, high anomalies. |

---

## 3. Global Navigation & Layout Shell

The global application shell ([`frontend/app/layout.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/layout.tsx) and [`frontend/components/layout/Sidebar.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/components/layout/Sidebar.tsx)) provides persistent 64-pixel sidebar navigation:

```text
+-----------------------+-------------------------------------------------------+
|  Sales Intel AI       |  Top Header (Page Title, Dataset Ledger Coverage)     |
|  Enterprise Platform  +-------------------------------------------------------+
+-----------------------+                                                       |
|  * Overview           |  Main Interactive Content Area                        |
|  * Forecast Lab       |                                                       |
|  * Reports & Exports  |  (Controls, Metric Cards, Charts, Tables)             |
|  * Anomalies          |                                                       |
|  * Scenario Lab       |                                                       |
|  * Inventory Intel    |                                                       |
|  * Model Health       |                                                       |
|  * Gemini AI          |                                                       |
|  * Data Ingestion     |                                                       |
+-----------------------+                                                       |
|  User Session & Auth  |                                                       |
+-----------------------+-------------------------------------------------------+
```

---

## 4. Forecast Lab & Model Selection UI ([`frontend/app/forecast/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/forecast/page.tsx))

### 4.1 Target Name Combobox
- Combines a searchable dropdown and custom SKU entry mode.
- Autocomplete search filters by product title, SKU code, or category label.
- Displays unambiguous SKU badges (`SKU: LOGI-102`) when duplicate product names exist.
- Defaults to `"All Products (Global Aggregate)"` (`ALL`).

### 4.2 Horizon Mode Segmented Control
- Two-option segmented pill control:
  - **Option A: Selected Date** (Calendar icon).
  - **Option B: Date Range** (CalendarDays icon).
- **Option A (Selected Date)**:
  - Native HTML5 date input (`<input type="date">`).
  - Presets: *Latest Recorded*, *Next Day (+1d)*, *Future (+7d)*.
  - Explanatory note: Historical dates display actual transactions and deltas; future dates execute forward ML walk-forward models.
- **Option B (Date Range)**:
  - Start Date and End Date dual pickers.
  - Presets: *Last 30 Days*, *Last 90 Days*, *Actuals + Next 14d Forecast*.
  - Boundary validation: Real-time visual alert when `Start Date > End Date`.

### 4.3 Model Engine Selector & Action Trigger
- Dropdown select:
  - `Auto-Select (Walk-Forward Best Model)` (default)
  - `ARIMA (Auto-Regressive Integrated MA)`
  - `Seasonal Naive (snaive Baseline)`
- Action Trigger: **`"Analyse & Generate Report"`** button with gradient styling and spinning state.
- Secondary Quick Action: **`"Generate Professional Sales Report"`** button triggering immediate CSV report generation for the selected product and dates.

### 4.4 Report Display Sections
1. **Section A (Header Manifest)**: Target Name, SKU code, analysis mode, generation timestamp, status badge (`HISTORICAL ACTUALS` in emerald or `PROJECTED DEMAND` in blue). Includes direct `"Export Professional Report (.csv)"` and `"Reports Center"` links.
2. **Section B (Telemetry Grid)**: 4 KPI cards (Total Sales Revenue, Quantity Sold, Daily Sales Average, Period Comparison).
3. **Section C (Model Performance Bounds)**: Evaluation metrics (MAE, RMSE, WAPE), forecast point, lower bound, upper bound, and methodological notes.
4. **Section D (Interactive Chart)**: Dynamic Recharts graph with solid emerald actuals, dashed blue forecast, and shaded confidence band.
5. **Section E (Business Insights)**: 3 grounded action cards (replenishment triggers, peak sales dates, baseline demand signals).

---

## 5. Reports & Export Center UI ([`frontend/app/reports/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/reports/page.tsx))

### 5.1 Configuration & Scope Panel
- Target Product Scope selector matching Forecast Lab options.
- Date Horizon toggles (Option A vs. Option B) with coverage presets (*Full Dataset Coverage*, *Last 30 Days*, *Last 90 Days*).
- Action Button: **`"Generate Professional Sales Report"`**.

### 5.2 Executive KPI Telemetry Cards
Four top-level summary cards:
1. **Total Tracked Revenue**: Formatted as currency (`$2,326,534.35`).
2. **Distinct Order Volume**: True distinct store orders (`COUNT(DISTINCT order_id)`).
3. **Units Sold**: Integer transaction volume.
4. **Tracked Net Profit & Profit Margin**: Colored green if profitable, red if negative (commercial loss), or displays `"N/A"` if profit data is missing.

### 5.3 Category & Sub-Category Commercial Performance Table
A high-density tabular grid displaying the 7 required columns:
- `Category` (sortable text)
- `Sub-Category` (sortable text)
- `Total Orders` (sortable integer, right-aligned)
- `Total Quantity Sold` (sortable integer, right-aligned)
- `Total Sales (USD)` (sortable currency, right-aligned)
- `Total Profit (USD)` (sortable, formatted to 2 decimals or `"N/A"`, styled red if negative)
- `Profit Margin (%)` (sortable percentage or `"N/A"`, badge highlighted green if >= 20%)

Features:
- Instant client-side search input filtering categories and sub-categories.
- Interactive sort arrows on every column header.
- Schema notice card listing dataset limitations (e.g. absent profit or order ID).

### 5.4 Export Delivery Center
- **Download Detail CSV**: Downloads `professional_sales_summary_YYYY-MM-DD.csv` containing strictly the 7 data columns.
- **Download Summary CSV**: Downloads `professional_sales_summary_summary_YYYY-MM-DD.csv` containing metadata and summary KPIs.
- **Download JSON**: Full nested structured JSON object.
- **Print / Save as PDF**: Triggers browser print preview with dedicated print styles.

### 5.5 Print / PDF Stylesheet Specifications
Print styles (`@media print`) ensure clean executive reports:
- Hides sidebar, control panels, search bars, and action buttons (`print:hidden`).
- Removes borders and shadows (`print:border-none`).
- Expands table to 100% printable page width.
- Sets high-contrast black text on white background for crisp paper and PDF output.

---

## 6. Other Dashboard Interfaces

### 6.1 Anomaly Center ([`frontend/app/anomalies/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/anomalies/page.tsx))
- Displays moving Z-score anomalies with severity badges: `HIGH` (red), `MEDIUM` (amber), `LOW` (blue).
- Suggests immediate investigation actions (e.g. check supplier lead times, audit transaction logs).

### 6.2 Scenario Simulation Lab ([`frontend/app/scenarios/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/scenarios/page.tsx))
- Interactive sliders for Price Adjustment (-50% to +50%), Discount Rate (0% to 50%), and Demand Multiplier (0.5x to 2.0x).
- Visual delta cards comparing baseline revenue with simulated projections.

### 6.3 Data Ingestion & Management ([`frontend/app/data/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/data/page.tsx))
- Drag-and-drop CSV upload dropzone.
- Status indicator displaying total ingested records and min/max ledger dates.
- Clean duplicates and database reset actions.

### 6.4 Gemini Pro Sales Advisor ([`frontend/app/gemini/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/gemini/page.tsx))
- Natural-language query interface with quick-action prompt chips.
- Renders structured markdown responses and grounded empirical evidence.
- Diagnostic error report card when API keys are unconfigured or rate limits occur.

---

**End of UI/UX Design Specification**
