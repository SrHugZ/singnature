from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import User, UserRole
from app.schemas.analytics import DashboardStats, AnalyticsReport
from app.api.deps import get_current_user, require_role
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Estatísticas do dashboard (admin/owner only)"""
    return analytics_service.get_dashboard_stats(db, current_user.organization_id)


@router.get("/report", response_model=AnalyticsReport)
def generate_report(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Gerar relatório de analytics (admin/owner only)"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return analytics_service.generate_report(
        db=db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )
