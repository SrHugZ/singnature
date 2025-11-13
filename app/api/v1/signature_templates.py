from fastapi import APIRouter, Depends, HTTPException, status
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
