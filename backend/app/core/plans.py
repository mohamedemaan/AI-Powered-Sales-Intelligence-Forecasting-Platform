from typing import Dict, Any, List
from datetime import datetime, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.tenant import Tenant, TenantMember, TenantInvitation
from app.models.forecast import ModelRun
from app.models.data import RawSalesData

PLANS_CONFIG: Dict[str, Dict[str, Any]] = {
    "FREE": {
        "tier": "FREE",
        "name": "Free Community Tier",
        "description": "Essential analytics and baseline forecasting for individual retailers and pilot testing.",
        "price_monthly": 0,
        "max_members": 2,
        "max_datasets": 3,
        "max_forecasts_per_month": 10,
        "max_exports_per_month": 5,
        "features": [
            "Baseline Sales Forecasting (ARIMA & Naive)",
            "Up to 2 Workspace Team Members",
            "Up to 3 Ingested Datasets",
            "10 Forecast Runs per Month",
            "Standard CSV Data Exports"
        ]
    },
    "PRO": {
        "tier": "PRO",
        "name": "Professional Tier",
        "description": "Advanced AI intelligence, higher forecast volume, and team collaboration for scaling retail operations.",
        "price_monthly": 49,
        "max_members": 10,
        "max_datasets": 25,
        "max_forecasts_per_month": 100,
        "max_exports_per_month": 50,
        "features": [
            "Advanced Multi-Model ML Forecasting",
            "Up to 10 Workspace Team Members",
            "Up to 25 Ingested Datasets",
            "100 Forecast Runs per Month",
            "Priority ETL Processing & Deduplication",
            "Audited Financial Reports & Exports"
        ]
    },
    "BUSINESS": {
        "tier": "BUSINESS",
        "name": "Business Enterprise Tier",
        "description": "Unlimited capacity, dedicated tenant quotas, and full multi-seat organizational control.",
        "price_monthly": 199,
        "max_members": 50,
        "max_datasets": 500,
        "max_forecasts_per_month": 2000,
        "max_exports_per_month": 500,
        "features": [
            "Enterprise Multi-Model Grid Search",
            "Up to 50 Workspace Team Members",
            "High-Capacity Dataset Storage (500 datasets)",
            "2,000 Forecast Runs per Month",
            "Custom CSV & Ledger Audit Exports",
            "Full RBAC Administration & Audit Logs"
        ]
    },
    "ENTERPRISE": {
        "tier": "ENTERPRISE",
        "name": "Custom Enterprise Tier",
        "description": "Custom SLAs, dedicated database instances, and unlimited operational capacity.",
        "price_monthly": 499,
        "max_members": 9999,
        "max_datasets": 9999,
        "max_forecasts_per_month": 99999,
        "max_exports_per_month": 99999,
        "features": [
            "Unlimited Team Members & Workspaces",
            "Unlimited Datasets & Model Runs",
            "Dedicated Support & Custom Integrations"
        ]
    }
}

def get_plan_config(tier: str) -> Dict[str, Any]:
    clean_tier = (tier or "FREE").strip().upper()
    return PLANS_CONFIG.get(clean_tier, PLANS_CONFIG["FREE"])

def get_tenant_usage(db: Session, tenant_id: UUID) -> Dict[str, Any]:
    """
    Computes real, un-fabricated usage metrics directly from the tenant-partitioned database tables.
    """
    # 1. Members count (active members + pending invitations)
    active_members = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == tenant_id).scalar() or 0
    pending_invites = db.query(func.count(TenantInvitation.id)).filter(
        TenantInvitation.tenant_id == tenant_id,
        TenantInvitation.status == "PENDING"
    ).scalar() or 0
    total_seat_usage = active_members + pending_invites

    # 2. Datasets count
    has_data = db.query(RawSalesData.id).filter(RawSalesData.tenant_id == tenant_id).first() is not None
    datasets_count = 1 if has_data else 0

    # 3. Forecasts run in the current calendar month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    monthly_forecasts = db.query(func.count(ModelRun.id)).filter(
        ModelRun.tenant_id == tenant_id,
        ModelRun.created_at >= start_of_month
    ).scalar() or 0

    return {
        "active_members_count": active_members,
        "pending_invites_count": pending_invites,
        "total_seats_used": total_seat_usage,
        "datasets_count": datasets_count,
        "forecasts_month_count": monthly_forecasts,
        "billing_period_start": start_of_month.strftime("%Y-%m-%d")
    }

