import pytest
import uuid
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.models.forecast import ModelRun
from app.core import security
from app.core.plans import PLANS_CONFIG

client = TestClient(app)
PRECOMPUTED_HASH = security.get_password_hash("SecretPass123!")

def create_workspace_for_subscription(db, tier="FREE", prefix="sub_user"):
    uid = uuid.uuid4()
    email = f"{prefix}_{uid.hex[:6]}@enterprise.com"
    user = User(
        id=uid,
        email=email,
        username=f"user_{uid.hex[:6]}",
        full_name=f"Sub {prefix.capitalize()}",
        password_hash=PRECOMPUTED_HASH,
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(
        name=f"Workspace for {prefix}",
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
        role=TenantMemberRole.OWNER.value
    )
    db.add(member)
    user.tenant_id = tenant.id
    db.commit()
    db.refresh(user)
    db.refresh(tenant)

    token = security.create_access_token(user.id)
    return user, tenant, token

def test_get_subscription_details():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_for_subscription(db, tier="FREE", prefix="sub_details")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.get(f"/api/v1/organizations/{tenant.id}/subscription", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["tier"] == "FREE"
        assert data["usage"]["members_count"] == 1
        assert data["usage"]["members_limit"] == 2
        assert data["usage"]["remaining_seats"] == 1
        assert len(data["available_plans"]) == 4
    finally:
        db.close()

def test_enforce_team_member_quota_and_upgrade_flow():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_for_subscription(db, tier="FREE", prefix="sub_quota")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        # Free tier limit = 2 members. Owner is 1.
        # Invite 1st member -> seats = 2
        res1 = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": f"invitee1_{uuid.uuid4().hex[:6]}@test.com", "role": "ANALYST"},
            headers=headers
        )
        assert res1.status_code == 200

        # Invite 2nd member -> seats = 3 > 2 (Limit exceeded!)
        res2 = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": f"invitee2_{uuid.uuid4().hex[:6]}@test.com", "role": "VIEWER"},
            headers=headers
        )
        assert res2.status_code == 402, res2.text
        assert "Team seat limit reached" in res2.json()["detail"]

        # Owner upgrades workspace to PRO
        upgrade_res = client.post(
            f"/api/v1/organizations/{tenant.id}/subscription/upgrade",
            json={"plan_tier": "PRO"},
            headers=headers
        )
        assert upgrade_res.status_code == 200, upgrade_res.text
        assert upgrade_res.json()["tier"] == "PRO"
        assert upgrade_res.json()["usage"]["members_limit"] == 10

        # Now 2nd member invitation succeeds!
        res3 = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": f"invitee2_{uuid.uuid4().hex[:6]}@test.com", "role": "VIEWER"},
            headers=headers
        )
        assert res3.status_code == 200
    finally:
        db.close()

def test_non_owner_cannot_upgrade_subscription():
    db = SessionLocal()
    try:
        owner, tenant, _ = create_workspace_for_subscription(db, tier="FREE", prefix="sub_no_owner")

        # Create admin member
        admin_uid = uuid.uuid4()
        admin_user = User(
            id=admin_uid,
            email=f"admin_{admin_uid.hex[:6]}@test.com",
            username=f"admin_{admin_uid.hex[:6]}",
            full_name="Admin User",
            password_hash=PRECOMPUTED_HASH,
            role=UserRole.ADMIN,
            is_active=True,
            tenant_id=tenant.id
        )
        db.add(admin_user)
        admin_mem = TenantMember(
            tenant_id=tenant.id,
            user_id=admin_user.id,
            role=TenantMemberRole.ADMIN.value
        )
        db.add(admin_mem)
        db.commit()

        admin_token = security.create_access_token(admin_user.id)
        admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Organization-ID": str(tenant.id)}

        unauth_upgrade = client.post(
            f"/api/v1/organizations/{tenant.id}/subscription/upgrade",
            json={"plan_tier": "BUSINESS"},
            headers=admin_headers
        )
        assert unauth_upgrade.status_code == 403
        assert "Only an organization Owner can manage subscriptions" in unauth_upgrade.json()["detail"]
    finally:
        db.close()

def test_enforce_forecast_monthly_quota():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_for_subscription(db, tier="FREE", prefix="sub_fc")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        now = datetime.datetime.utcnow()
        # Seed 10 ModelRun rows to simulate reaching the Free tier 10 forecasts/month limit
        for i in range(10):
            mr = ModelRun(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                sku="ALL",
                model_name="ARIMA",
                model_version="1.0.0",
                created_at=now
            )
            db.add(mr)
        db.commit()

        # Attempt to train model -> 402 Payment Required
        res = client.post("/api/v1/ml/train?sku=ALL", headers=headers)
        assert res.status_code == 402, res.text
        assert "Monthly forecast quota reached" in res.json()["detail"]
    finally:
        db.close()

def test_owner_can_cancel_subscription():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_for_subscription(db, tier="PRO", prefix="sub_cancel")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.post(f"/api/v1/organizations/{tenant.id}/subscription/cancel", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "success"

        # Check tenant in DB
        db.refresh(tenant)
        assert tenant.subscription_status == "CANCELED"
    finally:
        db.close()

