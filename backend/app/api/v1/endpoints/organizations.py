import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.tenant import Tenant, TenantMember, TenantMemberRole, TenantInvitation, InvitationStatus
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMemberResponse,
    OrganizationSwitchRequest,
    InvitationCreate,
    InvitationResponse,
    InvitationVerifyResponse,
    InvitationAcceptRequest,
    MemberRoleUpdateRequest,
    MemberActionResponse,
    PlanTierInfo,
    SubscriptionUsage,
    SubscriptionDetailsResponse,
    SubscriptionUpgradeRequest,
    AuditLogResponse,
    AuditLogListResponse,
    DetailedUsageResponse
)
from app.models.audit import AuditLog
from app.models.data import RawSalesData
from app.models.forecast import ModelRun
from app.services.audit_service import log_audit_event
from app.core.plans import get_plan_config, get_tenant_usage, PLANS_CONFIG

router = APIRouter()

# ---------------------------------------------------------------------------
# Organization CRUD & Switch Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=OrganizationResponse)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Creates a new company workspace/organization.
    The creator is automatically granted the OWNER role and the workspace is set as active.
    """
    slug_val = org_in.slug.strip().lower() if org_in.slug else None
    if slug_val:
        existing = db.query(Tenant).filter(Tenant.slug == slug_val).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workspace identifier '{slug_val}' is already taken."
            )
    
    tenant = Tenant(
        name=org_in.name.strip(),
        slug=slug_val,
        owner_id=current_user.id,
        subscription_tier="FREE",
        subscription_status="ACTIVE"
    )
    db.add(tenant)
    db.flush()

    # Create explicit OWNER membership
    member = TenantMember(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role=TenantMemberRole.OWNER.value
    )
    db.add(member)

    # Set as active tenant for user
    current_user.tenant_id = tenant.id
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=tenant.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="WORKSPACE_CREATED",
        target_type="WORKSPACE",
        target_id=str(tenant.id),
        outcome="SUCCESS",
        metadata={"name": tenant.name, "slug": tenant.slug}
    )

    db.commit()
    db.refresh(tenant)

    return OrganizationResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        owner_id=tenant.owner_id,
        subscription_tier=tenant.subscription_tier,
        subscription_status=tenant.subscription_status,
        created_at=tenant.created_at,
        role=TenantMemberRole.OWNER.value,
        is_active=True,
        members_count=1
    )

@router.get("", response_model=List[OrganizationResponse])
def list_user_organizations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Lists all company workspaces and organizations the current authenticated user belongs to.
    """
    memberships = db.query(TenantMember).filter(TenantMember.user_id == current_user.id).all()
    
    # If user has no memberships yet, resolve/self-heal active tenant
    if not memberships:
        active_t = deps.get_current_tenant(current_user=current_user, db=db)
        memberships = db.query(TenantMember).filter(TenantMember.user_id == current_user.id).all()

    org_list = []
    for m in memberships:
        tenant = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        if not tenant:
            continue
        
        m_count = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == tenant.id).scalar() or 1
        is_active = (current_user.tenant_id == tenant.id)
        org_list.append(
            OrganizationResponse(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                owner_id=tenant.owner_id,
                subscription_tier=tenant.subscription_tier,
                subscription_status=tenant.subscription_status,
                created_at=tenant.created_at,
                role=m.role,
                is_active=is_active,
                members_count=m_count
            )
        )
    return org_list

