from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.matcher import score_candidate
from app.watchlist import WATCHLIST

app = FastAPI(
    title="Sanctions Screening & Fuzzy Match Entity Resolution Service",
    version="1.0.0",
)


class ScreenRequest(BaseModel):
    name: str = Field(..., min_length=2, examples=["Victor Sokolov"])
    country: Optional[str] = Field(None, min_length=2, max_length=2, examples=["RU"])
    dob: Optional[str] = Field(None, examples=["1974-05-12"])
    min_score: float = Field(65.0, ge=0.0, le=100.0)


class MatchHit(BaseModel):
    watchlist_id: str
    canonical_name: str
    matched_alias: str
    program: str
    name_similarity: float
    composite_score: float
    decision_tier: str
    reasons: List[str]


class ScreenResponse(BaseModel):
    query_name: str
    overall_status: str
    total_hits: int
    hits: List[MatchHit]


@app.get("/")
def root():
    return {
        "service": "Sanctions Screening & Fuzzy Match Entity Resolution Service",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "screen": "POST /screen",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "watchlist_size": len(WATCHLIST)}


@app.post("/screen", response_model=ScreenResponse)
def screen_entity(payload: ScreenRequest):
    scored = [
        score_candidate(payload.name, payload.country, payload.dob, rec)
        for rec in WATCHLIST
    ]
    hits = [item for item in scored if item["composite_score"] >= payload.min_score]
    hits.sort(key=lambda x: x["composite_score"], reverse=True)

    if any(h["decision_tier"] == "HIGH_RISK_HIT" for h in hits):
        overall = "BLOCK_OR_ESCALATE"
    elif any(h["decision_tier"] == "MANUAL_REVIEW" for h in hits):
        overall = "REVIEW_REQUIRED"
    else:
        overall = "CLEAR"

    return {
        "query_name": payload.name,
        "overall_status": overall,
        "total_hits": len(hits),
        "hits": hits,
    }