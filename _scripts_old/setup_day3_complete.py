#!/usr/bin/env python3
"""
Script de Setup Automático - DIA 3
Sistema de Assinaturas de E-mail
- Templates de assinaturas
- Upload de imagens
- Variáveis dinâmicas
- Preview de assinaturas
"""

import os
from pathlib import Path

BASE_DIR = Path.home() / "Pessoais" / "signatures-platform"

def create_file(filepath, content):
    """Cria um arquivo com o conteúdo especificado"""
    full_path = BASE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Criado: {filepath}")

def main():
    print("🚀 Iniciando Setup do DIA 3...")
    print("=" * 50)
    
    if not BASE_DIR.exists():
        print(f"❌ Erro: Diretório {BASE_DIR} não encontrado!")
        return
    
    os.chdir(BASE_DIR)
    
    print("\n📝 Criando modelos de assinaturas...")
    
    # ARQUIVO 1: Atualizar models.py com Signature
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
    
    users = relationship("User", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    signature_templates = relationship("SignatureTemplate", back_populates="organization", cascade="all, delete-orphan")


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
    
    variables = Column(JSON, nullable=True)  # Lista de variáveis disponíveis
    
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
    
    # Dados customizados da assinatura
    custom_data = Column(JSON, nullable=True)
    
    # HTML final renderizado
    html_content = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="signatures")
    template = relationship("SignatureTemplate", back_populates="signatures")
''')

    # ARQUIVO 2: Schemas de assinaturas
    create_file("app/schemas/signature.py", '''from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime


# ===== SIGNATURE TEMPLATE SCHEMAS =====

class SignatureTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    html_template: str
    css_styles: Optional[str] = None
    variables: Optional[List[str]] = None
    is_default: bool = False
    is_active: bool = True


class SignatureTemplateCreate(SignatureTemplateBase):
    pass


class SignatureTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    html_template: Optional[str] = None
    css_styles: Optional[str] = None
    variables: Optional[List[str]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class SignatureTemplateResponse(SignatureTemplateBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== SIGNATURE SCHEMAS =====

class SignatureBase(BaseModel):
    name: str
    custom_data: Optional[Dict[str, Any]] = None


class SignatureCreate(SignatureBase):
    template_id: int


class SignatureUpdate(BaseModel):
    name: Optional[str] = None
    template_id: Optional[int] = None
    custom_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SignatureResponse(SignatureBase):
    id: int
    user_id: int
    template_id: Optional[int] = None
    html_content: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignaturePreviewRequest(BaseModel):
    template_id: int
    custom_data: Dict[str, Any]


class SignaturePreviewResponse(BaseModel):
    html_content: str
''')

    # ARQUIVO 3: Serviço de upload de imagens
    create_file("app/services/storage_service.py", '''import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status


class StorageService:
    """Serviço de armazenamento de arquivos"""
    
    def __init__(self):
        self.upload_dir = Path("/app/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Tipos de arquivo permitidos
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
    
    async def upload_image(self, file: UploadFile, organization_id: int) -> str:
        """
        Upload de imagem
        Retorna a URL da imagem
        """
        # Validar extensão
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Gerar nome único
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        
        # Criar diretório da organização
        org_dir = self.upload_dir / str(organization_id)
        org_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminho completo
        file_path = org_dir / filename
        
        # Salvar arquivo
        try:
            contents = await file.read()
            
            # Validar tamanho
            if len(contents) > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Max size: {self.max_file_size / 1024 / 1024}MB"
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Retornar URL relativa
            return f"/uploads/{organization_id}/{filename}"
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    def delete_image(self, image_url: str) -> bool:
        """Deletar imagem"""
        try:
            # Extrair caminho do arquivo
            file_path = self.upload_dir / image_url.replace("/uploads/", "")
            
            if file_path.exists():
                file_path.unlink()
                return True
            
            return False
        
        except Exception:
            return False


# Instância global do serviço
storage_service = StorageService()
''')

    # ARQUIVO 4: Serviço de renderização de assinaturas
    create_file("app/services/signature_service.py", '''from jinja2 import Template
from sqlalchemy.orm import Session
from typing import Dict, Any
from premailer import transform

from app.db.models import SignatureTemplate, Signature, User


class SignatureService:
    """Serviço de renderização de assinaturas"""
    
    def render_signature(
        self,
        template: SignatureTemplate,
        user: User,
        custom_data: Dict[str, Any] = None
    ) -> str:
        """
        Renderiza uma assinatura baseada no template e dados do usuário
        """
        # Preparar contexto com dados do usuário
        context = {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone or "",
            "job_title": user.job_title or "",
            "avatar_url": user.avatar_url or "",
            "organization_name": user.organization.name if user.organization else "",
            "organization_logo": user.organization.logo_url if user.organization else "",
            "department": user.department.name if user.department else "",
        }
        
        # Adicionar dados customizados
        if custom_data:
            context.update(custom_data)
        
        # Renderizar template HTML
        template_obj = Template(template.html_template)
        html_content = template_obj.render(**context)
        
        # Inline CSS (para compatibilidade com email clients)
        if template.css_styles:
            full_html = f"<style>{template.css_styles}</style>{html_content}"
            html_content = transform(full_html)
        
        return html_content
    
    def create_signature_from_template(
        self,
        db: Session,
        user: User,
        template: SignatureTemplate,
        name: str,
        custom_data: Dict[str, Any] = None
    ) -> Signature:
        """Criar uma nova assinatura baseada em um template"""
        
        # Renderizar HTML
        html_content = self.render_signature(template, user, custom_data)
        
        # Criar assinatura
        signature = Signature(
            user_id=user.id,
            template_id=template.id,
            name=name,
            custom_data=custom_data,
            html_content=html_content,
            is_active=True
        )
        
        db.add(signature)
        db.commit()
        db.refresh(signature)
        
        return signature
    
    def update_signature(
        self,
        db: Session,
        signature: Signature,
        user: User,
        template: SignatureTemplate = None,
        custom_data: Dict[str, Any] = None
    ) -> Signature:
        """Atualizar uma assinatura existente"""
        
        if template:
            signature.template_id = template.id
        
        if custom_data:
            signature.custom_data = custom_data
        
        # Re-renderizar HTML
        current_template = template or signature.template
        signature.html_content = self.render_signature(
            current_template,
            user,
            signature.custom_data
        )
        
        db.commit()
        db.refresh(signature)
        
        return signature


# Instância global do serviço
signature_service = SignatureService()
''')

    # ARQUIVO 5: Rotas de templates
    create_file("app/api/v1/signature_templates.py", '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, SignatureTemplate, UserRole
from app.schemas.signature import (
    SignatureTemplateCreate,
    SignatureTemplateUpdate,
    SignatureTemplateResponse
)
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[SignatureTemplateResponse])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todos os templates da organização"""
    templates = db.query(SignatureTemplate).filter(
        SignatureTemplate.organization_id == current_user.organization_id,
        SignatureTemplate.is_active == True
    ).all()
    
    return templates


@router.get("/{template_id}", response_model=SignatureTemplateResponse)
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter um template específico"""
    template = db.query(SignatureTemplate).filter(
        SignatureTemplate.id == template_id,
        SignatureTemplate.organization_id == current_user.organization_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.post("/", response_model=SignatureTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: SignatureTemplateCreate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Criar novo template (admin/owner only)"""
    
    # Se é default, desmarcar outros
    if template_data.is_default:
        db.query(SignatureTemplate).filter(
            SignatureTemplate.organization_id == current_user.organization_id,
            SignatureTemplate.is_default == True
        ).update({"is_default": False})
    
    template = SignatureTemplate(
        organization_id=current_user.organization_id,
        **template_data.model_dump()
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.patch("/{template_id}", response_model=SignatureTemplateResponse)
def update_template(
    template_id: int,
    template_update: SignatureTemplateUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Atualizar template (admin/owner only)"""
    
    template = db.query(SignatureTemplate).filter(
        SignatureTemplate.id == template_id,
        SignatureTemplate.organization_id == current_user.organization_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Se está marcando como default, desmarcar outros
    if template_update.is_default:
        db.query(SignatureTemplate).filter(
            SignatureTemplate.organization_id == current_user.organization_id,
            SignatureTemplate.is_default == True,
            SignatureTemplate.id != template_id
        ).update({"is_default": False})
    
    # Atualizar campos
    for field, value in template_update.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Deletar template (admin/owner only)"""
    
    template = db.query(SignatureTemplate).filter(
        SignatureTemplate.id == template_id,
        SignatureTemplate.organization_id == current_user.organization_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Soft delete
    template.is_active = False
    db.commit()
    
    return None
''')

    # ARQUIVO 6: Rotas de assinaturas
    create_file("app/api/v1/signatures.py", '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, Signature, SignatureTemplate
from app.schemas.signature import (
    SignatureCreate,
    SignatureUpdate,
    SignatureResponse,
    SignaturePreviewRequest,
    SignaturePreviewResponse
)
from app.api.deps import get_current_user
from app.services.signature_service import signature_service

router = APIRouter()


@router.get("/", response_model=List[SignatureResponse])
def list_my_signatures(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar minhas assinaturas"""
    signatures = db.query(Signature).filter(
        Signature.user_id == current_user.id
    ).all()
    
    return signatures


@router.get("/{signature_id}", response_model=SignatureResponse)
def get_signature(
    signature_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter uma assinatura específica"""
    signature = db.query(Signature).filter(
        Signature.id == signature_id,
        Signature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found"
        )
    
    return signature


@router.post("/", response_model=SignatureResponse, status_code=status.HTTP_201_CREATED)
def create_signature(
    signature_data: SignatureCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar nova assinatura"""
    
    # Verificar se o template existe
    template = db.query(SignatureTemplate).filter(
        SignatureTemplate.id == signature_data.template_id,
        SignatureTemplate.organization_id == current_user.organization_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Criar assinatura
    signature = signature_service.create_signature_from_template(
        db=db,
        user=current_user,
        template=template,
        name=signature_data.name,
        custom_data=signature_data.custom_data
    )
    
    return signature


@router.patch("/{signature_id}", response_model=SignatureResponse)
def update_signature(
    signature_id: int,
    signature_update: SignatureUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualizar assinatura"""
    
    signature = db.query(Signature).filter(
        Signature.id == signature_id,
        Signature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found"
        )
    
    # Atualizar nome se fornecido
    if signature_update.name:
        signature.name = signature_update.name
    
    # Atualizar status se fornecido
    if signature_update.is_active is not None:
        signature.is_active = signature_update.is_active
    
    # Atualizar template e/ou dados customizados
    template = None
    if signature_update.template_id:
        template = db.query(SignatureTemplate).filter(
            SignatureTemplate.id == signature_update.template_id,
            SignatureTemplate.organization_id == current_user.organization_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
    
    # Atualizar assinatura
    signature = signature_service.update_signature(
        db=db,
        signature=signature,
        user=current_user,
        template=template,
        custom_data=signature_update.custom_data
    )
    
    return signature


@router.delete("/{signature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signature(
    signature_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletar assinatura"""
    
    signature = db.query(Signature).filter(
        Signature.id == signature_id,
        Signature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found"
        )
    
    db.delete(signature)
    db.commit()
    
    return None


@router.post("/preview", response_model=SignaturePreviewResponse)
def preview_signature(
    preview_data: SignaturePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview de assinatura antes de salvar"""
    
    # Verificar se o template existe
    template = db.query(SignatureTemplate).filter(
        SignatureTemplate.id == preview_data.template_id,
        SignatureTemplate.organization_id == current_user.organization_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Renderizar preview
    html_content = signature_service.render_signature(
        template=template,
        user=current_user,
        custom_data=preview_data.custom_data
    )
    
    return SignaturePreviewResponse(html_content=html_content)
''')

    # ARQUIVO 7: Rotas de upload
    create_file("app/api/v1/uploads.py", '''from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.db.models import User
from app.api.deps import get_current_user
from app.services.storage_service import storage_service

router = APIRouter()


class UploadResponse(BaseModel):
    url: str
    filename: str


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload de imagem para assinaturas"""
    
    # Upload da imagem
    image_url = await storage_service.upload_image(
        file=file,
        organization_id=current_user.organization_id
    )
    
    return UploadResponse(
        url=image_url,
        filename=file.filename
    )
''')

    # ARQUIVO 8: Atualizar main.py
    create_file("app/main.py", '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.db.session import test_db_connection
from app.db.redis_client import test_redis_connection

# Import routers
from app.api.v1 import auth, organizations, members, signature_templates, signatures, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")
    
    # Criar diretório de uploads
    upload_dir = Path("/app/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
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

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])
app.include_router(signature_templates.router, prefix="/api/v1/signature-templates", tags=["Signature Templates"])
app.include_router(signatures.router, prefix="/api/v1/signatures", tags=["Signatures"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["Uploads"])


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

    # ARQUIVO 9: Migration para assinaturas
    create_file("alembic/versions/002_signature_tables.py", '''"""Add signature tables

Revision ID: 002
Revises: 001
Create Date: 2024-11-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create signature_templates table
    op.create_table(
        'signature_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_template', sa.Text(), nullable=False),
        sa.Column('css_styles', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create signatures table
    op.create_table(
        'signatures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('custom_data', sa.JSON(), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['signature_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('signatures')
    op.drop_table('signature_templates')
''')

    # ARQUIVO 10: Template HTML básico
    create_file("app/templates/signatures/basic_template.html", '''<table style="font-family: Arial, sans-serif; font-size: 14px; color: #333; border-collapse: collapse;">
    <tr>
        <td style="padding-right: 20px; vertical-align: top;">
            {% if avatar_url %}
            <img src="{{ avatar_url }}" alt="{{ full_name }}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover;">
            {% endif %}
        </td>
        <td style="vertical-align: top; border-left: 2px solid #0066cc; padding-left: 20px;">
            <div style="font-weight: bold; font-size: 16px; color: #0066cc; margin-bottom: 5px;">
                {{ full_name }}
            </div>
            {% if job_title %}
            <div style="font-style: italic; color: #666; margin-bottom: 10px;">
                {{ job_title }}
            </div>
            {% endif %}
            {% if email %}
            <div style="margin-bottom: 5px;">
                <span style="color: #666;">📧</span> <a href="mailto:{{ email }}" style="color: #0066cc; text-decoration: none;">{{ email }}</a>
            </div>
            {% endif %}
            {% if phone %}
            <div style="margin-bottom: 5px;">
                <span style="color: #666;">📱</span> {{ phone }}
            </div>
            {% endif %}
            {% if organization_name %}
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;">
                <strong>{{ organization_name }}</strong>
                {% if organization_logo %}
                <br><img src="{{ organization_logo }}" alt="{{ organization_name }}" style="max-width: 150px; margin-top: 10px;">
                {% endif %}
            </div>
            {% endif %}
        </td>
    </tr>
</table>
''')

    print("\n" + "=" * 50)
    print("✅ Todos os arquivos do DIA 3 criados!")
    print("=" * 50)
    
    print("\n📋 Próximos passos:")
    print("1. Aplicar migrations:")
    print("   sudo docker-compose exec api alembic upgrade head")
    print()
    print("2. Reiniciar a API:")
    print("   sudo docker-compose restart api")
    print()
    print("3. Testar os novos endpoints:")
    print("   curl https://signature.thebroker.vip/docs")
    print()
    print("🎉 DIA 3 - Setup completo!")


if __name__ == "__main__":
    main()
