import asyncio

import pytest
from fastapi import HTTPException

from routers.warranty import pre_check_complaint


def get_preview(title, description):
    return asyncio.run(pre_check_complaint(title, description, "Standard"))


def test_safety_preview_does_not_mislabel_other_escalation_as_battery_hazard():
    preview = get_preview("Unauthorized account access", "Someone accessed my account without permission.")

    assert preview["estimated_category"] == "Account Security"
    assert preview["estimated_priority"] == "P0"
    assert "security or privacy" in preview["safety_advisory"].lower()
    assert "battery" not in preview["safety_advisory"].lower()
    assert "warranty coverage" not in preview["safety_advisory"].lower()


def test_safety_preview_is_explicitly_advisory_and_non_diagnostic():
    preview = get_preview("Battery swelling", "The device battery is swollen and emitting smoke.")

    assert preview["estimated_category"] == "Safety Hazard"
    assert "not a diagnosis" in preview["safety_advisory"]
    assert "no GenAI analysis" in preview["preview_basis"]


def test_non_escalated_preview_does_not_claim_warranty_coverage():
    preview = get_preview("Where is my invoice?", "I cannot find the invoice for my recent order.")

    assert "did not detect a mandatory escalation trigger" in preview["safety_advisory"]
    assert "coverage" not in preview["safety_advisory"].lower()


def test_preview_rejects_missing_or_trivial_complaint_text():
    with pytest.raises(HTTPException) as error:
        get_preview("Hi", "Short")

    assert error.value.status_code == 400
