SANCTIONED_COUNTRIES = ["IR", "KP", "SY", "CU"]


def evaluate_risk(destination_country: str, confidence: float):
    
    # 🚫 Hard block countries
    if destination_country in SANCTIONED_COUNTRIES:
        return {
            "status": "blocked",
            "blocked": True,
            "reason": "Sanctioned country"
        }

    # ⚠️ Low confidence → manual review
    if confidence < 0.75:
        return {
            "status": "review",
            "blocked": False,
            "reason": "Low confidence classification"
        }

    # ✅ Safe
    return {
        "status": "approved",
        "blocked": False,
        "reason": "Compliant"
    }