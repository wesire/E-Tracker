"""API router for watchlist management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Watchlist, WatchlistCreate
from app.core.database import get_db
from app.models.models import UserWatchlist

router = APIRouter()


@router.get("/watchlist", response_model=List[Watchlist])
def get_watchlist(
    db: Session = Depends(get_db),
    user_session_id: str = Query(..., description="User session ID (required)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get user's watchlist.

    Args:
        user_session_id: User session ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of watchlist items
    """
    watchlist = (
        db.query(UserWatchlist)
        .filter(UserWatchlist.user_session_id == user_session_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return watchlist


@router.post("/watchlist", response_model=Watchlist, status_code=201)
def add_to_watchlist(
    watchlist_item: WatchlistCreate,
    db: Session = Depends(get_db),
):
    """Add a series to user's watchlist.

    Args:
        watchlist_item: Watchlist item to create

    Returns:
        Created watchlist item
    """
    # Check if already exists
    existing = (
        db.query(UserWatchlist)
        .filter(
            UserWatchlist.user_session_id == watchlist_item.user_session_id,
            UserWatchlist.series_id == watchlist_item.series_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Series already in watchlist")

    db_item = UserWatchlist(**watchlist_item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/watchlist/{watchlist_id}", status_code=204)
def remove_from_watchlist(
    watchlist_id: int,
    user_session_id: str = Query(..., description="User session ID for authorization"),
    db: Session = Depends(get_db),
):
    """Remove a series from user's watchlist.

    Args:
        watchlist_id: Watchlist item ID
        user_session_id: User session ID for authorization

    Returns:
        No content (204)
    """
    item = db.query(UserWatchlist).filter(UserWatchlist.id == watchlist_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if item.user_session_id != user_session_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")

    db.delete(item)
    db.commit()
    return None
