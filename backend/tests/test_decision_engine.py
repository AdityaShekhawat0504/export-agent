from unittest.mock import AsyncMock

import pytest

from app.services import decision_engine
from app.services.decision_engine import classify_with_intelligence
from app.services.feedback_service import apply_feedback
from app.services.memory import find_memory, save_memory


@pytest.fixture
def fake_classifier(monkeypatch):
    mock = AsyncMock(return_value={"hs_code": "8501.10", "confidence": 0.9})
    monkeypatch.setattr(decision_engine, "classify_product", mock)
    return mock


async def test_memory_miss_uses_ai_and_stores_result(db, fake_classifier):
    result = await classify_with_intelligence(db, "Electric motor")

    assert result == {"hs_code": "8501.10", "confidence": 0.9, "source": "ai"}
    fake_classifier.assert_awaited_once_with("Electric motor")
    assert (await find_memory("electric motor", db)).hs_code == "8501.10"


async def test_weak_memory_is_ignored(db, fake_classifier):
    # Below the 0.95 trust threshold and not human-verified -> AI is called again.
    await save_memory("electric motor", "0000.00", 0.9, db)

    result = await classify_with_intelligence(db, "electric motor")

    assert result["source"] == "ai"
    fake_classifier.assert_awaited_once()


async def test_strong_ai_memory_is_reused(db, fake_classifier):
    await save_memory("electric motor", "8501.10", 0.95, db)

    result = await classify_with_intelligence(db, "electric motor")

    assert result == {"hs_code": "8501.10", "confidence": 0.95, "source": "memory"}
    fake_classifier.assert_not_awaited()


async def test_human_feedback_memory_is_trusted(db, fake_classifier):
    await apply_feedback("Lithium ion battery", "8507.60", db)
    await db.commit()

    result = await classify_with_intelligence(db, "lithium ion battery")

    assert result == {"hs_code": "8507.60", "confidence": 1.0, "source": "memory"}
    fake_classifier.assert_not_awaited()
    assert (await find_memory("lithium ion battery", db)).memory_hits == 1
