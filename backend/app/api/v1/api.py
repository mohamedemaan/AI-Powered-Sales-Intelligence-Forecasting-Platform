from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    products,
    orders,
    data,
    ml,
    analytics,
    intelligence,
    billing,
    organizations
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(data.router, prefix='/data', tags=['data'])
api_router.include_router(ml.router, prefix='/ml', tags=['ml'])
api_router.include_router(analytics.router, prefix='/analytics', tags=['analytics'])
api_router.include_router(intelligence.router, prefix='/intelligence', tags=['intelligence'])
api_router.include_router(billing.router, prefix='/billing', tags=['billing'])
