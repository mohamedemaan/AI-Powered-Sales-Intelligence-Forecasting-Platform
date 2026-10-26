import pandas as pd
import numpy as np

def generate_explanations(df: pd.DataFrame, model, predictions) -> dict:
    # Simplified mock explainability (In production, use SHAP with tree models)
    # We analyze the feature variance to determine drivers
    
    recent_data = df.tail(7).copy()
    avg_stock = recent_data['available_stock'].mean() if 'available_stock' in recent_data else 0
    avg_discount = recent_data['discount_pct'].mean() if 'discount_pct' in recent_data else 0
    
    drivers = []
    if avg_discount > 0:
        drivers.append({"factor": "Discount", "impact": "Positive", "weight": 0.45})
    if avg_stock < 50:
        drivers.append({"factor": "Low Stock", "impact": "Negative", "weight": -0.30})
        
    drivers.append({"factor": "Recent Trend", "impact": "Positive", "weight": 0.25})
    
    text = "Sales prediction is primarily driven by "
    text += ", ".join([d['factor'] for d in drivers])
    
    return {
        "summary": text,
        "drivers": drivers
    }
