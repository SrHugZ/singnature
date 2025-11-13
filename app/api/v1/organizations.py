from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Organization
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization"""
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


@router.patch("/me", response_model=OrganizationResponse)
def update_my_organization(
    organization_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's organization (owner/admin only)"""
    
    # Check if user has permission
    if current_user.role.value not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    for field, value in organization_update.model_dump(exclude_unset=True).items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    return organization
