from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from fastapi import Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class OAuth2PasswordRequestFormData:
    """
    Pydantic v2 / Python 3.12 compatible OAuth2 password request form dependency.
    """
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        grant_type: Optional[str] = Form(default="password"),
        scope: str = Form(default=""),
        client_id: Optional[str] = Form(default=None),
        client_secret: Optional[str] = Form(default=None),
    ):
        self.username = username
        self.password = password
        self.grant_type = grant_type
        self.scopes: List[str] = scope.split() if scope else []
        self.client_id = client_id
        self.client_secret = client_secret

@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )
    
    if user_in.username:
        existing_username = db.query(User).filter(User.username == user_in.username).first()
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="This username is already taken. Please choose another.",
            )
    
    from app.models.tenant import Tenant, TenantMember, TenantMemberRole

    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        username=user_in.username or user_in.email.split('@')[0],
        full_name=user_in.full_name,
        password_hash=hashed_password,
        role=user_in.role,
        is_active=user_in.is_active,
        tenant_id=user_in.tenant_id
    )
    db.add(db_user)
    db.flush()

    if user_in.tenant_id:
        # User joined an existing organization
        member = TenantMember(
            tenant_id=user_in.tenant_id,
            user_id=db_user.id,
            role=TenantMemberRole.MEMBER.value
        )
        db.add(member)
    else:
        # Create an initial company workspace for this user
        workspace_name = f"{(user_in.full_name or user_in.username or 'SalesMind')}'s Workspace"
        new_tenant = Tenant(
            name=workspace_name,
            owner_id=db_user.id,
            subscription_tier="FREE",
            subscription_status="ACTIVE"
        )
        db.add(new_tenant)
        db.flush()
        
        member = TenantMember(
            tenant_id=new_tenant.id,
            user_id=db_user.id,
            role=TenantMemberRole.OWNER.value
        )
        db.add(member)
        db_user.tenant_id = new_tenant.id

    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestFormData = Depends()
):
    user = db.query(User).filter(
        or_(User.email == form_data.username, User.username == form_data.username)
    ).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email, username, or password.")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account.")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
