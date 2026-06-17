"""
Route: POST /feedback
       GET  /feedback

Records user thumbs-up / thumbs-down ratings on action plans.
POST appends one JSON line to backend/feedback.jsonl.
GET  returns all recorded feedback entries as a JSON array.

POST body:
{
  "incident_context": { ... },
  "action_plan": "Officers: ...",
  "rating": "up" | "down"
}

POST response:
{ "status": "ok" }

GET response:
[ { "timestamp": "...", "incident_context": {...}, "action_plan": "...", "rating": "up" } ]
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Feedback file — sits alongside main.py in the backend directory
# ---------------------------------------------------------------------------
_FEEDBACK_PATH = Path("backend/feedback.jsonl")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    incident_context: Dict[str, Any] = Field(
        ...,
        description="Full incident context dict (zone, event_cause, priority, etc.)",
    )
    action_plan: str = Field(
        ...,
        description="The LLM-generated action plan text shown to the user.",
    )
    rating: str = Field(
        ...,
        description="User rating: 'up' or 'down'.",
        pattern="^(up|down)$",
    )


class FeedbackResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# POST /feedback
# ---------------------------------------------------------------------------

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Record thumbs-up/down rating on an action plan",
    tags=["Feedback"],
)
async def post_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Appends a single JSON line to feedback.jsonl.
    Each entry includes an ISO timestamp, the full incident context,
    the action plan text, and the rating.

    Not used for live retraining — exists for post-demo review.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incident_context": request.incident_context,
        "action_plan": request.action_plan,
        "rating": request.rating,
    }

    try:
        _FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _FEEDBACK_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info("Feedback recorded: rating=%s", request.rating)
        return FeedbackResponse(status="ok")
    except OSError as exc:
        logger.exception("Failed to write feedback: %s", exc)
        raise HTTPException(status_code=500, detail=f"Could not save feedback: {exc}")


# ---------------------------------------------------------------------------
# GET /feedback
# ---------------------------------------------------------------------------

@router.get(
    "/feedback",
    summary="Retrieve all recorded feedback entries",
    tags=["Feedback"],
)
async def get_feedback() -> List[Dict[str, Any]]:
    """
    Returns all entries from feedback.jsonl as a JSON array.
    Used for post-demo review. Returns an empty list if the file does not exist.
    """
    if not _FEEDBACK_PATH.exists():
        return []

    entries = []
    try:
        with _FEEDBACK_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed feedback line.")
    except OSError as exc:
        logger.exception("Failed to read feedback file: %s", exc)
        raise HTTPException(status_code=500, detail=f"Could not read feedback: {exc}")

    return entries
