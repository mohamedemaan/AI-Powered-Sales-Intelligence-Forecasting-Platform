import pandas as pd
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
