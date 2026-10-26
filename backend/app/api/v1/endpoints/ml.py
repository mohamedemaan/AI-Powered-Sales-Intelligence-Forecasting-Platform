from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
import logging

from app.api import deps
from app.api.deps import get_db
from app.models.tenant import Tenant
from app.models.data import RawSalesData
from app.pipelines.etl import extract_for_features
from app.features.engineering import generate_features
from app.ml.baseline import BaselineModel
from app.ml.training import train_arima
from app.ml.evaluation import evaluate_metrics
from app.ml.selection import select_best_model
from app.ml.prediction import generate_future_dates, save_predictions_to_db

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalyzeRequest(BaseModel):
    target_name: Optional[str] = Field("ALL", description="Product Name, SKU, or 'ALL'")
    mode: Optional[str] = Field("range", description="'single' for Selected Date or 'range' for Date Range")
    selected_date: Optional[str] = Field(None, description="Target date YYYY-MM-DD for single-date mode")
    start_date: Optional[str] = Field(None, description="Start date YYYY-MM-DD for date-range mode")
    end_date: Optional[str] = Field(None, description="End date YYYY-MM-DD for date-range mode")
    model_preference: Optional[str] = Field("auto", description="'auto', 'baseline', or 'arima'")


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


def predict_future_steps(model: Any, steps: int) -> List[float]:
    """
    Safely forecasts future steps from either BaselineModel or statsmodels ARIMA.
    Checks `forecast` first so statsmodels ARIMA is never erroneously called with `.predict(steps)`.
    """
    if model is None or steps <= 0:
        return [0.0] * max(1, steps)
        
    try:
        if hasattr(model, 'forecast'):
            preds = model.forecast(steps=steps)
            if hasattr(preds, 'values'):
                preds = preds.values
            return [float(max(0.0, p)) for p in preds]
        elif hasattr(model, 'predict'):
            preds = model.predict(steps)
            if hasattr(preds, 'values'):
                preds = preds.values
            return [float(max(0.0, p)) for p in preds]
    except Exception as e:
        logger.warning(f"Forecasting error with {type(model).__name__}: {e}")
        
    return [0.0] * steps


def save_model_health_run_log(
    db: Session,
    sku: Optional[str],
    model_name: str,
    mae: Optional[float],
    rmse: Optional[float],
    wape: Optional[float],
    chart_data: Optional[List[dict]] = None,
    tenant_id: Optional[Any] = None
) -> Optional[Any]:
    """
    Persists model evaluation metrics and generated forecast steps into ModelRun and Forecast tables.
    Allows continuous Model Health and Prediction History tracking across all Forecast Lab runs.
    """
    try:
        from app.models.forecast import ModelRun, Forecast
        clean_sku = sku or "ALL"
        clean_model = (model_name or "BASELINE").upper()
        
        new_model_log = ModelRun(
            tenant_id=tenant_id,
            model_name=clean_model,
            model_version=clean_model,
            status="SUCCESS",
            sku=clean_sku,
            mae=float(mae) if mae is not None else None,
            rmse=float(rmse) if rmse is not None else None,
            wape=float(wape) if wape is not None else None
        )
        db.add(new_model_log)
        db.commit()
        db.refresh(new_model_log)

        if chart_data:
            for pt in chart_data:
                if pt.get("forecast") is not None and pt.get("full_date"):
                    try:
                        fc = Forecast(
                            tenant_id=tenant_id,
                            model_run_id=new_model_log.id,
                            forecast_date=pd.to_datetime(pt["full_date"]).to_pydatetime(),
                            sku=clean_sku,
                            predicted_demand=int(round(float(pt["forecast"]))),
                            confidence_lower=float(pt.get("lower")) if pt.get("lower") is not None else None,
                            confidence_upper=float(pt.get("upper")) if pt.get("upper") is not None else None
                        )
                        db.add(fc)
                    except Exception:
                        pass
            db.commit()
        return new_model_log
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not persist ModelRun log to database: {e}")
        return None


