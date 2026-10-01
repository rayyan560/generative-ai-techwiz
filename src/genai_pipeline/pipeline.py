import json
import logging
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from config.settings import settings
from src.knowledge_base.manager import KnowledgeBaseManager
from src.prompt_templates.templates import SYSTEM_INSTRUCTION, build_complaint_analysis_prompt
from src.schemas.models import GenAIIntelligenceOutput
from src.security.prompt_defense import PromptDefense

logger = logging.getLogger("SupportNova.GenAIPipeline")


class GenAIUnavailableError(RuntimeError):
    pass


class GenAIPipeline:
    def __init__(self):
        self.api_keys = settings.GEMINI_API_KEYS
        self.current_key_idx = 0
        self.provider = "Google Gemini"
        self.model_name = settings.DEFAULT_MODEL

    def _get_next_api_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        key = self.api_keys[self.current_key_idx]
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        return key

    def _clean_json(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].removesuffix("```").strip()
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Provider response did not contain a JSON object.")
        return text[start:end + 1]

    def generate_intelligence(self, complaint_dict: Dict[str, Any]) -> GenAIIntelligenceOutput:
        title = complaint_dict.get("complaint_title", "")
        description = complaint_dict.get("complaint_description", "")
        suspicious, flags = PromptDefense.inspect_text_for_injections(f"{title} {description}")
        policies = KnowledgeBaseManager.retrieve_relevant_policy_chunks(
            category=complaint_dict.get("category", "General"),
            query=f"{title} {description}",
            top_k=3,
        )
        prompt = build_complaint_analysis_prompt(complaint_dict, policies)
        last_error = "No API key configured"

        for attempt in range(min(len(self.api_keys), 3)):
            key = self._get_next_api_key()
            if not key:
                break
            try:
                with genai.Client(
                    api_key=key,
                    http_options=types.HttpOptions(timeout=12000),
                ) as client:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            response_mime_type="application/json",
                            response_schema=GenAIIntelligenceOutput,
                        ),
                    )
                if not response.text:
                    raise ValueError("Provider returned an empty response.")
                data = json.loads(self._clean_json(response.text))
                data["complaint_id"] = complaint_dict.get("complaint_id", "CMP-00001")
                if suspicious:
                    data["adversarial_warning"] = "; ".join(flags)
                return GenAIIntelligenceOutput.model_validate(data)
            except Exception as error:
                last_error = type(error).__name__
                logger.warning("GenAI attempt %s failed (%s).", attempt + 1, last_error)

        logger.error("GenAI analysis unavailable (%s); human review required.", last_error)
        raise GenAIUnavailableError("GenAI analysis is unavailable; the complaint must be reviewed by a human.")


genai_pipeline = GenAIPipeline()
