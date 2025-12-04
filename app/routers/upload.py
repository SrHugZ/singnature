from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
from pathlib import Path
from PIL import Image
import io

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "avatars").mkdir(exist_ok=True)
(UPLOAD_DIR / "logos").mkdir(exist_ok=True)

def validate_image(file: UploadFile) -> tuple[bool, str]:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
    if not file.content_type.startswith('image/'):
        return False, "Arquivo não é uma imagem"
    return True, "OK"

def optimize_image(image_data: bytes, max_dimension: int = 1000) -> bytes:
    img = Image.open(io.BytesIO(image_data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    width, height = img.size
    if width > max_dimension or height > max_dimension:
        if width > height:
            new_width = max_dimension
            new_height = int((max_dimension / width) * height)
        else:
            new_height = max_dimension
            new_width = int((max_dimension / height) * width)
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_valid, message = validate_image(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 5MB")
        
        optimized_image = optimize_image(contents, max_dimension=800)
        
        ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / "avatars" / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(optimized_image)
        
        avatar_url = f"https://signature.thebroker.vip/uploads/avatars/{unique_filename}"
        
        from app.models import User
        user = db.query(User).filter(User.id == current_user.id).first()
        if user:
            if user.avatar_url and "uploads/avatars/" in user.avatar_url:
                old_filename = user.avatar_url.split("/")[-1]
                old_path = UPLOAD_DIR / "avatars" / old_filename
                if old_path.exists():
                    old_path.unlink()
            user.avatar_url = avatar_url
            db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Avatar enviado com sucesso",
            "avatar_url": avatar_url,
            "filename": unique_filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_valid, message = validate_image(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 5MB")
        
        optimized_image = optimize_image(contents, max_dimension=500)
        
        ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / "logos" / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(optimized_image)
        
        logo_url = f"https://signature.thebroker.vip/uploads/logos/{unique_filename}"
        
        from app.models import Organization
        org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
        if org:
            if org.logo_url and "uploads/logos/" in org.logo_url:
                old_filename = org.logo_url.split("/")[-1]
                old_path = UPLOAD_DIR / "logos" / old_filename
                if old_path.exists():
                    old_path.unlink()
            org.logo_url = logo_url
            db.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Logo enviada com sucesso",
            "logo_url": logo_url,
            "filename": unique_filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.delete("/avatar")
async def delete_avatar(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models import User
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user or not user.avatar_url:
        raise HTTPException(status_code=404, detail="Avatar não encontrado")
    
    if "uploads/avatars/" in user.avatar_url:
        filename = user.avatar_url.split("/")[-1]
        file_path = UPLOAD_DIR / "avatars" / filename
        if file_path.exists():
            file_path.unlink()
    
    user.avatar_url = None
    db.commit()
    
    return JSONResponse(status_code=200, content={
        "success": True,
        "message": "Avatar removido com sucesso"
    })
