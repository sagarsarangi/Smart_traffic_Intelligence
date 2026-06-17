"""
Route: GET /heatmap

Returns weighted lat/lng points for the Leaflet heatmap layer.
Data is pre-computed once at startup by the data loader and served from cache.

Response: list of { lat, lng, weight }
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.data.loader import get_heatmap_cache

logger = logging.getLogger(__name__)

router = APIRouter()


class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    weight: float


@router.get(
    "/heatmap",
    response_model=List[HeatmapPoint],
    summary="Heatmap weight data for all incidents",
    tags=["Map Data"],
)
async def get_heatmap() -> List[HeatmapPoint]:
    """
    Returns a list of weighted lat/lng points for every incident in the dataset.

    Weight formula (from architecture.md §3):
    - base_weight = 2 if priority == 'High', else 1
    - duration_factor = normalised resolution_minutes (0–1 scale)
    - weight = base_weight × duration_factor

    Pre-computed at startup; served from memory. Frontend calls this once on load.
    """
    try:
        cache = get_heatmap_cache()
        return cache
    except RuntimeError as exc:
        logger.error("Heatmap cache not ready: %s", exc)
        raise HTTPException(status_code=503, detail="Heatmap data not yet available.")
