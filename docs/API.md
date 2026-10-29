# Sales Intelligence Platform
# API Specification & Reference

**Version:** 3.0  
**Planning Year:** 2026  
**Last Synchronized:** October 30, 2026  
**Status:** Verified & Synchronized Specification  
**Base URL:** `http://127.0.0.1:8000` (Local) / `/api/v1` (Production)  
**Interactive Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI) / [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) (ReDoc)

---

## 1. Authentication & Security

Protected endpoints require a valid JWT Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```
- Tokens are issued by `POST /api/v1/auth/login`.
- Algorithm: HMAC-SHA256 (`HS256`).
- Expiration: 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- Multi-tenancy: User organization tenancy is validated automatically from the token payload.

---

## 2. API Endpoints Directory

### 2.1 Analytics & Reporting Router (`/api/v1/analytics`)
Implemented in [`backend/app/api/v1/endpoints/analytics.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/analytics.py).

#### `POST /api/v1/analytics/report` & `GET /api/v1/analytics/report`
- **Purpose**: Generates the comprehensive Professional Sales Summary Report containing summary KPIs, metadata, category/sub-category commercial performance breakdowns, and pre-formatted CSV payloads.
- **Frontend Caller**: [`frontend/app/reports/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/reports/page.tsx) and [`frontend/app/forecast/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/forecast/page.tsx).
- **Request Parameters**:
  - `target_name` (string, default `"ALL"`): Target product title, SKU code, or `"ALL"` for global store aggregate.
  - `mode` (string, default `"range"`): `"single"` for Selected Date, `"range"` for Date Range.
  - `selected_date` (string, optional): Target calendar date (`YYYY-MM-DD`).
  - `start_date` (string, optional): Beginning of date range (`YYYY-MM-DD`, inclusive).
  - `end_date` (string, optional): End of date range (`YYYY-MM-DD`, inclusive).
- **Request Body (POST)**:
  ```json
  {
    "target_name": "ALL",
    "mode": "range",
    "start_date": "2024-01-01",
    "end_date": "2026-12-30"
  }
  ```
- **Response Schema (`200 OK`)**:
  ```json
  {
    "report_metadata": {
      "report_title": "Professional Sales Summary Report",
      "generated_at": "2026-10-22T20:30:00Z",
      "filename": "professional_sales_summary_2026-10-22.csv",
      "summary_filename": "professional_sales_summary_summary_2026-10-22.csv",
      "analysis_mode": "Date Range: 2024-01-01 to 2026-12-30",
      "mode_type": "range",
      "selected_date": null,
      "start_date": "2024-01-01",
      "end_date": "2026-12-30",
      "target_product": "All Products (Global Aggregate)",
      "currency": "USD",
      "total_records_included": 10194,
      "has_data": true,
      "empty_reason": null,
      "data_coverage_period": {
        "min_date": "2023-01-03",
        "max_date": "2026-12-30",
        "total_store_records": 10194
      },
      "features_available": {
        "has_category": true,
        "has_sub_category": true,
        "has_order_id": true,
        "has_profit": true,
        "has_sales": true
      },
      "missing_data_notes": []
    },
    "summary": {
      "total_revenue": 2297200.86,
      "total_distinct_orders": 5009,
      "total_quantity_sold": 37873,
      "total_profit": 286397.02,
      "overall_profit_margin_pct": 12.47,
      "total_categories": 3,
      "total_sub_categories": 17,
      "total_skus_analyzed": 1862,
      "total_records_analyzed": 10194
    },
    "category_breakdown": [
      {
        "category": "Technology",
        "sub_category": "Phones",
        "total_orders": 876,
        "total_quantity_sold": 3289,
        "total_sales_usd": 330007.05,
        "total_profit_usd": 44515.73,
        "profit_margin_pct": 13.49
      },
      {
        "category": "Furniture",
        "sub_category": "Tables",
        "total_orders": 319,
        "total_quantity_sold": 1241,
        "total_sales_usd": 206965.53,
        "total_profit_usd": -17725.48,
        "profit_margin_pct": -8.56
      }
    ],
    "detail_csv": "Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage\nTechnology,Phones,876,3289,330007.05,44515.73,13.49\nFurniture,Tables,319,1241,206965.53,-17725.48,-8.56\n",
    "summary_csv": "Report_Metadata,Value\nReport Title,Professional Sales Summary Report\nTotal Revenue (USD),\"$2,297,200.86\"\nTotal Distinct Orders,5009\n"
  }
  ```

