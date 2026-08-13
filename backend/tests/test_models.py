from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.seed import seed_default_categories
from app.models import Budget, BudgetCategory, Category, SavingsGoal, Transaction, User
from app.models.enums import CategoryType, RecurringFrequency, TransactionType


def make_user(db_session, email="jane@example.com") -> User:
    user = User(email=email, hashed_password="hashed", full_name="Jane Doe")
    db_session.add(user)
    db_session.flush()
    return user


def make_category(db_session, user=None, name="Groceries", type_=CategoryType.EXPENSE) -> Category:
    category = Category(user_id=user.id if user else None, name=name, type=type_)
    db_session.add(category)
    db_session.flush()
    return category


def test_user_relationships_cascade_on_delete(db_session):
    user = make_user(db_session)
    category = make_category(db_session, user=user)
    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("42.50"),
            payee="Trader Joe's",
            transaction_date=date(2026, 8, 1),
        )
    )
    db_session.flush()

    assert len(user.transactions) == 1
    assert user.transactions[0].category.name == "Groceries"

    db_session.delete(user)
    db_session.flush()

    assert db_session.query(Transaction).count() == 0


def test_category_unique_per_user_name_type(db_session):
    user = make_user(db_session)
    make_category(db_session, user=user, name="Groceries", type_=CategoryType.EXPENSE)

    db_session.add(Category(user_id=user.id, name="Groceries", type=CategoryType.EXPENSE))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_amount_must_be_positive(db_session):
    user = make_user(db_session)
    category = make_category(db_session, user=user)

    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("-5.00"),
            payee="Refund",
            transaction_date=date(2026, 8, 1),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_recurring_requires_frequency(db_session):
    user = make_user(db_session)
    category = make_category(db_session, user=user)

    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("15.00"),
            payee="Netflix",
            transaction_date=date(2026, 8, 1),
            is_recurring=True,
            recurring_frequency=None,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_recurring_with_frequency_succeeds(db_session):
    user = make_user(db_session)
    category = make_category(db_session, user=user)

    db_session.add(
        Transaction(
            user_id=user.id,
            category_id=category.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("15.00"),
            payee="Netflix",
            transaction_date=date(2026, 8, 1),
            is_recurring=True,
            recurring_frequency=RecurringFrequency.MONTHLY,
        )
    )
    db_session.flush()

    assert db_session.query(Transaction).count() == 1


def test_budget_unique_per_user_month_year(db_session):
    user = make_user(db_session)
    db_session.add(Budget(user_id=user.id, month=8, year=2026, overall_amount=Decimal("3000")))
    db_session.flush()

    db_session.add(Budget(user_id=user.id, month=8, year=2026, overall_amount=Decimal("3500")))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_budget_category_limit_relates_to_budget(db_session):
    user = make_user(db_session)
    category = make_category(db_session, user=user)
    budget = Budget(user_id=user.id, month=8, year=2026)
    db_session.add(budget)
    db_session.flush()

    db_session.add(
        BudgetCategory(budget_id=budget.id, category_id=category.id, amount=Decimal("400.00"))
    )
    db_session.flush()

    assert len(budget.category_limits) == 1
    assert budget.category_limits[0].amount == Decimal("400.00")


def test_savings_goal_current_amount_cannot_be_negative(db_session):
    user = make_user(db_session)

    db_session.add(
        SavingsGoal(
            user_id=user.id,
            name="Emergency Fund",
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("-1.00"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_seed_default_categories_is_idempotent(db_session):
    created = seed_default_categories(db_session)
    assert len(created) == 19

    again = seed_default_categories(db_session)
    assert again == []
    assert db_session.query(Category).filter(Category.is_default.is_(True)).count() == 19
