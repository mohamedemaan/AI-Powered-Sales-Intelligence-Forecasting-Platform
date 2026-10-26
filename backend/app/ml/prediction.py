import pandas as pd
import numpy as np
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def generate_future_dates(last_date, steps=7):
    return [pd.to_datetime(last_date) + timedelta(days=i) for i in range(1, steps + 1)]

def save_predictions_to_db(db, sku, dates, predictions, model_name, mae=None, rmse=None, wape=None):
    try:
        from app.models.forecast import Forecast, ModelRun
        
        # Create Model Run record with evaluation metrics
        run = ModelRun(
            model_version=model_name,
            status="SUCCESS",
            sku=sku,
            mae=float(mae) if mae is not None else None,
            rmse=float(rmse) if rmse is not None else None,
            wape=float(wape) if wape is not None else None
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Store predictions for SKU
        for dt, pred in zip(dates, predictions):
            forecast = Forecast(
                model_run_id=run.id,
                forecast_date=pd.to_datetime(dt).to_pydatetime(),
                sku=sku,
                predicted_demand=int(max(0, float(pred)))
            )
            db.add(forecast)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not persist predictions to DB: {e}")
