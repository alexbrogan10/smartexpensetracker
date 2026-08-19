import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.notification import MarkAllReadResult, NotificationRead, UnreadCountRead
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationRead])
def list_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[NotificationRead]:
    items, total = notification_service.list_notifications(
        db, current_user.id, unread_only, page, page_size
    )
    return PaginatedResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountRead)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadCountRead:
    return UnreadCountRead(count=notification_service.get_unread_count(db, current_user.id))


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    try:
        notification = notification_service.mark_as_read(db, current_user.id, notification_id)
    except notification_service.NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        ) from exc
    return NotificationRead.model_validate(notification)


@router.post("/read-all", response_model=MarkAllReadResult)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkAllReadResult:
    marked_read = notification_service.mark_all_as_read(db, current_user.id)
    return MarkAllReadResult(marked_read=marked_read)
