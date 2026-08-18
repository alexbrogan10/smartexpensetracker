import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.savings_goal import SavingsGoal
from app.schemas.savings_goal import SavingsGoalCreate, SavingsGoalRead, SavingsGoalUpdate


class SavingsGoalNotFoundError(Exception):
    """Raised when a savings goal doesn't exist or isn't owned by this user."""


def calculate_progress_percentage(current_amount: Decimal, target_amount: Decimal) -> float:
    if target_amount == 0:
        return 0.0
    percentage = float(current_amount / target_amount * 100)
    return round(min(percentage, 100.0), 1)


def calculate_on_track(
    target_amount: Decimal,
    current_amount: Decimal,
    target_date: date | None,
    created_at: datetime,
    as_of: date | None = None,
) -> bool | None:
    """Whether current savings pace is on track to hit the goal by its target date.

    None when there's no target date to assess against. Progress is tracked
    linearly from the goal's creation date: on_track compares the fraction of
    time elapsed against the fraction of the target amount saved so far.
    """
    if target_date is None:
        return None

    as_of = as_of or date.today()
    goal_met = current_amount >= target_amount

    if as_of >= target_date:
        return goal_met
    if goal_met:
        return True

    start_date = created_at.date()
    total_days = (target_date - start_date).days
    if total_days <= 0:
        return False

    elapsed_days = (as_of - start_date).days
    expected_fraction = max(0.0, min(1.0, elapsed_days / total_days))
    actual_fraction = float(current_amount / target_amount)

    return actual_fraction >= expected_fraction


def _build_read(goal: SavingsGoal) -> SavingsGoalRead:
    return SavingsGoalRead(
        id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        description=goal.description,
        progress_percentage=calculate_progress_percentage(goal.current_amount, goal.target_amount),
        is_on_track=calculate_on_track(
            goal.target_amount, goal.current_amount, goal.target_date, goal.created_at
        ),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


def get_goal_for_user(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> SavingsGoal:
    goal = db.get(SavingsGoal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise SavingsGoalNotFoundError(goal_id)
    return goal


def get_savings_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> SavingsGoalRead:
    return _build_read(get_goal_for_user(db, user_id, goal_id))


def list_savings_goals(db: Session, user_id: uuid.UUID) -> list[SavingsGoalRead]:
    stmt = (
        select(SavingsGoal)
        .where(SavingsGoal.user_id == user_id)
        .order_by(SavingsGoal.created_at.desc())
    )
    return [_build_read(g) for g in db.scalars(stmt).all()]


def create_savings_goal(
    db: Session, user_id: uuid.UUID, data: SavingsGoalCreate
) -> SavingsGoalRead:
    goal = SavingsGoal(
        user_id=user_id,
        name=data.name,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        target_date=data.target_date,
        description=data.description,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _build_read(goal)


def update_savings_goal(
    db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, data: SavingsGoalUpdate
) -> SavingsGoalRead:
    goal = get_goal_for_user(db, user_id, goal_id)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return _build_read(goal)


def delete_savings_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = get_goal_for_user(db, user_id, goal_id)
    db.delete(goal)
    db.commit()
