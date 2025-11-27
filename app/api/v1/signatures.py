from fastapi import APIRouter, Depends, HTTPException, status
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
    
    # Lógica para atualizar a assinatura
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
