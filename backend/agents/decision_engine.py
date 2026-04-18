"""
Decision Engine Agent
Determines optimal actions based on intent analysis, risk assessment, and location data.
Hybrid rule-based + AI-driven decision making.
"""

from typing import Dict, List


# Action templates by intent type
ACTION_TEMPLATES = {
    "sos": [
        {"action": "notify_guardians", "priority": "critical", "details": "Alert all emergency contacts with live location"},
        {"action": "contact_emergency_services", "priority": "critical", "details": "Dial 112/911 - Provide GPS coordinates to dispatcher"},
        {"action": "activate_tracking", "priority": "high", "details": "Enable real-time location sharing"},
        {"action": "sound_alarm", "priority": "high", "details": "Trigger device alarm for proximity alert"},
    ],
    "fire": [
        {"action": "contact_fire_department", "priority": "critical", "details": "Alert fire services with location"},
        {"action": "notify_guardians", "priority": "high", "details": "Notify emergency contacts about fire emergency"},
        {"action": "evacuation_guidance", "priority": "high", "details": "Provide evacuation route recommendations"},
        {"action": "medical_standby", "priority": "medium", "details": "Alert nearby medical services for potential injuries"},
    ],
    "medical": [
        {"action": "contact_ambulance", "priority": "critical", "details": "Dispatch ambulance to GPS location"},
        {"action": "notify_guardians", "priority": "high", "details": "Alert emergency contacts about medical emergency"},
        {"action": "first_aid_guidance", "priority": "high", "details": "Provide first-aid instructions based on condition"},
        {"action": "hospital_routing", "priority": "medium", "details": "Calculate route to nearest hospital"},
    ],
    "accident": [
        {"action": "contact_emergency_services", "priority": "critical", "details": "Alert 112 with accident location and details"},
        {"action": "contact_ambulance", "priority": "critical", "details": "Request medical assistance at scene"},
        {"action": "notify_guardians", "priority": "high", "details": "Inform emergency contacts about accident"},
        {"action": "traffic_alert", "priority": "medium", "details": "Report accident to traffic management"},
    ],
    "crime": [
        {"action": "contact_police", "priority": "critical", "details": "Alert police with location and incident details"},
        {"action": "notify_guardians", "priority": "high", "details": "Inform emergency contacts - silent notification mode"},
        {"action": "evidence_preservation", "priority": "medium", "details": "Begin logging incident details and timestamps"},
        {"action": "safe_location", "priority": "high", "details": "Guide to nearest safe public location"},
    ],
    "natural_disaster": [
        {"action": "contact_emergency_services", "priority": "critical", "details": "Alert disaster response teams"},
        {"action": "notify_guardians", "priority": "critical", "details": "Notify all contacts with current status and location"},
        {"action": "shelter_guidance", "priority": "high", "details": "Locate nearest emergency shelter"},
        {"action": "evacuation_guidance", "priority": "high", "details": "Provide evacuation routes based on disaster type"},
        {"action": "supply_info", "priority": "medium", "details": "Locate nearest emergency supply distribution points"},
    ],
    "general": [
        {"action": "assess_situation", "priority": "low", "details": "Gathering more information about the situation"},
        {"action": "standby", "priority": "low", "details": "System monitoring - ready to escalate if needed"},
    ],
}

# Recommendations by intent
RECOMMENDATIONS = {
    "sos": [
        "Stay calm and remain in your current location if safe",
        "Keep your phone charged and accessible",
        "If possible, move to a visible, well-lit area",
        "Make noise or signal for help if you can do so safely",
        "Help is being dispatched to your location",
    ],
    "fire": [
        "Evacuate the building immediately - do NOT use elevators",
        "Stay low to the ground to avoid smoke inhalation",
        "Feel doors before opening - if hot, use an alternate route",
        "Call out to alert others in the building",
        "Meet at a designated assembly point away from the building",
        "Do NOT re-enter the building for any reason",
    ],
    "medical": [
        "Do not move the person unless they are in immediate danger",
        "Check for breathing and pulse",
        "Apply pressure to any bleeding wounds",
        "Keep the person warm and comfortable",
        "Clear the airway if the person is unconscious",
        "Note the time symptoms began for emergency responders",
    ],
    "accident": [
        "Do not move injured persons unless there is danger of fire/explosion",
        "Turn on hazard lights and set up warning triangles",
        "Check for injuries in all vehicles involved",
        "Do not admit fault at the scene",
        "Document the scene with photos if safely possible",
        "Exchange information with other parties involved",
    ],
    "crime": [
        "Move to a safe location if possible",
        "Do not confront the perpetrator",
        "Try to remember physical descriptions and details",
        "Preserve any evidence - do not touch or clean the area",
        "Lock doors and windows if sheltering in place",
        "Stay on the phone with emergency services if possible",
    ],
    "natural_disaster": [
        "Follow local emergency broadcasting instructions",
        "Move to higher ground if flooding is occurring",
        "Take cover under sturdy furniture during earthquakes",
        "Stay away from windows during storms",
        "Have emergency supplies ready (water, food, first aid)",
        "Keep important documents in a waterproof container",
    ],
    "general": [
        "If you feel unsafe, trigger the SOS button",
        "Stay aware of your surroundings",
        "Keep your emergency contacts updated",
    ],
}


