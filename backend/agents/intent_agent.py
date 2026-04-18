"""
Intent Analysis Agent
Detects the type of emergency from user text input using keyword matching 
and pattern analysis. Lightweight and reliable alternative to BERT.
"""

import re
from typing import Dict, List, Tuple


# Emergency intent categories with weighted keywords
INTENT_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
    "fire": [
        ("fire", 0.9), ("burning", 0.85), ("smoke", 0.8), ("flames", 0.9),
        ("blaze", 0.85), ("arson", 0.9), ("combustion", 0.7), ("inferno", 0.9),
        ("wildfire", 0.9), ("house fire", 1.0), ("building fire", 1.0),
        ("gas leak", 0.7), ("explosion", 0.8), ("burnt", 0.7),
    ],
    "medical": [
        ("heart attack", 1.0), ("stroke", 0.95), ("bleeding", 0.85),
        ("unconscious", 0.9), ("not breathing", 1.0), ("choking", 0.9),
        ("seizure", 0.9), ("allergic reaction", 0.85), ("overdose", 0.9),
        ("chest pain", 0.9), ("broken bone", 0.8), ("fracture", 0.8),
        ("wound", 0.7), ("injury", 0.75), ("hurt", 0.6), ("pain", 0.5),
        ("ambulance", 0.9), ("doctor", 0.6), ("hospital", 0.6),
        ("fainted", 0.85), ("collapsed", 0.85), ("diabetic", 0.7),
        ("breathing difficulty", 0.9), ("cant breathe", 0.95),
        ("medical", 0.6), ("sick", 0.4), ("vomiting", 0.6), ("poison", 0.85),
    ],
    "accident": [
        ("crash", 0.9), ("collision", 0.9), ("accident", 0.85),
        ("car accident", 1.0), ("vehicle", 0.6), ("hit and run", 0.95),
        ("rollover", 0.9), ("pile up", 0.85), ("wreck", 0.85),
        ("derailment", 0.9), ("trapped", 0.8), ("pinned", 0.8),
        ("motorcycle", 0.5), ("truck", 0.4), ("pedestrian hit", 0.95),
    ],
    "crime": [
        ("robbery", 0.95), ("theft", 0.8), ("assault", 0.9),
        ("attack", 0.8), ("shooting", 1.0), ("stabbing", 1.0),
        ("kidnapping", 1.0), ("murder", 1.0), ("burglar", 0.9),
        ("break in", 0.85), ("intruder", 0.9), ("gun", 0.85),
        ("knife", 0.7), ("weapon", 0.8), ("threatening", 0.75),
        ("stalker", 0.8), ("harassing", 0.7), ("violence", 0.85),
        ("police", 0.5), ("stolen", 0.75), ("mugging", 0.9),
        ("hostage", 1.0), ("bomb", 1.0), ("terrorist", 1.0),
    ],
    "natural_disaster": [
        ("earthquake", 1.0), ("flood", 0.95), ("tsunami", 1.0),
        ("hurricane", 1.0), ("tornado", 1.0), ("cyclone", 1.0),
        ("landslide", 0.95), ("avalanche", 0.95), ("volcanic", 0.95),
        ("storm", 0.7), ("lightning", 0.7), ("hail", 0.6),
        ("drought", 0.6), ("mudslide", 0.9), ("sinkhole", 0.85),
    ],
}

# Urgency amplifiers
URGENCY_WORDS = [
    "help", "please", "urgent", "emergency", "hurry", "quick",
    "fast", "now", "immediately", "dying", "dead", "critical",
    "serious", "severe", "terrible", "horrible", "desperate",
    "save", "rescue", "sos", "911", "danger", "dangerous",
]


class IntentAgent:
    """Analyzes text to detect emergency intent."""

    def analyze(self, text: str) -> Dict:
        """
        Analyze input text and return intent classification.
        
        Returns:
            dict with intent, confidence, keywords_found, all_intents
        """
        if not text or not text.strip():
            return {
                "intent": "general",
                "confidence": 0.0,
                "keywords_found": [],
                "all_intents": {},
            }

        text_lower = text.lower().strip()
        
        # Check for direct SOS
        if self._is_sos(text_lower):
            return {
                "intent": "sos",
                "confidence": 1.0,
                "keywords_found": ["SOS"],
                "all_intents": {"sos": 1.0},
            }

        # Score each intent category
        intent_scores: Dict[str, float] = {}
        intent_keywords: Dict[str, List[str]] = {}

        for intent, keywords in INTENT_KEYWORDS.items():
            score, found = self._score_intent(text_lower, keywords)
            if score > 0:
                intent_scores[intent] = score
                intent_keywords[intent] = found

        # Apply urgency boost
        urgency_boost = self._urgency_score(text_lower)

        # Find the best match
        if not intent_scores:
            return {
                "intent": "general",
                "confidence": max(0.1, urgency_boost * 0.5),
                "keywords_found": [],
                "all_intents": {},
            }

        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = min(1.0, intent_scores[best_intent] + urgency_boost * 0.1)

        return {
            "intent": best_intent,
            "confidence": round(best_score, 3),
            "keywords_found": intent_keywords.get(best_intent, []),
            "all_intents": {k: round(v, 3) for k, v in intent_scores.items()},
        }

    def _is_sos(self, text: str) -> bool:
        """Check if the input is a direct SOS call."""
        sos_patterns = [
            r'\bsos\b', r'\b911\b', r'\bhelp\s*me\b', r'\bsave\s*me\b',
            r'\bemergency\b', r'\bmayday\b',
        ]
        return any(re.search(p, text) for p in sos_patterns)

    def _score_intent(self, text: str, keywords: List[Tuple[str, float]]) -> Tuple[float, List[str]]:
        """Score text against a list of keywords."""
        total_score = 0.0
        found = []

        for keyword, weight in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                total_score += weight
                found.append(keyword)

        # Normalize: cap at 1.0, scale by number of matches
        if found:
            normalized = min(1.0, total_score / max(len(found), 1))
            return normalized, found
        return 0.0, []

    def _urgency_score(self, text: str) -> float:
        """Calculate urgency score from urgency words."""
        count = sum(1 for word in URGENCY_WORDS if re.search(r'\b' + re.escape(word) + r'\b', text))
        return min(1.0, count * 0.15)
