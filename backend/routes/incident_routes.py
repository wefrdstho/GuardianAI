"""Incident tracking and analytics routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Incident
from ..schemas import IncidentResponse, IncidentAnalytics
from ..auth import get_current_user

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("/", response_model=List[IncidentResponse])
def list_incidents(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all incidents for the current user."""
    incidents = (
        db.query(Incident)
        .filter(Incident.user_id == current_user.id)
        .order_by(Incident.created_at.desc())
        .limit(limit)
        .all()
    )
    return [IncidentResponse.model_validate(i) for i in incidents]


@router.get("/analytics", response_model=IncidentAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get incident analytics for the current user."""
    incidents = db.query(Incident).filter(Incident.user_id == current_user.id).all()

    by_type = {}
    by_risk = {}
    by_status = {}

    for inc in incidents:
        by_type[inc.incident_type] = by_type.get(inc.incident_type, 0) + 1
        by_risk[inc.risk_level] = by_risk.get(inc.risk_level, 0) + 1
        by_status[inc.status] = by_status.get(inc.status, 0) + 1

    recent = sorted(incidents, key=lambda x: x.created_at, reverse=True)[:10]

    return IncidentAnalytics(
        total_incidents=len(incidents),
        by_type=by_type,
        by_risk_level=by_risk,
        by_status=by_status,
        recent_incidents=[IncidentResponse.model_validate(i) for i in recent],
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific incident."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id,
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return IncidentResponse.model_validate(incident)
