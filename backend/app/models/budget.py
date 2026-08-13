import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Budget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's budget for one calendar month. Category-level limits live in BudgetCategory."""

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "month", "year", name="uq_budget_user_month_year"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_budget_month_range"),
        CheckConstraint(
            "overall_amount IS NULL OR overall_amount > 0", name="ck_budget_overall_positive"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    month: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    overall_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    user: Mapped["User"] = relationship(back_populates="budgets")
    category_limits: Mapped[list["BudgetCategory"]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )


class BudgetCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A per-category spending limit within a budget."""

    __tablename__ = "budget_categories"
    __table_args__ = (
        UniqueConstraint("budget_id", "category_id", name="uq_budget_category"),
        CheckConstraint("amount > 0", name="ck_budget_category_amount_positive"),
    )

    budget_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    budget: Mapped["Budget"] = relationship(back_populates="category_limits")
    category: Mapped["Category"] = relationship()
