from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.db.models import User
from app.api.deps import get_current_user
from app.services.storage_service import storage_service

router = APIRouter()


class UploadResponse(BaseModel):
    url: str
    filename: str


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload de imagem para assinaturas"""
    
    # Upload da imagem
    image_url = await storage_service.upload_image(
        file=file,
        organization_id=current_user.organization_id
    )
    
    return UploadResponse(
        url=image_url,
        filename=file.filename
    )