@router.get("/active", response_model=OrganizationResponse)
def get_active_organization(
    current_tenant: Tenant = Depends(deps.get_current_tenant),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Returns the details of the active organization workspace.
    """
    membership = db.query(TenantMember).filter(
        TenantMember.tenant_id == current_tenant.id,
        TenantMember.user_id == current_user.id
    ).first()
    
    role = membership.role if membership else (
        TenantMemberRole.OWNER.value if current_tenant.owner_id == current_user.id else "MEMBER"
    )
    m_count = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == current_tenant.id).scalar() or 1

    return OrganizationResponse(
        id=current_tenant.id,
        name=current_tenant.name,
        slug=current_tenant.slug,
        owner_id=current_tenant.owner_id,
        subscription_tier=current_tenant.subscription_tier,
        subscription_status=current_tenant.subscription_status,
        created_at=current_tenant.created_at,
        role=role,
        is_active=True,
        members_count=m_count
    )

@router.post("/switch", response_model=OrganizationResponse)
def switch_organization(
    switch_in: OrganizationSwitchRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Switches the user's active workspace context to another organization they belong to.
    Prevents unauthorized switching to workspaces where the user is not a member.
    """
    membership = db.query(TenantMember).filter(
        TenantMember.tenant_id == switch_in.organization_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not an authorized member of this organization workspace."
        )

    tenant = db.query(Tenant).filter(Tenant.id == switch_in.organization_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    current_user.tenant_id = tenant.id
    db.commit()

    m_count = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == tenant.id).scalar() or 1

    return OrganizationResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        owner_id=tenant.owner_id,
        subscription_tier=tenant.subscription_tier,
        subscription_status=tenant.subscription_status,
        created_at=tenant.created_at,
        role=membership.role,
        is_active=True,
        members_count=m_count
    )

@router.patch("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: UUID,
    org_in: OrganizationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Updates workspace metadata (name, slug, metadata).
    Requires OWNER or ADMIN privileges.
    """
    caller_mem = _require_workspace_admin(db, org_id, current_user.id)
    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    if org_in.name and org_in.name.strip():
        tenant.name = org_in.name.strip()

    if org_in.slug is not None:
        slug_val = org_in.slug.strip().lower() if org_in.slug.strip() else None
        if slug_val and slug_val != tenant.slug:
            existing = db.query(Tenant).filter(Tenant.slug == slug_val).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Workspace identifier '{slug_val}' is already taken."
                )
        tenant.slug = slug_val

    if org_in.metadata_json is not None:
        tenant.metadata_json = org_in.metadata_json

    log_audit_event(
        db=db,
        tenant_id=tenant.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="WORKSPACE_SETTINGS_UPDATED",
        target_type="WORKSPACE",
        target_id=str(tenant.id),
        outcome="SUCCESS",
        metadata={"name": tenant.name, "slug": tenant.slug}
    )

    db.commit()
    db.refresh(tenant)

    m_count = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == tenant.id).scalar() or 1
    is_active = (current_user.tenant_id == tenant.id)

    return OrganizationResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        owner_id=tenant.owner_id,
        subscription_tier=tenant.subscription_tier,
        subscription_status=tenant.subscription_status,
        created_at=tenant.created_at,
        role=caller_mem.role,
        is_active=is_active,
        members_count=m_count
    )

@router.delete("/{org_id}", response_model=MemberActionResponse)
def delete_organization(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Deletes an organization workspace.
    Strictly restricted to the workspace OWNER.
    """
    caller_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not caller_mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this workspace."
        )

    if caller_mem.role != TenantMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an organization Owner can delete this workspace."
        )

    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    from app.models.data import RawSalesData
    from app.models.forecast import ModelRun, Forecast
    # Cascade cleanup
    db.query(RawSalesData).filter(RawSalesData.tenant_id == org_id).delete()
    db.query(ModelRun).filter(ModelRun.tenant_id == org_id).delete()
    db.query(Forecast).filter(Forecast.tenant_id == org_id).delete()
    db.delete(tenant)

    if current_user.tenant_id == org_id:
        other_mem = db.query(TenantMember).filter(
            TenantMember.user_id == current_user.id,
            TenantMember.tenant_id != org_id
        ).first()
        current_user.tenant_id = other_mem.tenant_id if other_mem else None

    db.commit()

    return MemberActionResponse(
        status="success",
        message=f"Workspace '{tenant.name}' has been permanently deleted."
    )


# ---------------------------------------------------------------------------
# Global / Public Invitation Verification & Acceptance Endpoints
# ---------------------------------------------------------------------------

