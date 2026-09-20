from datetime import datetime
from math import exp

REVISION_THRESHOLD = 0.60

def calculate_retention(mastery_score, last_updated, simulated_days=0):
    elapsed_days = (datetime.utcnow() - last_updated).total_seconds() / 86400
    elapsed_days += simulated_days

    # Higher original mastery means slower forgetting.
    stability_days = 2 + (12 * mastery_score)

    decayed_score = mastery_score * exp(-elapsed_days / stability_days)

    return {
        "days_since_review": round(elapsed_days, 2),
        "stability_days": round(stability_days, 2),
        "decayed_mastery": round(decayed_score, 3),
        "needs_revision": decayed_score < REVISION_THRESHOLD,
    }