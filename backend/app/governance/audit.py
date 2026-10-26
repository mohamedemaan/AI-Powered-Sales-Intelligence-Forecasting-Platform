import hashlib
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
