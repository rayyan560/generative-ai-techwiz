from fastapi.testclient import TestClient

from app import app
from routers.chat import ACTIVE_CALLS, STAFF_PRESENCE
from src.security.auth import AuthManager


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


def test_judge_cannot_send_chat_upload_files_or_initiate_calls(monkeypatch):
    judge = {"user_id": "judge-test", "username": "judge", "role": "judge"}
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: judge))
    monkeypatch.setitem(STAFF_PRESENCE["admin"], "online", True)
    ACTIVE_CALLS.clear()
    client = TestClient(app)

    sent = client.post("/api/chat/live/send", json={"message": "not allowed"})
    uploaded = client.post(
        "/api/chat/upload-file",
        files={"file": ("judge-test.txt", b"not allowed", "text/plain")},
    )
    called = client.post("/api/call/initiate", json={})

    assert sent.status_code == 403
    assert uploaded.status_code == 403
    assert called.status_code == 403
    assert ACTIVE_CALLS == {}


def test_judge_communication_page_hides_customer_messages_and_actions(monkeypatch):
    judge = {"user_id": "judge-test", "username": "judge", "role": "judge"}
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: judge))

    response = TestClient(app).get("/admin?view=communication")

    assert response.status_code == 200
    assert "Judge read-only view" in response.text
    assert "Broadcast to Listed Customers" not in response.text
    assert 'id="adminReplyInput"' not in response.text
    assert "/api/chat/live/conversations" not in response.text
    assert "Loading chats..." not in response.text


def test_judge_page_has_single_read_only_status_without_floating_banner(monkeypatch):
    judge = {"user_id": "judge-test", "username": "judge", "role": "judge"}
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: judge))

    response = TestClient(app).get("/admin")

    assert response.status_code == 200
    assert response.text.count("Read-only mode") == 1
    assert "Judge review mode · read-only" not in response.text
    assert "Prompt Injection / Traps" in response.text
    assert "Manual Review Queue" in response.text
    assert "complaint-filter-pills" in response.text
    assert "ï¸" not in response.text


def test_refunds_page_has_aligned_columns_and_accessible_pagination(monkeypatch):
    admin = {"user_id": "admin-test", "username": "admin", "role": "admin"}
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: admin))

    response = TestClient(app).get("/refunds")

    assert response.status_code == 200
    ledger_table = response.text.split('id="refundsTable"', 1)[1].split("</table>", 1)[0]
    assert ledger_table.count("<th>") == 9
    assert 'id="refundsPaginationStatus" aria-live="polite"' in response.text
    assert 'aria-label="Previous refund records page"' in response.text
    assert 'aria-label="Next refund records page"' in response.text
    assert 'colspan="9"' in response.text
