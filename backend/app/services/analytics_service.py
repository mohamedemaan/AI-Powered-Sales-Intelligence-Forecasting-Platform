import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc, literal

from app.models.data import RawSalesData
from app.models.forecast import ModelRun

logger = logging.getLogger(__name__)

def parse_date_safe(val: Any) -> Optional[date]:
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        s = str(val).strip()[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        import pandas as pd
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None

def format_date_safe(val: Any) -> Optional[str]:
    if not val:
        return None
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s

def normalize_wape(val: Optional[float]) -> Optional[float]:
    """
    Normalizes WAPE to a percentage between 0.0% and 100.0%.
    Handles both unit fractions (e.g. 0.452 -> 45.2%) and percentage values (e.g. 45.2 -> 45.2%),
    as well as accidental double-scaled values (e.g. 4520 -> 45.2%).
    """
    if val is None:
        return None
    try:
        f_val = float(val)
        if f_val <= 1.5:
            pct = f_val * 100.0
        else:
            pct = f_val
        while pct > 100.0 and pct <= 10000.0:
            pct = pct / 100.0
        return round(max(0.0, min(100.0, pct)), 1)
    except (ValueError, TypeError):
        return None

def get_period_dates(db: Session, period: str = "all", start_date: Optional[str] = None, end_date: Optional[str] = None, tenant_id: Optional[Any] = None):
    """
    Determines the current date window and prior equivalent window based on temporal grounding.
    Uses the latest historical transaction date in the ledger as 'today'.
    """
    query = db.query(func.min(RawSalesData.date), func.max(RawSalesData.date))
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    min_date, max_date = query.first()

    if not max_date or not min_date:
        return None, None, None, None

    if isinstance(min_date, str):
        min_date = parse_date_safe(min_date)
    if isinstance(max_date, str):
        max_date = parse_date_safe(max_date)

    clean_period = (period or "all").lower().strip()
    
    if clean_period == "today":
        curr_start = max_date
        curr_end = max_date
        prior_start = max_date - timedelta(days=1)
        prior_end = max_date - timedelta(days=1)
    elif clean_period == "7d":
        curr_start = max_date - timedelta(days=6)
        curr_end = max_date
        prior_end = curr_start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=6)
    elif clean_period == "30d":
        curr_start = max_date - timedelta(days=29)
        curr_end = max_date
        prior_end = curr_start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=29)
    elif clean_period == "this_month":
        curr_start = max_date.replace(day=1)
        curr_end = max_date
        # Prior month equivalent
        first_of_curr = curr_start
        prior_end = first_of_curr - timedelta(days=1)
        prior_start = prior_end.replace(day=1)
    elif clean_period == "last_month":
        first_of_curr = max_date.replace(day=1)
        curr_end = first_of_curr - timedelta(days=1)
        curr_start = curr_end.replace(day=1)
        prior_end = curr_start - timedelta(days=1)
        prior_start = prior_end.replace(day=1)
    elif clean_period == "custom" and start_date and end_date:
        curr_start = parse_date_safe(start_date) or min_date
        curr_end = parse_date_safe(end_date) or max_date
        if curr_start and curr_end and curr_start > curr_end:
            curr_start, curr_end = curr_end, curr_start
        duration_days = max(1, (curr_end - curr_start).days + 1)
        prior_end = curr_start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=duration_days - 1)
    else: # "all"
        curr_start = min_date
        curr_end = max_date
        prior_start = None
        prior_end = None

    return curr_start, curr_end, prior_start, prior_end

