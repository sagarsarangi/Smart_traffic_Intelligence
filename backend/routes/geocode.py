"""
Route: POST /geocode-zone

Resolves a free-text Bengaluru area / zone name into geographic coordinates
using the Groq API (groq/compound-mini).

This endpoint is called from the Submit Incident form (View 2) ONLY.
It is NOT used by the anomaly monitor "Generate Plan" path.

Response shapes:

  High confidence:
    {
      "lat": 12.9352,
      "lng": 77.6245,
      "resolved_name": "Koramangala 5th Block",
      "confidence": "high"
    }

  Ambiguous (user must pick or refine):
    {
      "candidates": [
        {"name": "HSR Layout Sector 1", "lat": 12.9081, "lng": 77.6476},
        {"name": "HSR Layout Sector 2", "lat": 12.9150, "lng": 77.6430}
      ],
      "confidence": "ambiguous"
    }

  Failed (Groq unavailable or cannot parse):
    {
      "confidence": "failed",
      "message": "Could not resolve location. Please check the backend configuration."
    }
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# System prompt for the geocoding agent
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a precise geographic coordinate resolver. Your primary focus is Bengaluru (Bangalore), India, but you can also resolve locations within a 600km radius of Bengaluru.

Given a place name, area, zone, locality, junction, city, or landmark, return its latitude and longitude.

Rules:
1. Resolve locations within Bengaluru or up to a 600km radius from Bengaluru (e.g., other cities in Karnataka or neighboring states).
2. If the input is a well-known, specific location, return a SINGLE high-confidence result.
3. If the input is vague or could refer to multiple places, return 2 to 4 distinct candidate locations.
4. Use your built-in geographic knowledge. Do not make up coordinates — only return coordinates you are confident about.
5. Coordinates must fall within the expanded bounding box: latitude between 7.0 and 19.0, longitude between 72.0 and 84.0.

RESPONSE FORMAT — return ONLY valid JSON, no markdown, no explanation:

For a specific, unambiguous location:
{"confidence": "high", "lat": <float>, "lng": <float>, "resolved_name": "<canonical name>"}

For an ambiguous or vague input:
{"confidence": "ambiguous", "candidates": [{"name": "<place name>", "lat": <float>, "lng": <float>}, ...]}

If the location cannot be resolved or is too far outside the 600km radius:
{"confidence": "failed", "message": "<brief reason>"}
"""

_FEW_SHOT_USER = "Koramangala"
_FEW_SHOT_MODEL = json.dumps({
    "confidence": "high",
    "lat": 12.9352,
    "lng": 77.6245,
    "resolved_name": "Koramangala, Bengaluru"
})

_FEW_SHOT_USER_2 = "Layout near old airport"
_FEW_SHOT_MODEL_2 = json.dumps({
    "confidence": "ambiguous",
    "candidates": [
        {"name": "Jeevan Bima Nagar Layout", "lat": 12.9698, "lng": 77.6473},
        {"name": "HAL Airport Layout", "lat": 12.9634, "lng": 77.6542},
        {"name": "New Thippasandra Layout", "lat": 12.9723, "lng": 77.6512}
    ]
})


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class GeocodeZoneRequest(BaseModel):
    zone: str


# ---------------------------------------------------------------------------
# Internal Groq call
# ---------------------------------------------------------------------------

