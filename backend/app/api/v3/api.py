from fastapi import APIRouter
from app.api.v3.endpoints import governance

api_router_v3 = APIRouter()
api_router_v3.include_router(governance.router, prefix="/governance", tags=["Global Governance & Trust"])
