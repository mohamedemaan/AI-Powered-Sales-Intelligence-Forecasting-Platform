import pandas as pd
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
            if self.last_values is None or len(self.last_values) == 0:
                return np.zeros(steps)
            repeats = int(np.ceil(steps / max(1, len(self.last_values))))
            predictions = np.tile(self.last_values, repeats)[:steps]
            return predictions
        elif self.method == 'sma':
            val = np.mean(self.last_values) if (self.last_values is not None and len(self.last_values) > 0) else 0
            return np.full(steps, val)
