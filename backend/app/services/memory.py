import hashlib
from sqlalchemy import select
from app.models.models import ProductMemory


def fingerprint(text: str):
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()


async def find_memory(description, db):
    fp = fingerprint(description)

    result = await db.execute(
        select(ProductMemory).where(ProductMemory.fingerprint == fp)
    )
    memory = result.scalar_one_or_none()

    return memory  # ✅ RETURN ORM OBJECT

    if memory:
        return {
            "id": memory.id,
            "hs_code": memory.hs_code,
            "confidence": memory.confidence,
            "source": memory.source,
            "memory_hits": memory.memory_hits
        }

    return None


async def save_memory(description, hs_code, confidence, db, source="ai"):
    fp = fingerprint(description)

    result = await db.execute(
        select(ProductMemory).where(ProductMemory.fingerprint == fp)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.total_observations += 1
        existing.memory_hits += 1
        existing.hs_code = hs_code
        existing.confidence = confidence
        existing.source = source

        await db.commit()

        return {
            "hs_code": existing.hs_code,
            "confidence": existing.confidence,
            "source": existing.source
        }

    entry = ProductMemory(
        id=fp,  # IMPORTANT
        fingerprint=fp,
        normalized_name=description.lower(),
        hs_code=hs_code,
        confidence=confidence,
        source=source,
        total_observations=1,
        memory_hits=0,
    )

    db.add(entry)
    await db.commit()

    return {
        "hs_code": hs_code,
        "confidence": confidence,
        "source": source
    }


async def record_hit(memory, db):
    memory.memory_hits += 1
    await db.commit()