import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.enums import PaymentMethod, TransactionType
from app.models.user import User
from app.repositories.transaction_repository import SortField, SortOrder, TransactionFilters
from app.schemas.category import CategoryRead
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _to_read(transaction) -> TransactionRead:
    return TransactionRead(
        id=transaction.id,
        type=transaction.type,
        category=CategoryRead.model_validate(transaction.category),
        amount=transaction.amount,
        payee=transaction.payee,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        payment_method=transaction.payment_method,
        is_recurring=transaction.is_recurring,
        recurring_frequency=transaction.recurring_frequency,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


@router.get("", response_model=PaginatedResponse[TransactionRead])
def list_transactions(
    type: TransactionType | None = None,
    category_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    is_recurring: bool | None = None,
    payment_method: PaymentMethod | None = None,
    search: str | None = None,
    sort_by: SortField = "transaction_date",
    sort_order: SortOrder = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TransactionRead]:
    filters = TransactionFilters(
        type=type,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        is_recurring=is_recurring,
        payment_method=payment_method,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    items, total = transaction_service.get_transactions(db, current_user.id, filters)
    return PaginatedResponse(
        items=[_to_read(t) for t in items], total=total, page=page, page_size=page_size
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    try:
        transaction = transaction_service.create_transaction(db, current_user.id, data)
    except transaction_service.CategoryTypeMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return _to_read(transaction)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    try:
        transaction = transaction_service.get_transaction(db, current_user.id, transaction_id)
    except transaction_service.TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        ) from exc
    return _to_read(transaction)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    try:
        transaction = transaction_service.update_transaction(
            db, current_user.id, transaction_id, data
        )
    except transaction_service.TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        ) from exc
    except (
        transaction_service.CategoryTypeMismatchError,
        transaction_service.InvalidRecurringStateError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return _to_read(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        transaction_service.delete_transaction(db, current_user.id, transaction_id)
    except transaction_service.TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        ) from exc
