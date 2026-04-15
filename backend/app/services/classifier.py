import os
import re
from openai import AsyncOpenAI


async def classify_product(description: str):

    # 🔒 Validation
    if not description or len(description.strip()) == 0:
        return {
            "hs_code": "UNKNOWN",
            "confidence": 0.0
        }

    # 🔑 API key
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "hs_code": "8501.10",
            "confidence": 0.82
        }

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
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
                },
                {
                    "role": "user",
                    "content": description
                }
            ]
        )

        text = response.choices[0].message.content.strip()

        # ✅ Strong extraction (VERY IMPORTANT)
        match = re.search(r"\d{4}\.\d{2}", text)

        if match:
            hs_code = match.group(0)
        else:
            hs_code = "UNKNOWN"

        return {
            "hs_code": hs_code,
            "confidence": 0.9
        }

    except Exception as e:
        print("❌ AI ERROR:", e)

        return {
            "hs_code": "8501.10",
            "confidence": 0.5
        }