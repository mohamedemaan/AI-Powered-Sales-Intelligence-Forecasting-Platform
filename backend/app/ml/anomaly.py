import pandas as pd
import numpy as np

def detect_anomalies(df: pd.DataFrame, target_col='units_sold', threshold=2.0) -> pd.DataFrame:
    df = df.copy()
    if df.empty or len(df) < 5:
        df['is_anomaly'] = False
        df['anomaly_severity'] = 'None'
        df['z_score'] = 0.0
        return df
        
    mean = df[target_col].mean()
    std = df[target_col].std()
    if pd.isna(std) or std == 0:
        std = 1.0
    
    # Z-Score method
    df['z_score'] = (df[target_col] - mean) / (std + 1e-9)
    
    conditions = [
        (df['z_score'].abs() >= 3.0),
        (df['z_score'].abs() >= 2.0),
        (df['z_score'].abs() >= 1.5)
    ]
    choices = ['High', 'Medium', 'Low']
    
    df['is_anomaly'] = df['z_score'].abs() >= threshold
    df['anomaly_severity'] = np.select(conditions, choices, default='None')
    
    return df
