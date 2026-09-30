import pytest
from src.genai_pipeline.pipeline import GenAIPipeline, GenAIUnavailableError

def test_genai_unavailable_requires_manual_review():
    sample_complaint = {
        "complaint_id": "CMP-TEST-001",
        "customer_name": "Sarah Connor",
        "customer_type": "VIP",
        "complaint_title": "Damaged laptop display on delivery",
        "complaint_description": "My NovaBook Pro arrived with a completely cracked screen. Order ORD-9921.",
        "order_reference": "ORD-9921",
        "product_or_service": "NovaBook Pro 16"
    }
    
    pipeline = GenAIPipeline()
    pipeline.api_keys = []
    with pytest.raises(GenAIUnavailableError):
        pipeline.generate_intelligence(sample_complaint)
