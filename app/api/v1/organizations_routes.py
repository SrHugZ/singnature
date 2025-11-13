from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Organization, UserRole
from app.schemas.user import OrganizationResponse, OrganizationUpdate
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's organization information
    """
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
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update organization information
    Only OWNER and ADMIN can update
    """
    # Check permissions
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can update organization"
        )
    
    # Get organization
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    return organization
