from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization or company name")
    slug: Optional[str] = Field(None, max_length=100, description="Unique workspace slug")

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)
    metadata_json: Optional[Dict[str, Any]] = None

class OrganizationMemberResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: Optional[str] = None
    owner_id: Optional[UUID] = None
    subscription_tier: str = "FREE"
    subscription_status: str = "ACTIVE"
    created_at: datetime
    role: Optional[str] = "MEMBER"
    is_active: bool = False
    members_count: int = 1
    model_config = ConfigDict(from_attributes=True)

class OrganizationSwitchRequest(BaseModel):
    organization_id: UUID

class InvitationCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="Invitee email address")
    role: str = Field("MEMBER", description="Assigned role: ADMIN, ANALYST, VIEWER, MEMBER")

class InvitationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by_name: Optional[str] = None
    invitation_link: Optional[str] = None
    development_mode_note: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class InvitationVerifyResponse(BaseModel):
    organization_name: str
    organization_id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    is_valid: bool
    message: Optional[str] = None

class InvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Invitation token")

class MemberRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="New role: OWNER, ADMIN, ANALYST, VIEWER, MEMBER")

class MemberActionResponse(BaseModel):
    status: str
    message: str


