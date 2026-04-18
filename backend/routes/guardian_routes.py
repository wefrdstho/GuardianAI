"""Guardian management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Guardian
from ..schemas import GuardianCreate, GuardianResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/guardians", tags=["Guardians"])


@router.get("/", response_model=List[GuardianResponse])
def list_guardians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all guardians for the current user."""
    guardians = db.query(Guardian).filter(Guardian.user_id == current_user.id).all()
    return [GuardianResponse.model_validate(g) for g in guardians]


@router.post("/", response_model=GuardianResponse)
def add_guardian(
    data: GuardianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new guardian contact."""
    guardian = Guardian(
        user_id=current_user.id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        relationship_type=data.relationship_type,
    )
    db.add(guardian)
    db.commit()
    db.refresh(guardian)
    return GuardianResponse.model_validate(guardian)


@router.delete("/{guardian_id}")
def remove_guardian(
    guardian_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a guardian contact."""
    guardian = db.query(Guardian).filter(
        Guardian.id == guardian_id,
        Guardian.user_id == current_user.id,
    ).first()

    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    db.delete(guardian)
    db.commit()
    return {"message": "Guardian removed successfully"}
