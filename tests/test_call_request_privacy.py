from fastapi.testclient import TestClient

from app import app
from routers.chat import ACTIVE_CALLS, STAFF_PRESENCE


def test_call_request_status_is_scoped_to_guest_cookie(monkeypatch):
    ACTIVE_CALLS.clear()
    monkeypatch.setitem(STAFF_PRESENCE["admin"], "online", True)
    client_a = TestClient(app)
    client_b = TestClient(app)

    created = client_a.post(
        "/api/call/initiate",
        json={"client_id": "another-customer", "client_name": "Impersonated Customer"},
    )
    assert created.status_code == 200
    call_id = created.json()["call_id"]
    assert ACTIVE_CALLS[call_id]["client_id"].startswith("guest:")
    assert ACTIVE_CALLS[call_id]["client_name"] == "Guest customer"

    own_status = client_a.get("/api/call/status")
    other_status = client_b.get("/api/call/status")
    assert own_status.json()["call"]["call_id"] == call_id
    assert other_status.json() == {"active": False, "status": "none"}
    ACTIVE_CALLS.clear()
