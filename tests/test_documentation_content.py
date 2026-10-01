from pathlib import Path

from fastapi.testclient import TestClient

from app import PROJECT_DOCUMENTS, TOPIC_DETAILS, app, build_document_sections
from src.security.auth import AuthManager


def test_every_project_document_topic_has_specific_content():
    for slug, document in PROJECT_DOCUMENTS.items():
        sections = build_document_sections(document)["sections"]
        assert len(sections) == len(document["topics"]), slug
        for section in sections:
            assert section["title"] in TOPIC_DETAILS
            assert len(section["summary"]) >= 80
            assert len(section["points"]) >= 3
            assert all(point.strip() for point in section["points"])


def test_documents_hub_lists_both_project_walkthroughs(monkeypatch):
    monkeypatch.setattr(
        AuthManager,
        "get_current_user",
        staticmethod(lambda request: {"user_id": "read-only-reviewer", "role": "judge"}),
    )

    response = TestClient(app).get("/admin/documents/demo-videos")

    assert response.status_code == 200
    assert "Full Project Walkthrough" in response.text
    assert "Authentication and Documents Walkthrough" in response.text
    assert "/project-docs/file/project-walkthrough.mp4" in response.text
    assert "/project-docs/file/auth-docs-walkthrough.mp4" in response.text


def test_project_walkthrough_is_served_as_playable_mp4(monkeypatch):
    monkeypatch.setattr(
        AuthManager,
        "get_current_user",
        staticmethod(lambda request: {"user_id": "read-only-reviewer", "role": "judge"}),
    )

    response = TestClient(app).get("/project-docs/file/project-walkthrough.mp4")

    expected = Path("video_assets/SupportNova_Project_Walkthrough_VoiceOver.mp4")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content[:8] == expected.read_bytes()[:8]
