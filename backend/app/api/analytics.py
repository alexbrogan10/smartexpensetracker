from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.enums import TransactionType
from app.models.user import User
from app.schemas.analytics import (
    CategoryBreakdownItem,
    MerchantItem,
    RecurringAnalysisRead,
    SummaryRead,
    TrendItem,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryRead)
def get_summary(
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryRead:
    today = date.today()
    return analytics_service.get_summary(
        db, current_user.id, year or today.year, month or today.month
    )


@router.get("/categories", response_model=list[CategoryBreakdownItem])
def get_categories(
    year: int | None = None,
    month: int | None = None,
    type: TransactionType = TransactionType.EXPENSE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryBreakdownItem]:
    today = date.today()
    return analytics_service.get_category_breakdown(
        db, current_user.id, year or today.year, month or today.month, type
    )


@router.get("/trends", response_model=list[TrendItem])
def get_trends(
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrendItem]:
    return analytics_service.get_trends(db, current_user.id, months)


@router.get("/merchants", response_model=list[MerchantItem])
def get_merchants(
    year: int | None = None,
    month: int | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MerchantItem]:
    today = date.today()
    return analytics_service.get_top_merchants(
        db, current_user.id, year or today.year, month or today.month, limit
    )


@router.get("/recurring", response_model=RecurringAnalysisRead)
def get_recurring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringAnalysisRead:
    return analytics_service.get_recurring_analysis(db, current_user.id)
