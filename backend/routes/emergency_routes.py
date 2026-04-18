"""Emergency analysis and SOS routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Incident
from ..schemas import EmergencyAnalyzeRequest, SOSRequest, EmergencyResponse, IncidentResponse
from ..auth import get_current_user
from ..agents.orchestrator import Orchestrator

router = APIRouter(prefix="/api/emergency", tags=["Emergency"])

orchestrator = Orchestrator()


@router.post("/analyze")
async def analyze_emergency(
    request: EmergencyAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze text for emergency intent, risk, and determine actions."""
    result = await orchestrator.process_emergency(
        text=request.text,
        user_id=current_user.id,
        db=db,
        latitude=request.latitude,
        longitude=request.longitude,
        is_sos=False,
    )
    return result


@router.post("/sos")
async def trigger_sos(
    request: SOSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger SOS emergency with location."""
    result = await orchestrator.process_emergency(
        text=request.message or "SOS Emergency",
        user_id=current_user.id,
        db=db,
        latitude=request.latitude,
        longitude=request.longitude,
        is_sos=True,
    )
    return result


@router.get("/status/{incident_id}")
def get_incident_status(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status of a specific incident."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.user_id == current_user.id,
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return IncidentResponse.model_validate(incident)
