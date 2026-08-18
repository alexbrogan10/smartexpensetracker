import uuid

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.repositories.transaction_repository import (
    TransactionFilters,
    get_transaction_for_user,
    list_transactions,
)
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.category_service import CategoryNotFoundError, get_category_for_user


class TransactionNotFoundError(Exception):
    """Raised when a transaction doesn't exist or isn't owned by this user."""


class CategoryTypeMismatchError(Exception):
    """Raised when a transaction's category doesn't match its income/expense type."""


class InvalidRecurringStateError(Exception):
    """Raised when is_recurring/recurring_frequency would end up inconsistent."""


def _validate_category(db: Session, user_id: uuid.UUID, category_id, expected_type) -> None:
    try:
        category = get_category_for_user(db, user_id, category_id)
    except CategoryNotFoundError as exc:
        raise CategoryTypeMismatchError(
            "Category does not exist or is not accessible to this user"
        ) from exc
    if category.type != expected_type:
        raise CategoryTypeMismatchError(
            f"Category type '{category.type}' does not match transaction type '{expected_type}'"
        )


def get_transactions(
    db: Session, user_id: uuid.UUID, filters: TransactionFilters
) -> tuple[list[Transaction], int]:
    return list_transactions(db, user_id, filters)


def get_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    transaction = get_transaction_for_user(db, user_id, transaction_id)
    if transaction is None:
        raise TransactionNotFoundError(transaction_id)
    return transaction


def create_transaction(db: Session, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
    _validate_category(db, user_id, data.category_id, data.type)

    transaction = Transaction(
        user_id=user_id,
        type=data.type,
        category_id=data.category_id,
        amount=data.amount,
        payee=data.payee,
        description=data.description,
        transaction_date=data.transaction_date,
        payment_method=data.payment_method,
        is_recurring=data.is_recurring,
        recurring_frequency=data.recurring_frequency,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID, data: TransactionUpdate
) -> Transaction:
    transaction = get_transaction(db, user_id, transaction_id)

    updates = data.model_dump(exclude_unset=True)

    new_type = updates.get("type", transaction.type)
    new_category_id = updates.get("category_id", transaction.category_id)
    if "type" in updates or "category_id" in updates:
        _validate_category(db, user_id, new_category_id, new_type)

    new_is_recurring = updates.get("is_recurring", transaction.is_recurring)
    new_recurring_frequency = updates.get("recurring_frequency", transaction.recurring_frequency)
    if new_is_recurring and new_recurring_frequency is None:
        raise InvalidRecurringStateError(
            "recurring_frequency is required when is_recurring is true"
        )
    if not new_is_recurring and new_recurring_frequency is not None:
        raise InvalidRecurringStateError(
            "recurring_frequency must be omitted when is_recurring is false"
        )

    for field, value in updates.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    transaction = get_transaction(db, user_id, transaction_id)
    db.delete(transaction)
    db.commit()
