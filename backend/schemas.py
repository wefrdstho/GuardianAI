from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


# ───── Auth Schemas ─────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ───── Guardian Schemas ─────

class GuardianCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=5)
    email: Optional[str] = None
    relationship_type: Optional[str] = None


class GuardianResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    relationship_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ───── Emergency Schemas ─────

class EmergencyAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SOSRequest(BaseModel):
    latitude: float
    longitude: float
    message: Optional[str] = "SOS Emergency"


class IntentResult(BaseModel):
    intent: str
    confidence: float
    keywords_found: List[str]


class RiskResult(BaseModel):
    level: str
    score: int
    reasoning: str


class LocationResult(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearby_services: List[dict] = []


class ActionItem(BaseModel):
    action: str
    priority: str
    status: str
    details: str


class EmergencyResponse(BaseModel):
    incident_id: int
    intent: IntentResult
    risk: RiskResult
    location: LocationResult
    actions: List[ActionItem]
    recommendations: List[str]
    timestamp: datetime


# ───── Incident Schemas ─────

class IncidentResponse(BaseModel):
    id: int
    incident_type: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    risk_level: str
    risk_score: int
    status: str
    actions_taken: Optional[str] = None
    ai_analysis: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentAnalytics(BaseModel):
    total_incidents: int
    by_type: dict
    by_risk_level: dict
    by_status: dict
    recent_incidents: List[IncidentResponse]
