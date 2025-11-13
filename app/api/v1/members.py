from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, UserRole, UserStatus
from app.schemas.user import MemberInvite, MemberUpdate, User as UserSchema
from app.api.deps import get_current_user, require_role
from app.services.security import hash_password

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
def list_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of the organization"""
    members = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).all()
    
    return members


@router.post("/invite", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def invite_member(
    member_invite: MemberInvite,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Invite a new member to the organization (admin/owner only)"""
    
    # Check if email already exists in organization
    existing_user = db.query(User).filter(
        User.email == member_invite.email,
        User.organization_id == current_user.organization_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists in this organization"
        )
    
    # Create pending user with temporary password
    temp_password = hash_password("temporary_password_change_me")
    
    new_user = User(
        organization_id=current_user.organization_id,
        email=member_invite.email,
        full_name=member_invite.full_name,
        hashed_password=temp_password,
        role=member_invite.role,
        status=UserStatus.PENDING,
        department_id=member_invite.department_id,
        job_title=member_invite.job_title
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # TODO: Send invitation email
    
    return new_user


@router.patch("/{user_id}", response_model=UserSchema)
def update_member(
    user_id: int,
    member_update: MemberUpdate,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a member's information (admin/owner only)"""
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent owner from being modified (except by themselves)
    if user.role == UserRole.OWNER and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify organization owner"
        )
    
    # Update fields
    if member_update.full_name is not None:
        user.full_name = member_update.full_name
    if member_update.role is not None:
        user.role = member_update.role
    if member_update.department_id is not None:
        user.department_id = member_update.department_id
    if member_update.job_title is not None:
        user.job_title = member_update.job_title
    if member_update.status is not None:
        user.status = member_update.status
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization (admin/owner only)"""
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent owner from being deleted
    if user.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete organization owner"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return None
