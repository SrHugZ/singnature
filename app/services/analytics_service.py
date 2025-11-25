from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from app.db.models import User, Signature, Banner, BannerClick, SignatureTemplate
from app.schemas.analytics import (
    DashboardStats,
    BannerPerformance,
    UserActivity,
    AnalyticsReport
)


class AnalyticsService:
    """Serviço de analytics e relatórios"""
    
    def get_dashboard_stats(
        self,
        db: Session,
        organization_id: int
    ) -> DashboardStats:
        """Estatísticas gerais do dashboard"""
        
        # Total de usuários
        total_users = db.query(func.count(User.id)).filter(
            User.organization_id == organization_id
        ).scalar() or 0
        
        # Total de assinaturas
        total_signatures = db.query(func.count(Signature.id)).join(User).filter(
            User.organization_id == organization_id
        ).scalar() or 0
        
        # Total de templates
        total_templates = db.query(func.count(SignatureTemplate.id)).filter(
            SignatureTemplate.organization_id == organization_id
        ).scalar() or 0
        
        # Banners
        total_banners = db.query(func.count(Banner.id)).filter(
            Banner.organization_id == organization_id
        ).scalar() or 0
        
        active_banners = db.query(func.count(Banner.id)).filter(
            Banner.organization_id == organization_id,
            Banner.is_active == True
        ).scalar() or 0
        
        # Stats de banners
        banner_stats = db.query(
            func.sum(Banner.views_count).label('total_views'),
            func.sum(Banner.clicks_count).label('total_clicks')
        ).filter(
            Banner.organization_id == organization_id
        ).first()
        
        total_views = banner_stats.total_views or 0
        total_clicks = banner_stats.total_clicks or 0
        avg_ctr = (total_clicks / total_views * 100) if total_views > 0 else 0.0
        click_rate = avg_ctr  # Alias para compatibilidade
        
        # Calcular mudanças (últimos 30 dias vs 30 dias anteriores)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        
        # Views dos últimos 30 dias
        recent_views = db.query(func.sum(Banner.views_count)).filter(
            Banner.organization_id == organization_id,
            Banner.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Views dos 30 dias anteriores
        previous_views = db.query(func.sum(Banner.views_count)).filter(
            Banner.organization_id == organization_id,
            Banner.created_at >= sixty_days_ago,
            Banner.created_at < thirty_days_ago
        ).scalar() or 1  # Evitar divisão por zero
        
        # Calcular mudança percentual
        impressions_change = 0.0
        if previous_views > 0:
            impressions_change = ((recent_views - previous_views) / previous_views) * 100
        
        # Mudança no número de banners
        banners_change = active_banners - total_banners + active_banners  # Simplificado
        
        return DashboardStats(
            total_users=total_users,
            total_signatures=total_signatures,
            total_banners=total_banners,
            active_banners=active_banners,
            total_banner_views=total_views,
            total_banner_clicks=total_clicks,
            average_ctr=round(avg_ctr, 2),
            click_rate=round(click_rate, 2),
            impressions_change=round(impressions_change, 2),
            banners_change=banners_change
        )
    
    def get_top_banners(
        self,
        db: Session,
        organization_id: int,
        limit: int = 10
    ) -> List[BannerPerformance]:
        """Top banners por performance"""
        
        banners = db.query(Banner).filter(
            Banner.organization_id == organization_id
        ).order_by(Banner.clicks_count.desc()).limit(limit).all()
        
        results = []
        for banner in banners:
            ctr = (banner.clicks_count / banner.views_count * 100) if banner.views_count > 0 else 0.0
            results.append(BannerPerformance(
                banner_id=banner.id,
                banner_name=banner.name,
                views=banner.views_count,
                clicks=banner.clicks_count,
                ctr=round(ctr, 2)
            ))
        
        return results
    
    def get_active_users(
        self,
        db: Session,
        organization_id: int,
        days: int = 30
    ) -> List[UserActivity]:
        """Usuários mais ativos"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        users = db.query(
            User.id,
            User.full_name,
            User.email,
            User.last_login,
            func.count(Signature.id).label('sig_count')
        ).outerjoin(Signature).filter(
            User.organization_id == organization_id,
            User.last_login >= cutoff_date
        ).group_by(User.id).order_by(func.count(Signature.id).desc()).limit(10).all()
        
        results = []
        for user in users:
            results.append(UserActivity(
                user_id=user.id,
                user_name=user.full_name,
                email=user.email,
                signatures_count=user.sig_count or 0,
                last_active=user.last_login or datetime.utcnow()
            ))
        
        return results
    
    def generate_report(
        self,
        db: Session,
        organization_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> AnalyticsReport:
        """Gerar relatório completo"""
        
        return AnalyticsReport(
            period_start=start_date,
            period_end=end_date,
            dashboard_stats=self.get_dashboard_stats(db, organization_id),
            top_banners=self.get_top_banners(db, organization_id),
            active_users=self.get_active_users(db, organization_id)
        )


analytics_service = AnalyticsService()