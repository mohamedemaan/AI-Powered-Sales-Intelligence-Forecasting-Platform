import numpy as np
import pandas as pd
import pytest
from app.ml.baseline import BaselineModel
from app.ml.evaluation import evaluate_metrics
from app.ml.selection import select_best_model

def test_baseline_snaive():
    df = pd.DataFrame({
        'units_sold': [10, 20, 30, 40, 50, 60, 70]
    })
    model = BaselineModel(method='snaive', window=7)
    model.fit(df)
    preds = model.predict(7)
    assert len(preds) == 7
    np.testing.assert_array_equal(preds, [10, 20, 30, 40, 50, 60, 70])

def test_baseline_sma():
    df = pd.DataFrame({
        'units_sold': [10, 20, 30, 40]
    })
    model = BaselineModel(method='sma', window=4)
    model.fit(df)
    preds = model.predict(3)
    assert len(preds) == 3
    assert np.all(preds == 25.0)

def test_evaluate_metrics():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 190.0, 300.0])
    metrics = evaluate_metrics(y_true, y_pred)
    
    # MAE = (|10| + |-10| + |0|) / 3 = 20 / 3 = 6.666...
    assert pytest.approx(metrics['mae'], 0.01) == 6.67
    assert metrics['wape'] == pytest.approx(20.0 / 600.0, 0.01)
    assert metrics['bias'] == 0.0

def test_select_best_model_prefers_better_model():
    eval_results = {
        'baseline': {'mae': 15.0},
        'arima': {'mae': 10.0}
    }
    selected = select_best_model(eval_results, metric='mae')
    assert selected == 'arima'

def test_select_best_model_rejects_worse_candidate():
    eval_results = {
        'baseline': {'mae': 12.0},
        'arima': {'mae': 14.5} # worse than baseline
    }
    selected = select_best_model(eval_results, metric='mae')
    assert selected == 'baseline'

