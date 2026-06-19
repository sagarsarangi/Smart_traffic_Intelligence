import os
import json
import logging
import re
from typing import AsyncGenerator, Dict, Any, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Allowed LLM models for Agent 4 (Action Planner) — all routed via Groq API
# ---------------------------------------------------------------------------
ALLOWED_MODELS = [
    "groq/compound-mini",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
]
DEFAULT_MODEL = "groq/compound-mini"


def sanitize_url(url: str) -> str:
    """Redacts the 'key' query parameter from a URL to prevent leaks."""
    try:
        parsed = urlparse(url)
        queries = parse_qsl(parsed.query)
        redacted_queries = [(k, '[REDACTED]' if k == 'key' else v) for k, v in queries]
        new_query = urlencode(redacted_queries)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return "[REDACTED_URL]"


class ActionPlannerAgent:
    """
    Agent 4 — Action Planner Agent.

    Generates a concise, structured deployment plan (Officers, Barricades, Diversion,
    Estimated Clearance, Escalation Trigger, Public Advisory) using an LLM.

    Currently uses Google Gemini as per the rest of the stack, falling back to a
    deterministic string stream if the API key is missing or the call fails.
    """

    def __init__(self, api_key: str = None):
        self.groq_key = api_key or os.environ.get("GROQ_API_KEY")
        self.default_model = DEFAULT_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        if self.groq_key:
            logger.info(
                "[Agent 4 - Action Planner] Initialised with Groq API. Default model: %s.",
                self.default_model,
            )
        else:
            logger.warning(
                "[Agent 4 - Action Planner] No Groq API key found. Using heuristic fallback stream."
            )

    def _build_system_prompt(self) -> str:
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

    def _build_user_prompt(self, params: Dict[str, Any]) -> str:
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

    async def stream_plan(
        self,
        params: Dict[str, Any],
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Takes incident parameters, builds the prompts, calls the Groq streaming API,
        and yields each text chunk as an SSE event.

        Args:
            params:     Full incident + prediction context dict.
            model_name: Groq model ID to use for this call. Falls back to
                        DEFAULT_MODEL if None or not in ALLOWED_MODELS.

        Falls back to a hardcoded structured plan if the API key is missing or fails.
        """
        # Resolve and validate model
        resolved_model = model_name if model_name in ALLOWED_MODELS else DEFAULT_MODEL
        if model_name and model_name not in ALLOWED_MODELS:
            logger.warning(
                "[Agent 4 - Action Planner] Unknown model %r requested; falling back to %s.",
                model_name,
                DEFAULT_MODEL,
            )

        user_prompt = self._build_user_prompt(params)

        if not self.groq_key:
            logger.warning(
                "[Agent 4 - Action Planner] WARNING: No Groq API key found. Model not loaded."
            )
            yield "data: WARNING: API key not found. Action Planner model is not loaded.\n\n"
            yield "data: [DONE]\n\n"
            return

        # Log which model is handling this plan request
        logger.info(
            "[Agent 4 - Action Planner] Calling Groq API — model: %s | zone: %s | priority: %s",
            resolved_model,
            params.get("zone", "unknown"),
            params.get("priority", "unknown"),
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_key}",
        }
        payload = {
            "model": resolved_model,
            "temperature": 0.3,
            "max_tokens": 600,
            "stream": True,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user",   "content": user_prompt},
            ],
        }

        try:
            with requests.post(
                self.base_url, headers=headers, json=payload, stream=True, timeout=30
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
                            delta = data_json["choices"][0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield f"data: {text}\n\n"
                        except (json.JSONDecodeError, KeyError):
                            continue

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "Unknown"
            reason = exc.response.reason if exc.response is not None else "Error"
            safe_url = sanitize_url(exc.request.url) if (exc.request and exc.request.url) else "URL"
            safe_err = f"{status_code} Client Error: {reason} for url: {safe_url}"
            logger.error(
                "[Agent 4 - Action Planner] Groq streaming error (model=%s): %s",
                resolved_model,
                safe_err,
            )
            yield f"data: WARNING: API call failed ({safe_err}). Action Planner model is not loaded.\n\n"
            yield "data: [DONE]\n\n"
            return
        except Exception as exc:
            safe_err = re.sub(r'(Bearer\s+)\S+', r'\1[REDACTED]', str(exc))
            logger.error(
                "[Agent 4 - Action Planner] Groq streaming error (model=%s): %s",
                resolved_model,
                safe_err,
            )
            yield f"data: WARNING: API call failed ({safe_err}). Action Planner model is not loaded.\n\n"
            yield "data: [DONE]\n\n"
            return

        yield "data: [DONE]\n\n"

    async def _fallback_stream(self, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        Deterministic fallback plan when the Gemini API is unavailable.
        """
        import asyncio

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
