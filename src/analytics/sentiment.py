import re
from typing import Dict, Any, List

class SentimentTelemetryEngine:
    """Estimates sentiment from complaint text using a keyword heuristic."""

    FRUSTRATION_TRIGGERS = {
        "critical_furious": ["unacceptable", "furious", "lawsuit", "lawyer", "attorney", "scam", "fraud", "police", "legal action", "garbage", "trash", "worst", "disaster", "horrible"],
        "high_frustration": ["broken", "cracked", "defective", "hazard", "fire", "danger", "swelling", "exploded", "smoke", "failed", "terrible", "useless", "ridiculous", "chargeback", "urgent", "immediate"],
        "moderate_dissatisfaction": ["disappointed", "poor", "slow", "delayed", "wrong", "missing", "damaged", "issue", "problem", "faulty", "not working", "replace", "refund"],
        "polite_constructive": ["please", "kindly", "appreciate", "help", "assist", "inquiry", "thank you", "regards", "understand"]
    }

    @classmethod
    def analyze(cls, title: str, description: str, customer_tier: str = "Standard") -> Dict[str, Any]:
        text = f"{title} {description}".lower()
        
        furious_hits = [w for w in cls.FRUSTRATION_TRIGGERS["critical_furious"] if w in text]
        high_hits = [w for w in cls.FRUSTRATION_TRIGGERS["high_frustration"] if w in text]
        mod_hits = [w for w in cls.FRUSTRATION_TRIGGERS["moderate_dissatisfaction"] if w in text]
        polite_hits = [w for w in cls.FRUSTRATION_TRIGGERS["polite_constructive"] if w in text]

        # Calculate Frustration Score (0 - 100)
        base_score = (len(furious_hits) * 35) + (len(high_hits) * 20) + (len(mod_hits) * 10) - (len(polite_hits) * 8)
        
        # Punctuation & capitalization intensity
        exclamations = text.count("!")
        caps_ratio = sum(1 for c in f"{title} {description}" if c.isupper()) / max(len(title + description), 1)
        if caps_ratio > 0.25:
            base_score += 18
        if exclamations >= 2:
            base_score += 12

        # Customer tier multiplier
        if customer_tier in ["VIP", "Corporate"]:
            base_score += 10

        frustration_index = max(12, min(98, int(base_score) if base_score > 0 else 24))
        
        # Determine Sentiment Polarity (-1.0 to +1.0)
        sentiment_polarity = round(max(-1.0, min(0.3, 0.2 - (frustration_index / 100) * 1.2)), 2)

        # Classify Emotional State & Color Heat
        if frustration_index >= 75 or len(furious_hits) > 0:
            emotion_state = "Strongly negative text signals"
            heat_level = "Critical Red"
            heat_color = "#e11d48"
        elif frustration_index >= 50 or len(high_hits) > 0:
            emotion_state = "Negative text signals"
            heat_level = "High Amber"
            heat_color = "#f59e0b"
        elif frustration_index >= 30:
            emotion_state = "Some negative text signals"
            heat_level = "Moderate Sky"
            heat_color = "#0ea5e9"
        else:
            emotion_state = "No strong negative text signals"
            heat_level = "Low Emerald"
            heat_color = "#10b981"

        # Unique detected keywords
        all_keywords = list(set(furious_hits + high_hits + mod_hits))[:6]
        if not all_keywords:
            all_keywords = ["general dispute"]

        return {
            "frustration_score": frustration_index,
            "sentiment_polarity": sentiment_polarity,
            "emotion_state": emotion_state,
            "heat_level": heat_level,
            "heat_color": heat_color,
            "urgency_flag": "Sentiment estimate only; determine urgency from independent complaint rules.",
            "key_emotional_triggers": all_keywords,
            "text_tone_estimate": "Strongly negative" if frustration_index > 70 else "Negative or concerned" if frustration_index > 40 else "Neutral or positive"
        }
