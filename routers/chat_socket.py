import datetime
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.chat_assistant import build_chat_welcome_message
from src.chat_response import generate_chat_response
from src.security.auth import AuthManager
from src.security.prompt_defense import PromptDefense

router = APIRouter(tags=["Customer and Staff Chat"])
logger = logging.getLogger("SupportNova.ChatSocket")

@router.websocket("/ws/chat")
async def chatbot_websocket(websocket: WebSocket, mode: str = "customer"):
    if mode not in {"customer", "admin"}:
        await websocket.close(code=1008)
        return
    if mode == "admin":
        token = websocket.cookies.get("supportnova_session")
        user = AuthManager.verify_session_token(token) if token else None
        if not user or user.get("role") not in {"admin", "agent", "warranty_manager"}:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    logger.info(f"Chatbot WebSocket connected - mode: {mode}")

    conversation_history: list = []

    await websocket.send_json({"type": "welcome", "content": build_chat_welcome_message(mode), "mode": mode})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Please send a valid message."})
                continue

            user_message = data.get("message") if isinstance(data, dict) else None
            if not isinstance(user_message, str):
                await websocket.send_json({"type": "error", "content": "Please send a text message."})
                continue
            user_message = user_message.strip()

            if not user_message:
                continue
            if len(user_message) > 4000:
                await websocket.send_json({"type": "error", "content": "Please keep messages under 4,000 characters."})
                continue

            suspicious, _ = PromptDefense.inspect_text_for_injections(user_message)
            if suspicious:
                await websocket.send_json({
                    "type": "error",
                    "content": "I can help with your service issue, but I cannot override safeguards or reveal internal instructions. Please describe the product or service problem.",
                })
                continue

            await websocket.send_json({"type": "typing", "content": "..."})

            bot_response = await generate_chat_response(mode, conversation_history, user_message)

            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": bot_response})

            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            await websocket.send_json({
                "type": "response",
                "content": bot_response,
                "mode": mode,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })

    except WebSocketDisconnect:
        logger.info(f"Chatbot WebSocket disconnected - mode: {mode}")
    except Exception as error:
        logger.error("Chatbot WebSocket error: %s", type(error).__name__)
        try:
            await websocket.send_json({"type": "error", "content": "Connection error. Please refresh and try again."})
        except Exception:
            logger.warning("Unable to send chatbot WebSocket error frame.")