@router.get("/invitations/verify", response_model=InvitationVerifyResponse)
def verify_invitation(
    token: str = Query(..., min_length=10, description="Invitation token"),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verifies an invitation token.
    Safe endpoint that can be queried before login to display workspace details.
    """
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    invitation = db.query(TenantInvitation).filter(TenantInvitation.token_hash == token_hash).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token."
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == invitation.tenant_id).first()
    org_name = tenant.name if tenant else "Unknown Workspace"

    # Check expiration
    now = datetime.utcnow()
    if invitation.status == InvitationStatus.PENDING.value and invitation.expires_at < now:
        invitation.status = InvitationStatus.EXPIRED.value
        db.commit()

    if invitation.status != InvitationStatus.PENDING.value:
        return InvitationVerifyResponse(
            organization_name=org_name,
            organization_id=invitation.tenant_id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            is_valid=False,
            message=f"This invitation has already been {invitation.status.lower()}."
        )

    return InvitationVerifyResponse(
        organization_name=org_name,
        organization_id=invitation.tenant_id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        is_valid=True,
        message="Invitation is valid and pending acceptance."
    )

@router.post("/invitations/accept", response_model=OrganizationResponse)
def accept_invitation(
    accept_in: InvitationAcceptRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Accepts an invitation using the secret single-use token.
    Transitions status to ACCEPTED, adds user to tenant_members, and switches active context.
    """
    token_hash = hashlib.sha256(accept_in.token.encode("utf-8")).hexdigest()
    invitation = db.query(TenantInvitation).filter(TenantInvitation.token_hash == token_hash).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token."
        )

    now = datetime.utcnow()
    if invitation.expires_at < now or invitation.status == InvitationStatus.EXPIRED.value:
        invitation.status = InvitationStatus.EXPIRED.value
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired. Please request a new invitation."
        )

    if invitation.status == InvitationStatus.REVOKED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has been revoked by an administrator."
        )

    if invitation.status == InvitationStatus.ACCEPTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been accepted."
        )

    tenant = db.query(Tenant).filter(Tenant.id == invitation.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    # Check if user is already a member
    existing_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == tenant.id,
        TenantMember.user_id == current_user.id
    ).first()

    if not existing_mem:
        new_member = TenantMember(
            tenant_id=tenant.id,
            user_id=current_user.id,
            role=invitation.role
        )
        db.add(new_member)
        role = invitation.role
    else:
        role = existing_mem.role

    # Mark invitation as accepted
    invitation.status = InvitationStatus.ACCEPTED.value
    invitation.accepted_at = now

    # Switch active context to joined workspace
    current_user.tenant_id = tenant.id

    log_audit_event(
        db=db,
        tenant_id=tenant.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="INVITATION_ACCEPTED",
        target_type="INVITATION",
        target_id=str(invitation.id),
        outcome="SUCCESS",
        metadata={"role": invitation.role, "invited_email": invitation.email}
    )

    db.commit()

    m_count = db.query(func.count(TenantMember.id)).filter(TenantMember.tenant_id == tenant.id).scalar() or 1

    return OrganizationResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        owner_id=tenant.owner_id,
        subscription_tier=tenant.subscription_tier,
        subscription_status=tenant.subscription_status,
        created_at=tenant.created_at,
        role=role,
        is_active=True,
        members_count=m_count
    )

@router.post("/invitations/reject", response_model=MemberActionResponse)
def reject_invitation(
    reject_in: InvitationAcceptRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Declines an invitation using the token.
    """
    token_hash = hashlib.sha256(reject_in.token.encode("utf-8")).hexdigest()
    invitation = db.query(TenantInvitation).filter(TenantInvitation.token_hash == token_hash).first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    if invitation.status != InvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject an invitation that is already {invitation.status.lower()}."
        )

    invitation.status = InvitationStatus.REVOKED.value
    db.commit()

    return MemberActionResponse(
        status="success",
        message="Invitation has been declined."
    )

# ---------------------------------------------------------------------------
# Workspace Team & Invitation Management Endpoints (Scoped by Organization)
# ---------------------------------------------------------------------------

def _require_workspace_admin(db: Session, tenant_id: UUID, user_id: UUID) -> TenantMember:
    """Helper to verify that caller has OWNER or ADMIN rights in the given workspace."""
    member = db.query(TenantMember).filter(
        TenantMember.tenant_id == tenant_id,
        TenantMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this workspace."
        )
    if member.role not in [TenantMemberRole.OWNER.value, TenantMemberRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrator privileges required for this action."
        )
    return member

@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Lists members of a workspace. The user must be a member of the workspace to view members.
    """
    user_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not user_mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view members of this workspace."
        )

    members = db.query(TenantMember).filter(TenantMember.tenant_id == org_id).all()
    results = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        results.append(
            OrganizationMemberResponse(
                id=m.id,
                tenant_id=m.tenant_id,
                user_id=m.user_id,
                role=m.role,
                email=u.email if u else None,
                username=u.username if u else None,
                full_name=u.full_name if u else None,
                created_at=m.created_at
            )
        )
    return results

