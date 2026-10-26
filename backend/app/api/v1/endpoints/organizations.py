from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMemberResponse,
    OrganizationSwitchRequest
)

router = APIRouter()

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
    # Check if slug is requested and unique
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
    # Retrieve all memberships for this user
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
        
        # Count members in this workspace
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

@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    org_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Lists members of a workspace. The user must be a member of the workspace to view other members.
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

