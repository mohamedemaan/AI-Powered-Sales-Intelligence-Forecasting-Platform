import os

files = {
    "backend/app/models/data.py": """from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey
from app.db.base import BaseModel

class RawSalesData(BaseModel):
    __tablename__ = "raw_sales_data"
    date = Column(Date, nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    units_sold = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2))
    discount_pct = Column(Numeric(5, 2))
    available_stock = Column(Integer)
    holiday_flag = Column(Integer, default=0)
    festival_flag = Column(Integer, default=0)
    status = Column(String(50), default="PENDING") # PENDING, PROCESSED, ERROR
""",

    "backend/app/data/validation.py": """import pandas as pd

def validate_sales_data(df: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
    required_cols = ['date', 'sku', 'units_sold']
    for col in required_cols:
        if col not in df.columns:
            return False, f"Missing required column: {col}", df
            
    # Check missing required fields
    if df['date'].isnull().any():
        return False, "Missing dates found", df
    if df['sku'].isnull().any():
        return False, "Missing SKU found", df
        
    # Convert and validate numeric fields
    df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce')
    if df['units_sold'].isnull().any() or (df['units_sold'] < 0).any():
        return False, "units_sold must be valid positive numbers", df
        
    # Handle duplicates by taking the latest if any
    df = df.drop_duplicates(subset=['date', 'sku'], keep='last')
    
    return True, "Valid", df
""",

    "backend/app/pipelines/etl.py": """import pandas as pd
from sqlalchemy.orm import Session
from app.models.data import RawSalesData
from app.data.validation import validate_sales_data
import logging

logger = logging.getLogger(__name__)

def process_upload(db: Session, file_path: str):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise ValueError("Invalid CSV file")

    is_valid, msg, df = validate_sales_data(df)
    if not is_valid:
        logger.error(f"Validation failed: {msg}")
        raise ValueError(f"Validation failed: {msg}")
        
    # Load to DB
    records = df.to_dict(orient='records')
    for r in records:
        # Convert date string to python date object if necessary, pandas usually handles format
        db.add(RawSalesData(**r, status="PROCESSED"))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database insertion failed: {e}")
        raise ValueError("Failed to save records to database")
        
    return len(records)

def extract_for_features(db: Session, sku: str = None) -> pd.DataFrame:
    query = db.query(RawSalesData).filter(RawSalesData.status == "PROCESSED")
    if sku:
        query = query.filter(RawSalesData.sku == sku)
    
    df = pd.read_sql(query.statement, query.session.bind)
    return df
""",

    "backend/app/features/engineering.py": """import pandas as pd
import numpy as np

def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
        
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['sku', 'date'])
    
    # Time features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Lag features (grouped by SKU)
    df['units_sold_lag_1'] = df.groupby('sku')['units_sold'].shift(1)
    df['units_sold_lag_7'] = df.groupby('sku')['units_sold'].shift(7)
    df['units_sold_lag_14'] = df.groupby('sku')['units_sold'].shift(14)
    df['units_sold_lag_28'] = df.groupby('sku')['units_sold'].shift(28)
    
    # Rolling features (grouped by SKU)
    df['rolling_mean_7'] = df.groupby('sku')['units_sold_lag_1'].transform(lambda x: x.rolling(7).mean())
    df['rolling_mean_14'] = df.groupby('sku')['units_sold_lag_1'].transform(lambda x: x.rolling(14).mean())
    df['rolling_std_7'] = df.groupby('sku')['units_sold_lag_1'].transform(lambda x: x.rolling(7).std())
    df['rolling_std_30'] = df.groupby('sku')['units_sold_lag_1'].transform(lambda x: x.rolling(30).std())
    
    # Fill NA to prevent data leakage (using 0 or forward fill where appropriate)
    # For lags and rolling windows at the start of series, 0 is a safe assumption for units sold baseline
    feature_cols = [c for c in df.columns if 'lag' in c or 'rolling' in c]
    df[feature_cols] = df[feature_cols].fillna(0)
    
    return df
""",

    "backend/app/ml/baseline.py": """import pandas as pd
import numpy as np

class BaselineModel:
    def __init__(self, method='snaive', window=7):
        self.method = method
        self.window = window
        self.last_values = None
        
    def fit(self, train_df: pd.DataFrame, target_col='units_sold'):
        # For seasonal naive, memorize the last 'window' values
        self.last_values = train_df[target_col].tail(self.window).values
        return self
        
    def predict(self, steps=7):
        if self.method == 'snaive':
            if len(self.last_values) == 0:
                return np.zeros(steps)
            repeats = int(np.ceil(steps / self.window))
            predictions = np.tile(self.last_values, repeats)[:steps]
            return predictions
        elif self.method == 'sma':
            val = np.mean(self.last_values) if len(self.last_values) > 0 else 0
            return np.full(steps, val)
""",

    "backend/app/ml/training.py": """import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings

# Ignore statsmodels convergence warnings for baseline simplicity
warnings.filterwarnings("ignore")

def train_arima(train_df: pd.DataFrame, target_col='units_sold'):
    if len(train_df) < 30:
        return None # Insufficient data for ARIMA
    
    try:
        # Simple ARIMA for baseline comparison
        model = ARIMA(train_df[target_col].values, order=(1,1,1))
        fitted = model.fit()
        return fitted
    except Exception:
        return None
""",

    "backend/app/ml/evaluation.py": """import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

def evaluate_metrics(y_true, y_pred):
    if len(y_true) == 0 or len(y_pred) == 0:
        return {'mae': float('inf'), 'rmse': float('inf'), 'wape': float('inf'), 'bias': float('inf')}
        
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    sum_true = np.sum(y_true)
    wape = np.sum(np.abs(y_true - y_pred)) / sum_true if sum_true > 0 else float('inf')
    bias = np.mean(y_pred - y_true)
    
    return {
        'mae': mae,
        'rmse': rmse,
        'wape': wape,
        'bias': bias
    }
""",

    "backend/app/ml/selection.py": """def select_best_model(eval_results: dict, metric='mae'):
    best_model = None
    best_score = float('inf')
    
    for model_name, metrics in eval_results.items():
        if metrics[metric] < best_score:
            best_score = metrics[metric]
            best_model = model_name
            
    # Baseline fallback: Reject complex models that do not strictly outperform the baseline
    if best_model != 'baseline' and 'baseline' in eval_results:
        baseline_score = eval_results['baseline'][metric]
        if best_score >= baseline_score:
            return 'baseline'
            
    return best_model
""",

    "backend/app/ml/prediction.py": """import pandas as pd
import numpy as np
from datetime import timedelta

def generate_future_dates(last_date, steps=7):
    return [pd.to_datetime(last_date) + timedelta(days=i) for i in range(1, steps + 1)]

def save_predictions_to_db(db, sku, dates, predictions, model_name):
    from app.models.forecast import Forecast, ModelRun
    
    # Create Model Run record
    run = ModelRun(model_version=model_name, status="SUCCESS")
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Assuming sku can be mapped to variant_id, simplified here
    for dt, pred in zip(dates, predictions):
        # We store predicted_demand
        forecast = Forecast(
            model_run_id=run.id,
            forecast_date=dt,
            predicted_demand=int(max(0, pred)) # Demand cannot be negative
        )
        db.add(forecast)
    db.commit()
""",

    "backend/app/api/v1/endpoints/data.py": """from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
import shutil
import os

router = APIRouter()

@router.post("/upload")
async def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    from app.pipelines.etl import process_upload
    try:
        records = process_upload(db, file_path)
        return {"status": "success", "records_processed": records}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    from app.models.data import RawSalesData
    count = db.query(RawSalesData).count()
    return {"status": "ok", "total_raw_records": count}
""",

    "backend/app/api/v1/endpoints/ml.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db

router = APIRouter()

@router.post("/train")
def train_and_select_models(sku: str, forecast_days: int = 7, db: Session = Depends(get_db)):
    # 1. Extract Data
    from app.pipelines.etl import extract_for_features
    df = extract_for_features(db, sku)
    if len(df) < 14: # Minimum viable for walk-forward baseline
        raise HTTPException(status_code=400, detail="Insufficient data to train models")
        
    # 2. Feature Engineering
    from app.features.engineering import generate_features
    df = generate_features(df)
    
    # 3. Train-Test Split (Last 7 days for evaluation)
    train_df = df.iloc[:-7]
    test_df = df.iloc[-7:]
    
    if len(train_df) == 0 or len(test_df) == 0:
        raise HTTPException(status_code=400, detail="Insufficient data after split")

    # 4. Train Models & Evaluate
    from app.ml.baseline import BaselineModel
    from app.ml.training import train_arima
    from app.ml.evaluation import evaluate_metrics
    from app.ml.selection import select_best_model
    
    eval_results = {}
    
    # Baseline Model
    baseline = BaselineModel(method='snaive', window=7)
    baseline.fit(train_df)
    base_preds = baseline.predict(7)
    eval_results['baseline'] = evaluate_metrics(test_df['units_sold'].values, base_preds)
    
    # ARIMA Model
    arima = train_arima(train_df)
    if arima:
        arima_preds = arima.forecast(steps=7)
        eval_results['arima'] = evaluate_metrics(test_df['units_sold'].values, arima_preds)
        
    # 5. Selection
    best_model = select_best_model(eval_results, metric='mae')
    
    # 6. Generate final predictions using full dataset with best model
    # (Simplified: predicting next days)
    if best_model == 'baseline':
        final_model = BaselineModel().fit(df)
        future_preds = final_model.predict(forecast_days)
    elif best_model == 'arima':
        final_model = train_arima(df)
        future_preds = final_model.forecast(steps=forecast_days) if final_model else np.zeros(forecast_days)
    
    # 7. Store Predictions (Stubbed)
    from app.ml.prediction import generate_future_dates, save_predictions_to_db
    last_date = df['date'].iloc[-1]
    future_dates = generate_future_dates(last_date, forecast_days)
    # save_predictions_to_db(db, sku, future_dates, future_preds, best_model) # Requires Forecast table linkage
    
    return {
        "status": "success",
        "best_model_selected": best_model,
        "evaluation_metrics": eval_results,
        "future_predictions": future_preds.tolist()
    }
""",

    "backend/sample_data.csv": """date,sku,units_sold,price,discount_pct,available_stock
2023-10-01,SKU-A001,15,99.99,0,100
2023-10-02,SKU-A001,18,99.99,0,85
2023-10-03,SKU-A001,12,99.99,0,67
2023-10-04,SKU-A001,25,89.99,10,55
2023-10-05,SKU-A001,30,89.99,10,30
2023-10-06,SKU-A001,14,99.99,0,16
2023-10-07,SKU-A001,20,99.99,0,100
2023-10-08,SKU-A001,16,99.99,0,80
2023-10-09,SKU-A001,19,99.99,0,64
2023-10-10,SKU-A001,11,99.99,0,45
"""
}

def create_phase2():
    # Write the new files
    for filepath, content in files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Update api.py to include new routes
    api_path = "backend/app/api/v1/api.py"
    if os.path.exists(api_path):
        with open(api_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "endpoints import data" not in content:
            with open(api_path, "w", encoding='utf-8') as f:
                # Add imports
                new_content = content.replace(
                    "from app.api.v1.endpoints import auth, users, products, orders",
                    "from app.api.v1.endpoints import auth, users, products, orders, data, ml"
                )
                # Add routers
                new_content += "\\napi_router.include_router(data.router, prefix='/data', tags=['data'])\\n"
                new_content += "api_router.include_router(ml.router, prefix='/ml', tags=['ml'])\\n"
                f.write(new_content)
                
    # Update requirements.txt
    req_path = "backend/requirements.txt"
    if os.path.exists(req_path):
        with open(req_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "pandas" not in content:
            with open(req_path, "a", encoding='utf-8') as f:
                f.write("\\npandas==2.1.1\\nscikit-learn==1.3.1\\nstatsmodels==0.14.0\\npython-multipart==0.0.6\\n")

if __name__ == "__main__":
    create_phase2()
    print("Phase 2 setup completed successfully!")