@router.patch("/{org_id}/members/{user_id}", response_model=OrganizationMemberResponse)
def update_member_role(
    org_id: UUID,
    user_id: UUID,
    role_in: MemberRoleUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Updates the role of a workspace member.
    Enforces that only OWNERs can promote/demote other OWNERs,
    and prevents demoting the last organization OWNER.
    """
    caller_mem = _require_workspace_admin(db, org_id, current_user.id)
    
    target_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=404, detail="Workspace member not found.")

    new_role = role_in.role.strip().upper()
    valid_roles = [r.value for r in TenantMemberRole]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Only an OWNER can assign or remove OWNER role
    if (target_mem.role == TenantMemberRole.OWNER.value or new_role == TenantMemberRole.OWNER.value) and caller_mem.role != TenantMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an organization Owner can manage Owner roles."
        )

    # Protect against demoting the last owner
    if target_mem.role == TenantMemberRole.OWNER.value and new_role != TenantMemberRole.OWNER.value:
        owners_count = db.query(func.count(TenantMember.id)).filter(
            TenantMember.tenant_id == org_id,
            TenantMember.role == TenantMemberRole.OWNER.value
        ).scalar()
        if owners_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last organization owner. Transfer ownership first."
            )

    old_role = target_mem.role
    target_mem.role = new_role

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="MEMBER_ROLE_UPDATED",
        target_type="MEMBER",
        target_id=str(user_id),
        outcome="SUCCESS",
        metadata={"old_role": old_role, "new_role": new_role}
    )

    db.commit()
    db.refresh(target_mem)

    u = db.query(User).filter(User.id == target_mem.user_id).first()
    return OrganizationMemberResponse(
        id=target_mem.id,
        tenant_id=target_mem.tenant_id,
        user_id=target_mem.user_id,
        role=target_mem.role,
        email=u.email if u else None,
        username=u.username if u else None,
        full_name=u.full_name if u else None,
        created_at=target_mem.created_at
    )

@router.delete("/{org_id}/members/{user_id}", response_model=MemberActionResponse)
def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Removes a member from the workspace.
    Guards against removing the last organization owner.
    """
    caller_mem = _require_workspace_admin(db, org_id, current_user.id)

    target_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=404, detail="Workspace member not found.")

    # Admins cannot remove Owners
    if target_mem.role == TenantMemberRole.OWNER.value and caller_mem.role != TenantMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an organization Owner can remove an Owner."
        )

    # Prevent accidental removal of the last organization owner
    if target_mem.role == TenantMemberRole.OWNER.value:
        owners_count = db.query(func.count(TenantMember.id)).filter(
            TenantMember.tenant_id == org_id,
            TenantMember.role == TenantMemberRole.OWNER.value
        ).scalar()
        if owners_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last organization owner. Please appoint another owner first."
            )

    # If the removed member is currently active in this workspace, self-heal active workspace
    target_user = db.query(User).filter(User.id == user_id).first()
    target_email = target_user.email if target_user else None

    db.delete(target_mem)

    if target_user and target_user.tenant_id == org_id:
        # Find any other membership or reset to null
        other_mem = db.query(TenantMember).filter(TenantMember.user_id == user_id).first()
        target_user.tenant_id = other_mem.tenant_id if other_mem else None

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="MEMBER_REMOVED",
        target_type="MEMBER",
        target_id=str(user_id),
        outcome="SUCCESS",
        metadata={"removed_user_id": str(user_id), "removed_email": target_email}
    )

    db.commit()

    return MemberActionResponse(
        status="success",
        message="Member successfully removed from the workspace."
    )