def calculate_kpis_for_window(db: Session, start_dt: Optional[date], end_dt: Optional[date], sku: Optional[str] = None, tenant_id: Optional[Any] = None):
    query = db.query(RawSalesData)
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    if start_dt and end_dt:
        query = query.filter(RawSalesData.date >= start_dt, RawSalesData.date <= end_dt)
    
    clean_sku = (sku or "").strip()
    if clean_sku and clean_sku.upper() not in ["ALL", "GLOBAL", "TOTAL", ""]:
        query = query.filter(or_(RawSalesData.sku == clean_sku, RawSalesData.product_name == clean_sku))

    # Revenue expression: prefer total_sales, fallback to units_sold * price
    rev_expr = func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0)))
    total_rev = query.with_entities(rev_expr).scalar() or 0.0

    # Total Quantity
    total_qty = query.with_entities(func.sum(RawSalesData.units_sold)).scalar() or 0

    # Distinct Orders: verify if order_id is present
    has_orders = query.filter(RawSalesData.order_id != None).first() is not None
    if has_orders:
        distinct_orders = query.with_entities(func.count(func.distinct(RawSalesData.order_id))).scalar() or 0
    else:
        distinct_orders = query.count()

    # Total Profit & Margin
    has_profit_col = query.filter(RawSalesData.profit != None).first() is not None
    if has_profit_col:
        total_profit_val = query.with_entities(func.sum(RawSalesData.profit)).scalar()
        total_profit = float(total_profit_val) if total_profit_val is not None else None
    else:
        total_profit = None

    profit_margin = None
    if total_profit is not None and total_rev > 0:
        profit_margin = round((total_profit / float(total_rev)) * 100, 2)

    # Average Order Value
    aov = round(float(total_rev) / distinct_orders, 2) if distinct_orders > 0 else 0.0

    return {
        "revenue": round(float(total_rev), 2),
        "total_orders": distinct_orders,
        "total_quantity": int(total_qty),
        "aov": aov,
        "total_profit": total_profit,
        "profit_margin_pct": profit_margin,
    }

