import logging

logger = logging.getLogger(__name__)

# Mocked Plan Limits
PLAN_LIMITS = {
    "FREE": {"users": 1, "forecasts": 10, "api_calls": 1000},
    "PRO": {"users": 5, "forecasts": 100, "api_calls": 50000},
    "BUSINESS": {"users": 20, "forecasts": 1000, "api_calls": 500000},
    "ENTERPRISE": {"users": float('inf'), "forecasts": float('inf'), "api_calls": float('inf')}
}

def check_usage_limits(tenant, feature: str) -> bool:
    '''
    Enforces SaaS feature gating and usage limits.
    '''
    limits = PLAN_LIMITS.get(tenant.subscription_tier, PLAN_LIMITS["FREE"])
    
    if feature == "forecasts":
        return tenant.forecasts_count < limits["forecasts"]
    elif feature == "api_calls":
        return tenant.api_calls_count < limits["api_calls"]
        
    return True

def record_usage(tenant, feature: str, amount: int = 1):
    '''
    Increments usage counters for the tenant.
    '''
    if feature == "forecasts":
        tenant.forecasts_count += amount
    elif feature == "api_calls":
        tenant.api_calls_count += amount
