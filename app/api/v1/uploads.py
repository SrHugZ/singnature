from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from PIL import Image
import io

from app.db.session import get_db
from app.db.models import User, UserRole, Organization, Signature, SignatureTemplate
from app.api.deps import get_current_user
from app.services.storage_service import storage_service
from app.services.signature_service import signature_service

router = APIRouter()

# Diretórios locais para uploads (avatar / logo)
UPLOAD_DIR = Path("/app/uploads")
AVATAR_DIR = UPLOAD_DIR / "avatars"
LOGO_DIR = UPLOAD_DIR / "logos"

# Criar diretórios se não existirem
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
LOGO_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class UploadResponse(BaseModel):
    url: str
    filename: str


def optimize_image(image_data: bytes, max_dimension: int = 800) -> bytes:
    """
    Otimiza e redimensiona imagem para não ficar pesada.
    """
    img = Image.open(io.BytesIO(image_data))

    # Converter para RGB se necessário (evita problemas com transparência)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

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

    # Salvar otimizado em JPEG
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue()


# =====================================================
# 1) Upload genérico de imagem para assinaturas (/image)
# =====================================================
@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload genérico de imagem (por exemplo, imagens usadas em assinaturas).
    Usa o storage_service (S3/obj storage, etc).
    """
    image_url = await storage_service.upload_image(
        file=file,
        organization_id=current_user.organization_id,
    )

    return UploadResponse(
        url=image_url,
        filename=file.filename,
    )


# ===========================================
# 2) Upload de avatar do usuário (/avatar)
# ===========================================
@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload de avatar do usuário (foto de perfil)."""

    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Ler arquivo todo em memória
    contents = await file.read()

    # Validar tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo: 5MB",
        )

    try:
        # Otimizar imagem
        optimized_image = optimize_image(contents, max_dimension=800)

        # Gerar nome único
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = AVATAR_DIR / unique_filename

        # Salvar arquivo localmente
        with open(file_path, "wb") as f:
            f.write(optimized_image)

        # Gerar URL pública
        avatar_url = f"/uploads/avatars/{unique_filename}"

        # Deletar avatar antigo se existir e for da mesma pasta
        if current_user.avatar_url and "uploads/avatars/" in current_user.avatar_url:
            old_filename = current_user.avatar_url.split("/")[-1]
            old_path = AVATAR_DIR / old_filename
            if old_path.exists():
                old_path.unlink()

        # Atualizar usuário
        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)

        # 🔁 REGERAR ASSINATURAS DESSE USUÁRIO
        user_signatures = (
            db.query(Signature)
            .filter(Signature.user_id == current_user.id)
            .all()
        )

        for sig in user_signatures:
            if sig.template:
                sig.html_content = signature_service.render_signature(
                    sig.template,
                    current_user,
                    sig.custom_data or {},
                )

        db.commit()

        return {
            "success": True,
            "message": "Avatar atualizado com sucesso",
            "avatar_url": avatar_url,
            "filename": unique_filename,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar imagem: {str(e)}",
        )


@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    # Limpar avatar do usuário
    current_user.avatar_url = None
    db.commit()
    db.refresh(current_user)

    # 🔁 REGERAR ASSINATURAS DESSE USUÁRIO (sem avatar agora)
    user_signatures = (
        db.query(Signature)
        .filter(Signature.user_id == current_user.id)
        .all()
    )

    for sig in user_signatures:
        if sig.template:
            sig.html_content = signature_service.render_signature(
                sig.template,
                current_user,
                sig.custom_data or {},
            )

    db.commit()

    return {
        "success": True,
        "message": "Avatar removido com sucesso",
    }


# ===========================================
# 3) Upload de logo da organização (/logo)
# ===========================================
@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload de logo da organização (apenas OWNER/ADMIN)."""

    # Verificar permissão
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas admins podem alterar o logo",
        )

    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Ler arquivo
    contents = await file.read()

    # Validar tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo: 5MB",
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

        # Gerar URL pública
        logo_url = f"/uploads/logos/{unique_filename}"

        # Buscar organização do usuário
        org = (
            db.query(Organization)
            .filter(Organization.id == current_user.organization_id)
            .first()
        )

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organização não encontrada",
            )

        # Deletar logo antigo se existir
        if org.logo_url and "uploads/logos/" in org.logo_url:
            old_filename = org.logo_url.split("/")[-1]
            old_path = LOGO_DIR / old_filename
            if old_path.exists():
                old_path.unlink()

        # Atualizar organização
        org.logo_url = logo_url
        db.commit()
        db.refresh(org)

        # 🔁 REGERAR TODAS AS ASSINATURAS DA ORGANIZAÇÃO
        org_signatures = (
            db.query(Signature)
            .join(User)
            .filter(User.organization_id == org.id)
            .all()
        )

        for sig in org_signatures:
            if sig.template and sig.user:
                sig.html_content = signature_service.render_signature(
                    sig.template,
                    sig.user,
                    sig.custom_data or {},
                )

        db.commit()

        return {
            "success": True,
            "message": "Logo atualizado com sucesso",
            "logo_url": logo_url,
            "filename": unique_filename,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar imagem: {str(e)}",
        )
