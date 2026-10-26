from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.api.deps import get_db
from app.api.v1.api import api_router
from app.api.v2.api import api_router_v2
from app.api.v3.api import api_router_v3
from app.api.v4.api import api_router_v4
from app.db.session import engine
from app.db.base import Base
import logging
import os

logger = logging.getLogger(__name__)

# Import all models so SQLAlchemy can register them before create_all
import app.models.user
import app.models.product
import app.models.order
import app.models.data
import app.models.tenant
import app.models.forecast

# Create tables for testing/local dev (In production, use Alembic)
Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite development database if any columns are missing
if str(engine.url).startswith("sqlite"):
    with engine.connect() as conn:
        try:
            # users table
            cursor_users = conn.exec_driver_sql("PRAGMA table_info(users)")
            user_cols = [row[1] for row in cursor_users.fetchall()]
            if "tenant_id" not in user_cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN tenant_id VARCHAR(36)")

            # raw_sales_data table
            cursor_sales = conn.exec_driver_sql("PRAGMA table_info(raw_sales_data)")
            sales_cols = [row[1] for row in cursor_sales.fetchall()]
            if "product_name" not in sales_cols:
                conn.exec_driver_sql("ALTER TABLE raw_sales_data ADD COLUMN product_name VARCHAR(255)")
                conn.exec_driver_sql("UPDATE raw_sales_data SET product_name = sku WHERE product_name IS NULL")
            for col_name, col_type in [
                ("order_id", "VARCHAR(100)"),
                ("category", "VARCHAR(100)"),
                ("sub_category", "VARCHAR(100)"),
                ("total_sales", "FLOAT"),
                ("profit", "FLOAT"),
            ]:
                if col_name not in sales_cols:
                    conn.exec_driver_sql(f"ALTER TABLE raw_sales_data ADD COLUMN {col_name} {col_type}")

            # model_runs table
            cursor_runs = conn.exec_driver_sql("PRAGMA table_info(model_runs)")
            runs_cols = [row[1] for row in cursor_runs.fetchall()]
            for col_name, col_type in [("sku", "VARCHAR(100)"), ("mae", "FLOAT"), ("rmse", "FLOAT"), ("wape", "FLOAT"), ("model_name", "VARCHAR(100)")]:
                if col_name not in runs_cols:
                    conn.exec_driver_sql(f"ALTER TABLE model_runs ADD COLUMN {col_name} {col_type}")
            if "model_name" in runs_cols:
                conn.exec_driver_sql("UPDATE model_runs SET model_name = model_version WHERE model_name IS NULL")

            # forecasts table
            cursor_fc = conn.exec_driver_sql("PRAGMA table_info(forecasts)")
            fc_cols = [row[1] for row in cursor_fc.fetchall()]
            for col_name, col_type in [("sku", "VARCHAR(100)"), ("confidence_lower", "FLOAT"), ("confidence_upper", "FLOAT")]:
                if col_name not in fc_cols:
                    conn.exec_driver_sql(f"ALTER TABLE forecasts ADD COLUMN {col_name} {col_type}")

            conn.commit()
        except Exception as e:
            logger.warning(f"SQLite auto-migration warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware (Configured to support all development origins securely)
cors_env = os.getenv("CORS_ORIGINS")
allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()] if cors_env else [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router_v2, prefix='/api/v2')
app.include_router(api_router_v3, prefix='/api/v3')
app.include_router(api_router_v4, prefix='/api/v4')

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    origin = request.headers.get("origin") or "http://localhost:3000"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}", "type": type(exc).__name__},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/")
def root():
    return {"message": "Welcome to the Sales Intelligence API", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/model-health/latest")
@app.get("/api/model-health")
def root_model_health_latest(db: Session = Depends(get_db)):
    from app.api.v1.endpoints.analytics import get_model_health
    return get_model_health(db=db)

@app.get("/api/forecast")
@app.post("/api/forecast")
def root_forecast_endpoint(
    sku: str = "ALL",
    forecast_days: int = 7,
    db: Session = Depends(get_db)
):
    from app.api.v1.endpoints.ml import train_and_select_models
    return train_and_select_models(sku=sku, forecast_days=forecast_days, db=db)
