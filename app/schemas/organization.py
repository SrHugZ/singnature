from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrganizationBase(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(OrganizationBase):
    id: int
    settings: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