#### `GET /api/v1/analytics/report/csv`
- **Purpose**: Direct streaming HTTP download of the RFC 4180 CSV report.
- **Query Parameters**:
  - `target_name` (string, default `"ALL"`)
  - `mode` (string, default `"range"`)
  - `selected_date` (string, optional)
  - `start_date` (string, optional)
  - `end_date` (string, optional)
  - `type` (string, default `"detail"`): `"detail"` returns `professional_sales_summary_YYYY-MM-DD.csv`; `"summary"` returns `professional_sales_summary_summary_YYYY-MM-DD.csv`.
- **Response (`200 OK`)**:
  - `Content-Type: text/csv; charset=utf-8`
  - `Content-Disposition: attachment; filename="professional_sales_summary_2026-10-22.csv"`

#### `GET /api/v1/analytics/overview`
- **Purpose**: Retrieves high-level business intelligence KPIs, period-over-period growth vs. prior equivalent cycles, total revenue, distinct orders (`COUNT(DISTINCT order_id)`), total quantity, average order value, commercial profit, margin %, forecasted revenue, anomaly count, and deterministic insights.
- **Query Parameters**:
  - `period` (string, default `"all"`): `"all"`, `"today"`, `"7d"`, `"30d"`, `"this_month"`, `"last_month"`, or `"custom"`.
  - `start_date` (string, optional): Start date for custom window (`YYYY-MM-DD`).
  - `end_date` (string, optional): End date for custom window (`YYYY-MM-DD`).
  - `sku` (string, optional): Target product or SKU filter.
- **Response (`200 OK`)**:
  ```json
  {
    "revenue": 2297200.86,
    "revenue_growth": 14.2,
    "total_records": 10194,
    "total_orders": 5009,
    "total_quantity": 37873,
    "aov": 458.62,
    "total_profit": 286397.02,
    "profit_margin_pct": 12.47,
    "active_predictions": 1862,
    "anomalies_detected": 4,
    "model_accuracy": 91.2,
    "forecasted_revenue": 53600.0,
    "period": "30d",
    "date_range": { "start_date": "2026-12-01", "end_date": "2026-12-30" },
    "comparison_range": { "start_date": "2026-11-01", "end_date": "2026-11-30" },
    "insights": [
      "Recorded $2,297,200.86 in revenue across 5,009 verified orders (AOV: $458.62).",
      "Net commercial profit stands at $286,397.02 with a 12.47% operating margin.",
      "Sales increased by 14.2% compared to the prior equivalent cycle."
    ]
  }
  ```

#### `GET /api/v1/analytics/trends`
- **Purpose**: Time-series trend analysis aggregating revenue, units sold, distinct orders, and commercial profit over daily, weekly, or monthly periods with period-over-period delta %.
- **Query Parameters**:
  - `interval` (string, default `"daily"`): `"daily"`, `"weekly"`, `"monthly"`.
  - `period` (string, default `"all"`): Pre-defined or custom date range filter.
- **Response (`200 OK`)**:
  ```json
  {
    "interval": "daily",
    "series": [
      {
        "date": "2026-12-15",
        "revenue": 8420.0,
        "units_sold": 140,
        "orders": 12,
        "profit": 1240.5,
        "growth_delta_pct": 15.2
      }
    ],
    "peak_date": "2026-12-15",
    "peak_revenue": 8420.0,
    "lowest_date": "2026-12-04",
    "lowest_revenue": 890.0
  }
  ```

