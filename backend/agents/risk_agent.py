"""
Risk Prediction Agent
Classifies the risk level of detected emergencies using a multi-factor scoring system.
"""

from typing import Dict
from datetime import datetime, timezone


# Risk weights by intent type
INTENT_BASE_RISK = {
    "sos": 85,
    "fire": 75,
    "crime": 70,
    "medical": 70,
    "accident": 65,
    "natural_disaster": 80,
    "general": 10,
}

# Keyword severity multipliers
CRITICAL_KEYWORDS = [
    "not breathing", "unconscious", "dying", "dead", "shooting",
    "stabbing", "bomb", "terrorist", "hostage", "kidnapping",
    "heart attack", "stroke", "tsunami", "earthquake", "murder",
    "trapped", "explosion", "collapsed",
]

HIGH_KEYWORDS = [
    "bleeding", "fire", "crash", "assault", "robbery", "gun",
    "knife", "seizure", "overdose", "flood", "tornado", "hurricane",
    "choking", "broken", "fracture", "intruder", "violence",
]


class RiskAgent:
    """Predicts risk level based on intent analysis and contextual factors."""

    def assess(self, intent_result: Dict, text: str = "", latitude: float = None, longitude: float = None) -> Dict:
        """
        Assess risk level.
        
        Args:
            intent_result: Output from IntentAgent
            text: Original emergency text
            latitude: User latitude
            longitude: User longitude
            
        Returns:
            dict with level, score (0-100), reasoning
        """
        intent = intent_result.get("intent", "general")
        confidence = intent_result.get("confidence", 0.0)
        text_lower = (text or "").lower()

        # 1. Base risk from intent type
        base_score = INTENT_BASE_RISK.get(intent, 10)
        reasoning = [f"Base risk for '{intent}': {base_score}"]

        # 2. Confidence modifier
        confidence_modifier = confidence * 15
        reasoning.append(f"Confidence modifier: +{confidence_modifier:.1f}")

        # 3. Keyword severity check
        critical_count = sum(1 for kw in CRITICAL_KEYWORDS if kw in text_lower)
        high_count = sum(1 for kw in HIGH_KEYWORDS if kw in text_lower)
        
        keyword_modifier = critical_count * 15 + high_count * 8
        if critical_count > 0:
            reasoning.append(f"Critical keywords detected ({critical_count}): +{critical_count * 15}")
        if high_count > 0:
            reasoning.append(f"High-severity keywords detected ({high_count}): +{high_count * 8}")

        # 4. Time-of-day factor (nighttime = higher risk)
        now = datetime.now(timezone.utc)
        hour = now.hour
        time_modifier = 0
        if hour >= 22 or hour <= 5:
            time_modifier = 5
            reasoning.append("Nighttime risk factor: +5")

        # 5. Multiple intent detection (indicates complex emergency)
        all_intents = intent_result.get("all_intents", {})
        if len(all_intents) > 1:
            multi_modifier = len(all_intents) * 3
            reasoning.append(f"Multiple emergency types detected ({len(all_intents)}): +{multi_modifier}")
        else:
            multi_modifier = 0

        # 6. Text length / detail factor
        word_count = len(text_lower.split()) if text_lower else 0
        detail_modifier = 0
        if word_count > 20:
            detail_modifier = 3
            reasoning.append("Detailed description provided: +3")

        # Calculate final score
        total_score = min(100, int(
            base_score + confidence_modifier + keyword_modifier +
            time_modifier + multi_modifier + detail_modifier
        ))

        # Determine level
        level = self._score_to_level(total_score)
        reasoning.append(f"Final risk score: {total_score}/100 → {level.upper()}")

        return {
            "level": level,
            "score": total_score,
            "reasoning": " | ".join(reasoning),
        }

    def _score_to_level(self, score: int) -> str:
        """Convert numeric score to risk level."""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 35:
            return "medium"
        else:
            return "low"
