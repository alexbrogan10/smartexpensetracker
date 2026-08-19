import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.categorization import TrainingExample, build_text, suggest_categories
from app.models.category import Category
from app.models.enums import TransactionType
from app.repositories.transaction_repository import list_categorized_texts
from app.schemas.categorization import CategorySuggestion, CategorySuggestionResponse


def suggest_category(
    db: Session,
    user_id: uuid.UUID,
    type_: TransactionType,
    payee: str,
    description: str | None,
) -> CategorySuggestionResponse:
    rows = list_categorized_texts(db, user_id, type_)
    examples = [
        TrainingExample(text=build_text(row_payee, row_description), category_id=category_id)
        for row_payee, row_description, category_id in rows
    ]

    query_text = build_text(payee, description)
    ranked = suggest_categories(examples, query_text)
    if not ranked:
        return CategorySuggestionResponse(status="insufficient_data", suggestions=[])

    category_ids = [s.category_id for s in ranked]
    stmt = select(Category).where(Category.id.in_(category_ids))
    categories = {c.id: c for c in db.scalars(stmt).all()}

    suggestions = [
        CategorySuggestion(
            category_id=s.category_id,
            category_name=categories[s.category_id].name,
            confidence=s.confidence,
        )
        for s in ranked
        if s.category_id in categories
    ]
    return CategorySuggestionResponse(status="ok", suggestions=suggestions)