#### `GET /api/v1/analytics/categories`
- **Purpose**: Category and sub-category contribution analysis, distinct order counts, revenue share %, and margins.
- **Query Parameters**: `period`, `start_date`, `end_date`.
- **Response (`200 OK`)**:
  ```json
  {
    "total_store_revenue": 2297200.86,
    "best_category": "Technology",
    "lowest_category": "Furniture",
    "category_summary": [
      { "category": "Technology", "revenue": 836154.03, "units_sold": 13420, "contribution_pct": 36.4 }
    ],
    "breakdown": [
      {
        "category": "Technology",
        "sub_category": "Phones",
        "revenue": 330007.05,
        "units_sold": 3289,
        "orders": 876,
        "profit": 44515.73,
        "profit_margin_pct": 13.49,
        "contribution_pct": 14.37
      }
    ]
  }
  ```

#### `GET /api/v1/analytics/products`
- **Purpose**: Product rankings returning top-selling and lowest-selling SKUs by gross revenue and volume with contribution %.
- **Query Parameters**: `limit` (default 10), `period`, `search`.

#### `GET /api/v1/analytics/transactions`
- **Purpose**: Interactive, searchable, sortable, paginated line-item transactions explorer.
- **Query Parameters**: `page` (int, default 1), `page_size` (int, default 25), `search`, `category`, `sub_category`, `sku`, `sort_by` (`date`, `order_id`, `total_sales`, `units_sold`, `profit`), `sort_dir` (`asc`, `desc`).

#### `GET /api/v1/analytics/anomalies`
- **Purpose**: Retrieves rolling Z-score detected anomalies with severity rankings and timestamps.
- **Query Parameters**: `sku` (string, optional).
- **Response (`200 OK`)**:
  ```json
  [
    {
      "date": "2026-03-18",
      "units_sold": 450,
      "anomaly_severity": "High",
      "z_score": 3.42
    }
  ]
  ```

#### `POST /api/v1/analytics/simulate`
- **Purpose**: Evaluates what-if pricing and discount scenarios against historical demand elasticity.
- **Query Parameters**: `sku`, `price_change` (float), `discount` (float), `demand_mult` (float).
- **Response (`200 OK`)**:
  ```json
  {
    "sku": "ALL",
    "baseline_revenue": 150000.0,
    "simulated_revenue": 162500.0,
    "revenue_impact_pct": 8.33,
    "simulated_volume": 4800,
    "volume_impact_pct": -4.0
  }
  ```

#### `POST /api/v1/analytics/copilot` & `POST /api/v1/analytics/gemini`
- **Purpose**: Natural-language conversational sales intelligence grounded in live metrics. Powered by the official `google-genai` SDK with fallback to supported models (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`).
- **Request Body**: `{"query": "Why did sales drop last week?", "sku": "ALL"}`.
- **Response (`200 OK`)**:
  ```json
  {
    "answer": "Sales experienced a 14.2% drop primarily driven by Furniture inventory stockouts in the Tables sub-category.",
    "recommendation": "Review supplier lead times for Tables and adjust reorder triggers.",
    "evidence": {
      "model_used": "gemini-2.0-flash",
      "historical_revenue": 2297200.86
    }
  }
  ```

#### `GET /api/v1/analytics/inventory`
- **Purpose**: Inventory risk analysis and SKU demand velocity tracking. If the ingested dataset does not contain an on-hand stock column, `has_inventory_tracking` is set to `false` and `available_stock` is returned as `null` (zero synthetic stock fabrication).
- **Response (`200 OK`)**:
  ```json
  [
    {
      "sku": "TEC-PH-10004977",
      "has_inventory_tracking": false,
      "available_stock": null,
      "daily_velocity": 4.2,
      "days_of_supply": null,
      "forecast_7d_demand": 29.4,
      "reorder_suggested": null,
      "health_status": "DEMAND_ONLY",
      "stockout_risk": "Inventory stock omitted in dataset"
    }
  ]
  ```

#### `GET /api/v1/analytics/model-health`
- **Purpose**: Returns model validation statistics, out-of-sample error telemetry, and dynamic drift calculation across sequential model runs without placeholder mock values.
- **Response (`200 OK`)**:
  ```json
  {
    "active_model": "Hybrid (Seasonal Naive + Auto-ARIMA)",
    "model_status": "HEALTHY",
    "total_observations": 10194,
    "avg_wape": 5.8,
    "avg_mae": 12.4,
    "avg_rmse": 16.2,
    "drift_status": "Stable (Low Drift)",
    "drift_score": 0.038,
    "validation_strategy": "Walk-Forward Rolling Cross-Validation",
    "last_trained_runs": [ ... ]
  }
  ```

---

### 2.2 Machine Learning & Forecasting Router (`/api/v1/ml`)
Implemented in [`backend/app/api/v1/endpoints/ml.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/ml.py).

#### `POST /api/v1/ml/analyze`
- **Purpose**: Core empirical ledger analysis and forward walk-forward ML projection engine powering Forecast Lab.
- **Frontend Caller**: [`frontend/app/forecast/page.tsx`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/frontend/app/forecast/page.tsx).
- **Request Body**:
  ```json
  {
    "target_name": "ALL",
    "mode": "range",
    "selected_date": "2026-12-30",
    "start_date": "2026-11-30",
    "end_date": "2026-12-30",
    "model_preference": "auto"
  }
  ```
- **Response Schema (`200 OK`)**:
  ```json
  {
    "summary": {
      "target_name": "All Products (Global Aggregate)",
      "sku": "ALL",
      "mode": "Date Range: 2026-11-30 to 2026-12-30",
      "selected_date": null,
      "start_date": "2026-11-30",
      "end_date": "2026-12-30",
      "data_points_analyzed": 31,
      "status": "HISTORICAL ACTUALS",
      "is_forecast": false,
      "model_used": "Empirical Ledger",
      "generated_at": "2026-10-22T20:30:00Z",
      "dataset_coverage": {
        "min_date": "2023-01-03",
        "max_date": "2026-12-30"
      }
    },
    "sales_performance": {
      "total_revenue": 94520.12,
      "total_units": 1580,
      "avg_daily_sales": 3049.04,
      "avg_unit_price": 59.82,
      "highest_sales_date": { "date": "2026-12-15", "units": 140, "revenue": 8420.0 },
      "lowest_sales_date": { "date": "2026-12-04", "units": 15, "revenue": 890.0 },
      "growth_vs_prior_period_pct": 5.4,
      "prior_period_revenue": 89680.0
    },
    "forecast_results": {
      "is_applicable": false,
      "model_name": "Empirical Ledger",
      "predicted_units": null,
      "predicted_revenue": null,
      "lower_bound": null,
      "upper_bound": null,
      "evaluation_metrics": {
        "mae": null,
        "rmse": null,
        "wape": null
      },
      "explanation": "Target horizon lies within historical dataset coverage; actual verified sales are displayed.",
      "limitations": "Forward machine learning projection is applied when targeting future dates."
    },
    "chart_data": [
      {
        "date": "2026-12-01",
        "full_date": "2026-12-01",
        "actual": 3200.0,
        "forecast": null,
        "lower": null,
        "upper": null
      }
    ],
    "insights": [
      {
        "type": "peak",
        "title": "Peak Demand Period",
        "description": "Highest daily revenue observed on 2026-12-15 with $8,420.00 across 140 units."
      }
    ]
  }
  ```

