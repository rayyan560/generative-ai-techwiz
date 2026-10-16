from typing import Any, Dict, List

from src.knowledge_base.manager import KnowledgeBaseManager
from src.security.prompt_defense import PromptDefense
from src.genai_pipeline.pipeline_errors import GenAIUnavailableError


def ensure_complaint_is_safe(complaint: Dict[str, Any]) -> None:
    title = complaint.get("complaint_title", "")
    description = complaint.get("complaint_description", "")
    suspicious, flags = PromptDefense.inspect_text_for_injections(f"{title} {description}")
    if suspicious:
        complaint["adversarial_input_warnings"] = flags
        raise GenAIUnavailableError("Adversarial instructions were detected in complaint text; the complaint must be reviewed by a human.")


def prepare_policy_context(complaint: Dict[str, Any]) -> List[Dict[str, Any]]:
    title = complaint.get("complaint_title", "")
    description = complaint.get("complaint_description", "")
    policies = KnowledgeBaseManager.retrieve_relevant_policy_chunks(
        category=complaint.get("category", "General"),
        query=f"{title} {description}",
        top_k=3,
    )
    policies = [
        policy for policy in policies
        if str(policy.get("status", "")).strip().casefold() == "active"
        and str(policy.get("document_id", "")).strip()
        and str(policy.get("content", "")).strip()
    ]
    if not policies:
        raise GenAIUnavailableError("No active policy source is indexed; the complaint must be reviewed by a human.")
    suspicious_sources = []
    for policy in policies:
        malicious, source_flags = PromptDefense.inspect_text_for_injections(str(policy.get("content", "")))
        if malicious:
            suspicious_sources.append({
                "document_id": str(policy.get("document_id", "Unknown")),
                "section_id": str(policy.get("section_id", "Unknown")),
                "flags": source_flags,
            })
    if suspicious_sources:
        complaint["policy_source_warnings"] = suspicious_sources
        raise GenAIUnavailableError("A retrieved policy source contains suspicious instructions; the complaint must be reviewed by a human.")
    complaint["retrieved_policy_sources"] = [
        {
            "document_id": str(policy.get("document_id", "")).strip(),
            "section_id": str(policy.get("section_id", "")).strip(),
            "version": str(policy.get("version", "")).strip(),
            "status": str(policy.get("status", "")).strip(),
        }
        for policy in policies
        if policy.get("document_id")
    ]
    return policies
