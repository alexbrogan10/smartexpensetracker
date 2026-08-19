import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.notification import Notification


class NotificationNotFoundError(Exception):
    """Raised when a notification doesn't exist or isn't owned by this user."""


def build_unusual_spending_notification(
    user_id: uuid.UUID,
    category_name: str,
    payee: str,
    amount: Decimal,
    transaction_id: uuid.UUID,
) -> Notification:
    """Construct (but don't persist) an unusual-spending notification.

    Callers add it to the session themselves, typically alongside the
    transaction that triggered it, so both commit together.
    """
    return Notification(
        user_id=user_id,
        type=NotificationType.UNUSUAL_SPENDING,
        title="Unusual spending detected",
        message=(
            f"Your {category_name} expense of ${amount:.2f} at {payee} is unusually high "
            "compared to your typical spending in this category."
        ),
        is_read=False,
        related_transaction_id=transaction_id,
    )


def list_notifications(
    db: Session, user_id: uuid.UUID, unread_only: bool, page: int, page_size: int
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    items_stmt = (
        stmt.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(items_stmt).all())
    return items, total


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).where(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    )
    return db.scalar(stmt) or 0


def _get_notification_for_user(
    db: Session, user_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFoundError(notification_id)
    return notification


def mark_as_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notification = _get_notification_for_user(db, user_id, notification_id)
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: uuid.UUID) -> int:
    stmt = select(Notification).where(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    )
    unread = list(db.scalars(stmt).all())
    for notification in unread:
        notification.is_read = True
    db.commit()
    return len(unread)
