import re
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz

CORP_SUFFIXES = r"\b(llc|ltd|limited|inc|incorporated|corp|corporation|pvt|plc|gmbh|sa|co)\b"


def normalize_name(name: str) -> str:
    cleaned = name.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(CORP_SUFFIXES, "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def score_candidate(
    query_name: str,
    query_country: Optional[str],
    query_dob: Optional[str],
    record: Dict[str, Any],
) -> Dict[str, Any]:
    norm_query = normalize_name(query_name)
    candidates = [record["name"]] + record.get("aliases", [])

    best_name_score = 0.0
    matched_term = record["name"]

    for candidate in candidates:
        norm_cand = normalize_name(candidate)
        sort_score = fuzz.token_sort_ratio(norm_query, norm_cand)
        w_score = fuzz.WRatio(norm_query, norm_cand)
        combined = round((0.6 * sort_score) + (0.4 * w_score), 2)

        if combined > best_name_score:
            best_name_score = combined
            matched_term = candidate

    reasons: List[str] = [f"Name similarity {best_name_score}% against '{matched_term}'"]
    final_score = best_name_score

    if query_country and record.get("country"):
        if query_country.strip().upper() == record["country"].upper():
            final_score = min(100.0, final_score + 5.0)
            reasons.append(f"Country match ({record['country']})")
        else:
            final_score = max(0.0, final_score - 5.0)
            reasons.append(f"Country mismatch ({query_country.strip().upper()} vs {record['country']})")

    if query_dob and record.get("dob"):
        if query_dob.strip() == record["dob"]:
            final_score = min(100.0, final_score + 10.0)
            reasons.append(f"Exact DOB match ({record['dob']})")
        else:
            final_score = max(0.0, final_score - 10.0)
            reasons.append("DOB mismatch")

    final_score = round(final_score, 2)

    if final_score >= 88.0:
        tier = "HIGH_RISK_HIT"
    elif final_score >= 72.0:
        tier = "MANUAL_REVIEW"
    else:
        tier = "AUTO_CLEAR"

    return {
        "watchlist_id": record["id"],
        "canonical_name": record["name"],
        "matched_alias": matched_term,
        "program": record["program"],
        "name_similarity": best_name_score,
        "composite_score": final_score,
        "decision_tier": tier,
        "reasons": reasons,
    }