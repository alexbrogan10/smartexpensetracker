from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.prediction import SpendingPredictionResponse
from app.services import predictions_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/spending", response_model=SpendingPredictionResponse)
def get_spending_prediction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SpendingPredictionResponse:
    return predictions_service.get_spending_prediction(db, current_user.id)
