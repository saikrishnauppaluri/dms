"""
Events and alerts API endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional

from models import EventListResponse, EventCreate

router = APIRouter()


@router.get("/", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    severity: Optional[str] = None,
    event_type: Optional[str] = None
):
    """List all events"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()

    events = fleet.events.copy()

    # Filter
    if severity:
        events = [e for e in events if e.severity == severity]
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    # Sort by timestamp (newest first)
    events.sort(key=lambda e: e.created_at, reverse=True)

    # Pagination
    total = len(events)
    start = (page - 1) * page_size
    end = start + page_size
    events = events[start:end]

    return EventListResponse(
        events=events,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/alerts")
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    resolved: Optional[bool] = None
):
    """List all alerts"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()

    alerts = fleet.alerts.copy()

    if resolved is not None:
        alerts = [a for a in alerts if a.resolved == resolved]

    # Sort by timestamp (newest first)
    alerts.sort(key=lambda a: a.created_at, reverse=True)

    # Pagination
    total = len(alerts)
    start = (page - 1) * page_size
    end = start + page_size
    alerts = alerts[start:end]

    return {"alerts": alerts, "total": total, "page": page, "page_size": page_size}
