import asyncio
import logging

from config.settings import settings
from src.chat_assistant import (
    build_admin_chatbot_system_prompt,
    build_chat_fallback_response,
    build_customer_chatbot_system_prompt,
    call_gemini_chat,
    get_complaints_summary_for_admin,
)


logger = logging.getLogger("SupportNova.ChatSocket")


async def generate_chat_response(mode: str, history: list, user_message: str) -> str:
    if mode == "admin":
        summary = await asyncio.get_running_loop().run_in_executor(None, get_complaints_summary_for_admin)
        system_prompt = build_admin_chatbot_system_prompt(summary)
    else:
        system_prompt = build_customer_chatbot_system_prompt()
    response = None
    last_error = None
    for attempt, key in enumerate(settings.GEMINI_API_KEYS):
        try:
            response = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda api_key=key: call_gemini_chat(
                    api_key, settings.DEFAULT_MODEL, system_prompt, history, user_message
                ),
            )
            if response:
                break
        except Exception as error:
            last_error = type(error).__name__
            logger.warning("Chatbot Gemini attempt %s failed: %s", attempt + 1, last_error)
    if not response:
        logger.warning("Chatbot API failed; using safe fallback. Last error type: %s", last_error)
        return build_chat_fallback_response(mode, user_message)
    return response
