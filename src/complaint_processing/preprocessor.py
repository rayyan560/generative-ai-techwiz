import re
import hashlib
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

class ComplaintPreprocessor:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Performs unicode normalization, whitespace collapsing, and basic cleaning."""
        if not text:
            return ""
        # Unicode NFKD normalization
        text = unicodedata.normalize("NFKD", text)
        # Collapse multi-spaces & irregular newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    @staticmethod
    def extract_regex_entities(text: str) -> Dict[str, Any]:
        """Deterministic regex entity extraction for orders, amounts, dates, tracking numbers, and serials."""
        entities = {}
        
        # Order ID patterns: ORD-12345, NV-9876, #123456
        order_match = re.search(r"\b(ORD[-\s]?\d{4,8}|NV[-\s]?\d{4,8}|#[0-9]{5,8})\b", text, re.IGNORECASE)
        if order_match:
            entities["order_id"] = order_match.group(0).upper().replace(" ", "-")

        # Transaction ID patterns: TXN-12345, PAY-98765
        txn_match = re.search(r"\b(TXN[-\s]?[A-Z0-9]{5,10}|PAY[-\s]?[A-Z0-9]{5,10})\b", text, re.IGNORECASE)
        if txn_match:
            entities["transaction_id"] = txn_match.group(0).upper().replace(" ", "-")

        # Amount patterns: $129.99, USD 450, 450.00 dollars
        amount_match = re.search(r"(\$|USD\s*|EUR\s*|GBP\s*)?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|\d+)\s*(dollars|usd|bucks)?\b", text, re.IGNORECASE)
        if amount_match:
            raw_val = amount_match.group(2).replace(",", "")
            try:
                val = float(raw_val)
                if val > 0 and val < 100000:
                    entities["amount"] = val
                    entities["currency"] = "USD"
            except ValueError:
                pass

        # Tracking Number: TRK-9876543, DHL-987654, FEDEX-123456
        trk_match = re.search(r"\b(TRK[-\s]?[0-9]{6,12}|FEDEX[-\s]?[0-9]{6,12}|UPS[-\s]?[A-Z0-9]{6,12})\b", text, re.IGNORECASE)
        if trk_match:
            entities["tracking_number"] = trk_match.group(0).upper().replace(" ", "-")

        # Serial Number: SN-98765-X
        sn_match = re.search(r"\b(SN[-\s]?[A-Z0-9]{5,12})\b", text, re.IGNORECASE)
        if sn_match:
            entities["serial_number"] = sn_match.group(0).upper().replace(" ", "-")

        # Date pattern: YYYY-MM-DD, DD/MM/YYYY, or Month DD, YYYY
        date_match = re.search(r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b", text, re.IGNORECASE)
        if date_match:
            entities["incident_date"] = date_match.group(0)

        return entities

    @staticmethod
    def validate_complaint_input(title: str, description: str) -> Tuple[bool, Optional[str]]:
        """Validates complaint completeness and detects trivial or empty submissions."""
        if not title or len(title.strip()) < 3:
            return False, "Complaint title is too short or missing (minimum 3 characters required)."
        if not description or len(description.strip()) < 10:
            return False, "Complaint description is too short or empty (minimum 10 characters required)."
        return True, None

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Computes SHA-256 fingerprint of normalized text for exact duplicate detection."""
        norm = ComplaintPreprocessor.normalize_text(text).lower()
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """Calculates token Jaccard similarity between two texts for near-duplicate & repeat complaint detection."""
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)
