#!/usr/bin/env python3
"""
Script de Setup Automático - DIA 2
Plataforma de Assinaturas de E-mail
Cria todos os arquivos necessários para Autenticação JWT e Multi-Tenancy
"""

import os
from pathlib import Path

# Definir diretório base
BASE_DIR = Path.home() / "Pessoais" / "signatures-platform"

def create_file(filepath, content):
    """Cria um arquivo com o conteúdo especificado"""
    full_path = BASE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Criado: {filepath}")

def main():
    print("🚀 Iniciando Setup do DIA 2...")
    print("=" * 50)
    
    # Verificar se está no diretório correto
    if not BASE_DIR.exists():
        print(f"❌ Erro: Diretório {BASE_DIR} não encontrado!")
        print("Execute: mkdir -p ~/Pessoais/signatures-platform")
        return
    
    os.chdir(BASE_DIR)
    
    # Criar diretórios necessários
    print("\n📁 Criando estrutura de diretórios...")
    dirs = [
        "app/schemas",
        "app/services",
        "app/api/v1",
        "alembic/versions"
    ]
    
    for dir_path in dirs:
        (BASE_DIR / dir_path).mkdir(parents=True, exist_ok=True)
        # Criar __init__.py se necessário
        if dir_path.startswith("app/"):
            init_file = BASE_DIR / dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("\n📝 Criando arquivos Python...")
    
    # ARQUIVO 1: models.py
    create_file("app/db/models.py", '''from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    settings = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    users = relationship("User", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    phone = Column(String(50), nullable=True)
    job_title = Column(String(255), nullable=True)
    
    avatar_url = Column(String(500), nullable=True)
    
    google_sub = Column(String(255), unique=True, nullable=True, index=True)
    google_refresh_token_encrypted = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
''')

    # ARQUIVO 2: schemas/user.py
    create_file("app/schemas/user.py", '''from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.db.models import UserRole, UserStatus


# ===== USER SCHEMAS =====

class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    organization_name: str
    organization_slug: str = Field(..., pattern="^[a-z0-9-]+$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    organization_id: int
    department_id: Optional[int] = None
    role: UserRole
    status: UserStatus
    phone: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


# ===== ORGANIZATION SCHEMAS =====

class OrganizationBase(BaseModel):
    name: str
    slug: str = Field(..., pattern="^[a-z0-9-]+$")
    domain: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: int
    logo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== MEMBER INVITATION SCHEMAS =====

class MemberInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.MEMBER
    department_id: Optional[int] = None
    job_title: Optional[str] = None


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department_id: Optional[int] = None
    job_title: Optional[str] = None
    status: Optional[UserStatus] = None


class MemberActivation(BaseModel):
    password: str = Field(..., min_length=8)
''')

    # ARQUIVO 3: services/security.py
    create_file("app/services/security.py", '''from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
''')

    # ARQUIVO 4: services/auth_service.py
    create_file("app/services/auth_service.py", '''from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import redis

from app.db.models import User, Organization, UserRole, UserStatus
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.security import hash_password, verify_password, create_access_token, create_refresh_token


def register_user(db: Session, user_create: UserCreate) -> TokenResponse:
    """Register a new user and create organization"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if organization slug already exists
    existing_org = db.query(Organization).filter(
        Organization.slug == user_create.organization_slug
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already taken"
        )
    
    # Create organization
    organization = Organization(
        name=user_create.organization_name,
        slug=user_create.organization_slug
    )
    db.add(organization)
    db.flush()
    
    # Create user (owner)
    hashed_pwd = hash_password(user_create.password)
    user = User(
        organization_id=organization.id,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_pwd,
        role=UserRole.OWNER,
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": organization.id, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )


def login_user(db: Session, user_login: UserLogin) -> TokenResponse:
    """Authenticate user and return tokens"""
    
    # Find user
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": user.organization_id, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )


def invalidate_token(redis_client: redis.Redis, token: str, exp: datetime):
    """Add token to blacklist"""
    ttl = int((exp - datetime.utcnow()).total_seconds())
    if ttl > 0:
        redis_client.setex(f"blacklist:{token}", ttl, "1")


def is_token_blacklisted(redis_client: redis.Redis, token: str) -> bool:
    """Check if token is blacklisted"""
    return redis_client.exists(f"blacklist:{token}") > 0
''')

    # ARQUIVO 5: api/deps.py
    create_file("app/api/deps.py", '''from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import redis

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.db.models import User, UserRole
from app.services.security import decode_token
from app.services.auth_service import is_token_blacklisted

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> User:
    """Get current authenticated user"""
    
    token = credentials.credentials
    
    # Check if token is blacklisted
    if is_token_blacklisted(redis_client, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def require_role(required_roles: list[UserRole]):
    """Dependency to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
''')

    # ARQUIVO 6: api/v1/auth.py
    create_file("app/api/v1/auth.py", '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.schemas.user import UserCreate, UserLogin, TokenResponse, TokenRefresh, User
from app.services.auth_service import register_user, login_user, invalidate_token
from app.services.security import decode_token, create_access_token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and organization"""
    return register_user(db, user_create)


@router.post("/login", response_model=TokenResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""
    return login_user(db, user_login)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Decode refresh token
    payload = decode_token(token_refresh.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    from app.db.models import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": user.organization_id, "role": user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=token_refresh.refresh_token,
        expires_in=1800
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Logout and invalidate token"""
    # Token blacklisting is handled in get_current_user
    return None


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
''')

    # ARQUIVO 7: api/v1/organizations.py
    create_file("app/api/v1/organizations.py", '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Organization, UserRole
from app.schemas.user import OrganizationResponse, OrganizationUpdate
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization"""
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


@router.patch("/me", response_model=OrganizationResponse)
def update_my_organization(
    organization_update: OrganizationUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update current user's organization (admin/owner only)"""
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    if organization_update.name is not None:
        organization.name = organization_update.name
    if organization_update.domain is not None:
        organization.domain = organization_update.domain
    if organization_update.logo_url is not None:
        organization.logo_url = organization_update.logo_url
    
    db.commit()
    db.refresh(organization)
    
    return organization
''')

    # ARQUIVO 8: api/v1/members.py
    create_file("app/api/v1/members.py", '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, UserRole, UserStatus
from app.schemas.user import MemberInvite, MemberUpdate, User as UserSchema
from app.api.deps import get_current_user, require_role
from app.services.security import hash_password

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
def list_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of the organization"""
    members = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).all()
    
    return members


@router.post("/invite", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def invite_member(
    member_invite: MemberInvite,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Invite a new member to the organization (admin/owner only)"""
    
    # Check if email already exists in organization
    existing_user = db.query(User).filter(
        User.email == member_invite.email,
        User.organization_id == current_user.organization_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists in this organization"
        )
    
    # Create pending user with temporary password
    temp_password = hash_password("temporary_password_change_me")
    
    new_user = User(
        organization_id=current_user.organization_id,
        email=member_invite.email,
        full_name=member_invite.full_name,
        hashed_password=temp_password,
        role=member_invite.role,
        status=UserStatus.PENDING,
        department_id=member_invite.department_id,
        job_title=member_invite.job_title
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # TODO: Send invitation email
    
    return new_user


@router.patch("/{user_id}", response_model=UserSchema)
def update_member(
    user_id: int,
    member_update: MemberUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a member's information (admin/owner only)"""
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent owner from being modified (except by themselves)
    if user.role == UserRole.OWNER and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify organization owner"
        )
    
    # Update fields
    if member_update.full_name is not None:
        user.full_name = member_update.full_name
    if member_update.role is not None:
        user.role = member_update.role
    if member_update.department_id is not None:
        user.department_id = member_update.department_id
    if member_update.job_title is not None:
        user.job_title = member_update.job_title
    if member_update.status is not None:
        user.status = member_update.status
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization (admin/owner only)"""
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent owner from being deleted
    if user.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete organization owner"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return None
''')

    # ARQUIVO 9: Atualizar main.py
    create_file("app/main.py", '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import test_db_connection
from app.db.redis_client import test_redis_connection

# Import routers
from app.api.v1 import auth, organizations, members


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")
    yield
    print("🛑 Shutting down application...")


app = FastAPI(
    title="Signatures Platform API",
    description="Dynamic Email Signatures & Banners Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])


@app.get("/health")
async def health_check():
    status = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown"
    }
    
    try:
        test_db_connection()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "error"
    
    try:
        test_redis_connection()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "error"
    
    if status["status"] == "error":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=status)
    
    return status


@app.get("/")
async def root():
    return {
        "message": "Signatures Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }
''')

    print("\n📝 Criando arquivos de configuração do Alembic...")
    
    # ARQUIVO 10: alembic.ini
    create_file("alembic.ini", '''[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = mysql+pymysql://signatures_user:signatures_pass@db:3306/signatures_db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
''')

    # ARQUIVO 11: alembic/env.py
    create_file("alembic/env.py", '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import Base and models
from app.db.session import Base
from app.db.models import *  # Import all models
from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
''')

    # ARQUIVO 12: alembic/script.py.mako
    create_file("alembic/script.py.mako", '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
''')

    # ARQUIVO 13: Migration inicial
    create_file("alembic/versions/001_initial_schema.py", '''"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.create_index(op.f('ix_organizations_domain'), 'organizations', ['domain'], unique=True)

    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', name='userrole'), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', 'pending', name='userstatus'), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('google_sub', sa.String(length=255), nullable=True),
        sa.Column('google_refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('departments')
    op.drop_index(op.f('ix_organizations_domain'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
''')

    print("\n" + "=" * 50)
    print("✅ Todos os arquivos criados com sucesso!")
    print("=" * 50)
    
    print("\n📋 Próximos passos:")
    print("1. Aplicar migrations no banco de dados:")
    print("   cd ~/Pessoais/signatures-platform")
    print("   sudo docker-compose exec api alembic upgrade head")
    print()
    print("2. Reiniciar a API:")
    print("   sudo docker-compose restart api")
    print()
    print("3. Testar os novos endpoints:")
    print("   curl http://localhost/docs")
    print()
    print("4. Verificar tabelas criadas:")
    print("   sudo docker-compose exec db mysql -u signatures_user -psignatures_pass signatures_db -e 'SHOW TABLES;'")
    print()
    print("🎉 DIA 2 - Setup completo!")


if __name__ == "__main__":
    main()
