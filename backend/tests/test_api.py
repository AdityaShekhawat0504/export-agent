"""End-to-end through the HTTP layer, with SQLite instead of Postgres.

httpx's ASGITransport does not run the app lifespan, so no Postgres connection
is attempted; the DB dependency is overridden with the test session factory.
"""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import get_db
from app.main import app
from app.services import decision_engine


@pytest.fixture
async def client(session_factory, monkeypatch):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    monkeypatch.setattr(
        decision_engine,
        "classify_product",
        AsyncMock(return_value={"hs_code": "8501.10", "confidence": 0.9}),
    )
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _shipment(description="Electric motor", country="DE"):
    return {
        "description": description,
        "destination_country": country,
        "counterparty_name": "ACME GmbH",
    }


async def test_health(client):
    response = await client.get("/health")
    assert response.json() == {"status": "ok"}


async def test_approved_shipment(client):
    body = (await client.post("/shipments", json=_shipment())).json()
    assert body["status"] == "approved"
    assert body["blocked"] is False
    assert body["hs_code"] == "8501.10"
    assert body["decision_reason"] == "Compliant (ai)"


async def test_sanctioned_shipment_is_blocked(client):
    body = (await client.post("/shipments", json=_shipment(country="IR"))).json()
    assert body["status"] == "blocked"
    assert body["blocked"] is True


async def test_feedback_then_shipment_uses_memory(client):
    response = await client.post(
        "/feedback", json={"description": "Lithium ion battery", "hs_code": "8507.60"}
    )
    assert response.json() == {
        "message": "Feedback applied successfully",
        "hs_code": "8507.60",
        "source": "human_feedback",
    }

    body = (await client.post("/shipments", json=_shipment("lithium ion battery"))).json()
    assert body["hs_code"] == "8507.60"
    assert body["source"] == "memory"
    assert body["decision_reason"] == "Compliant (memory)"


async def test_list_shipments(client):
    await client.post("/shipments", json=_shipment())
    await client.post("/shipments", json=_shipment(country="KP"))
    statuses = sorted(s["status"] for s in (await client.get("/shipments")).json())
    assert statuses == ["approved", "blocked"]


async def test_invalid_payload_is_rejected(client):
    assert (await client.post("/shipments", json={"description": "x"})).status_code == 422
