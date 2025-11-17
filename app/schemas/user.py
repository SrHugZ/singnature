from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str
    organization_slug: str
    job_title: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    custom_data: Optional[dict] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class User(BaseModel):
    id: int
    organization_id: int
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    phone: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Convert role to uppercase if it's a string"""
        if isinstance(v, str):
            return v.upper()
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Convert status to uppercase if it's a string"""
        if isinstance(v, str):
            return v.upper()
        return v

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    organization_id: int
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    phone: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Convert role to uppercase if it's a string"""
        if isinstance(v, str):
            return v.upper()
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Convert status to uppercase if it's a string"""
        if isinstance(v, str):
            return v.upper()
        return v

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None


class MemberInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.MEMBER
    department_id: Optional[int] = None


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    department_id: Optional[int] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
