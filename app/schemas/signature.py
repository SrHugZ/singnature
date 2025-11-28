from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class SignatureTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    html_template: str
    css_styles: Optional[str] = None
    variables: Optional[List[str]] = None
    is_default: bool = False


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
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    custom_data: Optional[Dict[str, Any]] = None


class SignaturePreviewResponse(BaseModel):
    html_content: str