def get_overview_data(
    db: Session,
    period: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sku: Optional[str] = None,
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    total_query = db.query(RawSalesData)
    if tenant_id:
        total_query = total_query.filter(RawSalesData.tenant_id == tenant_id)
    total_records = total_query.count()
    if total_records == 0:
        return {
            "revenue": 0.0,
            "revenue_growth": None,
            "total_records": 0,
            "total_orders": 0,
            "total_quantity": 0,
            "aov": 0.0,
            "total_profit": None,
            "profit_margin_pct": None,
            "active_predictions": 0,
            "anomalies_detected": 0,
            "model_accuracy": None,
            "forecasted_revenue": 0.0,
            "period": period,
            "date_range": None,
            "insights": ["No sales transactions imported yet. Ingest your CSV to calculate analytics."]
        }

    curr_start, curr_end, prior_start, prior_end = get_period_dates(
        db, period=period, start_date=start_date, end_date=end_date, tenant_id=tenant_id
    )

    current_kpis = calculate_kpis_for_window(db, curr_start, curr_end, sku, tenant_id=tenant_id)

    # Growth vs. prior period
    revenue_growth = None
    if prior_start and prior_end:
        prior_kpis = calculate_kpis_for_window(db, prior_start, prior_end, sku, tenant_id=tenant_id)
        if prior_kpis["revenue"] > 0:
            diff = current_kpis["revenue"] - prior_kpis["revenue"]
            revenue_growth = round((diff / prior_kpis["revenue"]) * 100, 1)

    # Active SKUs count
    skus_query = db.query(func.count(func.distinct(RawSalesData.sku)))
    if tenant_id:
        skus_query = skus_query.filter(RawSalesData.tenant_id == tenant_id)
    active_skus = skus_query.scalar() or 0

    # Model accuracy & WAPE
    latest_run = None
    if tenant_id:
        latest_run = db.query(ModelRun).filter(
            ModelRun.tenant_id == tenant_id,
            ModelRun.wape != None
        ).order_by(ModelRun.created_at.desc()).first()

    if not latest_run:
        # Fallback to general or legacy model runs
        latest_run = db.query(ModelRun).filter(
            ModelRun.wape != None
        ).order_by(ModelRun.created_at.desc()).first()

    # If no runs exist at all, but we have sufficient sales records, auto-evaluate baseline walk-forward benchmark
    if not latest_run and total_records >= 5:
        try:
            from app.pipelines.etl import extract_for_features
            from app.features.engineering import generate_features
            from app.ml.baseline import BaselineModel
            from app.ml.evaluation import evaluate_metrics
            import numpy as np
            import pandas as pd

            df_train = extract_for_features(db, None, tenant_id=tenant_id)
            if not df_train.empty and len(df_train) >= 5:
                df_train['date'] = pd.to_datetime(df_train['date'])
                df_train = df_train.groupby('date', as_index=False).agg({'units_sold': 'sum'}).sort_values('date').reset_index(drop=True)
                df_feat = generate_features(df_train)
                test_size = 7 if len(df_feat) >= 14 else max(1, min(len(df_feat) // 3, 3))
                tr = df_feat.iloc[:-test_size]
                te = df_feat.iloc[-test_size:]
                if len(tr) > 0 and len(te) > 0:
                    base = BaselineModel(method='snaive', window=min(7, len(tr)))
                    base.fit(tr)
                    preds = base.predict(len(te))
                    metrics = evaluate_metrics(te['units_sold'].values, np.array(preds))
                    w_val = metrics.get('wape')
                    mae_val = metrics.get('mae')
                    rmse_val = metrics.get('rmse')
                    if w_val is not None and not np.isnan(w_val) and not np.isinf(w_val):
                        norm_w = round(float(w_val) * 100, 1) if float(w_val) <= 1.5 else round(float(w_val), 1)
                        latest_run = ModelRun(
                            tenant_id=tenant_id,
                            model_name="BASELINE",
                            model_version="BASELINE",
                            status="SUCCESS",
                            sku="ALL",
                            mae=round(float(mae_val), 2) if mae_val is not None else None,
                            rmse=round(float(rmse_val), 2) if rmse_val is not None else None,
                            wape=norm_w
                        )
                        db.add(latest_run)
                        db.commit()
                        db.refresh(latest_run)
        except Exception as e:
            logger.warning(f"Could not auto-evaluate baseline forecast accuracy: {e}")

    model_accuracy = None
    model_wape = None
    if latest_run and latest_run.wape is not None:
        model_wape = normalize_wape(latest_run.wape)
        if model_wape is not None:
            model_accuracy = round(max(0.0, min(100.0, 100.0 - model_wape)), 1)

    # Anomaly count in window
    from app.ml.anomaly import detect_anomalies
    from app.pipelines.etl import extract_for_features
    import pandas as pd
    anomalies_count = 0
    try:
        df_feat = extract_for_features(db, None, tenant_id=tenant_id)
        if not df_feat.empty and len(df_feat) >= 7:
            df_feat['date'] = pd.to_datetime(df_feat['date'])
            df_anom = detect_anomalies(df_feat)
            if curr_start and curr_end:
                df_anom = df_anom[(df_anom['date'].dt.date >= curr_start) & (df_anom['date'].dt.date <= curr_end)]
            anomalies_count = int(df_anom['is_anomaly'].sum())
    except Exception:
        anomalies_count = 0

    # 7-day projected revenue run-rate or baseline forecast
    days_in_period = max(1, (curr_end - curr_start).days + 1) if (curr_start and curr_end) else 30
    daily_run_rate = current_kpis["revenue"] / days_in_period
    forecasted_revenue = round(daily_run_rate * 7, 2)

    # Deterministic Business Insights
    insights = []
    if current_kpis["revenue"] > 0:
        insights.append(f"Recorded ${current_kpis['revenue']:,.2f} in revenue across {current_kpis['total_orders']:,} verified orders (AOV: ${current_kpis['aov']:,.2f}).")
    
    if current_kpis["total_profit"] is not None:
        if current_kpis["total_profit"] >= 0:
            insights.append(f"Net commercial profit stands at ${current_kpis['total_profit']:,.2f} with a {current_kpis['profit_margin_pct']}% operating margin.")
        else:
            insights.append(f"Commercial loss of -${abs(current_kpis['total_profit']):,.2f} observed in this period (Margin: {current_kpis['profit_margin_pct']}%).")

    if revenue_growth is not None:
        direction = "increased" if revenue_growth >= 0 else "declined"
        insights.append(f"Sales {direction} by {abs(revenue_growth)}% compared to the prior equivalent cycle.")

    # Top performing category
    top_cat_query = db.query(
        RawSalesData.category,
        func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0))).label("cat_rev")
    ).filter(
        RawSalesData.category != None,
        RawSalesData.date >= curr_start if curr_start else True,
        RawSalesData.date <= curr_end if curr_end else True
    )
    if tenant_id:
        top_cat_query = top_cat_query.filter(RawSalesData.tenant_id == tenant_id)
    top_cat = top_cat_query.group_by(RawSalesData.category).order_by(desc("cat_rev")).first()

    if top_cat and top_cat[0]:
        insights.append(f"Top-performing category is '{top_cat[0]}' generating ${float(top_cat[1]):,.2f} in sales.")

    return {
        "revenue": current_kpis["revenue"],
        "revenue_growth": revenue_growth,
        "total_records": total_records,
        "total_orders": current_kpis["total_orders"],
        "total_quantity": current_kpis["total_quantity"],
        "aov": current_kpis["aov"],
        "total_profit": current_kpis["total_profit"],
        "profit_margin_pct": current_kpis["profit_margin_pct"],
        "active_predictions": active_skus,
        "anomalies_detected": anomalies_count,
        "model_accuracy": model_accuracy,
        "model_wape": model_wape,
        "forecasted_revenue": forecasted_revenue,
        "period": period,
        "date_range": {
            "start_date": format_date_safe(curr_start),
            "end_date": format_date_safe(curr_end)
        } if curr_start and curr_end else None,
        "comparison_range": {
            "start_date": format_date_safe(prior_start),
            "end_date": format_date_safe(prior_end)
        } if prior_start and prior_end else None,
        "insights": insights
    }

