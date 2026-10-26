import pandas as pd
from sqlalchemy.orm import Session
from app.models.data import RawSalesData
from app.data.validation import validate_sales_data
import logging

logger = logging.getLogger(__name__)

def read_csv_safe(file_path: str) -> pd.DataFrame:
    for enc in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ValueError(f"Invalid CSV structure: {e}")
    return pd.read_csv(file_path, encoding_errors='replace')

def process_upload(db: Session, file_path: str, replace: bool = True):
    try:
        df = read_csv_safe(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise ValueError(f"Invalid CSV file: {e}")

    is_valid, msg, df = validate_sales_data(df)
    if not is_valid:
        logger.error(f"Validation failed: {msg}")
        raise ValueError(f"Validation failed: {msg}")
        
    # Convert date string column to Python datetime.date objects required by SQLAlchemy SQLite Date
    df['date'] = pd.to_datetime(df['date']).dt.date

    # If replace is requested, wipe previous raw sales ledger and associated forecasts/model runs to prevent duplicate accumulation
    if replace:
        try:
            from app.models.forecast import Forecast, ModelRun
            db.query(Forecast).delete()
            db.query(ModelRun).delete()
            db.query(RawSalesData).delete()
            db.commit()
            logger.info("Cleared prior raw sales data, forecasts, and model runs before fresh upload.")
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not clear prior sales data: {e}")

    # Load to DB
    valid_cols = set(c.name for c in RawSalesData.__table__.columns)
    records = df.to_dict(orient='records')
    for r in records:
        # Strip NaN values and keep only valid SQLAlchemy table attributes
        clean_r = {k: v for k, v in r.items() if k in valid_cols and pd.notna(v) and k != 'id'}
        db.add(RawSalesData(**clean_r, status="PROCESSED"))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database insertion failed: {e}")
        raise ValueError(f"Failed to save records to database: {e}")
        
    return len(records)

def extract_for_features(db: Session, sku: str = None, target: str = None) -> pd.DataFrame:
    try:
        query_val = target or sku
        query = db.query(RawSalesData).filter(RawSalesData.status == "PROCESSED")
        if query_val and query_val.strip().upper() not in ["ALL", "GLOBAL", "TOTAL"]:
            clean_val = query_val.strip()
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    RawSalesData.sku == clean_val,
                    RawSalesData.product_name == clean_val
                )
            )
        
        rows = query.all()
        if not rows:
            return pd.DataFrame(columns=['date', 'sku', 'product_name', 'units_sold', 'price', 'discount_pct', 'available_stock'])
            
        data = [
            {
                'date': r.date,
                'sku': r.sku,
                'product_name': r.product_name or r.sku,
                'units_sold': r.units_sold,
                'price': float(r.price) if r.price is not None else 25.0,
                'discount_pct': float(r.discount_pct) if r.discount_pct is not None else 0.0,
                'available_stock': r.available_stock
            }
            for r in rows
        ]
        return pd.DataFrame(data)
    except Exception as e:
        logger.warning(f"extract_for_features returned empty DataFrame: {e}")
        return pd.DataFrame(columns=['date', 'sku', 'product_name', 'units_sold', 'price', 'discount_pct', 'available_stock'])
