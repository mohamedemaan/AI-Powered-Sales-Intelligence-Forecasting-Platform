import pytest
import uuid
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.models.data import RawSalesData
from app.models.forecast import ModelRun
from app.models.audit import AuditLog
from app.core import security
from app.services.audit_service import sanitize_metadata, log_audit_event

client = TestClient(app)
PRECOMPUTED_HASH = security.get_password_hash("SecretPass123!")


def create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, tier="PRO", prefix="aud"):
    uid = uuid.uuid4()
    email = f"{prefix}_{uid.hex[:6]}@salesmind.ai"
    user = User(
        id=uid,
        email=email,
        username=f"usr_{uid.hex[:6]}",
        full_name=f"User {prefix.capitalize()}",
        password_hash=PRECOMPUTED_HASH,
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(
        name=f"Audit Test Workspace {prefix}",
        owner_id=user.id,
        subscription_tier=tier,
        subscription_status="ACTIVE",
        current_period_end=(datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    )
    db.add(tenant)
    db.flush()

    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=role
    )
    db.add(member)
    user.tenant_id = tenant.id
    db.commit()
    db.refresh(user)
    db.refresh(tenant)

    token = security.create_access_token(user.id)
    return user, tenant, token


def test_audit_logs_sensitive_data_sanitization():
    """Verify that passwords, tokens, hashes, and secrets are masked."""
    raw = {
        "user_email": "test@example.com",
        "password": "SuperSecretPassword123",
        "api_key": "live_sk_98317293817293",
        "token_hash": "a1b2c3d4e5f6",
        "nested": {
            "auth_token": "bearer xyz",
            "safe_property": 42
        }
    }
    cleaned = sanitize_metadata(raw)
    assert cleaned["user_email"] == "test@example.com"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["token_hash"] == "[REDACTED]"
    assert cleaned["nested"]["auth_token"] == "[REDACTED]"
    assert cleaned["nested"]["safe_property"] == 42


def test_audit_logging_on_member_invitation_and_removal():
    """Verify MEMBER_INVITED and MEMBER_REMOVED emit proper audit log entries."""
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, prefix="inv_aud")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        # 1. Invite a member
        invitee_email = f"target_{uuid.uuid4().hex[:6]}@example.com"
        res = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            headers=headers,
            json={"email": invitee_email, "role": "ANALYST"}
        )
        assert res.status_code == 200, res.text
        inv_data = res.json()

        # Check audit log in DB
        logs = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant.id,
            AuditLog.event_type == "MEMBER_INVITED"
        ).all()
        assert len(logs) >= 1
        latest_inv_log = logs[-1]
        assert latest_inv_log.actor_id == owner.id
        assert latest_inv_log.actor_email == owner.email
        assert latest_inv_log.metadata_json.get("email") == invitee_email
        assert latest_inv_log.metadata_json.get("role") == "ANALYST"
        assert "token" not in latest_inv_log.metadata_json  # Non-leakage check

        # 2. Add a second user directly to tenant and remove them
        second_uid = uuid.uuid4()
        second_user = User(
            id=second_uid,
            email=f"remove_me_{second_uid.hex[:6]}@example.com",
            username=f"rem_{second_uid.hex[:6]}",
            password_hash=PRECOMPUTED_HASH,
            role=UserRole.ANALYST,
            is_active=True
        )
        db.add(second_user)
        db.flush()
        db.add(TenantMember(tenant_id=tenant.id, user_id=second_user.id, role=TenantMemberRole.VIEWER.value))
        db.commit()

        # Remove member via API
        del_res = client.delete(
            f"/api/v1/organizations/{tenant.id}/members/{second_user.id}",
            headers=headers
        )
        assert del_res.status_code == 200, del_res.text

        # Verify MEMBER_REMOVED audit log
        rem_logs = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant.id,
            AuditLog.event_type == "MEMBER_REMOVED"
        ).all()
        assert len(rem_logs) >= 1
        rem_log = rem_logs[-1]
        assert rem_log.actor_id == owner.id
        assert rem_log.target_id == str(second_user.id)
        assert rem_log.metadata_json.get("removed_email") == second_user.email
    finally:
        db.close()