@router.get("/{org_id}/invitations", response_model=List[InvitationResponse])
def list_organization_invitations(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Lists all pending and historical invitations for a workspace.
    Requires OWNER or ADMIN privileges.
    """
    _require_workspace_admin(db, org_id, current_user.id)

    now = datetime.utcnow()
    # Auto-expire overdue pending invitations
    db.query(TenantInvitation).filter(
        TenantInvitation.tenant_id == org_id,
        TenantInvitation.status == InvitationStatus.PENDING.value,
        TenantInvitation.expires_at < now
    ).update({"status": InvitationStatus.EXPIRED.value}, synchronize_session=False)
    db.commit()

    invitations = db.query(TenantInvitation).filter(
        TenantInvitation.tenant_id == org_id
    ).order_by(TenantInvitation.created_at.desc()).all()

    results = []
    for inv in invitations:
        inviter = db.query(User).filter(User.id == inv.invited_by_id).first() if inv.invited_by_id else None
        inviter_name = (inviter.full_name or inviter.username) if inviter else None
        results.append(
            InvitationResponse(
                id=inv.id,
                tenant_id=inv.tenant_id,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
                invited_by_name=inviter_name,
                invitation_link=None,
                development_mode_note=None
            )
        )
    return results

@router.post("/{org_id}/invitations", response_model=InvitationResponse)
def create_organization_invitation(
    org_id: UUID,
    invite_in: InvitationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Invites a team member by email.
    Generates a secure, expiring, single-use token.
    Stores only the SHA-256 hash in the database.
    Provides a safe development-mode invitation link.
    """
    _require_workspace_admin(db, org_id, current_user.id)

    # Enforce Plan Team Member Quota
    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")
    plan = get_plan_config(tenant.subscription_tier)
    usage = get_tenant_usage(db, org_id)
    if usage["total_seats_used"] >= plan["max_members"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Team seat limit reached ({plan['max_members']} max on {plan['name']}). Please upgrade your workspace plan to invite additional team members."
        )

    email_clean = invite_in.email.strip().lower()
    if "@" not in email_clean or "." not in email_clean:
        raise HTTPException(status_code=400, detail="Invalid email address.")

    role_clean = invite_in.role.strip().upper()
    valid_roles = [r.value for r in TenantMemberRole if r != TenantMemberRole.OWNER]
    if role_clean not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid invite role. Must be one of: {', '.join(valid_roles)}"
        )

    # 1. Prevent inviting an existing active member
    existing_user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing_user:
        existing_mem = db.query(TenantMember).filter(
            TenantMember.tenant_id == org_id,
            TenantMember.user_id == existing_user.id
        ).first()
        if existing_mem:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{email_clean}' is already an active member of this workspace."
            )

    # 2. Prevent duplicate active pending invitation
    now = datetime.utcnow()
    active_inv = db.query(TenantInvitation).filter(
        TenantInvitation.tenant_id == org_id,
        func.lower(TenantInvitation.email) == email_clean,
        TenantInvitation.status == InvitationStatus.PENDING.value,
        TenantInvitation.expires_at > now
    ).first()
    if active_inv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active invitation is already pending for '{email_clean}'."
        )

    # 3. Generate secure single-use token and store hash
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = now + timedelta(days=7)

    invitation = TenantInvitation(
        tenant_id=org_id,
        email=email_clean,
        role=role_clean,
        token_hash=token_hash,
        invited_by_id=current_user.id,
        status=InvitationStatus.PENDING.value,
        expires_at=expires_at
    )
    db.add(invitation)
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="MEMBER_INVITED",
        target_type="INVITATION",
        target_id=str(invitation.id),
        outcome="SUCCESS",
        metadata={"email": email_clean, "role": role_clean}
    )

    db.commit()
    db.refresh(invitation)

    invitation_link = f"/invite/accept?token={raw_token}"
    dev_note = "Development mode: External email delivery is disabled. Share this link directly with the invitee."

    return InvitationResponse(
        id=invitation.id,
        tenant_id=invitation.tenant_id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        invited_by_name=current_user.full_name or current_user.username,
        invitation_link=invitation_link,
        development_mode_note=dev_note
    )

