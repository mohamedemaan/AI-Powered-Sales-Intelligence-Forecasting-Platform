import pandas as pd
import numpy as np
import pytest
from app.ml.anomaly import detect_anomalies

def test_detect_anomalies_insufficient_data():
    df = pd.DataFrame({
        'units_sold': [10, 12, 11]
    })
    result = detect_anomalies(df)
    assert not result['is_anomaly'].any()
    assert (result['anomaly_severity'] == 'None').all()

def test_detect_anomalies_with_outlier():
    # 20 points around 100, and one massive spike of 1000
    values = [100.0] * 20 + [1000.0]
    df = pd.DataFrame({
        'units_sold': values
    })
    result = detect_anomalies(df, threshold=2.5)
    
    assert result['is_anomaly'].iloc[-1] == True
    assert result['anomaly_severity'].iloc[-1] in ['High', 'Medium']
    # The normal points should not be flagged as severe anomalies
    assert result['is_anomaly'].iloc[0] == False

