import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.savings_goal import SavingsGoalCreate, SavingsGoalRead, SavingsGoalUpdate
from app.services import savings_goal_service

router = APIRouter(prefix="/savings-goals", tags=["savings-goals"])


@router.get("", response_model=list[SavingsGoalRead])
def list_savings_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SavingsGoalRead]:
    return savings_goal_service.list_savings_goals(db, current_user.id)


@router.post("", response_model=SavingsGoalRead, status_code=status.HTTP_201_CREATED)
def create_savings_goal(
    data: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavingsGoalRead:
    return savings_goal_service.create_savings_goal(db, current_user.id, data)


@router.get("/{goal_id}", response_model=SavingsGoalRead)
def get_savings_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavingsGoalRead:
    try:
        return savings_goal_service.get_savings_goal(db, current_user.id, goal_id)
    except savings_goal_service.SavingsGoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found"
        ) from exc


@router.put("/{goal_id}", response_model=SavingsGoalRead)
def update_savings_goal(
    goal_id: uuid.UUID,
    data: SavingsGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavingsGoalRead:
    try:
        return savings_goal_service.update_savings_goal(db, current_user.id, goal_id, data)
    except savings_goal_service.SavingsGoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found"
        ) from exc


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_savings_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        savings_goal_service.delete_savings_goal(db, current_user.id, goal_id)
    except savings_goal_service.SavingsGoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found"
        ) from exc
