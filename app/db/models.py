from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


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
    
    users = relationship("User", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    signature_templates = relationship("SignatureTemplate", back_populates="organization", cascade="all, delete-orphan")
    banners = relationship("Banner", back_populates="organization", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
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
    
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    signatures = relationship("Signature", back_populates="user", cascade="all, delete-orphan")


class SignatureTemplate(Base):
    __tablename__ = "signature_templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    html_template = Column(Text, nullable=False)
    css_styles = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    organization = relationship("Organization", back_populates="signature_templates")
    signatures = relationship("Signature", back_populates="template")


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("signature_templates.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String(255), nullable=False)
    custom_data = Column(JSON, nullable=True)
    html_content = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="signatures")
    template = relationship("SignatureTemplate", back_populates="signatures")


class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    image_url = Column(String(500), nullable=False)
    target_url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    
    # Programação
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Segmentação
    target_departments = Column(JSON, nullable=True)  # Lista de department_ids
    target_users = Column(JSON, nullable=True)  # Lista de user_ids
    
    # Stats
    views_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    organization = relationship("Organization", back_populates="banners")
    clicks = relationship("BannerClick", back_populates="banner", cascade="all, delete-orphan")


class BannerClick(Base):
    __tablename__ = "banner_clicks"

    id = Column(Integer, primary_key=True, index=True)
    banner_id = Column(Integer, ForeignKey("banners.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Tracking info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referer = Column(String(500), nullable=True)
    
    banner = relationship("Banner", back_populates="clicks")