from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.db.models import Banner, User, BannerClick


class BannerService:
    """Serviço para gerenciamento de banners"""
    
    def get_active_banner_for_user(
        self,
        db: Session,
        user: User
    ) -> Optional[Banner]:
        """
        Retorna um banner ativo apropriado para o usuário
        Considera: data de vigência, segmentação e status ativo
        """
        now = datetime.utcnow()
        
        # Query base: banners ativos da organização
        query = db.query(Banner).filter(
            Banner.organization_id == user.organization_id,
            Banner.is_active == True
        )
        
        # Filtrar por data
        query = query.filter(
            (Banner.start_date == None) | (Banner.start_date <= now)
        ).filter(
            (Banner.end_date == None) | (Banner.end_date >= now)
        )
        
        banners = query.all()
        
        # Filtrar por segmentação
        for banner in banners:
            # Se não tem segmentação, é para todos
            if not banner.target_departments and not banner.target_users:
                return banner
            
            # Verificar se usuário está nos alvos
            if banner.target_users and user.id in banner.target_users:
                return banner
            
            # Verificar se departamento está nos alvos
            if banner.target_departments and user.department_id in banner.target_departments:
                return banner
        
        return None
    
    def track_banner_click(
        self,
        db: Session,
        banner: Banner,
        user: User = None,
        ip_address: str = None,
        user_agent: str = None,
        referer: str = None
    ) -> BannerClick:
        """Registra um clique no banner"""
        
        # Criar registro de clique
        click = BannerClick(
            banner_id=banner.id,
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        
        db.add(click)
        
        # Incrementar contador
        banner.clicks_count += 1
        
        db.commit()
        db.refresh(click)
        
        return click
    
    def track_banner_view(
        self,
        db: Session,
        banner: Banner
    ):
        """Incrementa contador de visualizações"""
        banner.views_count += 1
        db.commit()


banner_service = BannerService()