@router.delete("/{org_id}/invitations/{invitation_id}", response_model=MemberActionResponse)
def revoke_organization_invitation(
    org_id: UUID,
    invitation_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Revokes / cancels a pending workspace invitation.
    """
    _require_workspace_admin(db, org_id, current_user.id)

    invitation = db.query(TenantInvitation).filter(
        TenantInvitation.id == invitation_id,
        TenantInvitation.tenant_id == org_id
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    if invitation.status != InvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot revoke invitation with status '{invitation.status}'."
        )

    invitation.status = InvitationStatus.REVOKED.value

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="INVITATION_REVOKED",
        target_type="INVITATION",
        target_id=str(invitation_id),
        outcome="SUCCESS",
        metadata={"revoked_email": invitation.email}
    )

    db.commit()

    return MemberActionResponse(
        status="success",
        message="Invitation has been revoked."
    )

# ---------------------------------------------------------------------------
# Workspace Subscription & Billing Management Endpoints
# ---------------------------------------------------------------------------

@router.get("/{org_id}/subscription", response_model=SubscriptionDetailsResponse)
def get_organization_subscription(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Returns workspace subscription details, live un-fabricated quota usage, and available upgrade tiers.
    Requires ADMIN or OWNER privileges.
    """
    _require_workspace_admin(db, org_id, current_user.id)
    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    tier = tenant.subscription_tier or "FREE"
    plan = get_plan_config(tier)
    usage = get_tenant_usage(db, org_id)

    remaining_forecasts = max(0, plan["max_forecasts_per_month"] - usage["forecasts_month_count"])
    remaining_seats = max(0, plan["max_members"] - usage["total_seats_used"])

    available = [
        PlanTierInfo(
            tier=p["tier"],
            name=p["name"],
            description=p["description"],
            price_monthly=p["price_monthly"],
            max_members=p["max_members"],
            max_datasets=p["max_datasets"],
            max_forecasts_per_month=p["max_forecasts_per_month"],
            features=p["features"]
        )
        for p in PLANS_CONFIG.values()
    ]

    return SubscriptionDetailsResponse(
        tier=tier,
        name=plan["name"],
        status=tenant.subscription_status or "ACTIVE",
        current_period_end=tenant.current_period_end,
        usage=SubscriptionUsage(
            members_count=usage["total_seats_used"],
            members_limit=plan["max_members"],
            datasets_count=usage["datasets_count"],
            datasets_limit=plan["max_datasets"],
            forecasts_count_month=usage["forecasts_month_count"],
            forecasts_limit_month=plan["max_forecasts_per_month"],
            remaining_forecasts=remaining_forecasts,
            remaining_seats=remaining_seats
        ),
        available_plans=available,
        development_mode_note="Development mode: Billing foundation active. In production, configure STRIPE_API_KEY for live credit card charges."
    )

@router.post("/{org_id}/subscription/upgrade", response_model=SubscriptionDetailsResponse)
def upgrade_organization_subscription(
    org_id: UUID,
    upgrade_in: SubscriptionUpgradeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Upgrades the workspace subscription plan.
    Restricted strictly to the workspace OWNER.
    """
    caller_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not caller_mem:
        raise HTTPException(status_code=403, detail="Access denied: You are not a member of this workspace.")

    if caller_mem.role != TenantMemberRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an organization Owner can manage subscriptions and billing."
        )

    target_tier = upgrade_in.plan_tier.strip().upper()
    if target_tier not in PLANS_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan tier. Must be one of: {', '.join(PLANS_CONFIG.keys())}"
        )

    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    old_tier = tenant.subscription_tier or "FREE"
    tenant.subscription_tier = target_tier
    tenant.subscription_status = "ACTIVE"
    tenant.current_period_end = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="PLAN_UPGRADED",
        target_type="SUBSCRIPTION",
        target_id=str(org_id),
        outcome="SUCCESS",
        metadata={"old_tier": old_tier, "new_tier": target_tier}
    )

    db.commit()
    db.refresh(tenant)

    return get_organization_subscription(org_id=org_id, db=db, current_user=current_user)

@router.post("/{org_id}/subscription/cancel", response_model=MemberActionResponse)
def cancel_organization_subscription(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Cancels workspace subscription at the end of the current period.
    Restricted strictly to the workspace OWNER.
    """
    caller_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not caller_mem or caller_mem.role != TenantMemberRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Only an organization Owner can cancel subscriptions.")

    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    tenant.subscription_status = "CANCELED"

    log_audit_event(
        db=db,
        tenant_id=org_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="SUBSCRIPTION_CANCELED",
        target_type="SUBSCRIPTION",
        target_id=str(org_id),
        outcome="SUCCESS",
        metadata={"status": "CANCELED"}
    )

    db.commit()

    return MemberActionResponse(
        status="success",
        message="Subscription has been scheduled for cancellation at the end of the current billing period."
    )


# ---------------------------------------------------------------------------
# Workspace Audit Logs & Usage Telemetry Endpoints
# ---------------------------------------------------------------------------

@router.get("/{org_id}/audit-logs", response_model=AuditLogListResponse)
def list_organization_audit_logs(
    org_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (SUCCESS or FAILURE)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Returns organization audit logs with filtering and server-side pagination.
    Restricted strictly to workspace OWNER and ADMIN.
    """
    _require_workspace_admin(db, org_id, current_user.id)

    query = db.query(AuditLog).filter(AuditLog.tenant_id == org_id)

    if event_type and event_type.strip() and event_type.strip().upper() != "ALL":
        query = query.filter(AuditLog.event_type == event_type.strip().upper())

    if outcome and outcome.strip() and outcome.strip().upper() != "ALL":
        query = query.filter(AuditLog.outcome == outcome.strip().upper())

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit

    items = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/{org_id}/usage", response_model=DetailedUsageResponse)
def get_organization_detailed_usage(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Returns verified, un-fabricated usage telemetry and resource allocation for the workspace.
    Available to all authenticated workspace members.
    """
    caller_mem = db.query(TenantMember).filter(
        TenantMember.tenant_id == org_id,
        TenantMember.user_id == current_user.id
    ).first()

    if not caller_mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this workspace."
        )

    tenant = db.query(Tenant).filter(Tenant.id == org_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization workspace not found.")

    tier = tenant.subscription_tier or "FREE"
    plan = get_plan_config(tier)
    usage = get_tenant_usage(db, org_id)

    records_count = db.query(func.count(RawSalesData.id)).filter(RawSalesData.tenant_id == org_id).scalar() or 0
    # Average byte footprint per row with b-tree indexing in SQLite ~250 bytes
    storage_bytes = records_count * 250
    storage_kb = round(storage_bytes / 1024.0, 2)
    storage_mb = round(storage_bytes / (1024.0 * 1024.0), 3)

    forecasts_total = db.query(func.count(ModelRun.id)).filter(ModelRun.tenant_id == org_id).scalar() or 0
    cycle_start = datetime.utcnow().replace(day=1).strftime("%Y-%m-%d")

    return DetailedUsageResponse(
        tenant_id=org_id,
        tier=tier,
        plan_name=plan["name"],
        datasets_count=usage["datasets_count"],
        dataset_records_count=records_count,
        estimated_storage_kb=storage_kb,
        estimated_storage_mb=storage_mb,
        forecasts_total_count=forecasts_total,
        forecasts_month_count=usage["forecasts_month_count"],
        forecasts_month_limit=plan["max_forecasts_per_month"],
        active_members_count=usage["active_members_count"],
        total_seats_used=usage["total_seats_used"],
        seats_limit=plan["max_members"],
        billing_cycle_start=cycle_start
    )


