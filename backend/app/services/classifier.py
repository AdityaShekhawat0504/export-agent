import os
import re

from openai import AsyncOpenAI

# Returned whenever the agent has no trustworthy classification. Confidence 0.0
# guarantees the risk engine routes the shipment to a human instead of approving it.
UNKNOWN = {"hs_code": "UNKNOWN", "confidence": 0.0}

SYSTEM_PROMPT = (
    "You are a global trade expert in HS classification.\n\n"
    "Your job:\n"
    "1. Understand the product\n"
    "2. Identify its category\n"
    "3. Return the correct HS code\n\n"
    "RULES:\n"
    "- Return ONLY a 6-digit HS code\n"
    "- Format must be: XXXX.XX\n"
    "- No explanation\n\n"
    "Examples:\n"
    "Lithium ion battery → 8507.60\n"
    "Electric motor → 8501.10\n"
    "Apples → 0808.10\n"
    "Hydraulic pump → 8413.60"
)


async def classify_product(description: str):
    if not description or not description.strip():
        return dict(UNKNOWN)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Offline mode: no classifier is configured, so nothing is guessed.
        # The shipment goes to manual review; a human code via /feedback is reused later.
        return dict(UNKNOWN)

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": description},
            ],
        )
    except Exception as e:
        print("AI error:", e)
        return dict(UNKNOWN)

    text = response.choices[0].message.content.strip()
    match = re.search(r"\d{4}\.\d{2}", text)
    if not match:
        return dict(UNKNOWN)

    return {"hs_code": match.group(0), "confidence": 0.9}
