from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from PIL import Image
import io

from app.db.session import get_db
from app.db.models import User
from app.api.deps import get_current_user

router = APIRouter()

UPLOAD_DIR = Path("/app/uploads")
AVATAR_DIR = UPLOAD_DIR / "avatars"
LOGO_DIR = UPLOAD_DIR / "logos"

# Criar diretórios se não existirem
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
LOGO_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def optimize_image(image_data: bytes, max_dimension: int = 800) -> bytes:
    """Otimiza e redimensiona imagem"""
    img = Image.open(io.BytesIO(image_data))
    
    # Converter para RGB se necessário
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Redimensionar mantendo proporção
    width, height = img.size
    if width > max_dimension or height > max_dimension:
        if width > height:
            new_width = max_dimension
            new_height = int((max_dimension / width) * height)
        else:
            new_height = max_dimension
            new_width = int((max_dimension / height) * width)
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Salvar otimizado
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload de avatar do usuário"""
    
    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Ler arquivo
    contents = await file.read()
    
    # Validar tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. Máximo: 5MB"
        )
    
    try:
        # Otimizar imagem
        optimized_image = optimize_image(contents, max_dimension=800)
        
        # Gerar nome único
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = AVATAR_DIR / unique_filename
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(optimized_image)
        
        # Gerar URL
        avatar_url = f"https://signature.thebroker.vip/uploads/avatars/{unique_filename}"
        
        # Deletar avatar antigo se existir
        if current_user.avatar_url and "uploads/avatars/" in current_user.avatar_url:
            old_filename = current_user.avatar_url.split("/")[-1]
            old_path = AVATAR_DIR / old_filename
            if old_path.exists():
                old_path.unlink()
        
        # Atualizar banco de dados
        current_user.avatar_url = avatar_url
        db.commit()
        
        return {
            "success": True,
            "message": "Avatar atualizado com sucesso",
            "avatar_url": avatar_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")


@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletar avatar do usuário"""
    
    if not current_user.avatar_url:
        raise HTTPException(status_code=404, detail="Avatar não encontrado")
    
    # Deletar arquivo se existir
    if "uploads/avatars/" in current_user.avatar_url:
        filename = current_user.avatar_url.split("/")[-1]
        file_path = AVATAR_DIR / filename
        if file_path.exists():
            file_path.unlink()
    
    # Atualizar banco de dados
    current_user.avatar_url = None
    db.commit()
    
    return {
        "success": True,
        "message": "Avatar removido com sucesso"
    }


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload de logo da organização (apenas admin/owner)"""
    
    from app.db.models import UserRole, Organization
    
    # Verificar permissão
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Apenas admins podem alterar o logo")
    
    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Ler arquivo
    contents = await file.read()
    
    # Validar tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. Máximo: 5MB"
        )
    
    try:
        # Otimizar imagem
        optimized_image = optimize_image(contents, max_dimension=500)
        
        # Gerar nome único
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = LOGO_DIR / unique_filename
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(optimized_image)
        
        # Gerar URL
        logo_url = f"https://signature.thebroker.vip/uploads/logos/{unique_filename}"
        
        # Buscar organização
        org = db.query(Organization).filter(
            Organization.id == current_user.organization_id
        ).first()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organização não encontrada")
        
        # Deletar logo antigo se existir
        if org.logo_url and "uploads/logos/" in org.logo_url:
            old_filename = org.logo_url.split("/")[-1]
            old_path = LOGO_DIR / old_filename
            if old_path.exists():
                old_path.unlink()
        
        # Atualizar banco de dados
        org.logo_url = logo_url
        db.commit()
        
        return {
            "success": True,
            "message": "Logo atualizado com sucesso",
            "logo_url": logo_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")