class DecisionEngine:
    """Determines optimal response actions based on emergency analysis."""

    def decide(self, intent_result: Dict, risk_result: Dict, location_result: Dict) -> Dict:
        """
        Make decisions about what actions to take.
        
        Args:
            intent_result: Output from IntentAgent
            risk_result: Output from RiskAgent
            location_result: Output from LocationAgent
            
        Returns:
            dict with actions, recommendations, and priority
        """
        intent = intent_result.get("intent", "general")
        risk_level = risk_result.get("level", "low")
        risk_score = risk_result.get("score", 0)

        # Get base actions for this intent
        actions = self._get_actions(intent, risk_level)

        # Enhance actions with location data
        actions = self._enhance_with_location(actions, location_result)

        # Get recommendations
        recommendations = RECOMMENDATIONS.get(intent, RECOMMENDATIONS["general"])

        # Add risk-specific recommendations
        if risk_level == "critical":
            recommendations.insert(0, "[!] CRITICAL EMERGENCY - Help is being dispatched immediately")
        elif risk_level == "high":
            recommendations.insert(0, "[!] HIGH RISK situation detected - Emergency services alerted")

        return {
            "actions": actions,
            "recommendations": recommendations,
            "overall_priority": risk_level,
            "response_summary": self._generate_summary(intent, risk_level, risk_score),
        }

    def _get_actions(self, intent: str, risk_level: str) -> List[Dict]:
        """Get action list based on intent, adjusted for risk level."""
        base_actions = ACTION_TEMPLATES.get(intent, ACTION_TEMPLATES["general"])
        
        # Deep copy and add status
        actions = []
        for a in base_actions:
            action = {**a, "status": "executing"}
            actions.append(action)

        # For lower risk levels, downgrade some actions
        if risk_level == "low":
            for action in actions:
                if action["priority"] == "critical":
                    action["priority"] = "medium"
                    action["status"] = "standby"

        return actions

    def _enhance_with_location(self, actions: List[Dict], location_result: Dict) -> List[Dict]:
        """Add location context to actions."""
        nearby = location_result.get("nearby_services", [])
        address = location_result.get("address", "Unknown location")

        for action in actions:
            if "hospital" in action["action"] or "ambulance" in action["action"] or "medical" in action["action"]:
                hospitals = [s for s in nearby if s["type"] in ("hospital", "clinic")]
                if hospitals:
                    nearest = hospitals[0]
                    action["details"] += f" — Nearest: {nearest['name']}"
                    if nearest.get("phone"):
                        action["details"] += f" (📞 {nearest['phone']})"

            elif "police" in action["action"]:
                police = [s for s in nearby if s["type"] == "police"]
                if police:
                    nearest = police[0]
                    action["details"] += f" - Nearest: {nearest['name']}"
                    if nearest.get("phone"):
                        action["details"] += f" (Tel: {nearest['phone']})"

            elif "fire" in action["action"]:
                fire_stations = [s for s in nearby if s["type"] == "fire_station"]
                if fire_stations:
                    nearest = fire_stations[0]
                    action["details"] += f" - Nearest: {nearest['name']}"
                    if nearest.get("phone"):
                        action["details"] += f" (Tel: {nearest['phone']})"

        return actions

    def _generate_summary(self, intent: str, risk_level: str, risk_score: int) -> str:
        """Generate a human-readable response summary."""
        intent_labels = {
            "sos": "SOS Emergency",
            "fire": "Fire Emergency",
            "medical": "Medical Emergency",
            "accident": "Accident Report",
            "crime": "Crime/Security Threat",
            "natural_disaster": "Natural Disaster",
            "general": "General Alert",
        }
        label = intent_labels.get(intent, "Emergency")
        return (
            f"{label} detected with {risk_level.upper()} risk level "
            f"(score: {risk_score}/100). Emergency protocols activated."
        )
