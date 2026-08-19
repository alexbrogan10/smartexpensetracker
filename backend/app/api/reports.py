import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.enums import PaymentMethod, TransactionType
from app.models.user import User
from app.repositories.transaction_repository import TransactionFilters
from app.services import export_service

router = APIRouter(prefix="/reports", tags=["reports"])

_MEDIA_TYPES = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.get("/export")
def export_transactions(
    format: Literal["csv", "xlsx"] = "csv",
    type: TransactionType | None = None,
    category_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    is_recurring: bool | None = None,
    payment_method: PaymentMethod | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
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
    )

    if format == "xlsx":
        content = export_service.export_transactions_xlsx(db, current_user.id, filters)
    else:
        content = export_service.export_transactions_csv(db, current_user.id, filters)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"transactions-{timestamp}.{format}"

    return Response(
        content=content,
        media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
