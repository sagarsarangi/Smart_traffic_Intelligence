"""
Route: GET /anomaly

Returns the current anomaly scores for all zones/stations.
The background replay task (started in main.py) updates the cache every 5 seconds.
Frontend polls this endpoint every 5 seconds to update zone polygon colours
and the Anomaly Monitor sidebar cards.

Response: list of {
  zone, alert_level, incident_count, high_priority_ratio, mean_duration, anomaly_score
}
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter

from backend.agents.anomaly_detector import TrafficAnomalyDetector
from backend.data.loader import get_dataframe

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Shared state — written by background task, read by endpoint
# ---------------------------------------------------------------------------
_anomaly_cache: List[Dict[str, Any]] = []
_detector: Optional[TrafficAnomalyDetector] = None

# Replay pointer: tracks the simulated "current" position in the dataset
# (advances by REPLAY_STEP_HOURS every REPLAY_INTERVAL_SECONDS)
_replay_pointer: Optional[datetime] = None
_REPLAY_INTERVAL_SECONDS = 5
_REPLAY_STEP_HOURS = 6  # how many hours to advance per tick


# ---------------------------------------------------------------------------
# Initialisation (called by main.py)
# ---------------------------------------------------------------------------

def init_anomaly_detector(detector: TrafficAnomalyDetector) -> None:
    """
    Inject the fitted/loaded TrafficAnomalyDetector from main.py.
    Must be called before the background task starts.
    """
    global _detector
    _detector = detector
    logger.info("Anomaly route initialised with TrafficAnomalyDetector instance.")


def get_anomaly_cache() -> List[Dict[str, Any]]:
    """Return the current anomaly cache (used by the background task too)."""
    return _anomaly_cache


# ---------------------------------------------------------------------------
# Background replay task
# ---------------------------------------------------------------------------

async def anomaly_replay_loop(df: pd.DataFrame) -> None:
    """
    Background asyncio task.  Runs every REPLAY_INTERVAL_SECONDS.

    Each tick:
    1. Advance the replay pointer by REPLAY_STEP_HOURS.
    2. Select the 'active' slice of incidents at the simulated time
       (start_datetime <= pointer and either still open, or closed_datetime
       is within a reasonable window after pointer).
    3. Score each zone with the Isolation Forest.
    4. Update _anomaly_cache.

    If the detector is not ready (models not loaded), fills cache with
    Normal-level placeholder entries so the frontend always gets a valid list.
    """
    global _anomaly_cache, _replay_pointer

    df_work = df.copy()
    df_work["start_dt"] = pd.to_datetime(df_work["start_datetime"], errors="coerce")
    df_work["closed_dt"] = pd.to_datetime(df_work.get("closed_datetime"), errors="coerce")

    # Initialise replay pointer to the earliest incident in the dataset.
    # The dataset datetimes are timezone-aware (UTC), so the fallback must
    # also be timezone-aware to avoid TypeError on comparison.
    from datetime import timezone as tz
    min_ts = df_work["start_dt"].dropna().min()
    if pd.isna(min_ts):
        min_ts = datetime(2022, 1, 1, tzinfo=tz.utc)
    _replay_pointer = min_ts

    max_ts = df_work["start_dt"].dropna().max()

    while True:
        try:
            pointer = _replay_pointer

            if _detector is not None and _detector.model is not None:
                # Select incidents that were 'active' at the pointer time:
                # started before or at pointer, and either not yet closed or
                # closed within 24h after start (to keep data flowing)
                window_start = pointer - timedelta(hours=24)
                active_mask = (
                    (df_work["start_dt"] >= window_start)
                    & (df_work["start_dt"] <= pointer)
                )
                active_df = df_work[active_mask].copy()

                try:
                    scores = _detector.score_live_zones(
                        active_df, current_time=pointer
                    )
                    _anomaly_cache = scores
                    logger.debug(
                        "Anomaly cache updated at simulated time %s — %d zones scored",
                        pointer.isoformat(),
                        len(scores),
                    )
                except Exception as exc:
                    logger.warning("Anomaly scoring failed: %s", exc)
                    _anomaly_cache = _build_placeholder_cache(df_work)
            else:
                # Detector not loaded yet — return placeholder normals
                _anomaly_cache = _build_placeholder_cache(df_work)

            # Advance pointer; wrap around if we hit the end of the dataset
            _replay_pointer = pointer + timedelta(hours=_REPLAY_STEP_HOURS)
            if _replay_pointer > max_ts:
                _replay_pointer = min_ts
                logger.info("Anomaly replay pointer wrapped back to dataset start.")

        except Exception as exc:
            logger.exception("Unhandled error in anomaly_replay_loop: %s", exc)

        await asyncio.sleep(_REPLAY_INTERVAL_SECONDS)


def _build_placeholder_cache(df_work: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return all zones as Normal when the detector is not available."""
    # Gather unique zone/station names from the dataset
    zones = set()
    if "zone" in df_work.columns:
        zones.update(df_work["zone"].dropna().unique().tolist())
    if "police_station" in df_work.columns:
        # Add police stations for records with null zone
        null_zone_mask = df_work["zone"].isna() if "zone" in df_work.columns else pd.Series(True, index=df_work.index)
        zones.update(df_work.loc[null_zone_mask, "police_station"].dropna().unique().tolist())

    return [
        {
            "zone": z,
            "alert_level": "Normal",
            "incident_count": 0,
            "high_priority_ratio": 0.0,
            "mean_duration": 0.0,
            "anomaly_score": 0.1,
        }
        for z in sorted(zones)
    ]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/anomaly",
    summary="Current anomaly scores for all zones",
    tags=["Anomaly"],
)
async def get_anomaly() -> List[Dict[str, Any]]:
    """
    Returns the most recently computed anomaly scores for every zone/station.

    Updated every 5 seconds by the background replay task.
    Alert level mapping:
    - anomaly_score >  0.0  → Normal
    - anomaly_score >= -0.1 → Watch
    - anomaly_score <  -0.1 → Critical

    Frontend uses these to colour-code zone polygons on the map and
    badge colours on the Anomaly Monitor sidebar cards.
    """
    if not _anomaly_cache:
        # First call before background task has run — try to build placeholder
        try:
            df = get_dataframe()
            df_work = df.copy()
            return _build_placeholder_cache(df_work)
        except Exception:
            return []

    return _anomaly_cache
