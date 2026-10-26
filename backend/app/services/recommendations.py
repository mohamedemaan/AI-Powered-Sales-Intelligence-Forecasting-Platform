from typing import List, Dict

def generate_business_recommendations(sku: str, forecast_data: dict, current_stock: int) -> List[Dict]:
    '''
    Rule-based and ML-driven recommendation engine.
    Translates predictions into actionable business insights.
    '''
    recommendations = []
    
    # 1. Stock Out Risk Analysis
    predicted_demand_7d = sum(forecast_data.get('next_7_days', []))
    if predicted_demand_7d > current_stock:
        shortfall = predicted_demand_7d - current_stock
        recommendations.append({
            "type": "INVENTORY_ALERT",
            "priority": "HIGH",
            "action": f"Increase stock by at least {shortfall} units.",
            "reason": f"Predicted demand ({predicted_demand_7d}) exceeds current stock ({current_stock})."
        })
        
    # 2. Demand Spikes
    if len(forecast_data.get('next_7_days', [])) >= 2:
        if forecast_data['next_7_days'][-1] > forecast_data['next_7_days'][0] * 1.5:
            recommendations.append({
                "type": "PRICE_STRATEGY",
                "priority": "MEDIUM",
                "action": "Consider a 5% dynamic price increase for the weekend.",
                "reason": "Sudden demand spike detected towards the end of the forecast window."
            })

    # 3. Stagnant Inventory
    if predicted_demand_7d < (current_stock * 0.1) and current_stock > 100:
         recommendations.append({
            "type": "MARKETING_STRATEGY",
            "priority": "MEDIUM",
            "action": "Run a discount campaign.",
            "reason": "Slow-moving inventory detected. High stock availability with low forecasted demand."
        })
         
    return recommendations
