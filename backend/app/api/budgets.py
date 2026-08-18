import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.services import budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    year: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BudgetRead]:
    return budget_service.list_budgets(db, current_user.id, year)


@router.get("/current", response_model=BudgetRead | None)
def get_current_budget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead | None:
    return budget_service.get_current_budget(db, current_user.id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    try:
        return budget_service.create_budget(db, current_user.id, data)
    except budget_service.InvalidBudgetCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except budget_service.BudgetAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget already exists for this month",
        ) from exc


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    try:
        return budget_service.get_budget(db, current_user.id, budget_id)
    except budget_service.BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        ) from exc


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: uuid.UUID,
    data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    try:
        return budget_service.update_budget(db, current_user.id, budget_id, data)
    except budget_service.BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        ) from exc
    except budget_service.InvalidBudgetCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        budget_service.delete_budget(db, current_user.id, budget_id)
    except budget_service.BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        ) from exc
