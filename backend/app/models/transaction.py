import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentMethod, RecurringFrequency, TransactionType

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single income or expense record.

    Income and expenses share one table (discriminated by `type`) since
    the API, search/filter, and cash-flow calculations all need to treat
    them as one stream of transactions. `payee` holds the merchant for an
    expense or the source for income; `payment_method` only applies to
    expenses.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_amount_positive"),
        CheckConstraint(
            "(is_recurring = false AND recurring_frequency IS NULL) "
            "OR (is_recurring = true AND recurring_frequency IS NOT NULL)",
            name="ck_transaction_recurring_frequency_required",
        ),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_category", "user_id", "category_id"),
        Index("ix_transactions_user_type", "user_id", "type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, validate_strings=True, name="ck_transaction_type"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payee: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(
            PaymentMethod,
            native_enum=False,
            validate_strings=True,
            name="ck_transaction_payment_method",
        ),
        nullable=True,
    )
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_frequency: Mapped[RecurringFrequency | None] = mapped_column(
        Enum(
            RecurringFrequency,
            native_enum=False,
            validate_strings=True,
            name="ck_transaction_recurring_frequency",
        ),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="transactions")
    category: Mapped["Category"] = relationship(back_populates="transactions")
