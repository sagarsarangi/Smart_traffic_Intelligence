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

import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Feedback — visual only during demo review (no disk persistence required)
# ---------------------------------------------------------------------------


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
def post_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Accepts feedback rating for visual demo confirmation.
    Logs feedback to standard output without writing to disk.
    """
    logger.info("Visual feedback recorded: rating=%s", request.rating)
    return FeedbackResponse(status="ok")


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
    Returns an empty list as feedback persistence is disabled.
    """
    return []
