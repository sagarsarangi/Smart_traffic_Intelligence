"""
Route: GET /action-plan  (Server-Sent Events)

Agent 4 — Action Planner.

Accepts the full incident + prediction context as query parameters,
calls the Gemini API with stream=True, and streams each text chunk back to
the frontend as an SSE event.  The frontend accumulates tokens and renders
them typewriter-style in the IncidentPanel.

The plan is always structured in exactly six labeled sections:
  Officers | Barricades | Diversion | Estimated Clearance | Escalation Trigger | Public Advisory

For planned events (event_type == "planned") the prompt instructs
pre-emptive deployment framing.  For zone-level alerts (is_zone_alert=true)
the plan is framed as a pre-emptive zone response.

SSE format:
  data: <token text>\n\n
  ...
  data: [DONE]\n\n
"""

import json
import logging
import os
from typing import AsyncGenerator, Optional

import requests
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Gemini API config
# ---------------------------------------------------------------------------
_GEMINI_MODEL = "gemini-1.5-flash"
_GEMINI_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{_GEMINI_MODEL}:streamGenerateContent"
)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    return (
        "You are a traffic authority operations assistant for the Bengaluru Metropolitan Region. "
        "Your role is to generate concise, actionable deployment plans for traffic incidents. "
        "You have expert knowledge of Bengaluru's road network, including major corridors, "
        "junctions, ORR routes, and typical congestion patterns. "
        "Always produce your response in EXACTLY these six labeled sections — no preamble, "
        "no explanation, no markdown code blocks:\n\n"
        "Officers:\n"
        "Barricades:\n"
        "Diversion:\n"
        "Estimated Clearance:\n"
        "Escalation Trigger:\n"
        "Public Advisory:\n\n"
        "Keep each section brief (1–3 sentences). Be specific with officer counts, "
        "junction names, and road numbers where available."
    )


