import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status


class StorageService:
    """Serviço de armazenamento de arquivos"""
    
    def __init__(self):
        self.upload_dir = Path("/app/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Tipos de arquivo permitidos
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
    
    async def upload_image(self, file: UploadFile, organization_id: int) -> str:
        """
        Upload de imagem
        Retorna a URL da imagem
        """
        # Validar extensão
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Gerar nome único
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        
        # Criar diretório da organização
        org_dir = self.upload_dir / str(organization_id)
        org_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminho completo
        file_path = org_dir / filename
        
        # Salvar arquivo
        try:
            contents = await file.read()
            
            # Validar tamanho
            if len(contents) > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Max size: {self.max_file_size / 1024 / 1024}MB"
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Retornar URL relativa
            return f"/uploads/{organization_id}/{filename}"
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    def delete_image(self, image_url: str) -> bool:
        """Deletar imagem"""
        try:
            # Extrair caminho do arquivo
            file_path = self.upload_dir / image_url.replace("/uploads/", "")
            
            if file_path.exists():
                file_path.unlink()
                return True
            
            return False
        
        except Exception:
            return False


# Instância global do serviço
storage_service = StorageService()
