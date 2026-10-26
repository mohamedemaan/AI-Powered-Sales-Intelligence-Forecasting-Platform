import numpy as np
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
