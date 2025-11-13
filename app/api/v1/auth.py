from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.schemas.user import UserCreate, UserLogin, TokenResponse, TokenRefresh, User
from app.services.auth_service import register_user, login_user, invalidate_token
from app.services.security import decode_token, create_access_token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and organization"""
    return register_user(db, user_create)


@router.post("/login", response_model=TokenResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""
    return login_user(db, user_login)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Decode refresh token
    payload = decode_token(token_refresh.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    from app.db.models import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": user.organization_id, "role": user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=token_refresh.refresh_token,
        expires_in=1800
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Logout and invalidate token"""
    # Token blacklisting is handled in get_current_user
    return None


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