#### `POST /api/v1/ml/train`
- **Purpose**: Trains candidate models (Seasonal Naive vs. ARIMA) on an SKU, runs walk-forward rolling evaluation, and records the champion model.
- **Query Parameters**: `sku` (string, default `"ALL"`), `forecast_days` (int, default 7).
- **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "best_model_selected": "arima",
    "metrics": { "mae": 12.4, "rmse": 18.2, "wape": 0.088 },
    "future_predictions": [140.2, 138.5, 142.1, 145.0, 150.2, 148.0, 152.1]
  }
  ```

#### `GET /api/v1/ml/history`
- **Purpose**: Retrieves prediction audit logs containing persisted model runs, evaluation metrics (MAE, RMSE, WAPE), future forecast dates, and actual vs. predicted ground-truth reconciliation with variance calculation.
- **Query Parameters**: `limit` (int, default 50), `sku` (string, optional).
- **Response (`200 OK`)**:
  ```json
  {
    "total_runs": 8,
    "runs": [
      {
        "run_id": "c8f309a1-...",
        "created_at": "2026-10-22T21:40:00Z",
        "sku": "Global",
        "model_version": "ARIMA",
        "status": "SUCCESS",
        "metrics": { "mae": 12.4, "rmse": 16.2, "wape": 5.8 },
        "predictions_count": 7,
        "predictions": [
          {
            "forecast_date": "2026-12-31",
            "predicted_demand": 140,
            "actual_demand": 138,
            "variance": 2,
            "status": "Verified Actual"
          }
        ]
      }
    ]
  }
  ```

---

### 2.3 Data Ingestion Router (`/api/v1/data`)
Implemented in [`backend/app/api/v1/endpoints/data.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/data.py).

#### `POST /api/v1/data/upload`
- **Purpose**: Uploads and ingests a transactional CSV dataset.
- **Parameters**: `file` (multipart/form-data), `replace` (boolean query parameter, default `true`).
- **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "records_processed": 10194,
    "replaced": true
  }
  ```

#### `GET /api/v1/data/preview`
- **Purpose**: Comprehensive dataset inspection telemetry returning filename, row count, column count, schema data types, calendar date coverage, unique SKU and category counts, missing-value audit, and sample 10 parsed rows.
- **Query Parameters**: `limit` (int, default 10).
- **Response (`200 OK`)**:
  ```json
  {
    "has_data": true,
    "filename": "samplesuperstore.csv",
    "row_count": 10194,
    "column_count": 12,
    "columns": [
      { "name": "date", "type": "Date", "nullable": false },
      { "name": "order_id", "type": "String", "nullable": true },
      { "name": "sku", "type": "String", "nullable": false },
      { "name": "product_name", "type": "String", "nullable": true },
      { "name": "category", "type": "String", "nullable": true },
      { "name": "sub_category", "type": "String", "nullable": true },
      { "name": "units_sold", "type": "Integer", "nullable": false },
      { "name": "total_sales", "type": "Numeric(12,2)", "nullable": true },
      { "name": "profit", "type": "Numeric(12,2)", "nullable": true }
    ],
    "date_coverage": { "min_date": "2023-01-03", "max_date": "2026-12-30", "span_days": 1458 },
    "product_count": 1862,
    "category_count": 3,
    "missing_values": { "order_id": 0, "profit": 0, "category": 0 },
    "sample_rows": [ ... ]
  }
  ```

#### `GET /api/v1/data/products` & `GET /api/v1/data/skus`
- **Purpose**: Retrieves all unique products and SKUs in the dataset with record counts, date ranges, and disambiguated display labels.
- **Query Parameters**: `search` (string, optional), `limit` (int, default 200).
- **Response (`200 OK`)**:
  ```json
  [
    {
      "sku": "ALL",
      "product_name": "All Products (Global Aggregate)",
      "label": "All Products (Global Aggregate) — 10194 records",
      "count": 10194,
      "min_date": "2023-01-03",
      "max_date": "2026-12-30"
    },
    {
      "sku": "FUR-CH-10000454",
      "product_name": "Mitel 5320 IP Phone",
      "label": "Mitel 5320 IP Phone [SKU: FUR-CH-10000454] (32 records)",
      "count": 32,
      "min_date": "2023-02-14",
      "max_date": "2026-11-20"
    }
  ]
  ```

#### `POST /api/v1/data/clean-duplicates`
- **Purpose**: Scans and removes duplicate rows from repeated uploads while strictly preserving distinct orders.
- **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "records_before": 10194,
    "records_removed": 0,
    "total_records": 10194
  }
  ```

