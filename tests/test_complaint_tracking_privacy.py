from fastapi.testclient import TestClient

from app import app
from routers import warranty


class ComplaintCollection:
    def find_one(self, query):
        return {
            "complaint_id": query["complaint_id"],
            "customer_email": "owner@example.com",
            "customer_name": "Private Customer",
            "complaint_title": "Damaged device",
            "complaint_description": "Private complaint details",
            "product_or_service": "NovaPhone",
            "status": "AI Pipeline Processing",
            "department": "Warranty & Repairs",
            "created_at": "2026-10-01 10:00:00",
        }


def test_complaint_tracking_requires_matching_email_and_returns_minimal_data(monkeypatch):
    monkeypatch.setattr(warranty, "get_complaints_col", ComplaintCollection)
    client = TestClient(app)

    denied = client.get("/api/complaints/track/CMP-00001?email=other%40example.com")
    assert denied.status_code == 404

    allowed = client.get("/api/complaints/track/CMP-00001?email=OWNER%40EXAMPLE.COM")
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["assigned_department"] == "Warranty & Repairs"
    assert payload["submitted_at"] == "2026-10-01 10:00:00"
    assert payload["official_update"]
    assert "customer_email" not in payload
    assert "customer_name" not in payload
    assert "complaint_description" not in payload
