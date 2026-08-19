import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.ml.anomaly import detect_unusual_amount
from app.models.category import Category
from app.models.enums import (
    CategoryType,
    ImportStatus,
    PaymentMethod,
    RecurringFrequency,
    TransactionType,
)
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport
from app.repositories.transaction_repository import get_category_amounts, transaction_exists
from app.schemas.transaction_import import (
    ImportConfirmResult,
    ImportRowPreview,
    ParsedTransactionFields,
)
from app.services import category_service, notification_service
from app.services.import_parsers.base import MissingColumnsError, ParsedRow
from app.services.import_parsers.csv_parser import CsvTransactionParser

MAX_IMPORT_ROWS = 1000

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")


class ImportNotFoundError(Exception):
    """Raised when an import doesn't exist or isn't owned by this user."""


class ImportNotPendingError(Exception):
    """Raised when confirming/cancelling an import that's already resolved."""


class ImportFileError(Exception):
    """Raised for file-level problems: bad encoding, missing columns, no rows."""


class ImportTooLargeError(Exception):
    """Raised when a file exceeds MAX_IMPORT_ROWS."""


def _try_parse_date(value: str) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _try_parse_amount(value: str) -> Decimal | None:
    cleaned = value.replace(",", "").replace("$", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _find_category(
    db: Session, user_id: uuid.UUID, name: str, type_: TransactionType
) -> Category | None:
    categories = category_service.list_categories(db, user_id, CategoryType(type_.value))
    name_lower = name.strip().lower()
    return next((c for c in categories if c.name.lower() == name_lower), None)


def _validate_row(
    db: Session, user_id: uuid.UUID, row: ParsedRow, seen_in_batch: set[tuple[str, str, str]]
) -> ImportRowPreview:
    errors: list[str] = []
    raw = row.raw

    date_str = raw.get("date", "")
    type_str = raw.get("type", "").strip().lower()
    category_str = raw.get("category", "")
    payee = raw.get("payee", "")
    amount_str = raw.get("amount", "")

    if not date_str:
        errors.append("date is required")
    if type_str not in ("income", "expense"):
        errors.append("type must be 'income' or 'expense'")
    if not category_str:
        errors.append("category is required")
    if not payee:
        errors.append("payee is required")
    if not amount_str:
        errors.append("amount is required")

    parsed_date = _try_parse_date(date_str) if date_str else None
    if date_str and parsed_date is None:
        errors.append(f"invalid date: '{date_str}' (expected YYYY-MM-DD or MM/DD/YYYY)")

    parsed_amount = _try_parse_amount(amount_str) if amount_str else None
    if amount_str and parsed_amount is None:
        errors.append(f"invalid amount: '{amount_str}'")
    elif parsed_amount is not None and parsed_amount <= 0:
        errors.append("amount must be positive")

    category = None
    if category_str and type_str in ("income", "expense"):
        category = _find_category(db, user_id, category_str, TransactionType(type_str))
        if category is None:
            errors.append(f"unknown {type_str} category: '{category_str}'")

    payment_method: PaymentMethod | None = None
    payment_method_str = raw.get("payment_method", "").strip().lower()
    if payment_method_str:
        try:
            payment_method = PaymentMethod(payment_method_str)
        except ValueError:
            errors.append(f"unknown payment_method: '{payment_method_str}'")

    is_recurring = raw.get("is_recurring", "").strip().lower() in ("true", "yes", "1")
    recurring_frequency: RecurringFrequency | None = None
    if is_recurring:
        frequency_str = raw.get("recurring_frequency", "").strip().lower()
        try:
            recurring_frequency = RecurringFrequency(frequency_str) if frequency_str else None
        except ValueError:
            recurring_frequency = None
        if recurring_frequency is None:
            errors.append("is_recurring is set but recurring_frequency is missing or invalid")

    if errors:
        return ImportRowPreview(
            row_number=row.row_number, raw=raw, status="error", errors=errors, fields=None
        )

    assert parsed_date is not None
    assert parsed_amount is not None
    assert category is not None

    fields = ParsedTransactionFields(
        type=TransactionType(type_str),
        category_id=category.id,
        category_name=category.name,
        amount=parsed_amount,
        payee=payee,
        description=raw.get("description") or None,
        transaction_date=parsed_date,
        payment_method=payment_method,
        is_recurring=is_recurring,
        recurring_frequency=recurring_frequency,
    )

    dup_key = (parsed_date.isoformat(), payee.strip().lower(), str(parsed_amount))
    if dup_key in seen_in_batch:
        return ImportRowPreview(
            row_number=row.row_number,
            raw=raw,
            status="duplicate",
            errors=["duplicate of another row in this file"],
            fields=fields,
        )
    if transaction_exists(db, user_id, parsed_date, payee, parsed_amount):
        return ImportRowPreview(
            row_number=row.row_number,
            raw=raw,
            status="duplicate",
            errors=["duplicate of an existing transaction"],
            fields=fields,
        )

    seen_in_batch.add(dup_key)
    return ImportRowPreview(
        row_number=row.row_number, raw=raw, status="valid", errors=[], fields=fields
    )


def create_preview(
    db: Session, user_id: uuid.UUID, filename: str, file_bytes: bytes
) -> TransactionImport:
    try:
        rows = CsvTransactionParser().parse(file_bytes)
    except MissingColumnsError as exc:
        raise ImportFileError(str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise ImportFileError("Could not read file as UTF-8 text") from exc

    if len(rows) == 0:
        raise ImportFileError("File contains no data rows")
    if len(rows) > MAX_IMPORT_ROWS:
        raise ImportTooLargeError(f"File has {len(rows)} rows; the limit is {MAX_IMPORT_ROWS}")

    seen_in_batch: set[tuple[str, str, str]] = set()
    previews = [_validate_row(db, user_id, row, seen_in_batch) for row in rows]

    record = TransactionImport(
        user_id=user_id,
        filename=filename,
        status=ImportStatus.PENDING,
        total_rows=len(previews),
        valid_rows=sum(1 for p in previews if p.status == "valid"),
        error_rows=sum(1 for p in previews if p.status == "error"),
        duplicate_rows=sum(1 for p in previews if p.status == "duplicate"),
        rows=[p.model_dump(mode="json") for p in previews],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_import_for_user(db: Session, user_id: uuid.UUID, import_id: uuid.UUID) -> TransactionImport:
    record = db.get(TransactionImport, import_id)
    if record is None or record.user_id != user_id:
        raise ImportNotFoundError(import_id)
    return record


def confirm_import(
    db: Session, user_id: uuid.UUID, import_id: uuid.UUID, include_duplicates: bool
) -> ImportConfirmResult:
    record = get_import_for_user(db, user_id, import_id)
    if record.status != ImportStatus.PENDING:
        raise ImportNotPendingError(import_id)

    statuses_to_import = {"valid"} | ({"duplicate"} if include_duplicates else set())

    # Snapshot each category's pre-import history once, up front: every row
    # is compared against spending *before* this batch, not against amounts
    # from earlier in the same file.
    category_history: dict[uuid.UUID, list[Decimal]] = {}
    unusual_candidates: list[tuple[Transaction, str]] = []

    imported = 0
    skipped = 0
    for row in record.rows:
        fields = row.get("fields")
        if row["status"] not in statuses_to_import or fields is None:
            skipped += 1
            continue

        category = db.get(Category, uuid.UUID(fields["category_id"]))
        if category is None:
            skipped += 1
            continue

        transaction_type = TransactionType(fields["type"])
        amount = Decimal(fields["amount"])

        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            category_id=category.id,
            amount=amount,
            payee=fields["payee"],
            description=fields["description"],
            transaction_date=date.fromisoformat(fields["transaction_date"]),
            payment_method=PaymentMethod(fields["payment_method"])
            if fields["payment_method"]
            else None,
            is_recurring=fields["is_recurring"],
            recurring_frequency=RecurringFrequency(fields["recurring_frequency"])
            if fields["recurring_frequency"]
            else None,
        )
        db.add(transaction)
        imported += 1

        if transaction_type == TransactionType.EXPENSE:
            if category.id not in category_history:
                category_history[category.id] = get_category_amounts(db, user_id, category.id)
            if detect_unusual_amount(amount, category_history[category.id]):
                unusual_candidates.append((transaction, category.name))

    db.flush()  # assigns ids to the new transactions before notifications reference them
    for transaction, category_name in unusual_candidates:
        db.add(
            notification_service.build_unusual_spending_notification(
                user_id, category_name, transaction.payee, transaction.amount, transaction.id
            )
        )

    record.status = ImportStatus.CONFIRMED
    db.commit()

    return ImportConfirmResult(imported_count=imported, skipped_count=skipped)


def cancel_import(db: Session, user_id: uuid.UUID, import_id: uuid.UUID) -> None:
    record = get_import_for_user(db, user_id, import_id)
    if record.status != ImportStatus.PENDING:
        raise ImportNotPendingError(import_id)
    db.delete(record)
    db.commit()
