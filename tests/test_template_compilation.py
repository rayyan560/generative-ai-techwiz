from fastapi.testclient import TestClient

from app import PROJECT_DOCUMENTS, app, templates
from src.security.auth import AuthManager


def test_all_jinja_templates_compile():
    template_names = templates.env.list_templates()
    assert template_names
    for template_name in template_names:
        templates.get_template(template_name)


def test_react_tracker_is_mounted_and_assets_are_served():
    client = TestClient(app)
    portal = client.get("/")
    assert portal.status_code == 200
    assert 'id="reactComplaintTracker"' in portal.text
    assert "/static/react/complaint-tracker.js" in portal.text
    assert client.get("/static/react/complaint-tracker.js").status_code == 200
    assert client.get("/static/react/complaint-tracker.css").status_code == 200


def test_staff_dashboards_and_each_document_page_render_for_admin(monkeypatch):
    monkeypatch.setattr(
        AuthManager,
        "get_current_user",
        staticmethod(lambda request: {"user_id": "smoke-test-admin", "role": "admin"}),
    )
    client = TestClient(app)
    paths = [
        "/admin",
        "/agent",
        "/warranty",
        "/communication",
        "/refunds",
        "/knowledge",
        "/rules",
        "/analytics",
        "/admin/documents",
        *(f"/admin/documents/{slug}" for slug in PROJECT_DOCUMENTS),
    ]

    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        assert response.text.strip(), f"{path} returned an empty page"
