from fastapi import APIRouter
from app.api.v2.endpoints import automl

api_router_v2 = APIRouter()
api_router_v2.include_router(automl.router, prefix="/automl", tags=["AutoML Platform"])
