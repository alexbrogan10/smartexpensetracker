import csv
import io
import uuid

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionFilters, list_transactions_for_export

EXPORT_COLUMNS = [
    "date",
    "type",
    "category",
    "payee",
    "amount",
    "description",
    "payment_method",
    "is_recurring",
    "recurring_frequency",
]


def _row_values(transaction: Transaction) -> list[str]:
    return [
        transaction.transaction_date.isoformat(),
        transaction.type.value,
        transaction.category.name,
        transaction.payee,
        str(transaction.amount),
        transaction.description or "",
        transaction.payment_method.value if transaction.payment_method else "",
        "true" if transaction.is_recurring else "false",
        transaction.recurring_frequency.value if transaction.recurring_frequency else "",
    ]


def export_transactions_csv(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> bytes:
    transactions = list_transactions_for_export(db, user_id, filters)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for transaction in transactions:
        writer.writerow(_row_values(transaction))

    return buffer.getvalue().encode("utf-8")


def export_transactions_xlsx(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> bytes:
    transactions = list_transactions_for_export(db, user_id, filters)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"
    sheet.append(EXPORT_COLUMNS)
    for transaction in transactions:
        sheet.append(_row_values(transaction))

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
