from app.services.memory import find_memory, save_memory, record_hit
from app.services.classifier import classify_product


async def classify_with_intelligence(db, description: str):

    # 🔥 1. Check memory
    memory = await find_memory(description, db)

    if memory:
        # ✅ Only trust memory if strong enough
        if memory.confidence >= 0.95 or memory.source == "human_feedback":
            
            await record_hit(memory, db)

            return {
                "hs_code": memory.hs_code,
                "confidence": memory.confidence,
                "source": "memory"
            }

        # ⚠️ Weak memory → ignore and go to AI
        print("⚠️ Weak memory ignored, using AI")

    # 🔥 2. AI classification
    result = await classify_product(description)

    # 🔥 3. Save AI result to memory
    await save_memory(
        description,
        result["hs_code"],
        result["confidence"],
        db
    )

    return {
        "hs_code": result["hs_code"],
        "confidence": result["confidence"],
        "source": "ai"
    }