#### `POST /api/v1/data/reset`
- **Purpose**: Wipes all raw sales records, model runs, and forecasts to return to a clean initial state.
- **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "records_cleared": 10194
  }
  ```

---

### 2.4 Authentication Router (`/api/v1/auth`)
Implemented in [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/api/v1/endpoints/auth.py).

#### `POST /api/v1/auth/register`
- **Request Body**: `{"email": "analyst@example.com", "password": "Password123!", "role": "ANALYST"}`.
- **Response (`200 OK`)**: `{"id": "...", "email": "analyst@example.com", "role": "ANALYST", "is_active": true}`.

#### `POST /api/v1/auth/login`
- **Request Body**: OAuth2 form data or JSON with `username` (email) and `password`.
- **Response (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

#### `GET /api/v1/auth/me`
- **Headers**: `Authorization: Bearer <token>`.
- **Response (`200 OK`)**: Current user profile object.

---

### 2.5 System Root & Health Check
Implemented in [`backend/app/main.py`](file:///c:/Users/EMAAN/OneDrive/Documents/GitHub/sales-prediction-dashboards/backend/app/main.py).

#### `GET /health`
- **Response (`200 OK`)**: `{"status": "ok"}`.

#### `GET /`
- **Response (`200 OK`)**: `{"message": "Welcome to AI-Powered Sales Intelligence Platform API"}`.

---

### 2.6 Universal Data Cleaning & Preprocessing Router (`/api/v1/cleaning`)
Implemented in [`backend/app/api/v1/endpoints/cleaning.py`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/backend/app/api/v1/endpoints/cleaning.py).

#### `POST /api/v1/cleaning/upload`
- **Purpose**: Uploads and preserves original raw files (CSV, TSV, XLSX, Parquet, JSON, Media) with SHA-256 checksums in tenant-isolated vaults.
- **Form Data**: `file` (UploadFile), `dataset_name` (string, optional).
- **Response (`200 OK`)**: `CleaningUploadResponse` with `dataset_id`, `checksum_sha256`, dimensions, and initial profiling.

#### `GET /api/v1/cleaning/datasets`
- **Purpose**: Lists registered dataset versions for the active workspace with metadata, status, and dimensions.

#### `GET /api/v1/cleaning/datasets/{id}/download-original`
- **Purpose**: Streams the original unmodified file backup directly from tenant storage.

#### `POST /api/v1/cleaning/datasets/{id}/clean`
- **Purpose**: Executes the universal 20-step cleaning pipeline (deduplication, imputation, bound capping, date normalization, schema casting, quality scorecard).
- **Request Body**: `{"pipeline_config": {"imputation_strategy": "mean", "outlier_strategy": "iqr", "deduplication_strict": true}}`.
- **Response (`200 OK`)**: `{"status": "success", "job_id": "...", "result": {...}}`.

#### `GET /api/v1/cleaning/datasets/{id}/preview`
- **Purpose**: Returns side-by-side preview rows of raw vs. cleaned dataset for verification.

#### `GET /api/v1/cleaning/datasets/{id}/export?format={csv|tsv|xlsx|parquet|json|jsonl}`
- **Purpose**: Streams genuine converted tabular files in the user's requested format with auto-styled Excel formatting and Parquet compression.

#### `GET /api/v1/cleaning/jobs/{id}/report?format={pdf|xlsx|json}`
- **Purpose**: Downloads comprehensive cleaning & quality audit reports (Executive PDF, Multi-sheet Excel workbook, or JSON audit log).

#### `POST /api/v1/cleaning/datasets/{id}/activate`
- **Purpose**: Promotes verified cleaned dataset into `raw_sales_data`, reconciling transactions into the live sales ledger for downstream analytics and ML models.

---

### 2.7 Knowledge Assistant & RAG Router (`/api/v1/rag`)
Implemented in [`backend/app/api/v1/endpoints/rag.py`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/backend/app/api/v1/endpoints/rag.py).

#### `POST /api/v1/rag/documents`
- **Purpose**: Multi-format document ingestion (PDF, DOCX, TXT, MD, CSV, TSV, JSON) into tenant-isolated Knowledge Vault with structure-aware chunking and 768-dim vector embeddings.
- **Form Data**: `file` (UploadFile), `title` (string, optional), `category` (string, optional).
- **Headers**: `Authorization: Bearer <token>`, `X-Organization-ID: <tenant_id>`.
- **Response (`201 Created`)**:
  ```json
  {
    "document_id": "67b864a7-8f52-474c-81bc-569d6c97a5b1",
    "filename": "Q3_Enterprise_Sales_Playbook.pdf",
    "title": "Q3 Enterprise Sales Playbook",
    "file_type": "pdf",
    "total_chunks": 14,
    "status": "ready"
  }
  ```

#### `GET /api/v1/rag/documents`
- **Purpose**: Retrieves all ingested documents within the authenticated tenant workspace.
- **Response (`200 OK`)**: List of `RagDocumentResponse` items with status, chunk counts, and timestamps.

#### `GET /api/v1/rag/documents/{document_id}`
- **Purpose**: Fetches document detail including its indexed chunks, structural sections, and token counts.
- **Response (`200 OK`)**: `RagDocumentDetailResponse` containing metadata and ordered chunks.

#### `DELETE /api/v1/rag/documents/{document_id}`
- **Purpose**: Removes a document and all related chunks from ACID database storage and prunes vectors from the on-disk FAISS index.
- **Response (`200 OK`)**: `{"status": "deleted", "document_id": "..."}`.

#### `POST /api/v1/rag/documents/{document_id}/reindex`
- **Purpose**: Re-parses original file, recalculates chunk boundaries, regenerates vector embeddings, and synchronizes the tenant vector index.
- **Response (`200 OK`)**: Updated `RagDocumentResponse`.

#### `POST /api/v1/rag/chat`
- **Purpose**: Dual-engine hybrid RAG query. Analyzes question intent (`KNOWLEDGE`, `LEDGER_ANALYTICS`, or `HYBRID`), retrieves semantic document passages, executes exact SQL ledger queries where applicable, and produces grounded responses with structured citations and honesty abstention.
- **Request Body**:
  ```json
  {
    "query": "What are our high-margin discount guidelines?",
    "top_k": 4,
    "threshold": 0.35,
    "conversation_id": "conv-1234"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "answer": "According to the Sales Playbook, discounts exceeding 15% require VP approval...",
    "intent": "KNOWLEDGE",
    "citations": [
      {
        "document_id": "67b864a7-8f52-474c-81bc-569d6c97a5b1",
        "title": "Q3 Enterprise Sales Playbook",
        "filename": "Q3_Enterprise_Sales_Playbook.pdf",
        "section": "Discounting & Margin Governance",
        "page_number": 3,
        "score": 0.884,
        "snippet": "Discounts above 15% strictly mandate VP approval..."
      }
    ],
    "model": "gemini-1.5-pro",
    "latency_ms": 342.1
  }
  ```

#### `GET /api/v1/rag/health`
- **Purpose**: Reports RAG subsystem health, vector store index engine (`faiss` or `numpy`), active tenant vector count, and Gemini API readiness.
- **Response (`200 OK`)**:
  ```json
  {
    "status": "healthy",
    "vector_store": "faiss",
    "total_vectors": 14,
    "gemini_api_configured": true,
    "active_tenant_id": "org_default"
  }
  ```

#### `POST /api/v1/rag/seed-sample-knowledge`
- **Purpose**: Idempotently seeds default enterprise corporate knowledge documents (Sales Playbook, Return/Restocking Fee Policies, and Product Catalog Specifications) into the active tenant workspace.
- **Headers**: `Authorization: Bearer <token>`, `X-Organization-ID: <tenant_id>`.
- **Response (`200 OK`)**: `RagDocumentListResponse` with seeded documents and total counts.

---

### 2.8 Multi-Tenant Organizations Router (`/api/v1/organizations`)
Implemented in [`backend/app/api/v1/endpoints/organizations.py`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/backend/app/api/v1/endpoints/organizations.py).

#### `GET /api/v1/organizations/me`
- **Purpose**: Returns all organization workspaces where the authenticated user has verified membership, along with active workspace indicator.
- **Response (`200 OK`)**: List of organization summaries with `id`, `name`, `role`, and `subscription_tier`.

#### `POST /api/v1/organizations`
- **Purpose**: Creates a new isolated customer organization workspace and sets the calling user as `OWNER`.
- **Request Body**: `{"name": "Acme Retail Corp", "subdomain": "acme"}`.
- **Response (`201 Created`)**: Created organization entity.

#### `GET /api/v1/organizations/{id}/members`
- **Purpose**: Lists all members of the specified organization workspace with their respective roles (`OWNER`, `ADMIN`, `ANALYST`, `VIEWER`).
- **Response (`200 OK`)**: List of member profiles.

#### `POST /api/v1/organizations/{id}/invitations`
- **Purpose**: Creates an email invitation token to onboard new team members to a workspace.
- **Request Body**: `{"email": "colleague@acme.com", "role": "ANALYST"}`.
- **Response (`201 Created`)**: Invitation record with token hash and expiration.

#### `POST /api/v1/organizations/invitations/{token}/accept`
- **Purpose**: Validates token hash and links the accepting user to the workspace with the designated role.
- **Response (`200 OK`)**: `{"status": "accepted", "organization_id": "..."}`.

---

### 2.9 Subscription & Billing Router (`/api/v1/billing`)
Implemented in [`backend/app/api/v1/endpoints/billing.py`](file:///c:/Users/EMAAN/AI-Powered%20Sales%20Intelligence%20%26%20Forecasting%20Platform/backend/app/api/v1/endpoints/billing.py).

#### `GET /api/v1/billing/subscription`
- **Purpose**: Retrieves current tenant subscription plan, status, feature limits, and quota consumption.
- **Response (`200 OK`)**:
  ```json
  {
    "tier": "PROFESSIONAL",
    "status": "ACTIVE",
    "quotas": {
      "max_rows": 500000,
      "max_storage_mb": 1024,
      "monthly_llm_queries": 5000
    },
    "current_usage": {
      "rows_ingested": 10194,
      "storage_mb": 42.5,
      "llm_queries": 128
    }
  }
  ```

#### `POST /api/v1/billing/create-checkout-session`
- **Purpose**: Creates a Stripe Checkout Session URL for upgrading subscription tier (`STARTER`, `PROFESSIONAL`, `ENTERPRISE`).
- **Request Body**: `{"tier": "PROFESSIONAL", "interval": "monthly"}`.
- **Response (`200 OK`)**: `{"checkout_url": "https://checkout.stripe.com/..."}`.

#### `POST /api/v1/billing/customer-portal`
- **Purpose**: Generates a Stripe Customer Portal session URL for managing payment methods and viewing invoices.
- **Response (`200 OK`)**: `{"portal_url": "https://billing.stripe.com/..."}`.

#### `POST /api/v1/billing/webhook`
- **Purpose**: Handles asynchronous Stripe webhook notifications (`checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`).
- **Headers**: `Stripe-Signature: t=...,v1=...`.
- **Response (`200 OK`)**: `{"received": true}`.

---

**End of API Specification & Reference**
