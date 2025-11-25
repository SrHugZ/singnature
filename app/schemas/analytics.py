from pydantic import BaseModel
from typing import List
from datetime import datetime


class DashboardStats(BaseModel):
    total_users: int
    total_signatures: int
    total_banners: int
    active_banners: int
    total_banner_views: int
    total_banner_clicks: int
    average_ctr: float
    # Novos campos para o dashboard premium
    click_rate: float = 0.0
    impressions_change: float = 0.0
    banners_change: int = 0


class BannerPerformance(BaseModel):
    banner_id: int
    banner_name: str
    views: int
    clicks: int
    ctr: float


class UserActivity(BaseModel):
    user_id: int
    user_name: str
    email: str
    signatures_count: int
    last_active: datetime


class AnalyticsReport(BaseModel):
    period_start: datetime
    period_end: datetime
    dashboard_stats: DashboardStats
    top_banners: List[BannerPerformance]
    active_users: List[UserActivity]