import pytest
from src.genai_pipeline.pipeline import genai_pipeline
from src.schemas.models import GenAIIntelligenceOutput

def test_genai_pipeline_structure():
    sample_complaint = {
        "complaint_id": "CMP-TEST-001",
        "customer_name": "Sarah Connor",
        "customer_type": "VIP",
        "complaint_title": "Damaged laptop display on delivery",
        "complaint_description": "My NovaBook Pro arrived with a completely cracked screen. Order ORD-9921.",
        "order_reference": "ORD-9921",
        "product_or_service": "NovaBook Pro 16"
    }
    
    result = genai_pipeline.generate_intelligence(sample_complaint)
    assert isinstance(result, GenAIIntelligenceOutput)
    assert result.complaint_id == "CMP-TEST-001"
    assert result.category in ["Product Defect", "Delivery & Shipping"]
    assert result.recommended_department in ["Returns & Replacements", "Technical Support", "Logistics & Delivery"]
    assert len(result.resolution_steps) > 0
    assert result.customer_response is not None
