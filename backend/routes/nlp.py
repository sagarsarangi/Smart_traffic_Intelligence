"""
Route: POST /nlp-parse

Calls Agent 1 (NLPIncidentParser) to parse a free-text incident
description into structured fields.

Request:  { "description": "ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದೆ ಸರ್" }
Response: { root_cause, vehicle_type, severity, action_needed,
            normalized_summary } | null
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.nlp_parser import NLPIncidentParser

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Singleton — initialised by main.py at startup
# ---------------------------------------------------------------------------
_nlp_parser: Optional[NLPIncidentParser] = None


def init_nlp_parser(parser: NLPIncidentParser) -> None:
    """Inject the NLPIncidentParser instance from main.py startup."""
    global _nlp_parser
    _nlp_parser = parser
    logger.info("NLP parse route initialised with NLPIncidentParser instance.")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class NLPParseRequest(BaseModel):
    description: str


class NLPParseResponse(BaseModel):
    root_cause: Optional[str] = None
    vehicle_type: Optional[str] = None
    severity: Optional[int] = None
    action_needed: Optional[bool] = None
    normalized_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/nlp-parse",
    summary="Parse a free-text incident description into structured fields",
    tags=["NLP"],
)
async def nlp_parse(request: NLPParseRequest) -> Any:
    """
    Accepts a raw incident description in any language (Kannada, English,
    mixed / transliterated) and runs Agent 1 (NLPIncidentParser) to extract:

    - root_cause      — mapped to dataset event_cause vocabulary
    - vehicle_type    — mapped to dataset veh_type vocabulary, or null
    - severity        — 1 (low) | 2 (medium) | 3 (high)
    - action_needed   — boolean
    - normalized_summary — one-sentence English summary

    Returns null (HTTP 200) if the description cannot be parsed.
    Frontend shows the parsed section in IncidentPanel; on null it falls
    through to the user's typed structured fields.
    """
    if not request.description or not request.description.strip():
        return None

    if _nlp_parser is None:
        raise HTTPException(
            status_code=503,
            detail="NLP parser not initialised. Server may still be starting.",
        )

    try:
        result = _nlp_parser.parse_description(request.description)
        # result is already a dict or None
        return result
    except Exception as exc:
        logger.exception("NLP parse error: %s", exc)
        # Per spec: return null on failure, not an error status
        return None
