"""
Route: GET /incidents

Returns paginated incident records for Leaflet map markers.
Supports optional filtering by zone, priority, and event_type.

Response:
{
  "total": int,
  "page": int,
  "page_size": int,
  "incidents": [ { id, lat, lng, address, junction, corridor,
                    event_type, priority, status, police_station, zone } ]
}
"""

import logging
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.data.loader import get_dataframe

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class IncidentMarker(BaseModel):
    id: str
    lat: float
    lng: float
    address: Optional[str] = None
    junction: Optional[str] = None
    corridor: Optional[str] = None
    event_type: Optional[str] = None
    event_cause: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    police_station: Optional[str] = None
    zone: Optional[str] = None
    start_datetime: Optional[str] = None


class IncidentsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    incidents: List[IncidentMarker]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/incidents",
    response_model=IncidentsResponse,
    summary="Paginated incident markers for the map",
    tags=["Map Data"],
)
async def get_incidents(
    zone: Optional[str] = Query(None, description="Filter by zone name"),
    priority: Optional[str] = Query(None, description="Filter by priority: 'High' or 'Low'"),
    event_type: Optional[str] = Query(None, description="Filter by event type: 'planned' or 'unplanned'"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(200, ge=1, le=1000, description="Records per page"),
) -> IncidentsResponse:
    """
    Returns paginated incident records with lat/lng and key metadata
    for map marker rendering. Frontend uses `priority` to colour-code
    markers (red = High, amber = Low).

    Filters zone, priority, and event_type are all optional and can be combined.
    """
    try:
        df = get_dataframe()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Drop rows with invalid coordinates
    working = df.dropna(subset=["latitude", "longitude"]).copy()
    working = working[
        (working["latitude"] != 0) & (working["longitude"] != 0)
    ]

    # Apply optional filters
    if zone:
        working = working[working["zone"].str.strip().str.lower() == zone.strip().lower()]
    if priority:
        working = working[working["priority"].str.strip().str.lower() == priority.strip().lower()]
    if event_type:
        working = working[working["event_type"].str.strip().str.lower() == event_type.strip().lower()]

    total = len(working)

    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = working.iloc[start_idx:end_idx]

    def _safe_str(val) -> Optional[str]:
        if pd.isna(val):
            return None
        s = str(val).strip()
        return s if s else None

    incidents = []
    for _, row in page_df.iterrows():
        incidents.append(
            IncidentMarker(
                id=_safe_str(row.get("id")) or str(row.name),
                lat=float(row["latitude"]),
                lng=float(row["longitude"]),
                address=_safe_str(row.get("address")),
                junction=_safe_str(row.get("junction")),
                corridor=_safe_str(row.get("corridor")),
                event_type=_safe_str(row.get("event_type")),
                event_cause=_safe_str(row.get("event_cause")),
                priority=_safe_str(row.get("priority")),
                status=_safe_str(row.get("status")),
                police_station=_safe_str(row.get("police_station")),
                zone=_safe_str(row.get("zone")),
                start_datetime=_safe_str(row.get("start_datetime")),
            )
        )

    return IncidentsResponse(
        total=total,
        page=page,
        page_size=page_size,
        incidents=incidents,
    )
