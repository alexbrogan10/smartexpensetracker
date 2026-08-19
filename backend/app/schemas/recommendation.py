import uuid
from typing import Literal

from pydantic import BaseModel

RecommendationType = Literal["budget_pace", "category_trend", "savings_off_track"]
RecommendationSeverity = Literal["info", "warning", "critical"]


class Recommendation(BaseModel):
    type: RecommendationType
    severity: RecommendationSeverity
    message: str
    category_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None


class RecommendationsResponse(BaseModel):
    recommendations: list[Recommendation]
