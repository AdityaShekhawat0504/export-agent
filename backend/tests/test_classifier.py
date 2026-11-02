from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import classifier
from app.services.classifier import classify_product


def _fake_openai(monkeypatch, *, content=None, error=None):
    """Replace AsyncOpenAI with a mock returning `content` (or raising `error`)."""
    create = AsyncMock()
    if error is not None:
        create.side_effect = error
    else:
        create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )
    client = MagicMock()
    client.chat.completions.create = create
    monkeypatch.setattr(classifier, "AsyncOpenAI", MagicMock(return_value=client))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return create


@pytest.mark.parametrize("description", ["", "   "])
async def test_empty_description_is_unknown(description):
    assert await classify_product(description) == {"hs_code": "UNKNOWN", "confidence": 0.0}


async def test_without_api_key_returns_fallback():
    assert await classify_product("electric motor") == {"hs_code": "8501.10", "confidence": 0.82}


async def test_extracts_hs_code_from_model_output(monkeypatch):
    create = _fake_openai(monkeypatch, content="  HS code: 8507.60 (lithium-ion)  ")
    result = await classify_product("Lithium ion battery")
    assert result == {"hs_code": "8507.60", "confidence": 0.9}
    create.assert_awaited_once()
    assert create.await_args.kwargs["messages"][-1]["content"] == "Lithium ion battery"


async def test_unparseable_model_output_is_unknown(monkeypatch):
    _fake_openai(monkeypatch, content="I am not sure")
    assert await classify_product("mystery item") == {"hs_code": "UNKNOWN", "confidence": 0.9}


async def test_api_error_returns_low_confidence_fallback(monkeypatch):
    _fake_openai(monkeypatch, error=RuntimeError("network down"))
    assert await classify_product("pump") == {"hs_code": "8501.10", "confidence": 0.5}
