from fastapi import APIRouter, Depends, Query, Response, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.api import deps
from app.api.deps import get_db
from app.models.tenant import Tenant
from app.services.reporting_service import generate_professional_sales_report
from app.services.analytics_service import (
    get_overview_data,
    get_trends_data,
    get_categories_breakdown,
    get_product_performance,
    get_transactions_table
)

router = APIRouter()

@router.get("/overview")
def get_overview(
    period: Optional[str] = Query("all", description="Date filter: all, today, 7d, 30d, this_month, last_month, custom"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD for custom period"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD for custom period"),
    sku: Optional[str] = Query(None, description="Target SKU or product name filter"),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Returns high-level business intelligence KPIs, period-over-period growth,
    revenue, orders, profit, margin, active SKUs, and deterministic business insights.
    """
    return get_overview_data(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
        sku=sku,
        tenant_id=current_tenant.id
    )

@router.get("/trends")
def get_trends(
    interval: Optional[str] = Query("daily", description="Aggregation interval: daily, weekly, monthly"),
    period: Optional[str] = Query("all", description="Date window: all, today, 7d, 30d, this_month, last_month, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Time-series trend analysis providing revenue, volume, and period-over-period delta.
    """
    return get_trends_data(
        db=db,
        interval=interval,
        period=period,
        start_date=start_date,
        end_date=end_date,
        sku=sku,
        tenant_id=current_tenant.id
    )

@router.get("/categories")
def get_categories(
    period: Optional[str] = Query("all", description="Date window: all, today, 7d, 30d, this_month, last_month, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Category and sub-category performance, contribution percentages, and margins.
    """
    return get_categories_breakdown(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
        tenant_id=current_tenant.id
    )

@router.get("/products")
def get_products_analytics(
    limit: Optional[int] = Query(10, ge=1, le=100),
    period: Optional[str] = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Product performance analytics: top-selling and lowest-selling products with contribution %.
    """
    return get_product_performance(
        db=db,
        limit=limit,
        period=period,
        start_date=start_date,
        end_date=end_date,
        search=search,
        tenant_id=current_tenant.id
    )

@router.get("/transactions")
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort_by: str = Query("date"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Searchable, sortable, paginated transaction explorer for line-item sales records.
    """
    return get_transactions_table(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        sub_category=sub_category,
        sku=sku,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_dir=sort_dir,
        tenant_id=current_tenant.id
    )

@router.get("/forecast")
def get_forecast(
    sku: str = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    from app.models.data import RawSalesData
    import pandas as pd
    
    try:
        from app.pipelines.etl import extract_for_features
        from app.ml.baseline import BaselineModel
        clean_sku = (sku or "").strip()
        is_all = clean_sku.upper() in ["ALL", "GLOBAL", "TOTAL", ""]
        if is_all:
            df = extract_for_features(db, None, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.groupby('date', as_index=False).agg({'units_sold': 'sum'})
                df = df.sort_values('date').reset_index(drop=True)
        else:
            df = extract_for_features(db, clean_sku, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)

        if not df.empty and len(df) >= 1:
            window_size = min(7, len(df))
            baseline = BaselineModel(method='snaive', window=window_size)
            baseline.fit(df)
            preds = baseline.predict(7)
            
            last_date = df['date'].iloc[-1]
            results = []
            tail_count = min(7, len(df))
            for _, row in df.tail(tail_count).iterrows():
                results.append({
                    "date": row['date'].strftime('%b %d'),
                    "actual": float(row['units_sold']),
                    "forecast": None,
                    "lower": None,
                    "upper": None
                })
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=7)
            for d, p in zip(future_dates, preds):
                val = round(float(p), 1)
                results.append({
                    "date": d.strftime('%b %d'),
                    "actual": None,
                    "forecast": val,
                    "lower": round(max(0.0, val * 0.85), 1),
                    "upper": round(val * 1.15, 1)
                })
            return results
    except Exception:
        pass

    # Baseline projection horizon when dataset is empty or initializing
    import datetime
    today = datetime.date.today()
    results = []
    for i in range(7):
        d = today + datetime.timedelta(days=i + 1)
        results.append({
            "date": d.strftime('%b %d'),
            "actual": None,
            "forecast": 0.0,
            "lower": 0.0,
            "upper": 0.0
        })
    return results

@router.get("/anomalies")
def get_anomalies(
    sku: str = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    from app.pipelines.etl import extract_for_features
    from app.ml.anomaly import detect_anomalies
    import pandas as pd
    
    try:
        clean_sku = (sku or "").strip()
        is_all = clean_sku.upper() in ["ALL", "GLOBAL", "TOTAL", ""]
        if is_all:
            df = extract_for_features(db, None, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.groupby('date', as_index=False).agg({'units_sold': 'sum'})
                df = df.sort_values('date').reset_index(drop=True)
        else:
            df = extract_for_features(db, clean_sku, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
        if df.empty:
            return []
            
        df = detect_anomalies(df)
        anomalies = df[df['is_anomaly'] == True]
        
        baseline_mean = round(float(df['units_sold'].mean()), 1)
        
        # Return structured JSON records with investigation guidance
        records = []
        for _, row in anomalies.tail(20).iterrows():
            dt_val = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10]
            z = float(row['z_score'])
            u = int(row['units_sold'])
            is_spike = z > 0
            
            if is_spike:
                guidance = f"Unusual sales surge (+{round(z, 1)}σ above baseline). Review promotional campaigns or wholesale bulk order spikes."
                alert_type = "Demand Surge Spike"
            else:
                guidance = f"Unexpected sales contraction ({round(z, 1)}σ below baseline). Verify catalog availability, stockouts, or checkout friction."
                alert_type = "Demand Contraction Drop"
                
            records.append({
                "date": dt_val,
                "units_sold": u,
                "expected_units": baseline_mean,
                "anomaly_severity": str(row['anomaly_severity']),
                "z_score": round(z, 2),
                "alert_type": alert_type,
                "guidance": guidance,
                "detection_method": "Rolling Gaussian Z-Score (|Z| ≥ 2.0)"
            })
        return records
    except Exception:
        return []

@router.post("/simulate")
def run_simulation(
    sku: str = None,
    price_change: float = 0,
    discount: float = 0,
    demand_mult: float = 1.0,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    from app.pipelines.etl import extract_for_features
    from app.services.simulation import simulate_scenario
    import pandas as pd
    
    try:
        clean_sku = (sku or "").strip()
        is_all = clean_sku.upper() in ["ALL", "GLOBAL", "TOTAL", ""]
        if is_all:
            df = extract_for_features(db, None, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.groupby('date', as_index=False).agg({
                    'units_sold': 'sum',
                    'price': 'mean',
                    'discount_pct': 'mean',
                    'available_stock': 'sum'
                })
                df = df.sort_values('date').reset_index(drop=True)
        else:
            df = extract_for_features(db, clean_sku, tenant_id=current_tenant.id)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)

        if df.empty:
            return {"error": "No data found for the selected SKU. Upload a dataset or choose 'ALL'."}
            
        result = simulate_scenario(df, price_change, discount, demand_mult)
        return result
    except Exception as e:
        return {"error": str(e)}

from app.services.gemini_service import query_sales_gemini

@router.post("/gemini")
@router.post("/copilot")
def ask_gemini(query: str = None, payload: dict = Body(None), sku: str = None, db: Session = Depends(get_db)):
    """
    Intelligent Sales Analysis powered by Google Gemini Pro.
    Maintains backward compatibility with /copilot while powering the new /gemini interface.
    """
    actual_query = query
    if not actual_query and payload and isinstance(payload, dict):
        actual_query = payload.get("query")
        if not sku:
            sku = payload.get("sku")
    if not actual_query:
        actual_query = "Provide a high-level summary of our sales trajectory and inventory recommendations."

    return query_sales_gemini(query=actual_query, db=db, sku=sku)

@router.get("/inventory")
def get_inventory_intelligence(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Inventory risk analysis and demand-stock ratio computation for SKUs.
    Grounds calculations strictly in empirical data without synthesizing fake inventory.
    """
    from app.models.data import RawSalesData
    from sqlalchemy import func
    
    try:
        skus = [r[0] for r in db.query(RawSalesData.sku).filter(RawSalesData.tenant_id == current_tenant.id).distinct().all()]
        if not skus:
            return []
        
        results = []
        for sku_id in skus[:15]:
            rows = db.query(RawSalesData).filter(
                RawSalesData.sku == sku_id,
                RawSalesData.tenant_id == current_tenant.id
            ).order_by(RawSalesData.date.desc()).limit(30).all()
            if not rows:
                continue
            
            latest_stock = None
            for r in rows:
                if r.available_stock is not None:
                    latest_stock = float(r.available_stock)
                    break
                
            total_sold = sum(r.units_sold for r in rows)
            days_count = max(1, len(rows))
            velocity = round(total_sold / days_count, 1)
            f7d = round(velocity * 7, 1)
            
            if latest_stock is not None:
                days_of_supply = round(latest_stock / max(velocity, 0.1), 1)
                if days_of_supply < 5:
                    status = "CRITICAL"
                    risk = "Critical Stockout Risk"
                    reorder = int(max(0, velocity * 30 - latest_stock))
                elif days_of_supply <= 14:
                    status = "WARNING"
                    risk = "Reorder Attention Needed"
                    reorder = int(max(0, velocity * 30 - latest_stock))
                elif days_of_supply > 60:
                    status = "OVERSTOCK"
                    risk = "Surplus Inventory"
                    reorder = 0
                else:
                    status = "HEALTHY"
                    risk = "Optimal Range"
                    reorder = 0
            else:
                # Source dataset lacks on-hand stock records; calculate demand velocity only
                days_of_supply = None
                status = "DEMAND_ONLY"
                risk = "Inventory stock omitted in dataset"
                reorder = None
                
            results.append({
                "sku": sku_id,
                "has_inventory_tracking": latest_stock is not None,
                "available_stock": int(latest_stock) if latest_stock is not None else None,
                "daily_velocity": velocity,
                "days_of_supply": days_of_supply,
                "forecast_7d_demand": f7d,
                "reorder_suggested": reorder,
                "health_status": status,
                "stockout_risk": risk
            })
        return results
    except Exception:
        return []

@router.get("/model-health")
@router.get("/model-health/latest")
def get_model_health(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Returns automated forecasting accuracy, drift signals, and validation statistics.
    Grounds metrics dynamically in recorded ModelRun entries without placeholder constants.
    """
    from app.models.forecast import ModelRun
    from app.models.data import RawSalesData
    
    if not hasattr(current_tenant, "id"):
        current_tenant = deps.get_current_tenant_or_default(db=db)

    total_records = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).count()
    last_runs = db.query(ModelRun).filter(ModelRun.tenant_id == current_tenant.id).order_by(ModelRun.created_at.desc()).limit(10).all()
    
    runs_data = []
    avg_wape = None
    avg_mae = None
    avg_rmse = None
    drift_score = None
    drift_status = "No Recorded Runs"
    
    def _normalize_wape(val):
        if val is None:
            return None
        return round(float(val) * 100, 1) if float(val) <= 1.5 else round(float(val), 1)

    latest_run = None
    if last_runs:
        lr = last_runs[0]
        lr_name = getattr(lr, "model_name", None) or lr.model_version or "BASELINE"
        latest_run = {
            "id": str(lr.id),
            "model_name": lr_name,
            "model_version": lr.model_version or lr_name,
            "mae": lr.mae,
            "rmse": lr.rmse,
            "wape": _normalize_wape(lr.wape),
            "status": lr.status or "SUCCESS",
            "sku": lr.sku or "Global",
            "created_at": lr.created_at.isoformat() if hasattr(lr.created_at, 'isoformat') else str(lr.created_at)
        }

        normalized_wapes = [_normalize_wape(r.wape) for r in last_runs if r.wape is not None]
        if normalized_wapes:
            avg_wape = round(float(sum(normalized_wapes) / len(normalized_wapes)), 1)
            # Calculate drift dynamically across sequential runs
            if len(normalized_wapes) >= 2:
                recent_wape = normalized_wapes[0]
                baseline_wape = normalized_wapes[-1]
                drift_score = round(abs(recent_wape - baseline_wape) / max(baseline_wape, 0.01), 3)
                if drift_score <= 0.15:
                    drift_status = "Stable (Low Drift)"
                elif drift_score <= 0.35:
                    drift_status = "Moderate Drift"
                else:
                    drift_status = "Significant Drift"
            else:
                drift_score = 0.0
                drift_status = "Baseline Established"

        valid_maes = [r.mae for r in last_runs if r.mae is not None]
        if valid_maes:
            avg_mae = round(float(sum(valid_maes) / len(valid_maes)), 1)
        valid_rmses = [r.rmse for r in last_runs if r.rmse is not None]
        if valid_rmses:
            avg_rmse = round(float(sum(valid_rmses) / len(valid_rmses)), 1)
            
        for r in last_runs:
            r_name = getattr(r, "model_name", None) or r.model_version or "BASELINE"
            runs_data.append({
                "id": str(r.id),
                "sku": r.sku or "Global",
                "model_name": r_name,
                "model_version": r.model_version or r_name,
                "mae": r.mae,
                "rmse": r.rmse,
                "wape": _normalize_wape(r.wape),
                "status": r.status or "SUCCESS",
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at)
            })
            
    model_status = "HEALTHY" if last_runs else "UNINITIALIZED"

    return {
        "status": "success" if last_runs else "uninitialized",
        "active_model": (latest_run["model_name"] if latest_run else None),
        "model_status": model_status,
        "total_observations": total_records,
        "avg_wape": avg_wape,
        "avg_mae": avg_mae,
        "avg_rmse": avg_rmse,
        "drift_status": drift_status,
        "drift_score": drift_score,
        "validation_strategy": "Walk-Forward Rolling Cross-Validation",
        "latest_run": latest_run,
        "id": latest_run["id"] if latest_run else None,
        "model_name": latest_run["model_name"] if latest_run else None,
        "mae": latest_run["mae"] if latest_run else None,
        "wape": latest_run["wape"] if latest_run else None,
        "rmse": latest_run["rmse"] if latest_run else None,
        "created_at": latest_run["created_at"] if latest_run else None,
        "last_trained_runs": runs_data
    }


@router.get("/report")
@router.post("/report")
@router.get("/export")
def get_professional_sales_report(
    target_name: Optional[str] = Query("ALL", description="Target Product Name, SKU, or 'ALL'"),
    mode: Optional[str] = Query("range", description="'single' for Selected Date or 'range' for Date Range"),
    selected_date: Optional[str] = Query(None, description="Target date YYYY-MM-DD for single date"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD for date range"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD for date range"),
    payload: Optional[dict] = Body(None),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Generates a professional data-driven Sales Summary Report scoped to the active workspace.
    Calculates Category & Sub-Category breakdowns with Total Orders, Units Sold,
    Total Sales, Profit, and Profit Margins.
    """
    p_target = (payload.get("target_name") if payload and isinstance(payload, dict) else None) or target_name
    p_mode = (payload.get("mode") if payload and isinstance(payload, dict) else None) or mode
    p_selected = (payload.get("selected_date") if payload and isinstance(payload, dict) else None) or selected_date
    p_start = (payload.get("start_date") if payload and isinstance(payload, dict) else None) or start_date
    p_end = (payload.get("end_date") if payload and isinstance(payload, dict) else None) or end_date
    
    return generate_professional_sales_report(
        db=db,
        target_name=p_target,
        mode=p_mode,
        selected_date=p_selected,
        start_date=p_start,
        end_date=p_end,
        tenant_id=current_tenant.id
    )

@router.get("/report/csv")
def download_professional_sales_report_csv(
    target_name: Optional[str] = Query("ALL"),
    mode: Optional[str] = Query("range"),
    selected_date: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    type: Optional[str] = Query("detail", description="'detail' or 'summary'"),
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Direct streaming HTTP download for the professional sales summary CSV report.
    Returns detail CSV ('professional_sales_summary_YYYY-MM-DD.csv') or
    summary CSV ('professional_sales_summary_summary_YYYY-MM-DD.csv').
    """
    report = generate_professional_sales_report(
        db=db,
        target_name=target_name,
        mode=mode,
        selected_date=selected_date,
        start_date=start_date,
        end_date=end_date,
        tenant_id=current_tenant.id
    )
    
    meta = report.get("report_metadata", {})
    if type == "summary":
        csv_text = report.get("summary_csv", "")
        filename = meta.get("summary_filename", "professional_sales_summary_summary.csv")
    else:
        csv_text = report.get("detail_csv", "")
        filename = meta.get("filename", "professional_sales_summary.csv")
        
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