def get_trends_data(
    db: Session,
    interval: str = "daily",
    period: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sku: Optional[str] = None,
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Time-series trends aggregating revenue, units sold, orders, and profit over time.
    Supports 'daily', 'weekly', 'monthly'.
    """
    curr_start, curr_end, _, _ = get_period_dates(db, period=period, start_date=start_date, end_date=end_date, tenant_id=tenant_id)
    query = db.query(RawSalesData)
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    if curr_start and curr_end:
        query = query.filter(RawSalesData.date >= curr_start, RawSalesData.date <= curr_end)
    clean_sku = (sku or "").strip()
    if clean_sku and clean_sku.upper() not in ["ALL", "GLOBAL", "TOTAL", ""]:
        query = query.filter(or_(RawSalesData.sku == clean_sku, RawSalesData.product_name == clean_sku))

    rows = query.order_by(asc(RawSalesData.date)).all()
    if not rows:
        return {"interval": interval, "series": [], "peak_date": None, "lowest_date": None}

    import pandas as pd
    records = []
    for r in rows:
        rev = float(r.total_sales) if r.total_sales is not None else float(r.units_sold * (r.price or 0))
        records.append({
            "date": pd.to_datetime(r.date),
            "revenue": rev,
            "units_sold": r.units_sold,
            "order_id": r.order_id or str(r.id),
            "profit": float(r.profit) if r.profit is not None else None
        })
    df = pd.DataFrame(records)

    clean_int = (interval or "daily").lower().strip()
    if clean_int == "weekly":
        df['period_key'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
        format_str = "%Y-%m-%d"
    elif clean_int == "monthly":
        df['period_key'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time)
        format_str = "%Y-%m"
    else:
        df['period_key'] = df['date']
        format_str = "%Y-%m-%d"

    grouped = df.groupby('period_key').agg({
        'revenue': 'sum',
        'units_sold': 'sum',
        'order_id': 'nunique',
        'profit': lambda x: x.sum() if x.notna().any() else None
    }).reset_index().sort_values('period_key')

    series = []
    peak_date = None
    lowest_date = None
    max_rev = -float('inf')
    min_rev = float('inf')

    prev_rev = None
    for _, row in grouped.iterrows():
        dt_str = row['period_key'].strftime(format_str)
        rev = round(float(row['revenue']), 2)
        qty = int(row['units_sold'])
        orders = int(row['order_id'])
        prof = round(float(row['profit']), 2) if row['profit'] is not None else None

        delta_pct = None
        if prev_rev is not None and prev_rev > 0:
            delta_pct = round(((rev - prev_rev) / prev_rev) * 100, 1)
        prev_rev = rev

        if rev > max_rev:
            max_rev = rev
            peak_date = dt_str
        if rev < min_rev:
            min_rev = rev
            lowest_date = dt_str

        series.append({
            "date": dt_str,
            "revenue": rev,
            "units_sold": qty,
            "orders": orders,
            "profit": prof,
            "growth_delta_pct": delta_pct
        })

    return {
        "interval": clean_int,
        "series": series,
        "peak_date": peak_date,
        "peak_revenue": max_rev if peak_date else 0.0,
        "lowest_date": lowest_date,
        "lowest_revenue": min_rev if lowest_date else 0.0
    }

def get_categories_breakdown(
    db: Session,
    period: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Computes category and sub-category contribution, distinct orders, units, profit, and margin.
    """
    curr_start, curr_end, _, _ = get_period_dates(db, period=period, start_date=start_date, end_date=end_date, tenant_id=tenant_id)
    query = db.query(RawSalesData)
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    if curr_start and curr_end:
        query = query.filter(RawSalesData.date >= curr_start, RawSalesData.date <= curr_end)

    total_store_rev = query.with_entities(
        func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0)))
    ).scalar() or 0.0
    total_store_rev = float(total_store_rev)

    has_profit_col = query.filter(RawSalesData.profit != None).first() is not None

    # Group by category and sub_category
    cat_query = query.with_entities(
        func.coalesce(RawSalesData.category, "Uncategorized").label("cat"),
        func.coalesce(RawSalesData.sub_category, "General").label("subcat"),
        func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0))).label("revenue"),
        func.sum(RawSalesData.units_sold).label("units"),
        func.count(func.distinct(RawSalesData.order_id)).label("distinct_orders"),
        func.sum(RawSalesData.profit).label("profit") if has_profit_col else literal(None).label("profit")
    ).group_by(
        RawSalesData.category,
        RawSalesData.sub_category
    ).order_by(desc("revenue"))

    rows = cat_query.all()

    breakdown = []
    category_totals = {}

    for r in rows:
        rev = round(float(r.revenue or 0.0), 2)
        qty = int(r.units or 0)
        orders = int(r.distinct_orders or 0)
        prof = round(float(r.profit), 2) if (r.profit is not None) else None
        margin = round((prof / rev) * 100, 2) if (prof is not None and rev > 0) else None
        contrib = round((rev / total_store_rev) * 100, 2) if total_store_rev > 0 else 0.0

        item = {
            "category": r.cat,
            "sub_category": r.subcat,
            "revenue": rev,
            "units_sold": qty,
            "orders": orders,
            "profit": prof,
            "profit_margin_pct": margin,
            "contribution_pct": contrib
        }
        breakdown.append(item)

        # Aggregate category totals for top/lowest rankings
        if r.cat not in category_totals:
            category_totals[r.cat] = {"category": r.cat, "revenue": 0.0, "units": 0, "profit": 0.0 if has_profit_col else None}
        category_totals[r.cat]["revenue"] += rev
        category_totals[r.cat]["units"] += qty
        if prof is not None and category_totals[r.cat]["profit"] is not None:
            category_totals[r.cat]["profit"] += prof

    sorted_cats = sorted(category_totals.values(), key=lambda x: x["revenue"], reverse=True)
    best_category = sorted_cats[0]["category"] if sorted_cats else None
    lowest_category = sorted_cats[-1]["category"] if sorted_cats else None

    # Roll-up category summary
    category_summary = []
    for c in sorted_cats:
        c_rev = round(c["revenue"], 2)
        c_prof = round(c["profit"], 2) if c["profit"] is not None else None
        c_margin = round((c_prof / c_rev) * 100, 2) if (c_prof is not None and c_rev > 0) else None
        c_contrib = round((c_rev / total_store_rev) * 100, 2) if total_store_rev > 0 else 0.0
        category_summary.append({
            "category": c["category"],
            "revenue": c_rev,
            "units_sold": c["units"],
            "profit": c_prof,
            "profit_margin_pct": c_margin,
            "contribution_pct": c_contrib
        })

    return {
        "total_store_revenue": round(total_store_rev, 2),
        "best_category": best_category,
        "lowest_category": lowest_category,
        "category_summary": category_summary,
        "breakdown": breakdown
    }

