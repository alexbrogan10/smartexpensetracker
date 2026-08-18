import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.budget import Budget, BudgetCategory
from app.models.enums import CategoryType
from app.repositories.transaction_repository import (
    get_expense_totals_by_category,
    get_total_expenses,
)
from app.schemas.budget import (
    BudgetCategoryInput,
    BudgetCategoryRead,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
    compute_status,
)
from app.schemas.category import CategoryRead
from app.services.category_service import CategoryNotFoundError, get_category_for_user


class BudgetNotFoundError(Exception):
    """Raised when a budget doesn't exist or isn't owned by this user."""


class BudgetAlreadyExistsError(Exception):
    """Raised when a user already has a budget for the given month/year."""


class InvalidBudgetCategoryError(Exception):
    """Raised when a category limit references a category that can't be budgeted."""


def _validate_category_limits(
    db: Session, user_id: uuid.UUID, category_limits: list[BudgetCategoryInput]
) -> None:
    for limit in category_limits:
        try:
            category = get_category_for_user(db, user_id, limit.category_id)
        except CategoryNotFoundError as exc:
            raise InvalidBudgetCategoryError(
                f"Category {limit.category_id} does not exist or is not accessible"
            ) from exc
        if category.type != CategoryType.EXPENSE:
            raise InvalidBudgetCategoryError(
                f"Category '{category.name}' is not an expense category and cannot be budgeted"
            )


def _build_budget_read(db: Session, budget: Budget) -> BudgetRead:
    category_totals = get_expense_totals_by_category(db, budget.user_id, budget.year, budget.month)
    overall_spent = get_total_expenses(db, budget.user_id, budget.year, budget.month)

    category_reads = []
    for limit in budget.category_limits:
        spent = category_totals.get(limit.category_id, Decimal("0"))
        percent = float(spent / limit.amount * 100) if limit.amount else 0.0
        category_reads.append(
            BudgetCategoryRead(
                id=limit.id,
                category=CategoryRead.model_validate(limit.category),
                amount=limit.amount,
                spent=spent,
                remaining=limit.amount - spent,
                percent_used=round(percent, 1),
                status=compute_status(spent, limit.amount),
            )
        )

    overall_remaining = budget.overall_amount - overall_spent if budget.overall_amount else None
    overall_percent = (
        float(overall_spent / budget.overall_amount * 100) if budget.overall_amount else None
    )

    return BudgetRead(
        id=budget.id,
        month=budget.month,
        year=budget.year,
        overall_amount=budget.overall_amount,
        overall_spent=overall_spent,
        overall_remaining=overall_remaining,
        overall_percent_used=round(overall_percent, 1) if overall_percent is not None else None,
        overall_status=compute_status(overall_spent, budget.overall_amount),
        category_limits=category_reads,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


def get_budget_for_user(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget:
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != user_id:
        raise BudgetNotFoundError(budget_id)
    return budget


def get_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> BudgetRead:
    return _build_budget_read(db, get_budget_for_user(db, user_id, budget_id))


def get_current_budget(db: Session, user_id: uuid.UUID) -> BudgetRead | None:
    today = date.today()
    budget = db.scalar(
        select(Budget).where(
            Budget.user_id == user_id, Budget.year == today.year, Budget.month == today.month
        )
    )
    return _build_budget_read(db, budget) if budget else None


def list_budgets(db: Session, user_id: uuid.UUID, year: int | None = None) -> list[BudgetRead]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    if year is not None:
        stmt = stmt.where(Budget.year == year)
    stmt = stmt.order_by(Budget.year.desc(), Budget.month.desc())
    budgets = db.scalars(stmt).all()
    return [_build_budget_read(db, b) for b in budgets]


def create_budget(db: Session, user_id: uuid.UUID, data: BudgetCreate) -> BudgetRead:
    _validate_category_limits(db, user_id, data.category_limits)

    budget = Budget(
        user_id=user_id, month=data.month, year=data.year, overall_amount=data.overall_amount
    )
    budget.category_limits = [
        BudgetCategory(category_id=limit.category_id, amount=limit.amount)
        for limit in data.category_limits
    ]

    db.add(budget)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BudgetAlreadyExistsError(f"{user_id}:{data.year}-{data.month}") from exc
    db.refresh(budget)
    return _build_budget_read(db, budget)


def update_budget(
    db: Session, user_id: uuid.UUID, budget_id: uuid.UUID, data: BudgetUpdate
) -> BudgetRead:
    budget = get_budget_for_user(db, user_id, budget_id)
    updates = data.model_dump(exclude_unset=True)

    if "overall_amount" in updates:
        budget.overall_amount = data.overall_amount

    if "category_limits" in updates:
        new_limits = data.category_limits or []
        _validate_category_limits(db, user_id, new_limits)
        budget.category_limits = [
            BudgetCategory(category_id=limit.category_id, amount=limit.amount)
            for limit in new_limits
        ]

    db.commit()
    db.refresh(budget)
    return _build_budget_read(db, budget)


def delete_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
    budget = get_budget_for_user(db, user_id, budget_id)
    db.delete(budget)
    db.commit()
