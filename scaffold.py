import os

files = {
    "backend/requirements.txt": """fastapi[all]==0.103.2
uvicorn[standard]==0.23.2
sqlalchemy==2.0.21
asyncpg==0.28.0
psycopg2-binary==2.9.9
alembic==1.12.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
pydantic[email]==2.4.2
pydantic-settings==2.0.3
pytest==7.4.2
httpx==0.25.0
""",
    
    "backend/.env.example": """PROJECT_NAME="Sales Intelligence Platform API"
API_V1_STR="/api/v1"
SECRET_KEY="YOUR_SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

POSTGRES_SERVER="localhost"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="password"
POSTGRES_DB="sales_intel"
POSTGRES_PORT="5432"
""",

    "backend/database_schema.sql": """-- SQL Schema Representation (also generated via SQLAlchemy)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'ANALYST',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID REFERENCES categories(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id),
    sku VARCHAR(100) UNIQUE NOT NULL,
    attributes JSONB,
    price_adjustment DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id),
    variant_id UUID REFERENCES product_variants(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    variant_id UUID REFERENCES product_variants(id),
    quantity_change INT NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    variant_id UUID REFERENCES product_variants(id),
    snapshot_date DATE NOT NULL,
    quantity_on_hand INT NOT NULL,
    UNIQUE(variant_id, snapshot_date)
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
""",

    "backend/app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base

# Create tables for testing/local dev (In production, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}
""",

    "backend/app/core/config.py": """from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sales Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
""",

    "backend/app/core/security.py": """from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
""",

    "backend/app/db/session.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
""",

    "backend/app/db/base.py": """from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
""",

    "backend/app/models/user.py": """from sqlalchemy import Column, String, Boolean, Enum
from app.db.base import BaseModel
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    MANAGER = "MANAGER"

class User(BaseModel):
    __tablename__ = "users"
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True)
""",

    "backend/app/models/product.py": """from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    products = relationship("Product", back_populates="category")

class Product(BaseModel):
    __tablename__ = "products"
    category_id = Column(ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_price = Column(Numeric(10, 2), nullable=False)
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")

class ProductVariant(BaseModel):
    __tablename__ = "product_variants"
    product_id = Column(ForeignKey("products.id"))
    sku = Column(String(100), unique=True, nullable=False)
    attributes = Column(JSONB)
    price_adjustment = Column(Numeric(10, 2), default=0)
    product = relationship("Product", back_populates="variants")
""",

    "backend/app/models/order.py": """from sqlalchemy import Column, String, Numeric, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Order(BaseModel):
    __tablename__ = "orders"
    user_id = Column(ForeignKey("users.id"))
    status = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User")

class OrderItem(BaseModel):
    __tablename__ = "order_items"
    order_id = Column(ForeignKey("orders.id"))
    variant_id = Column(ForeignKey("product_variants.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")
""",

    "backend/app/schemas/user.py": """from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole
import re

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    role: UserRole = UserRole.ANALYST

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def password_strong(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r"[\W_]", v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
""",

    "backend/app/schemas/token.py": """from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str = None
""",

    "backend/app/schemas/product.py": """from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float

class ProductCreate(ProductBase):
    category_id: Optional[UUID] = None

class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
""",

    "backend/app/schemas/order.py": """from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class OrderItemCreate(BaseModel):
    variant_id: UUID
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    user_id: UUID
    status: str
    total_amount: float
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    total_amount: float
    created_at: datetime
    class Config:
        from_attributes = True
""",

    "backend/app/api/deps.py": """from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.id == UUID(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
""",

    "backend/app/api/v1/api.py": """from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, products, orders

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
""",

    "backend/app/api/v1/endpoints/auth.py": """from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from sqlalchemy.exc import IntegrityError

router = APIRouter()

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
            detail="The user with this username already exists in the system",
        )
    
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
""",

    "backend/app/api/v1/endpoints/users.py": """from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return current_user
""",

    "backend/app/api/v1/endpoints/products.py": """from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ProductResponse)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_active_admin)
) -> Any:
    db_product = Product(**product_in.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    products = db.query(Product).offset(skip).limit(limit).all()
    return products
""",

    "backend/app/api/v1/endpoints/orders.py": """from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse
from app.models.user import User

router = APIRouter()

@router.post("", response_model=OrderResponse)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: OrderCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    db_order = Order(
        user_id=order_in.user_id,
        status=order_in.status,
        total_amount=order_in.total_amount
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    # Order items not processed for simplicity of the example
    return db_order

@router.get("", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # Allow admin to see all, normal user only their own
    if current_user.role == "ADMIN":
        orders = db.query(Order).offset(skip).limit(limit).all()
    else:
        orders = db.query(Order).filter(Order.user_id == current_user.id).offset(skip).limit(limit).all()
    return orders
""",

    "backend/tests/test_auth.py": """from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
# Requires setting up a test DB instance to run real queries
""",

    "backend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app/backend

# Install required system packages
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
"""
}

def create_scaffold():
    for filepath, content in files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    create_scaffold()
    print("Scaffolding completed successfully!")
