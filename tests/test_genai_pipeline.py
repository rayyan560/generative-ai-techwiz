import pytest
from src.genai_pipeline import pipeline as pipeline_module
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


def test_genai_pipeline_validates_provider_json(monkeypatch):
    class ModelClient:
        def __init__(self, **kwargs):
            self.models = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def generate_content(self, **kwargs):
            class Response:
                text = '{"primary_issue":"display damage","category":"Product Defect","subcategory":"Physical Damage","sentiment":"Negative","urgency":"High","priority":"P1","recommended_department":"Returns & Replacements","customer_response":"We will review your case."}'
            return Response()

    monkeypatch.setattr(pipeline_module.genai, "Client", ModelClient)
    monkeypatch.setattr(pipeline_module.KnowledgeBaseManager, "retrieve_relevant_policy_chunks", lambda **kwargs: [])
    monkeypatch.setattr(pipeline_module.PromptDefense, "inspect_text_for_injections", lambda text: (False, []))
    pipeline = GenAIPipeline()
    pipeline.api_keys = ["test-key"]
    result = pipeline.generate_intelligence({"complaint_id": "CMP-TEST-2", "complaint_title": "Screen broken"})
    assert result.complaint_id == "CMP-TEST-2"
    assert result.primary_issue == "display damage"
