"""API router for notifications."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Notification
from app.core.database import get_db
from app.models.models import Alert, Notification as NotificationModel

router = APIRouter()


@router.get("/notifications", response_model=List[Notification])
def list_notifications(
    db: Session = Depends(get_db),
    user_session_id: str = Query(..., description="User session ID (required)"),
    unread_only: bool = Query(False, description="Filter to unread only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get user's notifications.

    Args:
        user_session_id: User session ID
        unread_only: Only return unread notifications
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of notifications
    """
    # Join with alerts to filter by user
    query = (
        db.query(NotificationModel)
        .join(Alert, NotificationModel.alert_id == Alert.id)
        .filter(Alert.user_session_id == user_session_id)
    )

    if unread_only:
        query = query.filter(NotificationModel.read == False)

    notifications = (
        query.order_by(NotificationModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications


@router.patch("/notifications/{notification_id}/read", response_model=Notification)
def mark_notification_read(
    notification_id: int,
    user_session_id: str = Query(..., description="User session ID for authorization"),
    db: Session = Depends(get_db),
):
    """Mark a notification as read.

    Args:
        notification_id: Notification ID
        user_session_id: User session ID for authorization

    Returns:
        Updated notification
    """
    notification = (
        db.query(NotificationModel)
        .filter(NotificationModel.id == notification_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check authorization via alert
    alert = db.query(Alert).filter(Alert.id == notification.alert_id).first()
    if not alert or alert.user_session_id != user_session_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this notification"
        )

    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/notifications/mark-all-read", status_code=204)
def mark_all_notifications_read(
    user_session_id: str = Query(..., description="User session ID (required)"),
    db: Session = Depends(get_db),
):
    """Mark all user's notifications as read.

    Args:
        user_session_id: User session ID

    Returns:
        No content (204)
    """
    # Get all user's alert IDs
    alert_ids = [
        alert.id
        for alert in db.query(Alert.id)
        .filter(Alert.user_session_id == user_session_id)
        .all()
    ]

    if alert_ids:
        db.query(NotificationModel).filter(
            NotificationModel.alert_id.in_(alert_ids), NotificationModel.read == False
        ).update({"read": True}, synchronize_session=False)
        db.commit()

    return None
