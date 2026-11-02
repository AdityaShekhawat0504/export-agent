from app.services.feedback_service import apply_feedback
from app.services.memory import find_memory, fingerprint, save_memory


def test_fingerprint_ignores_case_and_outer_whitespace():
    assert fingerprint("  Electric Motor ") == fingerprint("electric motor")
    assert fingerprint("electric motor") != fingerprint("electric motors")


async def test_save_then_find(db):
    assert await find_memory("Hydraulic pump", db) is None

    await save_memory("Hydraulic pump", "8413.60", 0.9, db)
    memory = await find_memory("hydraulic pump", db)

    assert memory.hs_code == "8413.60"
    assert memory.confidence == 0.9
    assert memory.source == "ai"
    assert memory.total_observations == 1


async def test_save_existing_updates_counters(db):
    await save_memory("apples", "0808.10", 0.9, db)
    await save_memory("apples", "0808.10", 0.9, db)
    memory = await find_memory("apples", db)
    assert memory.total_observations == 2
    assert memory.memory_hits == 1


async def test_feedback_creates_new_memory(db):
    memory = await apply_feedback("Copper wire", "7408.11", db)
    await db.commit()

    stored = await find_memory("copper wire", db)
    assert stored is memory
    assert (stored.hs_code, stored.confidence, stored.source) == (
        "7408.11",
        1.0,
        "human_feedback",
    )


async def test_feedback_overrides_ai_memory(db):
    await save_memory("lithium battery", "8501.10", 0.9, db)

    await apply_feedback("Lithium Battery", "8507.60", db)
    await db.commit()

    stored = await find_memory("lithium battery", db)
    assert (stored.hs_code, stored.confidence, stored.source) == (
        "8507.60",
        1.0,
        "human_feedback",
    )
    assert stored.total_observations == 2