def _build_user_prompt(params: dict) -> str:
    event_type = params.get("event_type", "unplanned")
    event_cause = params.get("event_cause", "unknown")
    address = params.get("address", "Unknown location")
    junction = params.get("junction", "Unknown junction")
    corridor = params.get("corridor", "Non-corridor")
    police_station = params.get("police_station", "Local station")
    zone = params.get("zone", "Unknown zone")
    priority = params.get("priority", "High")
    confidence = params.get("confidence", 0.0)
    est_duration = params.get("estimated_duration_minutes", 60)
    requires_closure = params.get("requires_road_closure", "false")
    nlp_cause = params.get("nlp_cause", "")
    nlp_summary = params.get("nlp_summary", "")
    is_zone_alert = params.get("is_zone_alert", "false")

    # Determine framing based on alert type and event type
    if str(is_zone_alert).lower() == "true":
        framing = (
            f"ZONE-LEVEL PRE-EMPTIVE ALERT for {zone}. "
            "Multiple incidents detected in this zone. Respond with a zone-wide pre-emptive deployment plan."
        )
    elif event_type == "planned":
        framing = (
            f"PRE-ANNOUNCED PLANNED EVENT ({event_cause.replace('_', ' ')}). "
            "Resources must be positioned BEFORE the event starts, not dispatched reactively. "
            "Include staging instructions."
        )
    else:
        framing = f"ACTIVE UNPLANNED INCIDENT ({event_cause.replace('_', ' ')})."

    # Confidence as percentage
    try:
        conf_pct = f"{float(confidence) * 100:.0f}%"
    except (ValueError, TypeError):
        conf_pct = "N/A"

    lines = [
        f"INCIDENT BRIEF:",
        f"  Type: {event_type.upper()} — {framing}",
        f"  Cause: {event_cause.replace('_', ' ').title()}",
        f"  Location: {address}",
        f"  Junction: {junction}",
        f"  Corridor: {corridor}",
        f"  Zone: {zone}",
        f"  Responsible Station: {police_station}",
        f"  Road Closure Required: {str(requires_closure).lower()}",
        f"",
        f"ML PREDICTION:",
        f"  Priority: {priority} (confidence: {conf_pct})",
        f"  Estimated Resolution: {est_duration} minutes",
    ]

    if nlp_summary:
        lines += ["", f"DESCRIPTION (parsed): {nlp_summary}"]
        if nlp_cause:
            lines.append(f"  Root cause extracted: {nlp_cause.replace('_', ' ')}")

    lines += [
        "",
        "Generate the 6-section deployment plan now. Do not add any text before 'Officers:'.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gemini streaming call
# ---------------------------------------------------------------------------

async def _stream_gemini_sse(user_prompt: str) -> AsyncGenerator[str, None]:
    """
    Calls the Gemini streaming API and yields each text chunk as an SSE event.
    Falls back to a hardcoded structured plan if the API key is missing or
    the call fails, so the frontend always gets valid content.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        logger.warning("No Gemini API key — streaming fallback plan.")
        async for chunk in _fallback_stream(user_prompt):
            yield chunk
        return

    url = f"{_GEMINI_BASE_URL}?key={api_key}&alt=sse"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "systemInstruction": {
            "parts": [{"text": _build_system_prompt()}]
        },
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 600,
        },
    }

    try:
        with requests.post(
            url, headers=headers, json=payload, stream=True, timeout=30
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data_json = json.loads(data_str)
                        candidates = data_json.get("candidates", [])
                        for candidate in candidates:
                            parts = candidate.get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield f"data: {text}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue

    except Exception as exc:
        logger.exception("Gemini streaming error: %s", exc)
        async for chunk in _fallback_stream(user_prompt):
            yield chunk
        return

    yield "data: [DONE]\n\n"


async def _fallback_stream(user_prompt: str) -> AsyncGenerator[str, None]:
    """
    Deterministic fallback plan when the Gemini API is unavailable.
    Parses basic context from user_prompt to produce a contextual-ish response.
    """
    import asyncio

    # Extract priority from prompt
    priority = "High" if "Priority: High" in user_prompt else "Low"
    officer_count = 6 if priority == "High" else 3

    plan_lines = [
        f"Officers: Deploy {officer_count} officers immediately — 2 at the primary incident site, "
        f"2 at approach diversions, and {officer_count - 4} in reserve for crowd management.\n",
        "Barricades: Place reflective barricades 50m upstream of the incident on both approach lanes. "
        "Position cones along the diversion route entry points.\n",
        "Diversion: Route traffic via the nearest parallel arterial. "
        "Use the alternate service road where available; update variable message signs.\n",
        f"Estimated Clearance: {'60–90' if priority == 'High' else '30–45'} minutes from deployment. "
        "Reassess after 45 minutes if not cleared.\n",
        "Escalation Trigger: Escalate to zone control if incident is not contained within 90 minutes, "
        "if a secondary incident occurs, or if queue length exceeds 500 metres.\n",
        "Public Advisory: Motorists advised to avoid the affected corridor. "
        "Use alternate routes. Allow additional 20 minutes travel time. Follow officer directions.\n",
    ]

    for line in plan_lines:
        yield f"data: {line}\n\n"
        await asyncio.sleep(0.05)

    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/action-plan",
    summary="Stream an LLM action plan as Server-Sent Events",
    tags=["Action Plan"],
)
async def get_action_plan(
    request: Request,
    event_type: Optional[str] = None,
    event_cause: Optional[str] = None,
    address: Optional[str] = None,
    junction: Optional[str] = None,
    corridor: Optional[str] = None,
    police_station: Optional[str] = None,
    zone: Optional[str] = None,
    priority: Optional[str] = None,
    confidence: Optional[str] = None,
    estimated_duration_minutes: Optional[str] = None,
    requires_road_closure: Optional[str] = None,
    nlp_cause: Optional[str] = None,
    nlp_summary: Optional[str] = None,
    is_zone_alert: Optional[str] = None,
) -> StreamingResponse:
    """
    Streams the Agent 4 action plan token-by-token as SSE.

    Called by the frontend after POST /predict completes.
    The full incident + prediction context is passed as query parameters.

    Each SSE event carries a text chunk:
        data: <text>\n\n

    Final event:
        data: [DONE]\n\n

    Always produces exactly six sections: Officers, Barricades, Diversion,
    Estimated Clearance, Escalation Trigger, Public Advisory.
    """
    params = {
        "event_type": event_type or "unplanned",
        "event_cause": event_cause or "unknown",
        "address": address or "Unknown location",
        "junction": junction or "Unknown junction",
        "corridor": corridor or "Non-corridor",
        "police_station": police_station or "Local station",
        "zone": zone or "Unknown zone",
        "priority": priority or "High",
        "confidence": confidence or "0",
        "estimated_duration_minutes": estimated_duration_minutes or "60",
        "requires_road_closure": requires_road_closure or "false",
        "nlp_cause": nlp_cause or "",
        "nlp_summary": nlp_summary or "",
        "is_zone_alert": is_zone_alert or "false",
    }

    user_prompt = _build_user_prompt(params)

    return StreamingResponse(
        _stream_gemini_sse(user_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
