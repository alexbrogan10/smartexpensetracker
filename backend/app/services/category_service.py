import uuid

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import CategoryType
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryNotFoundError(Exception):
    """Raised when a category doesn't exist or isn't visible to this user."""


class DefaultCategoryImmutableError(Exception):
    """Raised when trying to modify or delete a system default category."""


class CategoryInUseError(Exception):
    """Raised when deleting a category that still has transactions."""


class CategoryAlreadyExistsError(Exception):
    """Raised when a create/rename collides with an existing (user_id, name, type)."""


def list_categories(
    db: Session, user_id: uuid.UUID, type_: CategoryType | None = None
) -> list[Category]:
    """Return system default categories plus this user's custom categories."""
    stmt = select(Category).where(or_(Category.user_id.is_(None), Category.user_id == user_id))
    if type_ is not None:
        stmt = stmt.where(Category.type == type_)
    stmt = stmt.order_by(Category.type, Category.name)
    return list(db.scalars(stmt).all())


def get_category_for_user(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    """Fetch a category visible to this user (default or their own), or raise."""
    category = db.get(Category, category_id)
    if category is None or (category.user_id is not None and category.user_id != user_id):
        raise CategoryNotFoundError(category_id)
    return category


def create_category(db: Session, user_id: uuid.UUID, data: CategoryCreate) -> Category:
    category = Category(
        user_id=user_id,
        name=data.name,
        type=data.type,
        icon=data.icon,
        color=data.color,
        is_default=False,
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryAlreadyExistsError(data.name) from exc
    db.refresh(category)
    return category


def update_category(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, data: CategoryUpdate
) -> Category:
    category = get_category_for_user(db, user_id, category_id)
    if category.is_default:
        raise DefaultCategoryImmutableError(category_id)

    if data.name is not None:
        category.name = data.name
    if data.icon is not None:
        category.icon = data.icon
    if data.color is not None:
        category.color = data.color

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryAlreadyExistsError(data.name) from exc
    db.refresh(category)
    return category


def delete_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
    category = get_category_for_user(db, user_id, category_id)
    if category.is_default:
        raise DefaultCategoryImmutableError(category_id)

    db.delete(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryInUseError(category_id) from exc
