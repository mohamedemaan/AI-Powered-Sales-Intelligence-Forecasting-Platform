import io
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.models.data import RawSalesData
from app.core import security

client = TestClient(app)
PRECOMPUTED_HASH = security.get_password_hash("SecretPass123!")

def create_workspace_and_user_with_role(db, role="VIEWER", prefix="rbac_user"):
    uid = uuid.uuid4()
    email = f"{prefix}_{uid.hex[:6]}@enterprise.com"
    user = User(
        id=uid,
        email=email,
        username=f"user_{uid.hex[:6]}",
        full_name=f"RBAC {prefix.capitalize()}",
        password_hash=PRECOMPUTED_HASH,
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(
        name=f"Workspace for {prefix}",
        owner_id=user.id if role == "OWNER" else None,
        subscription_tier="PRO",
        subscription_status="ACTIVE"
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

def test_viewer_forbidden_from_upload_data():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="VIEWER", prefix="viewer_up")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        csv_content = b"date,sku,units_sold\n2026-03-01,SKU-1001,10\n"
        res = client.post(
            "/api/v1/data/upload",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            headers=headers
        )
        assert res.status_code == 403, res.text
        assert "Permission denied" in res.json()["detail"]
    finally:
        db.close()

def test_viewer_forbidden_from_clean_duplicates():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="VIEWER", prefix="viewer_clean")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.post("/api/v1/data/clean-duplicates", headers=headers)
        assert res.status_code == 403, res.text
        assert "Permission denied" in res.json()["detail"]
    finally:
        db.close()

def test_viewer_forbidden_from_reset_data():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="VIEWER", prefix="viewer_reset")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.post("/api/v1/data/reset", headers=headers)
        assert res.status_code == 403, res.text
        assert "Permission denied" in res.json()["detail"]
    finally:
        db.close()

def test_viewer_forbidden_from_train_model():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="VIEWER", prefix="viewer_train")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.post("/api/v1/ml/train?sku=ALL", headers=headers)
        assert res.status_code == 403, res.text
        assert "Permission denied" in res.json()["detail"]
    finally:
        db.close()

def test_viewer_allowed_read_status_and_preview():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="VIEWER", prefix="viewer_read")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        status_res = client.get("/api/v1/data/status", headers=headers)
        assert status_res.status_code == 200, status_res.text
        assert status_res.json()["organization_id"] == str(tenant.id)

        preview_res = client.get("/api/v1/data/preview", headers=headers)
        assert preview_res.status_code == 200, preview_res.text
    finally:
        db.close()

def test_analyst_can_upload_and_train():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="ANALYST", prefix="analyst_ok")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        csv_content = b"date,sku,product_name,category,units_sold,price,total_sales,profit\n2026-03-01,SKU-A1,Test Item,Technology,5,20.0,100.0,25.0\n"
        upload_res = client.post(
            "/api/v1/data/upload",
            files={"file": ("analyst_test.csv", io.BytesIO(csv_content), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 200, upload_res.text
        assert upload_res.json()["status"] == "success"
    finally:
        db.close()

def test_analyst_forbidden_from_managing_team():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="ANALYST", prefix="analyst_no_mgmt")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": "victim@test.com", "role": "MEMBER"},
            headers=headers
        )
        assert res.status_code == 403, res.text
    finally:
        db.close()

def test_admin_forbidden_from_delete_workspace():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="ADMIN", prefix="admin_no_del")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        res = client.delete(f"/api/v1/organizations/{tenant.id}", headers=headers)
        assert res.status_code == 403, res.text
        assert "Only an organization Owner can delete this workspace" in res.json()["detail"]
    finally:
        db.close()

def test_owner_can_update_and_delete_workspace():
    db = SessionLocal()
    try:
        user, tenant, token = create_workspace_and_user_with_role(db, role="OWNER", prefix="owner_lifecycle")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        # Update
        patch_res = client.patch(
            f"/api/v1/organizations/{tenant.id}",
            json={"name": "Renamed Global Enterprise"},
            headers=headers
        )
        assert patch_res.status_code == 200, patch_res.text
        assert patch_res.json()["name"] == "Renamed Global Enterprise"

        # Delete
        del_res = client.delete(f"/api/v1/organizations/{tenant.id}", headers=headers)
        assert del_res.status_code == 200, del_res.text
        assert del_res.json()["status"] == "success"

        # Verify tenant is gone
        t_check = db.query(Tenant).filter(Tenant.id == tenant.id).first()
        assert t_check is None
    finally:
        db.close()

def test_cross_tenant_idor_prevention():
    db = SessionLocal()
    try:
        user_a, tenant_a, token_a = create_workspace_and_user_with_role(db, role="ANALYST", prefix="tenant_a_user")
        user_b, tenant_b, token_b = create_workspace_and_user_with_role(db, role="OWNER", prefix="tenant_b_user")

        # User A tries to pass Tenant B's ID in X-Organization-ID header
        malicious_headers = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(tenant_b.id)}

        res = client.get("/api/v1/data/status", headers=malicious_headers)
        assert res.status_code == 403, res.text
        assert "Access denied: You are not an authorized member of this organization workspace" in res.json()["detail"]
    finally:
        db.close()

