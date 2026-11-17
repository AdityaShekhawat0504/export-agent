import pytest

from app.services.risk_engine import evaluate_risk
from app.services.screening import normalise, screen_party


def test_normalise_drops_case_punctuation_and_legal_forms():
    assert normalise("Mahan Air Co.") == "mahan air"
    assert normalise("ROSOBORONEXPORT, JSC") == "rosoboronexport"


@pytest.mark.parametrize("name", ["MAHAN AIR", "Mahan Air Co.", "Rosoboronexport JSC"])
def test_listed_party_matches_despite_spelling_variants(name):
    hit = screen_party(name)
    assert hit is not None and hit["score"] >= 0.9


@pytest.mark.parametrize("name", ["ACME GmbH", "Bosch GmbH", "Air France", "", None])
def test_ordinary_companies_do_not_match(name):
    assert screen_party(name) is None


def test_custom_list_can_be_passed_in():
    assert screen_party("Evil Corp Ltd", denied=["Evil Corp"])["match"] == "Evil Corp"
    assert screen_party("Evil Corp Ltd", denied=[]) is None


def test_list_loaded_from_file(tmp_path, monkeypatch):
    f = tmp_path / "denied.txt"
    f.write_text("Shadow Trading LLC\n\n")
    monkeypatch.setenv("DENIED_PARTIES_FILE", str(f))
    assert screen_party("shadow trading")["match"] == "Shadow Trading LLC"


def test_strong_match_blocks_the_shipment():
    result = evaluate_risk("DE", 1.0, hs_code="8802.40", counterparty_name="Mahan Air Co.")
    assert result["status"] == "blocked"
    assert result["blocked"] is True
    assert result["reason"].startswith("Denied party match: Mahan Air")


def test_near_match_goes_to_review():
    result = evaluate_risk("DE", 1.0, hs_code="8802.40", counterparty_name="Mahaan Airlines")
    assert result["status"] == "review"
    assert result["reason"].startswith("Possible denied party match: Mahan Air")


def test_country_block_takes_precedence_over_party_screening():
    assert evaluate_risk("IR", 1.0, counterparty_name="Mahan Air")["reason"] == "Sanctioned country"
