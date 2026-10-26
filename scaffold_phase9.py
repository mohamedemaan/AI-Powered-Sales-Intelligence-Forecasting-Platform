import os

gov_files = {
    "backend/app/governance/audit.py": """import hashlib
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DecisionAuditLog:
    '''
    Immutable Audit Trail for all AI decisions.
    Ensures absolute traceability for compliance (GDPR, AI Act).
    '''
    def __init__(self, db_session):
        self.db = db_session
        
    def record_decision(self, tenant_id: str, action_type: str, model_version: str, 
                        inputs: dict, outputs: dict, policy_result: dict, user_id: str = "SYSTEM"):
        
        timestamp = datetime.utcnow().isoformat()
        
        # Create a deterministic payload for hashing
        payload = {
            "tenant_id": tenant_id,
            "action_type": action_type,
            "model_version": model_version,
            "inputs": inputs,
            "outputs": outputs,
            "policy_result": policy_result,
            "user_id": user_id,
            "timestamp": timestamp
        }
        
        payload_str = json.dumps(payload, sort_keys=True)
        cryptographic_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        audit_record = {
            "hash": cryptographic_hash,
            **payload
        }
        
        # In production, this writes to a write-only WORM storage or enterprise blockchain ledger
        logger.info(f"[AUDIT] Decision Recorded: {cryptographic_hash} for Tenant: {tenant_id}")
        return cryptographic_hash
""",

    "backend/app/governance/policy_engine.py": """import logging

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
""",

    "backend/app/ml/ethics.py": """import pandas as pd
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
""",

    "backend/app/ml/trust_scoring.py": """def calculate_system_trust_score(model_accuracy: float, data_quality: float, drift_status: bool, ethics_passed: bool) -> dict:
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
""",

    "backend/app/api/v3/endpoints/governance.py": """from fastapi import APIRouter, Depends, HTTPException
from app.governance.audit import DecisionAuditLog
from app.governance.policy_engine import PolicyEngine
from app.ml.trust_scoring import calculate_system_trust_score

router = APIRouter()

@router.get("/trust-score")
def get_global_trust_score(tenant_id: str):
    '''
    Enterprise Control Center endpoint for system health & trust monitoring.
    '''
    # Mocking system states
    score_report = calculate_system_trust_score(
        model_accuracy=0.92,
        data_quality=0.98,
        drift_status=False,
        ethics_passed=True
    )
    return {"tenant_id": tenant_id, "governance_status": score_report}

@router.post("/evaluate-action")
def evaluate_autonomous_action(tenant_id: str, action: dict):
    '''
    Validates an AI recommendation against the Tenant's Governance Policy Engine.
    '''
    # Mock tenant policies
    policies = {
        "min_confidence": 0.90,
        "max_auto_financial_impact": 5000,
        "max_risk_tolerance": 5.0
    }
    
    engine = PolicyEngine(policies)
    result = engine.evaluate_decision(
        prediction_confidence=action.get('confidence', 0.8),
        risk_score=action.get('risk', 2.0),
        financial_impact=action.get('impact', 1000)
    )
    
    # Audit Logging
    audit = DecisionAuditLog(db_session=None)
    hash_id = audit.record_decision(
        tenant_id=tenant_id,
        action_type="EVALUATE_ACTION",
        model_version="v3.1.0-governed",
        inputs=action,
        outputs=result,
        policy_result=result
    )
    
    return {
        "evaluation": result,
        "audit_trace_id": hash_id
    }
""",

    "backend/app/api/v3/api.py": """from fastapi import APIRouter
from app.api.v3.endpoints import governance

api_router_v3 = APIRouter()
api_router_v3.include_router(governance.router, prefix="/governance", tags=["Global Governance & Trust"])
"""
}

def create_phase9():
    for filepath, content in gov_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Update API Router for V3 Governance API
    main_path = "backend/app/main.py"
    if os.path.exists(main_path):
        with open(main_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "api_router_v3" not in content:
            with open(main_path, "w", encoding='utf-8') as f:
                new_content = content.replace(
                    "from app.api.v1.api import api_router",
                    "from app.api.v1.api import api_router\\nfrom app.api.v2.api import api_router_v2\\nfrom app.api.v3.api import api_router_v3"
                )
                
                # Check if v2 is there, if not just append
                if "api_router_v2" not in new_content:
                    new_content = new_content.replace(
                        "from app.api.v1.api import api_router",
                        "from app.api.v1.api import api_router\\nfrom app.api.v3.api import api_router_v3"
                    )
                
                new_content += "\\napp.include_router(api_router_v3, prefix='/api/v3')\\n"
                f.write(new_content)

if __name__ == "__main__":
    create_phase9()
    print("Phase 9 setup (Global Governance, Trust, and Ethics) completed successfully!")
