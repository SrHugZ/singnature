from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User, UserRole
from app.schemas.user import MemberInvite, MemberActivate, MemberResponse
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, get_current_admin_user

router = APIRouter()


@router.post("/invite", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    invite_data: MemberInvite,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Invite a new member to the organization (RF-002)
    
    Only OWNER and ADMIN can invite members
    Returns the pending user with activation token
    """
    new_user = AuthService.invite_member(
        db,
        current_user,
        invite_data.email,
        invite_data.role,
        invite_data.department_id
    )
    
    return new_user


@router.post("/activate", response_model=MemberResponse)
def activate_member(
    activation_data: MemberActivate,
    db: Session = Depends(get_db)
):
    """
    Activate member account with token (RF-003)
    
    Sets password and full name, activates the account
    """
    user = AuthService.activate_member(
        db,
        activation_data.token,
        activation_data.password,
        activation_data.full_name
    )
    
    return user


@router.get("/", response_model=List[MemberResponse])
def list_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all members in the organization
    """
    members = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).all()
    
    return members


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get member details by ID
    """
    member = db.query(User).filter(
        User.id == member_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a member from the organization
    
    Only OWNER and ADMIN can delete members
    Cannot delete yourself or the organization owner
    """
    # Get member
    member = db.query(User).filter(
        User.id == member_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot delete yourself
    if member.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Cannot delete owner
    if member.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete organization owner"
        )
    
    db.delete(member)
    db.commit()
    
    return None
