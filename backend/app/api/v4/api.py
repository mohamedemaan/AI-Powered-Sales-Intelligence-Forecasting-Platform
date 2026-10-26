from fastapi import APIRouter
from app.api.v4.endpoints import evolution

api_router_v4 = APIRouter()
api_router_v4.include_router(evolution.router, prefix="/evolution", tags=["Autonomous Evolution & Multi-Agent Swarm"])
