import json

from src.multimodal import vision_forensics
from src.multimodal.image_validation import detect_image_type
from src.multimodal.vision_forensics import VisionForensicsEngine


def test_image_signature_detection_rejects_mime_spoofing():
    assert detect_image_type(b"\x89PNG\r\n\x1a\nrest") == "image/png"
    assert detect_image_type(b"\xff\xd8\xffrest") == "image/jpeg"
    assert detect_image_type(b"not an image") is None


def test_vision_without_api_key_requires_manual_review(monkeypatch):
    monkeypatch.setattr(vision_forensics.settings, "GEMINI_API_KEYS", [])
    result = VisionForensicsEngine.analyze_image(b"image", "image/png")
    assert result["status"] == "manual_review_required"
    assert result["manual_review_required"] is True
    assert "confidence_score" not in result


def test_vision_provider_output_is_labeled_advisory(monkeypatch):
    class ModelClient:
        def __init__(self, **kwargs):
            self.models = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def generate_content(self, **kwargs):
            class Response:
                text = json.dumps({
                    "visible_issue": "A visible crack on the outer glass",
                    "observations": ["The outer glass appears cracked"],
                    "severity": "high",
                    "potential_safety_hazard": False,
                    "serial_number_visible": False,
                    "serial_number": None,
                    "recommended_next_step": "Staff should inspect the device",
                })
            return Response()

    monkeypatch.setattr(vision_forensics.settings, "GEMINI_API_KEYS", ["test-key"])
    monkeypatch.setattr(vision_forensics.settings, "DEFAULT_MODEL", "test-model")
    monkeypatch.setattr(vision_forensics.genai, "Client", ModelClient)
    result = VisionForensicsEngine.analyze_image(b"\x89PNG\r\n\x1a\nrest", "image/png")
    assert result["status"] == "analyzed"
    assert result["manual_review_required"] is True
    assert result["visible_issue"] == "A visible crack on the outer glass"
