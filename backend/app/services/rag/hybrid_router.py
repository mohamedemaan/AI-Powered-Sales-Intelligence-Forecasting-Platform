import re
from typing import Tuple, Dict, Any, Optional

# Keywords indicating exact structured financial and sales inquiries
LEDGER_KEYWORDS = [
    "total sales", "total revenue", "distinct orders", "order count",
    "gross revenue", "profit margin", "units sold", "quantity sold",
    "how many orders", "what was the revenue", "top selling",
    "highest sales", "lowest sales", "aov", "average order value"
]

# Keywords indicating knowledge base / document lookups
DOCUMENT_KEYWORDS = [
    "policy", "handbook", "procedure", "document", "pdf", "contract",
    "documentation", "guidelines", "terms", "playbook", "sop", "manual",
    "what does it say", "according to", "clause", "agreement"
]

# Keywords indicating explanatory or diagnostic hybrid inquiries
HYBRID_KEYWORDS = [
    "why did", "explain the drop", "reason for decrease", "anomaly",
    "why are sales", "explain the trend", "what caused", "investigate",
    "reconciliation", "root cause", "explain anomaly"
]


def classify_user_intent(query: str) -> str:
    """
    Classifies the user's inquiry into:
    - 'LEDGER_ANALYTICS': Questions requesting exact quantitative metrics from the database ledger.
    - 'KNOWLEDGE': Questions asking about documents, policies, procedures, or text context.
    - 'HYBRID': Questions combining numerical business performance with qualitative documentation explanations.
    """
    q_lower = query.lower()

    has_ledger = any(k in q_lower for k in LEDGER_KEYWORDS)
    has_doc = any(k in q_lower for k in DOCUMENT_KEYWORDS)
    has_hybrid = any(k in q_lower for k in HYBRID_KEYWORDS)

    # Hybrid precedence: questions asking "Why did sales drop?" or combining both
    if (has_ledger and has_doc) or (has_hybrid and (has_ledger or has_doc)):
        return "HYBRID"
    elif has_doc:
        return "KNOWLEDGE"
    elif has_ledger:
        return "LEDGER_ANALYTICS"
    elif has_hybrid:
        return "HYBRID"

    # Default to KNOWLEDGE if general or ambiguous
    return "KNOWLEDGE"

