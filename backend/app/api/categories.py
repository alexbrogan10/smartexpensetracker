import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.enums import CategoryType
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    type: CategoryType | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryRead]:
    categories = category_service.list_categories(db, current_user.id, type)
    return [CategoryRead.model_validate(c) for c in categories]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryRead:
    try:
        category = category_service.create_category(db, current_user.id, data)
    except category_service.CategoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name and type already exists",
        ) from exc
    return CategoryRead.model_validate(category)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryRead:
    try:
        category = category_service.update_category(db, current_user.id, category_id, data)
    except category_service.CategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        ) from exc
    except category_service.DefaultCategoryImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Default categories cannot be modified"
        ) from exc
    except category_service.CategoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name and type already exists",
        ) from exc
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        category_service.delete_category(db, current_user.id, category_id)
    except category_service.CategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        ) from exc
    except category_service.DefaultCategoryImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Default categories cannot be deleted"
        ) from exc
    except category_service.CategoryInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a category that has transactions",
        ) from exc