@router.post("/train")
def train_and_select_models(
    sku: str = "ALL",
    forecast_days: int = 7,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    # Enforce Monthly Forecast Quota
    from app.core.plans import get_plan_config, get_tenant_usage
    plan = get_plan_config(current_tenant.subscription_tier)
    usage = get_tenant_usage(db, current_tenant.id)
    if usage["forecasts_month_count"] >= plan["max_forecasts_per_month"]:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly forecast quota reached ({plan['max_forecasts_per_month']} max on {plan['name']}). Please upgrade your workspace subscription to generate additional forecasts."
        )

    clean_sku = (sku or "").strip()
    is_all = clean_sku.upper() in ["ALL", "GLOBAL", "TOTAL", ""]
    
    # 1. Extract Data
    if is_all:
        df = extract_for_features(db, None, tenant_id=current_tenant.id)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby('date', as_index=False).agg({
                'units_sold': 'sum',
                'price': 'mean',
                'discount_pct': 'mean'
            })
            df['sku'] = 'ALL'
            df = df.sort_values('date').reset_index(drop=True)
    else:
        df = extract_for_features(db, clean_sku, tenant_id=current_tenant.id)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

    # Validate historical data sufficiency
    if df.empty or len(df) < 5:
        available_skus = [
            r[0] for r in db.query(RawSalesData.sku)
            .filter(RawSalesData.status == "PROCESSED")
            .distinct()
            .limit(10)
            .all() if r[0]
        ]
        
        if df.empty:
            if not available_skus:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient data: No processed sales data found. Please upload a dataset in the Data Ingestion tab first."
                )
            hint = f" Available SKUs: {', '.join(available_skus[:6])}."
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: No sales data found for SKU '{clean_sku}'.{hint} Select 'ALL' to train across all products."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: SKU '{clean_sku}' only has {len(df)} historical data points. A minimum of 5 records is required. Select 'ALL' to forecast across all products."
            )

    # 2. Feature Engineering
    df = generate_features(df)
    
    # 3. Train-Test Split (Adaptive: 7 days if >= 14 records, otherwise 1-3 days)
    test_size = 7 if len(df) >= 14 else max(1, min(len(df) // 3, 3))
    train_df = df.iloc[:-test_size]
    test_df = df.iloc[-test_size:]
    
    if len(train_df) == 0 or len(test_df) == 0:
        raise HTTPException(status_code=400, detail="Insufficient data to perform walk-forward evaluation split.")

    # 4. Train Models & Evaluate
    eval_results = {}
    
    # Baseline Model (Seasonal Naive)
    baseline = BaselineModel(method='snaive', window=min(7, len(train_df)))
    baseline.fit(train_df)
    base_preds = predict_future_steps(baseline, len(test_df))
    eval_results['baseline'] = evaluate_metrics(test_df['units_sold'].values, np.array(base_preds))
    
    # ARIMA Model
    arima = train_arima(train_df)
    if arima:
        arima_preds = predict_future_steps(arima, len(test_df))
        eval_results['arima'] = evaluate_metrics(test_df['units_sold'].values, np.array(arima_preds))
        
    # 5. Model Selection
    best_model = select_best_model(eval_results, metric='mae')
    if not best_model:
        best_model = 'baseline'
    
    # 6. Generate final predictions using full dataset with best model
    if best_model == 'baseline':
        final_model = BaselineModel(method='snaive', window=min(7, len(df))).fit(df)
        future_preds = predict_future_steps(final_model, forecast_days)
    elif best_model == 'arima':
        final_model = train_arima(df)
        if final_model:
            future_preds = predict_future_steps(final_model, forecast_days)
        else:
            final_model = BaselineModel(method='snaive', window=min(7, len(df))).fit(df)
            future_preds = predict_future_steps(final_model, forecast_days)
            best_model = 'baseline'
    else:
        future_preds = [0.0] * forecast_days

    # 7. Store Predictions & Metrics
    last_date = df['date'].iloc[-1]
    future_dates = generate_future_dates(last_date, forecast_days)
    
    target_sku = "ALL" if is_all else clean_sku
    best_metrics = eval_results.get(best_model, {})
    
    save_predictions_to_db(
        db,
        target_sku,
        future_dates,
        future_preds,
        best_model,
        mae=best_metrics.get('mae'),
        rmse=best_metrics.get('rmse'),
        wape=best_metrics.get('wape'),
        tenant_id=current_tenant.id
    )
    
    return {
        "status": "success",
        "sku": target_sku,
        "historical_records": len(df),
        "best_model_selected": best_model,
        "evaluation_metrics": eval_results,
        "future_predictions": [float(p) for p in future_preds],
        "future_dates": [d.strftime('%Y-%m-%d') for d in future_dates]
    }


@router.post("/analyze")
def analyze_and_forecast_sales(
    payload: Optional[AnalyzeRequest] = Body(None),
    target_name: Optional[str] = None,
    mode: Optional[str] = None,
    selected_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model_preference: Optional[str] = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Unified date-based sales analysis & forecasting workflow.
    Supports Option A (Selected Date) and Option B (Date Range).
    """
    try:
        # 1. Resolve parameters from JSON Body or Query
        p_target = (payload.target_name if payload and payload.target_name else target_name) or "ALL"
        p_mode = (payload.mode if payload and payload.mode else mode) or "range"
        p_selected_date = (payload.selected_date if payload and payload.selected_date else selected_date)
        p_start_date = (payload.start_date if payload and payload.start_date else start_date)
        p_end_date = (payload.end_date if payload and payload.end_date else end_date)
        p_model = (payload.model_preference if payload and payload.model_preference else model_preference) or "auto"

        clean_target = p_target.strip()
        is_all = clean_target.upper() in ["ALL", "GLOBAL", "TOTAL", "", "ALL PRODUCTS", "ALL SKUS"]

        # 2. Check if any sales data exists for the current organization
        total_sales_count = db.query(RawSalesData).filter(
            RawSalesData.status == "PROCESSED",
            RawSalesData.tenant_id == current_tenant.id
        ).count()
        if total_sales_count == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No processed sales data found in {current_tenant.name}. Please upload a dataset in the Data Ingestion tab first."
            )

        # 3. Query records for requested product
        if is_all:
            query = db.query(RawSalesData).filter(
                RawSalesData.status == "PROCESSED",
                RawSalesData.tenant_id == current_tenant.id
            )
            resolved_name = "All Products (Global Aggregate)"
            resolved_sku = "ALL"
        else:
            # Match by product_name or sku
            query = db.query(RawSalesData).filter(
                RawSalesData.status == "PROCESSED",
                RawSalesData.tenant_id == current_tenant.id,
                or_(
                    RawSalesData.product_name == clean_target,
                    RawSalesData.sku == clean_target
                )
            )
            first_match = query.first()
            if not first_match:
                # Case-insensitive / partial search
                query = db.query(RawSalesData).filter(
                    RawSalesData.status == "PROCESSED",
                    RawSalesData.tenant_id == current_tenant.id,
                    or_(
                        RawSalesData.product_name.ilike(f"%{clean_target}%"),
                        RawSalesData.sku.ilike(f"%{clean_target}%")
                    )
                )
                first_match = query.first()

            if not first_match:
                sample_products = db.query(
                    func.coalesce(RawSalesData.product_name, RawSalesData.sku)
                ).filter(
                    RawSalesData.status == "PROCESSED",
                    RawSalesData.tenant_id == current_tenant.id
                ).distinct().limit(5).all()
                samples_str = ", ".join([f"'{s[0]}'" for s in sample_products if s[0]])
                raise HTTPException(
                    status_code=400,
                    detail=f"Target Name '{clean_target}' was not found in {current_tenant.name}. Available products include: {samples_str}. Or choose 'All Products (Global Aggregate)'."
                )
            resolved_name = first_match.product_name or first_match.sku
            resolved_sku = first_match.sku
            resolved_sku = first_match.sku

        # Read records directly from SQLAlchemy query
        rows = query.all()
        if not rows:
            raise HTTPException(
                status_code=400,
                detail=f"No sales observations recorded for '{resolved_name}' ({resolved_sku})."
            )

        data = []
        for r in rows:
            d_val = parse_date_safe(r.date)
            if not d_val:
                continue
            u_sold = int(r.units_sold) if r.units_sold is not None else 1
            u_price = float(r.price) if r.price is not None else 25.0
            data.append({
                "date": d_val,
                "sku": r.sku,
                "product_name": r.product_name or r.sku,
                "units_sold": u_sold,
                "price": u_price,
                "revenue": u_sold * u_price,
                "discount_pct": float(r.discount_pct) if r.discount_pct is not None else 0.0
            })

        if not data:
            raise HTTPException(
                status_code=400,
                detail=f"No sales observations with valid dates recorded for '{resolved_name}' ({resolved_sku})."
            )

        df = pd.DataFrame(data)

        # Group daily
        daily_df = df.groupby('date', as_index=False).agg({
            'units_sold': 'sum',
            'revenue': 'sum',
            'price': 'mean'
        }).sort_values('date').reset_index(drop=True)

        dataset_min_date = parse_date_safe(daily_df['date'].min())
        dataset_max_date = parse_date_safe(daily_df['date'].max())

        # 4. Train Model / Evaluate Walk-Forward
        eval_metrics = {}
        best_model_name = "snaive"
        forecast_fitted_model = None

        if len(daily_df) >= 5:
            test_size = 7 if len(daily_df) >= 14 else max(1, min(len(daily_df) // 3, 3))
            train_daily = daily_df.iloc[:-test_size]
            test_daily = daily_df.iloc[-test_size:]

            # Baseline
            baseline = BaselineModel(method='snaive', window=min(7, len(train_daily)))
            baseline.fit(train_daily)
            b_preds = predict_future_steps(baseline, len(test_daily))
            eval_metrics['baseline'] = evaluate_metrics(test_daily['units_sold'].values, np.array(b_preds))

            # ARIMA
            arima = train_arima(train_daily)
            if arima:
                a_preds = predict_future_steps(arima, len(test_daily))
                eval_metrics['arima'] = evaluate_metrics(test_daily['units_sold'].values, np.array(a_preds))

            if p_model == "arima" and arima:
                best_model_name = "arima"
                forecast_fitted_model = train_arima(daily_df) or BaselineModel().fit(daily_df)
            elif p_model == "baseline":
                best_model_name = "baseline"
                forecast_fitted_model = BaselineModel(method='snaive', window=min(7, len(daily_df))).fit(daily_df)
            else:
                selected = select_best_model(eval_metrics, metric='mae')
                best_model_name = selected or "baseline"
                if best_model_name == "arima":
                    forecast_fitted_model = train_arima(daily_df) or BaselineModel().fit(daily_df)
                else:
                    forecast_fitted_model = BaselineModel(method='snaive', window=min(7, len(daily_df))).fit(daily_df)
        else:
            forecast_fitted_model = BaselineModel(method='sma', window=len(daily_df)).fit(daily_df)
            eval_metrics['baseline'] = {"mae": 0.0, "rmse": 0.0, "wape": 0.0}
            best_model_name = "sma"

        avg_unit_price = float(daily_df['price'].mean()) if len(daily_df) > 0 else 25.0

        # 5. Execute Option A (Selected Date) or Option B (Date Range)
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if p_mode == "single":
            req_date = parse_date_safe(p_selected_date)
            if not req_date:
                req_date = dataset_max_date

            is_future = req_date > dataset_max_date
            status_msg = "Future Forecast Generated" if is_future else "Historical Actuals Retrieved"

            # Check for actual records
            rec = daily_df[daily_df['date'] == req_date]
            has_actual = not rec.empty and not is_future

            if has_actual:
                actual_row = rec.iloc[0]
                actual_units = int(actual_row['units_sold'])
                actual_rev = float(actual_row['revenue'])
                pred_units = None
                pred_rev = None
                lower_b = None
                upper_b = None
            else:
                actual_units = 0 if not is_future else None
                actual_rev = 0.0 if not is_future else None
                # Generate forecast for the requested date
                if is_future:
                    days_ahead = (req_date - dataset_max_date).days
                    future_steps = min(max(days_ahead, 1), 365)
                    f_preds = predict_future_steps(forecast_fitted_model, future_steps)
                    pred_val = float(max(0, f_preds[-1]))
                    pred_units = round(pred_val, 1)
                    pred_rev = round(pred_val * avg_unit_price, 2)
                    lower_b = round(max(0.0, pred_val * 0.85), 1)
                    upper_b = round(pred_val * 1.15, 1)
                else:
                    # Historical date missing from dataset
                    status_msg = "No Transactions Recorded on Date"
                    pred_units = None
                    pred_rev = None
                    lower_b = None
                    upper_b = None

            # Historical Comparisons
            prev_day = req_date - timedelta(days=1)
            prev_week = req_date - timedelta(days=7)
            prev_day_row = daily_df[daily_df['date'] == prev_day]
            prev_week_row = daily_df[daily_df['date'] == prev_week]

            prev_day_pct = None
            if has_actual and not prev_day_row.empty:
                p_val = float(prev_day_row.iloc[0]['units_sold'])
                if p_val > 0:
                    prev_day_pct = round(((actual_units - p_val) / p_val) * 100, 1)

            prev_week_pct = None
            if has_actual and not prev_week_row.empty:
                pw_val = float(prev_week_row.iloc[0]['units_sold'])
                if pw_val > 0:
                    prev_week_pct = round(((actual_units - pw_val) / pw_val) * 100, 1)

            trailing_window = daily_df[daily_df['date'] <= req_date].tail(30)
            trailing_30d_avg = round(float(trailing_window['units_sold'].mean()), 1) if not trailing_window.empty else 0.0

            # Build Chart Data: 14-day window around req_date or trailing dataset
            if not is_future:
                window_df = daily_df[daily_df['date'] <= min(dataset_max_date, req_date + timedelta(days=3))].tail(14)
                chart_df = (window_df if not window_df.empty else daily_df.tail(14)).copy()
            else:
                chart_df = daily_df.tail(14).copy()

            chart_data = []
            for _, row in chart_df.iterrows():
                chart_data.append({
                    "date": row['date'].strftime('%b %d'),
                    "full_date": row['date'].strftime('%Y-%m-%d'),
                    "actual": float(row['units_sold']),
                    "forecast": None,
                    "lower": None,
                    "upper": None
                })

            if is_future:
                # Interpolate or step to future date
                if days_ahead <= 14:
                    date_range_future = pd.date_range(start=dataset_max_date + timedelta(days=1), end=req_date)
                    future_steps_all = len(date_range_future)
                    preds_all = predict_future_steps(forecast_fitted_model, future_steps_all)
                    for dt, p in zip(date_range_future, preds_all):
                        val = round(float(max(0, p)), 1)
                        chart_data.append({
                            "date": dt.strftime('%b %d'),
                            "full_date": dt.strftime('%Y-%m-%d'),
                            "actual": None,
                            "forecast": val,
                            "lower": round(max(0.0, val * 0.85), 1),
                            "upper": round(val * 1.15, 1)
                        })
                else:
                    chart_data.append({
                        "date": req_date.strftime('%b %d'),
                        "full_date": req_date.strftime('%Y-%m-%d'),
                        "actual": None,
                        "forecast": pred_units,
                        "lower": lower_b,
                        "upper": upper_b
                    })

            # Insights
            insights = []
            if has_actual:
                insights.append({
                    "type": "trend",
                    "title": f"Single Date Sales Record: {req_date.strftime('%b %d, %Y')}",
                    "description": f"Recorded {actual_units} units sold generating ${actual_rev:,.2f} in sales revenue."
                })
                if prev_week_pct is not None:
                    dir_word = "higher" if prev_week_pct >= 0 else "lower"
                    insights.append({
                        "type": "comparison",
                        "title": f"Week-Over-Week: {abs(prev_week_pct)}% {dir_word}",
                        "description": f"Demand was {abs(prev_week_pct)}% {dir_word} compared to the exact same day of the prior week ({prev_week.strftime('%b %d')})."
                    })
            elif is_future:
                insights.append({
                    "type": "trend",
                    "title": f"Future Forecast for {req_date.strftime('%b %d, %Y')}",
                    "description": f"Model predicts {pred_units} units (${pred_rev:,.2f}) based on seasonal patterns with an expected band of {lower_b} to {upper_b} units."
                })
                insights.append({
                    "type": "action",
                    "title": "Inventory Buffer Recommendation",
                    "description": f"Maintain at least {int(np.ceil(upper_b))} units in safety stock to cover potential 85th-percentile demand spikes."
                })
            else:
                insights.append({
                    "type": "anomaly",
                    "title": f"Zero Recorded Sales on {req_date.strftime('%b %d, %Y')}",
                    "description": f"No transactions were registered for this product on this historical calendar date. 30-day baseline average was {trailing_30d_avg} units/day."
                })

            summary = {
                "target_name": resolved_name,
                "sku": resolved_sku,
                "mode": "Selected Date",
                "selected_date": req_date.strftime('%Y-%m-%d'),
                "start_date": None,
                "end_date": None,
                "data_points_analyzed": len(daily_df),
                "status": status_msg,
                "is_forecast": is_future,
                "model_used": best_model_name.upper(),
                "generated_at": now_ts,
                "dataset_coverage": {
                    "min_date": format_date_safe(dataset_min_date),
                    "max_date": format_date_safe(dataset_max_date)
                }
            }

            sales_performance = {
                "total_revenue": actual_rev if actual_rev is not None else 0.0,
                "total_units": actual_units if actual_units is not None else 0,
                "avg_daily_sales": actual_rev if actual_rev is not None else 0.0,
                "avg_unit_price": round(avg_unit_price, 2),
                "highest_sales_date": {"date": req_date.strftime('%Y-%m-%d'), "units": actual_units or 0, "revenue": actual_rev or 0.0} if has_actual else None,
                "lowest_sales_date": None,
                "growth_vs_prior_period_pct": prev_day_pct,
                "prior_period_revenue": None,
                "historical_comparisons": {
                    "previous_day_pct": prev_day_pct,
                    "previous_week_pct": prev_week_pct,
                    "trailing_30d_avg_units": trailing_30d_avg
                }
            }

            best_m = eval_metrics.get(best_model_name, eval_metrics.get('baseline', {}))
            forecast_results = {
                "is_applicable": is_future,
                "model_name": best_model_name.upper(),
                "predicted_units": pred_units,
                "predicted_revenue": pred_rev,
                "lower_bound": lower_b,
                "upper_bound": upper_b,
                "evaluation_metrics": {
                    "mae": round(float(best_m.get('mae', 0.0)), 2),
                    "rmse": round(float(best_m.get('rmse', 0.0)), 2),
                    "wape": round(float(best_m.get('wape', 0.0)) * 100, 1) if best_m.get('wape') is not None else None
                },
                "explanation": f"Walk-forward cross-validation evaluated {best_model_name.upper()} against seasonal naive baseline. Predictions use data strictly before {format_date_safe(dataset_max_date)}." if is_future else "Historical date requested; empirical transactions displayed directly without synthetic approximation.",
                "limitations": "Confidence interval represents standard 15% volatility bound. External supply disruptions or sudden marketing promos may cause variances."
            }

            # Persist evaluation metrics to database so Model Health & History stay 100% in sync
            logged_run = save_model_health_run_log(
                db=db,
                sku=resolved_sku or "ALL",
                model_name=best_model_name,
                mae=forecast_results["evaluation_metrics"]["mae"],
                rmse=forecast_results["evaluation_metrics"]["rmse"],
                wape=forecast_results["evaluation_metrics"]["wape"],
                chart_data=chart_data
            )
            if logged_run:
                summary["model_run_id"] = str(logged_run.id)

            return {
                "summary": summary,
                "sales_performance": sales_performance,
                "forecast_results": forecast_results,
                "chart_data": chart_data,
                "insights": insights
            }

        else:
            # OPTION B: DATE RANGE
            r_start = parse_date_safe(p_start_date)
            r_end = parse_date_safe(p_end_date)

            if not r_start:
                # Default to last 30 days of dataset
                r_start = max(dataset_min_date, dataset_max_date - timedelta(days=30))
            if not r_end:
                r_end = dataset_max_date

            if r_start > r_end:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed: Start Date ({r_start}) cannot be later than End Date ({r_end}). Please choose an ascending date range."
                )

            # Historical sub-range
            hist_end = min(r_end, dataset_max_date)
            has_historical_portion = r_start <= dataset_max_date
            has_future_portion = r_end > dataset_max_date

            if has_historical_portion:
                range_df = daily_df[(daily_df['date'] >= r_start) & (daily_df['date'] <= hist_end)]
            else:
                range_df = pd.DataFrame(columns=daily_df.columns)

            num_calendar_days = (r_end - r_start).days + 1
            num_hist_days = (hist_end - r_start).days + 1 if has_historical_portion else 0

            total_units = int(range_df['units_sold'].sum()) if not range_df.empty else 0
            total_revenue = float(range_df['revenue'].sum()) if not range_df.empty else 0.0
            avg_daily_sales = round(total_revenue / max(num_hist_days, 1), 2)
            avg_daily_units = round(total_units / max(num_hist_days, 1), 1)

            highest_date_obj = None
            lowest_date_obj = None
            if not range_df.empty:
                max_idx = range_df['revenue'].idxmax()
                min_idx = range_df['revenue'].idxmin()
                highest_row = range_df.loc[max_idx]
                lowest_row = range_df.loc[min_idx]
                highest_date_obj = {
                    "date": highest_row['date'].strftime('%Y-%m-%d'),
                    "units": int(highest_row['units_sold']),
                    "revenue": round(float(highest_row['revenue']), 2)
                }
                lowest_date_obj = {
                    "date": lowest_row['date'].strftime('%Y-%m-%d'),
                    "units": int(lowest_row['units_sold']),
                    "revenue": round(float(lowest_row['revenue']), 2)
                }

            # Prior equivalent period comparison
            growth_pct = None
            prior_revenue = None
            if has_historical_portion and num_hist_days > 0:
                prior_end = r_start - timedelta(days=1)
                prior_start = prior_end - timedelta(days=num_hist_days - 1)
                prior_df = daily_df[(daily_df['date'] >= prior_start) & (daily_df['date'] <= prior_end)]
                if not prior_df.empty:
                    prior_revenue = float(prior_df['revenue'].sum())
                    if prior_revenue > 0:
                        growth_pct = round(((total_revenue - prior_revenue) / prior_revenue) * 100, 1)

            # Generate Future Forecasts if r_end > dataset_max_date
            chart_data = []
            if has_historical_portion:
                date_range_idx = pd.date_range(start=r_start, end=hist_end)
                lookup = {row['date']: row for _, row in range_df.iterrows()}
                for dt in date_range_idx:
                    d_date = dt.date()
                    if d_date in lookup:
                        row = lookup[d_date]
                        chart_data.append({
                            "date": d_date.strftime('%b %d'),
                            "full_date": d_date.strftime('%Y-%m-%d'),
                            "actual": float(row['units_sold']),
                            "forecast": None,
                            "lower": None,
                            "upper": None
                        })
                    else:
                        chart_data.append({
                            "date": d_date.strftime('%b %d'),
                            "full_date": d_date.strftime('%Y-%m-%d'),
                            "actual": 0.0,
                            "forecast": None,
                            "lower": None,
                            "upper": None
                        })

            future_pred_total = 0.0
            if has_future_portion:
                future_start_date = max(dataset_max_date + timedelta(days=1), r_start)
                future_range_idx = pd.date_range(start=pd.to_datetime(future_start_date), end=pd.to_datetime(r_end))
                steps_needed = (r_end - dataset_max_date).days
                if steps_needed > 0:
                    f_all = predict_future_steps(forecast_fitted_model, steps_needed)
                    offset = max(0, (future_start_date - (dataset_max_date + timedelta(days=1))).days)
                    for i, dt in enumerate(future_range_idx):
                        pred_idx = offset + i
                        val = float(max(0, f_all[pred_idx])) if pred_idx < len(f_all) else float(f_all[-1])
                        val = round(val, 1)
                        future_pred_total += val
                        chart_data.append({
                            "date": dt.strftime('%b %d'),
                            "full_date": dt.strftime('%Y-%m-%d'),
                            "actual": None,
                            "forecast": val,
                            "lower": round(max(0.0, val * 0.85), 1),
                            "upper": round(val * 1.15, 1)
                        })

            # Insights
            insights = []
            if has_historical_portion and total_revenue > 0:
                trend_str = "increasing" if (growth_pct and growth_pct > 0) else "moderating" if (growth_pct and growth_pct < 0) else "stable"
                insights.append({
                    "type": "trend",
                    "title": f"Range Revenue Performance ({trend_str.capitalize()})",
                    "description": f"Generated ${total_revenue:,.2f} across {total_units:,} units sold between {r_start.strftime('%b %d, %Y')} and {hist_end.strftime('%b %d, %Y')}."
                })
                if highest_date_obj:
                    insights.append({
                        "type": "peak",
                        "title": f"Peak Trading Day: {highest_date_obj['date']}",
                        "description": f"Highest volume reached {highest_date_obj['units']} units generating ${highest_date_obj['revenue']:,.2f} in sales revenue."
                    })
                if growth_pct is not None:
                    verb = "grew by" if growth_pct >= 0 else "contracted by"
                    insights.append({
                        "type": "comparison",
                        "title": f"Period-over-Period: {growth_pct}%",
                        "description": f"Sales revenue {verb} {abs(growth_pct)}% compared to the immediately preceding {num_hist_days}-day period (${prior_revenue:,.2f})."
                    })

            if has_future_portion:
                future_rev_est = future_pred_total * avg_unit_price
                insights.append({
                    "type": "trend",
                    "title": "Forward Forecast Extension",
                    "description": f"Model projects an additional {round(future_pred_total, 1)} units (~${future_rev_est:,.2f}) for the period extending through {r_end.strftime('%b %d, %Y')}."
                })
                insights.append({
                    "type": "action",
                    "title": "Procurement Strategy",
                    "description": "Align supplier purchase orders at least 10 business days prior to anticipated demand crests to avoid costly stockouts."
                })

            status_text = "Historical Period Analysis"
            if has_historical_portion and has_future_portion:
                status_text = "Blended Actuals & Future Forecast"
            elif has_future_portion:
                status_text = "Full Future Period Forecast"

            summary = {
                "target_name": resolved_name,
                "sku": resolved_sku,
                "mode": "Date Range",
                "selected_date": None,
                "start_date": r_start.strftime('%Y-%m-%d'),
                "end_date": r_end.strftime('%Y-%m-%d'),
                "data_points_analyzed": len(range_df),
                "status": status_text,
                "is_forecast": has_future_portion,
                "model_used": best_model_name.upper(),
                "generated_at": now_ts,
                "dataset_coverage": {
                    "min_date": format_date_safe(dataset_min_date),
                    "max_date": format_date_safe(dataset_max_date)
                }
            }

            sales_performance = {
                "total_revenue": total_revenue,
                "total_units": total_units,
                "avg_daily_sales": avg_daily_sales,
                "avg_unit_price": round(avg_unit_price, 2),
                "highest_sales_date": highest_date_obj,
                "lowest_sales_date": lowest_date_obj,
                "growth_vs_prior_period_pct": growth_pct,
                "prior_period_revenue": prior_revenue,
                "historical_comparisons": None
            }

            best_m = eval_metrics.get(best_model_name, eval_metrics.get('baseline', {}))
            forecast_results = {
                "is_applicable": has_future_portion,
                "model_name": best_model_name.upper(),
                "predicted_units": round(future_pred_total, 1) if has_future_portion else None,
                "predicted_revenue": round(future_pred_total * avg_unit_price, 2) if has_future_portion else None,
                "lower_bound": round(future_pred_total * 0.85, 1) if has_future_portion else None,
                "upper_bound": round(future_pred_total * 1.15, 1) if has_future_portion else None,
                "evaluation_metrics": {
                    "mae": round(float(best_m.get('mae', 0.0)), 2),
                    "rmse": round(float(best_m.get('rmse', 0.0)), 2),
                    "wape": round(float(best_m.get('wape', 0.0)) * 100, 1) if best_m.get('wape') is not None else None
                },
                "explanation": f"Walk-forward evaluation selected {best_model_name.upper()}. Training strictly quarantined data $\\le$ {format_date_safe(dataset_max_date)} to avoid future leakage." if has_future_portion else "Complete empirical timeline analyzed directly from validated sales ledger.",
                "limitations": "Predictions assume structural continuity of seasonality and price elasticity without macro shocks."
            }

            # Persist evaluation metrics to database so Model Health & History stay 100% in sync
            logged_run = save_model_health_run_log(
                db=db,
                sku=resolved_sku or "ALL",
                model_name=best_model_name,
                mae=forecast_results["evaluation_metrics"]["mae"],
                rmse=forecast_results["evaluation_metrics"]["rmse"],
                wape=forecast_results["evaluation_metrics"]["wape"],
                chart_data=chart_data,
                tenant_id=current_tenant.id
            )
            if logged_run:
                summary["model_run_id"] = str(logged_run.id)

            return {
                "summary": summary,
                "sales_performance": sales_performance,
                "forecast_results": forecast_results,
                "chart_data": chart_data,
                "insights": insights
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_and_forecast_sales: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/history")
def get_prediction_history(
    limit: int = 50,
    sku: Optional[str] = None,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Returns prediction history audit log scoped to the active workspace:
    Model runs, saved forecasts, horizon, metrics (MAE, RMSE, WAPE),
    and actual vs. predicted comparisons where ground truth exists in RawSalesData.
    """
    from app.models.forecast import ModelRun, Forecast
    
    query = db.query(ModelRun).filter(ModelRun.tenant_id == current_tenant.id).order_by(ModelRun.created_at.desc())
    if sku and sku.upper() not in ["ALL", "GLOBAL", "TOTAL", ""]:
        query = query.filter(ModelRun.sku == sku)
        
    runs = query.limit(limit).all()
    if not runs:
        return {"total_runs": 0, "runs": [], "organization_id": str(current_tenant.id)}
        
    result_runs = []
    for r in runs:
        forecasts = db.query(Forecast).filter(Forecast.model_run_id == r.id, Forecast.tenant_id == current_tenant.id).order_by(Forecast.forecast_date.asc()).all()
        forecast_items = []
        for f in forecasts:
            f_date = f.forecast_date.date() if hasattr(f.forecast_date, 'date') else f.forecast_date
            
            # Check for actual sales on that date
            actual_sales_query = db.query(func.sum(RawSalesData.units_sold)).filter(RawSalesData.date == f_date)
            if f.sku and f.sku.upper() not in ["ALL", "GLOBAL", "TOTAL", ""]:
                actual_sales_query = actual_sales_query.filter(RawSalesData.sku == f.sku)
            actual_val = actual_sales_query.scalar()
            
            variance = None
            if actual_val is not None:
                variance = int(f.predicted_demand - actual_val)
                
            forecast_items.append({
                "forecast_date": format_date_safe(f_date),
                "predicted_demand": f.predicted_demand,
                "actual_demand": int(actual_val) if actual_val is not None else None,
                "variance": variance,
                "status": "Verified Actual" if actual_val is not None else "Pending Actuals"
            })
            
        result_runs.append({
            "run_id": str(r.id),
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
            "sku": r.sku or "Global",
            "model_version": r.model_version,
            "status": r.status,
            "metrics": {
                "mae": r.mae,
                "rmse": r.rmse,
                "wape": round(r.wape * 100, 1) if r.wape is not None else None
            },
            "predictions_count": len(forecasts),
            "predictions": forecast_items
        })
        
    return {
        "total_runs": len(result_runs),
        "runs": result_runs
    }
