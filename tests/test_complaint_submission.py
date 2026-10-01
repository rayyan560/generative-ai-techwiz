from fastapi.testclient import TestClient

from app import app
from routers import warranty


class InMemoryComplaintCollection:
    def __init__(self):
        self.records = []

    def find(self, query, **kwargs):
        return []

    def count_documents(self, query):
        return len(self.records)

    def insert_one(self, document):
        self.records.append(document)


def _submission_data(**overrides):
    data = {
        "customer_name": "Demo Tester",
        "customer_email": "demo@example.com",
        "customer_type": "Standard",
        "complaint_title": "Screen arrived cracked",
        "complaint_description": "The display arrived with a crack across one corner.",
        "preferred_channel": "Web Form",
    }
    data.update(overrides)
    return data


def test_valid_complaint_submission_creates_a_ticket_without_external_storage(monkeypatch):
    collection = InMemoryComplaintCollection()

    async def skip_background_processing(*args, **kwargs):
        return None

    monkeypatch.setattr(warranty, "get_complaints_col", lambda: collection)
    monkeypatch.setattr(warranty, "_process_complaint_bg", skip_background_processing)

    response = TestClient(app).post("/api/complaints/submit", data=_submission_data())

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["complaint_id"] == "CMP-00001"
    assert len(collection.records) == 1
    assert collection.records[0]["complaint_title"] == "Screen arrived cracked"


def test_complaint_submission_explains_title_minimum(monkeypatch):
    collection = InMemoryComplaintCollection()
    monkeypatch.setattr(warranty, "get_complaints_col", lambda: collection)

    response = TestClient(app).post(
        "/api/complaints/submit",
        data=_submission_data(complaint_title="ha", complaint_description="haha"),
    )

    assert response.status_code == 400
    assert "title" in response.json()["detail"].lower()
    assert collection.records == []


def test_complaint_submission_explains_description_minimum(monkeypatch):
    collection = InMemoryComplaintCollection()
    monkeypatch.setattr(warranty, "get_complaints_col", lambda: collection)

    response = TestClient(app).post(
        "/api/complaints/submit",
        data=_submission_data(complaint_description="haha"),
    )

    assert response.status_code == 400
    assert "description" in response.json()["detail"].lower()
    assert collection.records == []
