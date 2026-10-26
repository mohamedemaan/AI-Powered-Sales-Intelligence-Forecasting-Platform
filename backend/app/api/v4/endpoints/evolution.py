from fastapi import APIRouter
from app.autonomous.multi_agent import SwarmOrchestrator
from app.autonomous.knowledge_graph import GlobalKnowledgeGraph
from app.autonomous.meta_learning import MetaLearningEngine

router = APIRouter()
swarm = SwarmOrchestrator()
graph = GlobalKnowledgeGraph()
meta = MetaLearningEngine()

@router.post("/strategic-decision")
def get_autonomous_decision(sku: str):
    '''
    V4 Apex API: Triggers the Multi-Agent Swarm to generate a strategic, graph-aware decision.
    '''
    # 1. Pull context from Long-Term Memory (Knowledge Graph)
    context = graph.query_strategic_context(sku)
    
    # 2. Swarm debates and synthesizes strategy
    decision = swarm.synthesize_decision(context)
    
    # 3. Log to memory for future learning
    graph.ingest_event(f"DECISION_{sku}", "STRATEGIC_ACTION", decision)
    
    return {
        "sku": sku,
        "context_analyzed": context,
        "autonomous_decision": decision
    }

@router.post("/meta-optimize")
def trigger_meta_learning(tenant_id: str):
    '''
    Triggers the system to evaluate its own architecture and apply cross-tenant learnings.
    '''
    optimization_plan = meta.dynamic_architecture_search({"volatility": 0.85})
    return {"tenant_id": tenant_id, "architecture_update": optimization_plan}
