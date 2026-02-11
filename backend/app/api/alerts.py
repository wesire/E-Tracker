"""API router for alerts management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Alert, AlertCreate, AlertUpdate
from app.core.database import get_db
from app.models.models import Alert as AlertModel

router = APIRouter()


@router.get("/alerts", response_model=List[Alert])
def list_alerts(
    db: Session = Depends(get_db),
    user_session_id: str = Query(..., description="User session ID (required)"),
    is_active: bool = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get user's alerts.

    Args:
        user_session_id: User session ID
        is_active: Optional filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of alerts
    """
    query = db.query(AlertModel).filter(AlertModel.user_session_id == user_session_id)

    if is_active is not None:
        query = query.filter(AlertModel.is_active == is_active)

    alerts = query.offset(skip).limit(limit).all()
    return alerts


@router.get("/alerts/{alert_id}", response_model=Alert)
def get_alert(
    alert_id: int,
    user_session_id: str = Query(..., description="User session ID for authorization"),
    db: Session = Depends(get_db),
):
    """Get a specific alert.

    Args:
        alert_id: Alert ID
        user_session_id: User session ID for authorization

    Returns:
        Alert details
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.user_session_id != user_session_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this alert")

    return alert


@router.post("/alerts", response_model=Alert, status_code=201)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
):
    """Create a new alert.

    Args:
        alert: Alert to create

    Returns:
        Created alert
    """
    db_alert = AlertModel(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


@router.patch("/alerts/{alert_id}", response_model=Alert)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    user_session_id: str = Query(..., description="User session ID for authorization"),
    db: Session = Depends(get_db),
):
    """Update an alert.

    Args:
        alert_id: Alert ID
        alert_update: Alert fields to update
        user_session_id: User session ID for authorization

    Returns:
        Updated alert
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.user_session_id != user_session_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this alert")

    # Update fields
    update_data = alert_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    user_session_id: str = Query(..., description="User session ID for authorization"),
    db: Session = Depends(get_db),
):
    """Delete an alert.

    Args:
        alert_id: Alert ID
        user_session_id: User session ID for authorization

    Returns:
        No content (204)
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.user_session_id != user_session_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this alert")

    db.delete(alert)
    db.commit()
    return None
