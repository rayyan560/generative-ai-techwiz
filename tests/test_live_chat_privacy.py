from fastapi.testclient import TestClient

from app import app
from routers import chat_messages


class InMemoryChatCollection:
    def __init__(self):
        self.messages = []

    def find(self, query):
        return [message.copy() for message in self.messages if message.get("client_id") == query.get("client_id")]

    def insert_one(self, document):
        self.messages.append(document.copy())


def test_anonymous_live_chat_messages_are_isolated_per_guest_cookie(monkeypatch):
    collection = InMemoryChatCollection()
    monkeypatch.setattr(chat_messages, "get_live_chats_col", lambda: collection)
    customer_one = TestClient(app)
    customer_two = TestClient(app)

    sent = customer_one.post("/api/chat/live/send", json={"message": "My account needs help."})
    own_messages = customer_one.get("/api/chat/live/messages")
    other_messages = customer_two.get("/api/chat/live/messages")

    assert sent.status_code == 200
    assert sent.json()["message"]["client_id"].startswith("guest:")
    assert len(own_messages.json()["messages"]) == 1
    assert other_messages.json()["messages"] == []


def test_live_chat_rejects_non_text_and_oversized_messages_without_storing(monkeypatch):
    collection = InMemoryChatCollection()
    monkeypatch.setattr(chat_messages, "get_live_chats_col", lambda: collection)
    client = TestClient(app)

    non_text = client.post("/api/chat/live/send", json={"message": ["not", "text"]})
    oversized = client.post("/api/chat/live/send", json={"message": "x" * 4001})

    assert non_text.status_code == 400
    assert oversized.status_code == 413
    assert collection.messages == []
