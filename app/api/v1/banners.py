from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, Banner, UserRole
from app.schemas.banner import BannerCreate, BannerUpdate, BannerResponse, BannerStatsResponse
from app.api.deps import get_current_user, require_role
from app.services.banner_service import banner_service

router = APIRouter()


@router.get("/", response_model=List[BannerResponse])
def list_banners(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """Listar banners da organização"""
    query = db.query(Banner).filter(
        Banner.organization_id == current_user.organization_id
    )
    
    if not include_inactive:
        query = query.filter(Banner.is_active == True)
    
    return query.all()


@router.get("/active", response_model=BannerResponse)
def get_active_banner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter banner ativo para o usuário atual"""
    banner = banner_service.get_active_banner_for_user(db, current_user)
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active banner found"
        )
    
    # Registrar visualização
    banner_service.track_banner_view(db, banner)
    
    return banner


@router.get("/{banner_id}", response_model=BannerResponse)
def get_banner(
    banner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter um banner específico"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.organization_id == current_user.organization_id
    ).first()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    return banner


@router.post("/", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
def create_banner(
    banner_data: BannerCreate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Criar novo banner (admin/owner only)"""
    banner = Banner(
        organization_id=current_user.organization_id,
        **banner_data.model_dump()
    )
    
    db.add(banner)
    db.commit()
    db.refresh(banner)
    
    return banner


@router.patch("/{banner_id}", response_model=BannerResponse)
def update_banner(
    banner_id: int,
    banner_update: BannerUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Atualizar banner (admin/owner only)"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.organization_id == current_user.organization_id
    ).first()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    for field, value in banner_update.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    
    db.commit()
    db.refresh(banner)
    
    return banner


@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(
    banner_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Deletar banner (admin/owner only)"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.organization_id == current_user.organization_id
    ).first()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    db.delete(banner)
    db.commit()
    
    return None


@router.get("/{banner_id}/stats", response_model=BannerStatsResponse)
def get_banner_stats(
    banner_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Obter estatísticas do banner"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.organization_id == current_user.organization_id
    ).first()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    ctr = (banner.clicks_count / banner.views_count * 100) if banner.views_count > 0 else 0.0
    
    return BannerStatsResponse(
        banner_id=banner.id,
        banner_name=banner.name,
        views=banner.views_count,
        clicks=banner.clicks_count,
        ctr=round(ctr, 2),
        created_at=banner.created_at
    )


@router.get("/click/{banner_id}")
async def track_click_and_redirect(
    banner_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Rastrear clique e redirecionar para URL do banner"""
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    # Registrar clique
    banner_service.track_banner_click(
        db=db,
        banner=banner,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer")
    )
    
    # Redirecionar
    return RedirectResponse(url=banner.target_url, status_code=302)
