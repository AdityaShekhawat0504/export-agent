import pytest

from app.services.risk_engine import SANCTIONED_COUNTRIES, evaluate_risk


@pytest.mark.parametrize("country", SANCTIONED_COUNTRIES)
def test_sanctioned_country_is_blocked_even_with_full_confidence(country):
    result = evaluate_risk(country, 1.0)
    assert result == {"status": "blocked", "blocked": True, "reason": "Sanctioned country"}


def test_low_confidence_goes_to_review():
    result = evaluate_risk("DE", 0.5)
    assert result["status"] == "review"
    assert result["blocked"] is False


def test_threshold_is_inclusive():
    assert evaluate_risk("DE", 0.75)["status"] == "approved"
    assert evaluate_risk("DE", 0.7499)["status"] == "review"


def test_high_confidence_is_approved():
    assert evaluate_risk("US", 0.9) == {
        "status": "approved",
        "blocked": False,
        "reason": "Compliant",
    }


def test_unknown_hs_code_goes_to_review_even_with_high_confidence():
    result = evaluate_risk("DE", 0.9, hs_code="UNKNOWN")
    assert result == {
        "status": "review",
        "blocked": False,
        "reason": "No HS classification available",
    }


def test_country_code_is_normalised():
    assert evaluate_risk(" ir ", 1.0)["status"] == "blocked"
