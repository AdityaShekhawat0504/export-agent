SANCTIONED_COUNTRIES = ["IR", "KP", "SY", "CU"]

CONFIDENCE_THRESHOLD = 0.75


def evaluate_risk(destination_country: str, confidence: float, hs_code: str | None = None):

    # 🚫 Hard block countries
    if (destination_country or "").strip().upper() in SANCTIONED_COUNTRIES:
        return {
            "status": "blocked",
            "blocked": True,
            "reason": "Sanctioned country"
        }

    # ⚠️ No classification at all → a human decides, never auto-approve
    if hs_code == "UNKNOWN":
        return {
            "status": "review",
            "blocked": False,
            "reason": "No HS classification available"
        }

    # ⚠️ Low confidence → manual review
    if confidence < CONFIDENCE_THRESHOLD:
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
