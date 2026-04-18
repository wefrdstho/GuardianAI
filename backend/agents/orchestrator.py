"""
Orchestrator Agent
Coordinates all AI agents in a pipeline to process emergency requests.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Optional
from sqlalchemy.orm import Session

from .intent_agent import IntentAgent
from .risk_agent import RiskAgent
from .location_agent import LocationAgent
from .decision_engine import DecisionEngine
from ..models import Incident, IncidentStatus


class Orchestrator:
    """Coordinates the emergency response pipeline across all agents."""

    def __init__(self):
        self.intent_agent = IntentAgent()
        self.risk_agent = RiskAgent()
        self.location_agent = LocationAgent()
        self.decision_engine = DecisionEngine()

    async def process_emergency(
        self,
        text: str,
        user_id: int,
        db: Session,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        is_sos: bool = False,
    ) -> Dict:
        """
        Full emergency processing pipeline.
        
        Steps:
        1. Intent Analysis
        2. Risk Assessment
        3. Location Intelligence
        4. Decision Engine
        5. Log Incident
        
        Returns:
            Complete emergency response dict
        """
        timestamp = datetime.now(timezone.utc)

        # ─── Step 1: Intent Analysis ───
        if is_sos:
            intent_result = {
                "intent": "sos",
                "confidence": 1.0,
                "keywords_found": ["SOS"],
                "all_intents": {"sos": 1.0},
            }
        else:
            intent_result = self.intent_agent.analyze(text)

        # ─── Step 2: Risk Assessment ───
        risk_result = self.risk_agent.assess(
            intent_result, text, latitude, longitude
        )

        # ─── Step 3: Location Intelligence ───
        if latitude is not None and longitude is not None:
            location_result = await self.location_agent.get_location_info(latitude, longitude)
        else:
            location_result = {
                "address": None,
                "latitude": None,
                "longitude": None,
                "nearby_services": [],
            }

        # ─── Step 4: Decision Engine ───
        decision_result = self.decision_engine.decide(
            intent_result, risk_result, location_result
        )

        # ─── Step 5: Log Incident ───
        incident = Incident(
            user_id=user_id,
            incident_type=intent_result["intent"],
            description=text,
            latitude=latitude,
            longitude=longitude,
            address=location_result.get("address"),
            risk_level=risk_result["level"],
            risk_score=risk_result["score"],
            status=IncidentStatus.ACTIVE.value,
            actions_taken=json.dumps(decision_result["actions"]),
            ai_analysis=json.dumps({
                "intent": intent_result,
                "risk": risk_result,
            }),
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # ─── Simulate guardian notifications ───
        self._simulate_notifications(decision_result["actions"], intent_result["intent"])

        # ─── Build Response ───
        return {
            "incident_id": incident.id,
            "intent": intent_result,
            "risk": risk_result,
            "location": location_result,
            "actions": decision_result["actions"],
            "recommendations": decision_result["recommendations"],
            "response_summary": decision_result["response_summary"],
            "timestamp": timestamp.isoformat(),
        }

    def _simulate_notifications(self, actions: list, intent: str):
        """Simulate sending notifications (console log for demo)."""
        for action in actions:
            if action["action"] == "notify_guardians":
                print(f"\n{'='*60}")
                print(f"[ALERT SIMULATION] Guardian notification sent!")
                print(f"   Emergency type: {intent.upper()}")
                print(f"   Priority: {action['priority'].upper()}")
                print(f"   Message: {action['details']}")
                print(f"{'='*60}\n")
            elif "contact" in action["action"]:
                print(f"[ALERT SIMULATION] Contacting: {action['action']} - {action['details']}")
