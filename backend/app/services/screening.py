"""Denied-party screening of the shipment's counterparty.

Names are normalised (case, punctuation, legal forms such as GmbH or LLC are
removed) and compared with fuzzy matching, so "Mahan Air Co." still hits
"MAHAN AIR". A strong match blocks the shipment; a near match goes to review.

DENIED_PARTIES is a small illustrative sample of entities from public sanctions
lists. A production system would load the full EU consolidated list and the
OFAC SDN list instead (set DENIED_PARTIES_FILE to a text file, one name per line).
"""

import os
import re
from difflib import SequenceMatcher

DENIED_PARTIES = [
    "Islamic Republic of Iran Shipping Lines",
    "Mahan Air",
    "Rosoboronexport",
    "Korea Mining Development Trading Corporation",
    "Tidewater Middle East Co",
]

BLOCK_THRESHOLD = 0.90
REVIEW_THRESHOLD = 0.75

LEGAL_FORMS = {
    "gmbh", "ag", "kg", "co", "corp", "corporation", "company", "inc", "ltd",
    "llc", "plc", "sa", "srl", "bv", "nv", "jsc", "ojsc", "pjsc", "ooo", "the",
}


def normalise(name: str) -> str:
    words = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    return " ".join(w for w in words if w not in LEGAL_FORMS)


def load_denied_parties() -> list[str]:
    path = os.getenv("DENIED_PARTIES_FILE")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return DENIED_PARTIES


def screen_party(name: str, denied: list[str] | None = None):
    """Return the best match as {"match": listed_name, "score": 0..1}, or None."""
    candidate = normalise(name)
    if not candidate:
        return None

    best = None
    for listed in denied if denied is not None else load_denied_parties():
        target = normalise(listed)
        if not target:
            continue
        score = SequenceMatcher(None, candidate, target).ratio()
        if score > (best["score"] if best else 0):
            best = {"match": listed, "score": round(score, 2)}

    if best and best["score"] >= REVIEW_THRESHOLD:
        return best
    return None
