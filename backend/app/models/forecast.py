from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Uuid
from app.db.base import BaseModel


class ModelRun(BaseModel):
    __tablename__ = "model_runs"

    model_version = Column(String(100), nullable=True)
    model_name = Column(String(100), nullable=True)
    status = Column(String(50), default="SUCCESS")
    sku = Column(String(100), nullable=True, index=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    wape = Column(Float, nullable=True)

    def __init__(self, **kwargs):
        if "model_name" in kwargs and not kwargs.get("model_version"):
            kwargs["model_version"] = kwargs["model_name"]
        elif "model_version" in kwargs and not kwargs.get("model_name"):
            kwargs["model_name"] = kwargs["model_version"]
        super().__init__(**kwargs)


# Canonical alias for ModelHealthLog
ModelHealthLog = ModelRun


class Forecast(BaseModel):
    __tablename__ = "forecasts"

    model_run_id = Column(Uuid(as_uuid=True), ForeignKey("model_runs.id"), nullable=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_demand = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)

