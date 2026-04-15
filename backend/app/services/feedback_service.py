from sqlalchemy import select
from app.models.models import ProductMemory
from app.services.memory import fingerprint


async def apply_feedback(description: str, correct_hs_code: str, db):
    fp = fingerprint(description)

    result = await db.execute(
        select(ProductMemory).where(ProductMemory.fingerprint == fp)
    )
    memory = result.scalar_one_or_none()

    if memory:
        # 🔥 Override with human truth
        memory.hs_code = correct_hs_code
        memory.confidence = 1.0
        memory.source = "human_feedback"
        memory.total_observations += 1

    else:
        # 🔥 Create new entry from feedback
        memory = ProductMemory(
            fingerprint=fp,
            normalized_name=description.lower(),
            hs_code=correct_hs_code,
            confidence=1.0,
            source="human_feedback",
            total_observations=1,
            memory_hits=0,
        )
        db.add(memory)

    return memory