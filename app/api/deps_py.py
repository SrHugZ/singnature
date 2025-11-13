from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import redis

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.db.models import User, UserStatus
from app.services.security import decode_token

# Security scheme for Swagger UI
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    Validates token and checks if it's blacklisted
    """
    token = credentials.credentials
    
    # Check if token is blacklisted
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is ADMIN or OWNER
    """
    from app.db.models import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user
