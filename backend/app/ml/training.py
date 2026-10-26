import pandas as pd
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
