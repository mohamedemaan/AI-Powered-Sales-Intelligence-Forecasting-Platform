import pytest
from fastapi.testclient import TestClient
import uuid
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.models.data import RawSalesData
from app.core import security
from datetime import date

client = TestClient(app)

def create_test_user_and_token(db, email_prefix="user"):
    unique_id = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique_id}@example.com"
    username = f"{email_prefix}_{unique_id}"
    password = "StrongPassword123!"
    hashed = security.get_password_hash(password)
    
    user = User(
        email=email,
        username=username,
        full_name=f"Test {email_prefix.capitalize()}",
        password_hash=hashed,
        role=UserRole.ANALYST,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = security.create_access_token(user.id)
    return user, token

def test_create_organization_assigns_owner():
    db = SessionLocal()
    try:
        user, token = create_test_user_and_token(db, "org_creator")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = client.post(
            "/api/v1/organizations",
            headers=headers,
            json={"name": "Acme Global Enterprise", "slug": f"acme-{uuid.uuid4().hex[:6]}"}
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["name"] == "Acme Global Enterprise"
        assert data["role"] == "OWNER"
        assert data["is_active"] is True
        assert data["members_count"] == 1
        
        # Verify database record
        tenant_id = uuid.UUID(data["id"])
        member = db.query(TenantMember).filter(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user.id
        ).first()
        assert member is not None
        assert member.role == TenantMemberRole.OWNER.value
    finally:
        db.close()

def test_list_organizations_shows_memberships():
    db = SessionLocal()
    try:
        user, token = create_test_user_and_token(db, "list_user")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Org 1
        res1 = client.post("/api/v1/organizations", headers=headers, json={"name": "Org Alpha"})
        assert res1.status_code == 200
        org1_id = res1.json()["id"]
        
        # Create Org 2
        res2 = client.post("/api/v1/organizations", headers=headers, json={"name": "Org Beta"})
        assert res2.status_code == 200
        org2_id = res2.json()["id"]
        
        # List organizations
        list_res = client.get("/api/v1/organizations", headers=headers)
        assert list_res.status_code == 200
        orgs = list_res.json()
        
        org_ids = [o["id"] for o in orgs]
        assert org1_id in org_ids
        assert org2_id in org_ids
    finally:
        db.close()

def test_switch_organization_updates_active_context():
    db = SessionLocal()
    try:
        user, token = create_test_user_and_token(db, "switch_user")
        headers = {"Authorization": f"Bearer {token}"}
        
        res1 = client.post("/api/v1/organizations", headers=headers, json={"name": "First Workspace"})
        org1_id = res1.json()["id"]
        
        res2 = client.post("/api/v1/organizations", headers=headers, json={"name": "Second Workspace"})
        org2_id = res2.json()["id"]
        
        # User's currently active workspace is Org 2 (most recently created)
        active_res = client.get("/api/v1/organizations/active", headers=headers)
        assert active_res.status_code == 200
        assert active_res.json()["id"] == org2_id
        
        # Switch back to Org 1
        switch_res = client.post(
            "/api/v1/organizations/switch",
            headers=headers,
            json={"organization_id": org1_id}
        )
        assert switch_res.status_code == 200
        assert switch_res.json()["id"] == org1_id
        
        # Verify active context
        active_res2 = client.get("/api/v1/organizations/active", headers=headers)
        assert active_res2.status_code == 200
        assert active_res2.json()["id"] == org1_id
    finally:
        db.close()

def test_switch_organization_unauthorized_blocked():
    db = SessionLocal()
    try:
        user_a, token_a = create_test_user_and_token(db, "user_a")
        user_b, token_b = create_test_user_and_token(db, "user_b")
        
        # User A creates Org A
        res_a = client.post("/api/v1/organizations", headers={"Authorization": f"Bearer {token_a}"}, json={"name": "Org A Private"})
        org_a_id = res_a.json()["id"]
        
        # User B attempts to switch to Org A without membership
        switch_unauthorized = client.post(
            "/api/v1/organizations/switch",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"organization_id": org_a_id}
        )
        assert switch_unauthorized.status_code == 403
        assert "Access denied" in switch_unauthorized.json()["detail"]
    finally:
        db.close()

def test_tenant_resource_isolation_sales_data():
    db = SessionLocal()
    try:
        user_a, token_a = create_test_user_and_token(db, "iso_a")
        user_b, token_b = create_test_user_and_token(db, "iso_b")
        
        res_a = client.post("/api/v1/organizations", headers={"Authorization": f"Bearer {token_a}"}, json={"name": "Org Isolation A"})
        org_a_id = uuid.UUID(res_a.json()["id"])
        
        res_b = client.post("/api/v1/organizations", headers={"Authorization": f"Bearer {token_b}"}, json={"name": "Org Isolation B"})
        org_b_id = uuid.UUID(res_b.json()["id"])
        
        # Directly insert 2 transaction records stamped with Org A's tenant_id
        rec1 = RawSalesData(
            tenant_id=org_a_id,
            date=date(2026, 1, 1),
            order_id="ORD-ISO-A1",
            sku="SKU-ISO-A",
            product_name="Product Alpha",
            category="Technology",
            units_sold=10,
            price=100.0,
            total_sales=1000.0,
            profit=250.0,
            status="PROCESSED"
        )
        rec2 = RawSalesData(
            tenant_id=org_a_id,
            date=date(2026, 1, 2),
            order_id="ORD-ISO-A2",
            sku="SKU-ISO-A",
            product_name="Product Alpha",
            category="Technology",
            units_sold=5,
            price=100.0,
            total_sales=500.0,
            profit=125.0,
            status="PROCESSED"
        )
        db.add_all([rec1, rec2])
        db.commit()
        
        # Query preview under Org A
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(org_a_id)}
        preview_a = client.get("/api/v1/data/preview", headers=headers_a)
        assert preview_a.status_code == 200
        assert preview_a.json()["row_count"] == 2
        
        # Query preview under Org B (must show 0 records - total data isolation!)
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": str(org_b_id)}
        preview_b = client.get("/api/v1/data/preview", headers=headers_b)
        assert preview_b.status_code == 200
        assert preview_b.json()["row_count"] == 0
    finally:
        db.close()

