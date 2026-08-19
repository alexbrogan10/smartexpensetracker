import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ImportStatus

if TYPE_CHECKING:
    from app.models.user import User


class TransactionImport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A CSV (or future format) import batch.

    `rows` holds the full parsed/validated preview as JSON — transient
    staging data with no need for its own relational schema. Once
    confirmed, valid rows become real Transaction records; this row
    itself is kept as a record of the import, not re-used afterward.
    """

    __tablename__ = "transaction_imports"
    __table_args__ = (
        CheckConstraint("total_rows >= 0", name="ck_import_total_rows_non_negative"),
        CheckConstraint("valid_rows >= 0", name="ck_import_valid_rows_non_negative"),
        CheckConstraint("error_rows >= 0", name="ck_import_error_rows_non_negative"),
        CheckConstraint("duplicate_rows >= 0", name="ck_import_duplicate_rows_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, native_enum=False, validate_strings=True, name="ck_import_status"),
        default=ImportStatus.PENDING,
        nullable=False,
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    rows: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship(back_populates="transaction_imports")
