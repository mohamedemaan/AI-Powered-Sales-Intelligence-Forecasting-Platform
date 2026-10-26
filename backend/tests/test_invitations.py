import pytest
import uuid
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole, TenantInvitation, InvitationStatus
from app.core import security

client = TestClient(app)
PRECOMPUTED_HASH = security.get_password_hash("SecretPass123!")

def create_user_with_token(db, email_prefix="inv_user", role="OWNER"):
    uid = uuid.uuid4()
    email = f"{email_prefix}_{uid.hex[:6]}@example.com"
    user = User(
        id=uid,
        email=email,
        username=f"user_{uid.hex[:6]}",
        full_name=f"Test User {uid.hex[:4]}",
        password_hash=PRECOMPUTED_HASH,
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(
        name=f"Workspace for {email_prefix}",
        owner_id=user.id,
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

def test_invite_member_and_verify_metadata():
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_with_token(db, "inv_owner")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        invitee_email = f"colleague_{uuid.uuid4().hex[:6]}@enterprise.com"
        res = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": invitee_email, "role": "ANALYST"},
            headers=headers
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["email"] == invitee_email
        assert data["role"] == "ANALYST"
        assert data["status"] == "PENDING"
        assert data["invitation_link"] is not None
        assert "token=" in data["invitation_link"]
        raw_token = data["invitation_link"].split("token=")[1]

        # Verify database does NOT store the raw token, only a 64-char hex hash
        inv_db = db.query(TenantInvitation).filter(TenantInvitation.id == uuid.UUID(data["id"])).first()
        assert inv_db is not None
        assert inv_db.token_hash != raw_token
        assert len(inv_db.token_hash) == 64

        # Verify endpoint returns valid metadata
        v_res = client.get(f"/api/v1/organizations/invitations/verify?token={raw_token}")
        assert v_res.status_code == 200, v_res.text
        v_data = v_res.json()
        assert v_data["is_valid"] is True
        assert v_data["organization_name"] == tenant.name
        assert v_data["email"] == invitee_email
        assert v_data["role"] == "ANALYST"
    finally:
        db.close()

def test_invite_duplicate_or_existing_member_blocked():
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_with_token(db, "dup_owner")
        headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(tenant.id)}

        target_email = f"target_{uuid.uuid4().hex[:6]}@test.com"
        res1 = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": target_email, "role": "VIEWER"},
            headers=headers
        )
        assert res1.status_code == 200

        # Duplicate pending invite should return 400
        res2 = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": target_email, "role": "ADMIN"},
            headers=headers
        )
        assert res2.status_code == 400
        assert "already pending" in res2.text

        # Attempting to invite the owner themselves should return 400
        res_owner = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": owner.email, "role": "MEMBER"},
            headers=headers
        )
        assert res_owner.status_code == 400
        assert "already an active member" in res_owner.text
    finally:
        db.close()

def test_accept_invitation_flow():
    db = SessionLocal()
    try:
        owner, tenant, owner_token = create_user_with_token(db, "accept_owner")
        headers = {"Authorization": f"Bearer {owner_token}"}

        invitee_user, _, invitee_token = create_user_with_token(db, "invitee_user")

        inv_res = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": invitee_user.email, "role": "ANALYST"},
            headers=headers
        )
        assert inv_res.status_code == 200
        raw_token = inv_res.json()["invitation_link"].split("token=")[1]

        # Invitee accepts invitation
        accept_headers = {"Authorization": f"Bearer {invitee_token}"}
        accept_res = client.post(
            "/api/v1/organizations/invitations/accept",
            json={"token": raw_token},
            headers=accept_headers
        )
        assert accept_res.status_code == 200, accept_res.text
        acc_data = accept_res.json()
        assert acc_data["id"] == str(tenant.id)
        assert acc_data["role"] == "ANALYST"
        assert acc_data["is_active"] is True

        # Verify membership in DB
        membership = db.query(TenantMember).filter(
            TenantMember.tenant_id == tenant.id,
            TenantMember.user_id == invitee_user.id
        ).first()
        assert membership is not None
        assert membership.role == "ANALYST"

        # Re-accepting should fail
        reaccept_res = client.post(
            "/api/v1/organizations/invitations/accept",
            json={"token": raw_token},
            headers=accept_headers
        )
        assert reaccept_res.status_code == 400
        assert "already been accepted" in reaccept_res.text
    finally:
        db.close()

def test_revoke_invitation():
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_with_token(db, "rev_owner")
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": f"rev_{uuid.uuid4().hex[:6]}@example.com", "role": "VIEWER"},
            headers=headers
        )
        assert res.status_code == 200
        inv_id = res.json()["id"]
        raw_token = res.json()["invitation_link"].split("token=")[1]

        rev_res = client.delete(
            f"/api/v1/organizations/{tenant.id}/invitations/{inv_id}",
            headers=headers
        )
        assert rev_res.status_code == 200

        _, _, other_token = create_user_with_token(db, "other_acc")
        fail_res = client.post(
            "/api/v1/organizations/invitations/accept",
            json={"token": raw_token},
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert fail_res.status_code == 400
        assert "revoked" in fail_res.text
    finally:
        db.close()

def test_prevent_removing_last_owner():
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_with_token(db, "sole_owner")
        headers = {"Authorization": f"Bearer {token}"}

        del_res = client.delete(
            f"/api/v1/organizations/{tenant.id}/members/{owner.id}",
            headers=headers
        )
        assert del_res.status_code == 400
        assert "Cannot remove the last organization owner" in del_res.text
    finally:
        db.close()

def test_update_member_role_and_owner_protection():
    db = SessionLocal()
    try:
        owner, tenant, token = create_user_with_token(db, "role_owner")
        headers = {"Authorization": f"Bearer {token}"}

        member_user, _, _ = create_user_with_token(db, "regular_mem")
        new_mem = TenantMember(
            tenant_id=tenant.id,
            user_id=member_user.id,
            role="VIEWER"
        )
        db.add(new_mem)
        db.commit()

        # Promote to ANALYST
        update_res = client.patch(
            f"/api/v1/organizations/{tenant.id}/members/{member_user.id}",
            json={"role": "ANALYST"},
            headers=headers
        )
        assert update_res.status_code == 200
        assert update_res.json()["role"] == "ANALYST"

        # Demote sole owner should fail
        demote_res = client.patch(
            f"/api/v1/organizations/{tenant.id}/members/{owner.id}",
            json={"role": "VIEWER"},
            headers=headers
        )
        assert demote_res.status_code == 400
        assert "Cannot demote the last organization owner" in demote_res.text
    finally:
        db.close()

def test_unauthorized_member_cannot_manage_team():
    db = SessionLocal()
    try:
        owner, tenant, _ = create_user_with_token(db, "org_boss")

        viewer_user, _, viewer_token = create_user_with_token(db, "org_viewer")
        v_mem = TenantMember(
            tenant_id=tenant.id,
            user_id=viewer_user.id,
            role="VIEWER"
        )
        db.add(v_mem)
        db.commit()

        viewer_headers = {"Authorization": f"Bearer {viewer_token}", "X-Organization-ID": str(tenant.id)}

        unauth_invite = client.post(
            f"/api/v1/organizations/{tenant.id}/invitations",
            json={"email": "newbie@corp.com", "role": "MEMBER"},
            headers=viewer_headers
        )
        assert unauth_invite.status_code == 403

        unauth_delete = client.delete(
            f"/api/v1/organizations/{tenant.id}/members/{owner.id}",
            headers=viewer_headers
        )
        assert unauth_delete.status_code == 403
    finally:
        db.close()
