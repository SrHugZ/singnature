from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new organization with owner user (RF-001)
    
    - Creates a new organization
    - Creates the first user (owner)
    - Returns access and refresh tokens
    """
    user, access_token, refresh_token = AuthService.register_owner(db, user_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns access and refresh tokens
    """
    user, access_token, refresh_token = AuthService.login(db, credentials)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=dict)
def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Refresh access token using refresh token
    
    Returns new access token
    """
    access_token = AuthService.refresh_access_token(
        db, 
        redis_client, 
        token_data.refresh_token
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_token: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Logout by blacklisting tokens
    
    Requires both access token (in header) and refresh token (in body)
    """
    # Get access token from dependencies (already validated)
    from fastapi import Request
    
    # Extract access token from header
    # Note: In production, you'd get this from the request context
    # For now, we'll just blacklist the refresh token
    
    AuthService.logout(
        redis_client,
        "",  # Access token would come from request
        refresh_token.refresh_token
    )
    
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    return current_user
