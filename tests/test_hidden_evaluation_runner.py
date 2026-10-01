import csv
import json

import pytest

from hidden_test_ready import evaluator_runner
from src.genai_pipeline.pipeline import GenAIUnavailableError


def test_missing_evaluator_input_fails_without_writing_a_report(tmp_path):
    input_path = tmp_path / "not-provided.json"
    output_path = tmp_path / "must-not-exist.csv"

    with pytest.raises(FileNotFoundError, match="Evaluator input file"):
        evaluator_runner.run_hidden_evaluation(str(input_path), str(output_path))

    assert not output_path.exists()


def test_existing_report_is_never_overwritten(tmp_path):
    input_path = tmp_path / "evaluator-cases.json"
    output_path = tmp_path / "historical-report.csv"
    input_path.write_text("[]", encoding="utf-8")
    output_path.write_text("historical evidence", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        evaluator_runner.run_hidden_evaluation(str(input_path), str(output_path))

    assert output_path.read_text(encoding="utf-8") == "historical evidence"


def test_unavailable_provider_is_reported_as_manual_review(monkeypatch, tmp_path):
    input_path = tmp_path / "evaluator-cases.json"
    output_path = tmp_path / "results.csv"
    input_path.write_text(
        json.dumps([{
            "complaint_id": "HIDDEN-TEST-001",
            "customer_name": "Local Test",
            "customer_type": "Standard",
            "complaint_title": "Cracked laptop display",
            "complaint_description": "The laptop screen arrived with a crack across one corner.",
            "customer_email": "review@example.com",
        }]),
        encoding="utf-8",
    )

    def provider_unavailable(_complaint):
        raise GenAIUnavailableError("Provider unavailable during local test.")

    monkeypatch.setattr(evaluator_runner.genai_pipeline, "generate_intelligence", provider_unavailable)

    evaluator_runner.run_hidden_evaluation(str(input_path), str(output_path), limit=1)

    with output_path.open(encoding="utf-8", newline="") as report_file:
        results = list(csv.DictReader(report_file))

    assert len(results) == 1
    assert results[0]["Complaint_ID"] == "HIDDEN-TEST-001"
    assert results[0]["Verification_Status"] == "Manual Review Required"
    assert results[0]["GenAI_Category"] == "Unavailable"
