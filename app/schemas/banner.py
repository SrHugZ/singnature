from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class BannerBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: str
    target_url: str
    alt_text: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_departments: Optional[List[int]] = None
    target_users: Optional[List[int]] = None


class BannerCreate(BannerBase):
    pass


class BannerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    target_url: Optional[str] = None
    alt_text: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_departments: Optional[List[int]] = None
    target_users: Optional[List[int]] = None
    is_active: Optional[bool] = None


class BannerResponse(BannerBase):
    id: int
    organization_id: int
    views_count: int
    clicks_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BannerStatsResponse(BaseModel):
    banner_id: int
    banner_name: str
    views: int
    clicks: int
    ctr: float  # Click-through rate
    created_at: datetime