def _call_groq(zone_input: str) -> Optional[Dict[str, Any]]:
    """
    Calls Groq (groq/compound-mini) to geocode the given zone/area string.
    Returns the parsed JSON response dict, or None on any failure.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        logger.warning("No Groq API key found — geocoding cannot proceed.")
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_key}",
    }
    payload = {
        "model": "groq/compound-mini",
        "temperature": 0.0,
        "messages": [
            {"role": "system",    "content": _SYSTEM_PROMPT},
            # Few-shot example 1
            {"role": "user",      "content": _FEW_SHOT_USER},
            {"role": "assistant", "content": _FEW_SHOT_MODEL},
            # Few-shot example 2
            {"role": "user",      "content": _FEW_SHOT_USER_2},
            {"role": "assistant", "content": _FEW_SHOT_MODEL_2},
            # Actual query
            {"role": "user",      "content": zone_input.strip()},
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if the model adds them despite the instruction
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        return json.loads(raw_text)
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response else "?"
        safe = re.sub(r"(Bearer\s+)\S+", r"\1[REDACTED]", str(exc))
        logger.error("Groq geocode HTTP error %s: %s", status, safe)
        return None
    except Exception as exc:
        safe = re.sub(r"(Bearer\s+)\S+", r"\1[REDACTED]", str(exc))
        logger.error("Groq geocode error: %s", safe)
        return None


def _validate_bengaluru_coords(lat: float, lng: float) -> bool:
    """Sanity-check that coordinates fall within an approx 600km radius of Bengaluru."""
    # Center: ~12.9 lat, 77.6 lng. 600km is roughly +/- 5.5 degrees.
    return 7.0 <= lat <= 19.0 and 72.0 <= lng <= 84.0


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/geocode-zone",
    summary="Resolve a Bengaluru area/zone name to lat/lng coordinates",
    tags=["Geocoding"],
)
async def geocode_zone(request: GeocodeZoneRequest) -> Dict[str, Any]:
    """
    Accepts a free-text zone/area/locality name for a Bengaluru location
    and returns either:

    - A single high-confidence {lat, lng, resolved_name} if unambiguous.
    - A list of candidate locations {candidates} if the input is vague.
    - {confidence: "failed"} if Groq cannot resolve it.

    Called exclusively from the Submit Incident form (View 2).
    The anomaly monitor "Generate Plan" path does NOT call this endpoint.
    """
    zone_input = (request.zone or "").strip()
    if not zone_input:
        return {"confidence": "failed", "message": "Zone name is empty."}

    logger.info("Geocoding zone: %r", zone_input)

    result = _call_groq(zone_input)

    if result is None:
        return {
            "confidence": "failed",
            "message": (
                "Could not resolve location. The AI geocoder is unavailable. "
                "Please check the server configuration."
            ),
        }

    confidence = result.get("confidence", "failed")

    if confidence == "high":
        lat = result.get("lat")
        lng = result.get("lng")
        resolved_name = result.get("resolved_name", zone_input)

        # Validate coordinates are within Bengaluru
        if lat is None or lng is None or not _validate_bengaluru_coords(lat, lng):
            logger.warning(
                "Groq returned out-of-bounds coords for %r: lat=%s lng=%s",
                zone_input, lat, lng,
            )
            return {
                "confidence": "failed",
                "message": (
                    f"The resolved location '{resolved_name}' does not appear to be "
                    "within a 600km radius of Bengaluru. Please provide a closer area name."
                ),
            }

        logger.info(
            "Geocoded %r → %s (%.4f, %.4f)", zone_input, resolved_name, lat, lng
        )
        return {
            "confidence": "high",
            "lat": float(lat),
            "lng": float(lng),
            "resolved_name": resolved_name,
        }

    elif confidence == "ambiguous":
        candidates: List[Dict[str, Any]] = result.get("candidates", [])
        # Filter candidates to valid Bengaluru bounds
        valid_candidates = [
            c for c in candidates
            if _validate_bengaluru_coords(
                float(c.get("lat", 0)), float(c.get("lng", 0))
            )
        ]
        if not valid_candidates:
            return {
                "confidence": "failed",
                "message": (
                    "Could not find valid locations within the 600km radius for this input. "
                    "Try including a landmark, street, or more specific area name."
                ),
            }
        logger.info(
            "Geocode ambiguous for %r — returning %d candidates",
            zone_input, len(valid_candidates),
        )
        return {
            "confidence": "ambiguous",
            "candidates": [
                {
                    "name": c.get("name", "Unknown"),
                    "lat": float(c.get("lat", 0)),
                    "lng": float(c.get("lng", 0)),
                }
                for c in valid_candidates
            ],
        }

    else:
        # confidence == "failed" or unexpected
        message = result.get(
            "message",
            "Could not resolve this location. Try a more specific address.",
        )
        logger.info("Geocode failed for %r: %s", zone_input, message)
        return {"confidence": "failed", "message": message}
