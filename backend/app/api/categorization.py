from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.categorization import CategorySuggestionRequest, CategorySuggestionResponse
from app.services import categorization_service

router = APIRouter(prefix="/categorization", tags=["categorization"])


@router.post("/suggest", response_model=CategorySuggestionResponse)
def suggest_category(
    data: CategorySuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategorySuggestionResponse:
    return categorization_service.suggest_category(
        db, current_user.id, data.type, data.payee, data.description
    )
