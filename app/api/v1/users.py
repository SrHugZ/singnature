from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserUpdate, UserResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obter informações do usuário atual"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualizar informações do usuário atual"""
    
    # Atualizar campos permitidos
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    
    if user_update.job_title is not None:
        current_user.job_title = user_update.job_title
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )
