"""
Route: GET /analytics

Returns all four chart datasets in a single pre-computed response.
Data is computed once at startup by the data loader and served from cache.

Response structure (architecture.md §3):
{
  "volume_grid":          [[...7 rows × 24 cols...]],
  "top_junctions":        [{ junction, count, lat, lng }],
  "corridor_durations":   [{ corridor_rank, label, median_minutes }],
  "planned_vs_unplanned": [{ month, planned, unplanned }]
}
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.data.loader import get_analytics_cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/analytics",
    summary="Pre-computed analytics datasets for all four charts",
    tags=["Analytics"],
)
async def get_analytics() -> Dict[str, Any]:
    """
    Returns all four analytics chart payloads in a single call.
    Computed once at startup from the full 8,173-record dataset.
    Frontend calls this once when the Analytics view mounts.

    Charts:
    1. volume_grid          — 7×24 incident count matrix (day × hour)
    2. top_junctions        — Top 15 junctions by incident count
    3. corridor_durations   — Median resolution minutes by corridor rank
    4. planned_vs_unplanned — Monthly incident volumes by event type
    """
    try:
        return get_analytics_cache()
    except RuntimeError as exc:
        logger.error("Analytics cache not ready: %s", exc)
        raise HTTPException(status_code=503, detail="Analytics data not yet available.")
