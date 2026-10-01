from fastapi.testclient import TestClient

from app import app, templates


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
