import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def detect_data_drift(reference_df: pd.DataFrame, current_df: pd.DataFrame, threshold: float = 0.05) -> dict:
    '''
    Detects data distribution drift using the Kolmogorov-Smirnov test.
    Returns a dictionary of drifted features.
    '''
    numeric_cols = reference_df.select_dtypes(include=[np.number]).columns
    drift_report = {}
    
    for col in numeric_cols:
        if col in current_df.columns:
            stat, p_value = stats.ks_2samp(reference_df[col].dropna(), current_df[col].dropna())
            if p_value < threshold:
                drift_report[col] = {"drift_detected": True, "p_value": p_value}
                logger.warning(f"Data Drift detected in feature '{col}' (p-value: {p_value:.4f})")
                
    return drift_report

def detect_model_drift(historical_wape: list, current_wape: float, tolerance: float = 0.10) -> bool:
    '''
    Detects model performance degradation over time.
    If the current error is worse than the historical moving average by the tolerance threshold, trigger retraining.
    '''
    if not historical_wape or len(historical_wape) < 3:
        return False # Need more history
        
    avg_historical = sum(historical_wape[-5:]) / min(len(historical_wape), 5)
    
    if (current_wape - avg_historical) / (avg_historical + 1e-9) > tolerance:
        logger.warning(f"Model Drift detected! Current WAPE: {current_wape:.2f} | Historical: {avg_historical:.2f}")
        return True
        
    return False
