import logging

logger = logging.getLogger(__name__)

class PolicyEngine:
    '''
    Enterprise Rule Engine enforcing Human-in-the-Loop (HITL) and risk thresholds.
    Overrides AI decisions based on organizational policies.
    '''
    def __init__(self, tenant_policies: dict):
        self.policies = tenant_policies
        
    def evaluate_decision(self, prediction_confidence: float, risk_score: float, financial_impact: float):
        '''
        Evaluates an AI recommendation against tenant-specific rules.
        '''
        result = {
            "status": "APPROVED",
            "requires_human_approval": False,
            "reasoning": []
        }
        
        # Policy 1: Confidence Threshold
        min_confidence = self.policies.get("min_confidence", 0.85)
        if prediction_confidence < min_confidence:
            result["status"] = "BLOCKED"
            result["requires_human_approval"] = True
            result["reasoning"].append(f"Model confidence ({prediction_confidence}) below policy threshold ({min_confidence})")
            
        # Policy 2: Financial Risk Cap
        max_impact = self.policies.get("max_auto_financial_impact", 10000)
        if financial_impact > max_impact:
            result["status"] = "PENDING_APPROVAL"
            result["requires_human_approval"] = True
            result["reasoning"].append(f"Financial impact (${financial_impact}) exceeds auto-approval limit (${max_impact})")
            
        # Policy 3: General Risk Scoring
        if risk_score > self.policies.get("max_risk_tolerance", 7.0):
            result["status"] = "BLOCKED"
            result["requires_human_approval"] = True
            result["reasoning"].append(f"Risk score ({risk_score}) exceeded tolerance.")
            
        logger.info(f"Policy Engine Evaluation: {result['status']}")
        return result
