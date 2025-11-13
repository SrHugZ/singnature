from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import redis
import logging

from app.db.session import get_db
from app.db.redis_client import get_redis_client
from app.db.models import User, UserRole
from app.services.security import decode_token
from app.services.auth_service import is_token_blacklisted

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Importante: auto_error=False


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> User:
    """Get current authenticated user"""
    
    # Check if credentials were provided
    if not credentials:
        logger.warning("No authorization credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(redis_client, token):
            logger.warning(f"Blacklisted token attempted: {token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            logger.warning("Invalid token - could not decode")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token type
        if payload.get("type") != "access":
            logger.warning(f"Invalid token type: {payload.get('type')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("No user ID in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in get_current_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )


def require_role(required_roles: list[UserRole]):
    """Dependency to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            logger.warning(f"User {current_user.id} attempted to access resource requiring roles {required_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker