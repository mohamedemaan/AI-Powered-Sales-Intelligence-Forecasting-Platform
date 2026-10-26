import pandas as pd
import logging

logger = logging.getLogger(__name__)

def evaluate_bias_and_fairness(predictions_df: pd.DataFrame, protected_attributes: list):
    '''
    Ethical AI Framework: Tests predictions for statistical parity and disparate impact
    across different regions, store types, or customer segments.
    '''
    ethics_report = {
        "passed": True,
        "warnings": []
    }
    
    if predictions_df.empty:
        return ethics_report
        
    for attr in protected_attributes:
        if attr in predictions_df.columns:
            # Calculate variance in predicted error rates across segments
            grouped_variance = predictions_df.groupby(attr)['error_rate'].mean().var()
            
            # Simple threshold for disparate impact
            if grouped_variance > 0.05:
                ethics_report["passed"] = False
                ethics_report["warnings"].append(
                    f"High variance in prediction error across '{attr}' segments. Potential systemic bias detected."
                )
                logger.warning(f"[ETHICS] Bias detected in attribute: {attr}")
                
    return ethics_report