def get_product_performance(
    db: Session,
    limit: int = 10,
    period: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Returns top-selling and lowest-selling products with contribution %, volume, and profit.
    """
    curr_start, curr_end, _, _ = get_period_dates(db, period=period, start_date=start_date, end_date=end_date, tenant_id=tenant_id)
    query = db.query(RawSalesData)
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    if curr_start and curr_end:
        query = query.filter(RawSalesData.date >= curr_start, RawSalesData.date <= curr_end)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(RawSalesData.product_name.ilike(s), RawSalesData.sku.ilike(s)))

    total_store_rev = query.with_entities(
        func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0)))
    ).scalar() or 0.0
    total_store_rev = float(total_store_rev)

    has_profit_col = query.filter(RawSalesData.profit != None).first() is not None

    p_query = query.with_entities(
        RawSalesData.sku,
        func.coalesce(RawSalesData.product_name, RawSalesData.sku).label("p_name"),
        func.coalesce(RawSalesData.category, "Uncategorized").label("category"),
        func.sum(func.coalesce(RawSalesData.total_sales, RawSalesData.units_sold * func.coalesce(RawSalesData.price, 0))).label("revenue"),
        func.sum(RawSalesData.units_sold).label("units"),
        func.count(func.distinct(RawSalesData.order_id)).label("orders"),
        func.sum(RawSalesData.profit).label("profit") if has_profit_col else literal(None).label("profit")
    ).group_by(
        RawSalesData.sku,
        RawSalesData.product_name,
        RawSalesData.category
    )

    all_products = p_query.order_by(desc("revenue")).all()
    if not all_products:
        return {"top_selling": [], "lowest_selling": [], "total_products": 0}

    def serialize_product(r):
        rev = round(float(r.revenue or 0.0), 2)
        qty = int(r.units or 0)
        orders = int(r.orders or 0)
        prof = round(float(r.profit), 2) if r.profit is not None else None
        margin = round((prof / rev) * 100, 2) if (prof is not None and rev > 0) else None
        contrib = round((rev / total_store_rev) * 100, 2) if total_store_rev > 0 else 0.0
        return {
            "sku": r.sku,
            "product_name": r.p_name,
            "category": r.category,
            "revenue": rev,
            "units_sold": qty,
            "orders": orders,
            "profit": prof,
            "profit_margin_pct": margin,
            "contribution_pct": contrib
        }

    top_items = [serialize_product(r) for r in all_products[:limit]]
    lowest_items = [serialize_product(r) for r in reversed(all_products[-limit:])]

    return {
        "top_selling": top_items,
        "lowest_selling": lowest_items,
        "total_products": len(all_products),
        "total_store_revenue": round(total_store_rev, 2)
    }

def get_transactions_table(
    db: Session,
    page: int = 1,
    page_size: int = 25,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    sku: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "date",
    sort_dir: str = "desc",
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Interactive transaction explorer with search, sorting, filtering, and pagination.
    """
    query = db.query(RawSalesData)
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)

    if start_date:
        s_dt = parse_date_safe(start_date)
        if s_dt:
            query = query.filter(RawSalesData.date >= s_dt)
    if end_date:
        e_dt = parse_date_safe(end_date)
        if e_dt:
            query = query.filter(RawSalesData.date <= e_dt)

    if category and category.upper() not in ["ALL", ""]:
        query = query.filter(RawSalesData.category == category)
    if sub_category and sub_category.upper() not in ["ALL", ""]:
        query = query.filter(RawSalesData.sub_category == sub_category)
    if sku and sku.upper() not in ["ALL", "GLOBAL", "TOTAL", ""]:
        query = query.filter(or_(RawSalesData.sku == sku, RawSalesData.product_name == sku))

    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                RawSalesData.product_name.ilike(s_term),
                RawSalesData.sku.ilike(s_term),
                RawSalesData.order_id.ilike(s_term),
                RawSalesData.category.ilike(s_term)
            )
        )

    total_count = query.count()

    # Sorting
    sort_column_map = {
        "date": RawSalesData.date,
        "order_id": RawSalesData.order_id,
        "product_name": RawSalesData.product_name,
        "category": RawSalesData.category,
        "units_sold": RawSalesData.units_sold,
        "price": RawSalesData.price,
        "total_sales": RawSalesData.total_sales,
        "profit": RawSalesData.profit
    }
    col = sort_column_map.get(sort_by, RawSalesData.date)
    order_func = desc if sort_dir.lower() == "desc" else asc
    query = query.order_by(order_func(col))

    # Pagination
    limit = max(1, min(page_size, 100))
    offset = (max(1, page) - 1) * limit
    rows = query.offset(offset).limit(limit).all()

    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "date": format_date_safe(r.date),
            "order_id": r.order_id or f"ORD-{r.id}",
            "sku": r.sku,
            "product_name": r.product_name or r.sku,
            "category": r.category or "N/A",
            "sub_category": r.sub_category or "N/A",
            "units_sold": r.units_sold,
            "price": float(r.price) if r.price is not None else None,
            "total_sales": float(r.total_sales) if r.total_sales is not None else float(r.units_sold * (r.price or 0)),
            "profit": float(r.profit) if r.profit is not None else None,
            "discount_pct": float(r.discount_pct) if r.discount_pct is not None else None,
            "status": r.status
        })

    total_pages = max(1, (total_count + limit - 1) // limit)

    return {
        "items": items,
        "total_count": total_count,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }

