from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.ml.drift import detect_model_drift, detect_data_drift
from app.ml.retraining import automated_retraining_pipeline
from app.services.recommendations import generate_business_recommendations
from app.services.copilot_v2 import AdvancedCopilot

router = APIRouter()
copilot_engine = AdvancedCopilot()

@router.get("/recommendations/{sku}")
def get_recommendations(sku: str, db: Session = Depends(get_db)):
    # Mocking forecast and stock for integration
    forecast_mock = {"next_7_days": [20, 22, 25, 45, 50, 48, 55]}
    current_stock_mock = 80
    
    recommendations = generate_business_recommendations(sku, forecast_mock, current_stock_mock)
    return {"sku": sku, "recommendations": recommendations}

@router.post("/trigger-retraining/{sku}")
def trigger_retraining(sku: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Background tasks must create their own DB session to avoid request-scoped session leak
    from app.db.session import SessionLocal
    def _run_retraining(sku: str):
        session = SessionLocal()
        try:
            automated_retraining_pipeline(sku, session)
        finally:
            session.close()
    background_tasks.add_task(_run_retraining, sku)
    return {"message": "Automated retraining pipeline triggered in the background."}

from fastapi import Body

@router.post("/copilot-v2")
def ask_advanced_copilot(query: str = None, payload: dict = Body(None), sku: str = "ALL"):
    actual_query = query
    if not actual_query and payload and isinstance(payload, dict):
        actual_query = payload.get("query")
        if payload.get("sku"):
            sku = payload.get("sku")
    context = {"sku": sku}
    response = copilot_engine.process_query(actual_query or "", context)
    return response