def test_audit_logs_pagination_and_filtering():
    """Verify GET /{org_id}/audit-logs supports pagination and event filtering."""
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, prefix="page_aud")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        # Seed distinct audit events directly
        for i in range(12):
            log_audit_event(
                db=db,
                tenant_id=tenant.id,
                actor_id=owner.id,
                actor_email=owner.email,
                event_type="DATASET_UPLOADED" if i % 2 == 0 else "MEMBER_INVITED",
                target_type="TEST",
                target_id=f"id_{i}",
                outcome="SUCCESS",
                metadata={"index": i}
            )
        db.commit()

        # Query page 1 with limit 5
        res = client.get(
            f"/api/v1/organizations/{tenant.id}/audit-logs?page=1&limit=5",
            headers=headers
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["limit"] == 5
        assert data["total"] >= 12
        assert data["total_pages"] >= 3

        # Query filter by event_type=DATASET_UPLOADED
        filter_res = client.get(
            f"/api/v1/organizations/{tenant.id}/audit-logs?event_type=DATASET_UPLOADED",
            headers=headers
        )
        assert filter_res.status_code == 200, filter_res.text
        filter_data = filter_res.json()
        assert filter_data["total"] >= 6
        for item in filter_data["items"]:
            assert item["event_type"] == "DATASET_UPLOADED"
    finally:
        db.close()


def test_non_admin_forbidden_from_audit_logs():
    """Verify that VIEWER and ANALYST roles receive 403 Forbidden on audit-logs."""
    db = SessionLocal()
    try:
        owner, tenant, owner_token = create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, prefix="adm_aud")
        
        # Create Viewer member
        viewer_id = uuid.uuid4()
        viewer_user = User(
            id=viewer_id,
            email=f"viewer_{viewer_id.hex[:6]}@example.com",
            username=f"view_{viewer_id.hex[:6]}",
            password_hash=PRECOMPUTED_HASH,
            role=UserRole.ANALYST,
            is_active=True
        )
        db.add(viewer_user)
        db.flush()
        db.add(TenantMember(tenant_id=tenant.id, user_id=viewer_user.id, role=TenantMemberRole.VIEWER.value))
        viewer_user.tenant_id = tenant.id
        db.commit()

        viewer_token = security.create_access_token(viewer_user.id)
        viewer_headers = {"Authorization": f"Bearer {viewer_token}", "X-Organization-ID": str(tenant.id)}

        res = client.get(f"/api/v1/organizations/{tenant.id}/audit-logs", headers=viewer_headers)
        assert res.status_code == 403, f"Expected 403 Forbidden for Viewer, got {res.status_code}"
    finally:
        db.close()


def test_detailed_usage_calculation():
    """Verify detailed usage calculation (storage KB/MB, forecasts total and monthly, seats used)."""
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, tier="BUSINESS", prefix="use_calc")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        # Seed 10 raw sales data rows for this tenant
        for i in range(10):
            db.add(RawSalesData(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                date=datetime.date(2026, 5, i + 1),
                order_id=f"ORD_{i}",
                sku="SKU-TEST",
                product_name="Test Product",
                category="Office Supplies",
                units_sold=5,
                price=10.0,
                total_sales=50.0,
                status="PROCESSED"
            ))
        
        # Seed 2 ModelRuns for this tenant
        for i in range(2):
            db.add(ModelRun(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                sku="SKU-TEST",
                model_name="arima",
                model_version="arima",
                created_at=datetime.datetime.utcnow()
            ))
        db.commit()

        res = client.get(f"/api/v1/organizations/{tenant.id}/usage", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()

        assert data["tenant_id"] == str(tenant.id)
        assert data["tier"] == "BUSINESS"
        assert data["dataset_records_count"] == 10
        assert data["estimated_storage_kb"] > 0
        assert data["forecasts_total_count"] == 2
        assert data["forecasts_month_count"] == 2
        assert data["total_seats_used"] == 1
        assert data["seats_limit"] == 50  # Business plan limit: 50 seats
    finally:
        db.close()
