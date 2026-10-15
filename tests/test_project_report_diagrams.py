from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_report_contains_required_analysis_diagrams():
    report = (PROJECT_ROOT / "PROJECT_REPORT.md").read_text(encoding="utf-8")
    diagrams = report.split("### Required Design Diagrams", 1)[1].split("## 4. Database", 1)[0]

    assert "#### Data-Flow Diagram" in diagrams
    assert "#### Use-Case Diagram" in diagrams
    assert "#### Activity Diagram" in diagrams
    assert "#### Sequence Diagram" in diagrams
    assert diagrams.count("```mermaid") == 4
    assert "sequenceDiagram" in diagrams
    assert "not parallel in orchestration" in report
