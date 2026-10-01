from pathlib import Path

import pytest
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


@pytest.mark.parametrize(
    ("route", "filename"),
    [
        ("project-walkthrough.mp4", "SupportNova_Project_Walkthrough_VoiceOver.mp4"),
        ("auth-docs-walkthrough.mp4", "SupportNova_Authentication_Documents_VoiceOver.mp4"),
    ],
)
def test_walkthroughs_are_served_as_playable_mp4(monkeypatch, route, filename):
    monkeypatch.setattr(
        AuthManager,
        "get_current_user",
        staticmethod(lambda request: {"user_id": "read-only-reviewer", "role": "judge"}),
    )

    response = TestClient(app).get(f"/project-docs/file/{route}")

    expected = Path("video_assets") / filename
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content[:8] == expected.read_bytes()[:8]


def test_project_walkthrough_supports_browser_range_requests(monkeypatch):
    monkeypatch.setattr(
        AuthManager,
        "get_current_user",
        staticmethod(lambda request: {"user_id": "read-only-reviewer", "role": "judge"}),
    )

    response = TestClient(app).get(
        "/project-docs/file/project-walkthrough.mp4",
        headers={"Range": "bytes=0-1023"},
    )

    assert response.status_code == 206
    assert response.headers["content-range"].startswith("bytes 0-1023/")
    assert response.headers["content-type"].startswith("video/mp4")
    assert len(response.content) == 1024
