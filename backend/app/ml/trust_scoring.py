def calculate_system_trust_score(model_accuracy: float, data_quality: float, drift_status: bool, ethics_passed: bool) -> dict:
    '''
    Calculates a composite Trust & Reliability Index (0-100) for the dashboard.
    Ensures business users know exactly how much they can trust the current system state.
    '''
    # Base weights
    accuracy_weight = 0.50
    data_quality_weight = 0.30
    drift_penalty = 15 if drift_status else 0
    ethics_penalty = 25 if not ethics_passed else 0
    
    # Calculation
    base_score = (model_accuracy * 100 * accuracy_weight) + (data_quality * 100 * data_quality_weight)
    final_score = max(0, base_score - drift_penalty - ethics_penalty)
    
    # Classification
    if final_score >= 90:
        level = "HIGHLY_RELIABLE"
    elif final_score >= 70:
        level = "MODERATE"
    else:
        level = "UNTRUSTWORTHY"
        
    return {
        "trust_score": round(final_score, 1),
        "reliability_level": level,
        "factors": {
            "accuracy_contribution": round(model_accuracy * 100 * accuracy_weight, 1),
            "data_quality_contribution": round(data_quality * 100 * data_quality_weight, 1),
            "drift_penalty": -drift_penalty,
            "ethics_penalty": -ethics_penalty
        }
    }
