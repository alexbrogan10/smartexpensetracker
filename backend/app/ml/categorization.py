"""Text-based transaction categorization.

Trains a small classifier per request from one user's own transaction
history (payee + description -> category) and ranks candidate categories
for a new transaction. No model is persisted: with the dataset sizes a
personal expense tracker produces (hundreds, not millions, of rows),
training a TF-IDF + Naive Bayes pipeline from scratch takes well under
100ms, so caching or versioning a serialized model would add real
complexity for no measurable benefit.
"""

import uuid
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MIN_TRANSACTIONS = 10
MIN_DISTINCT_CATEGORIES = 2


@dataclass(frozen=True)
class TrainingExample:
    text: str
    category_id: uuid.UUID


@dataclass(frozen=True)
class CategorySuggestion:
    category_id: uuid.UUID
    confidence: float


def build_text(payee: str, description: str | None) -> str:
    """Combine payee and description into one text field for the vectorizer."""
    return f"{payee} {description}".strip() if description else payee


def has_enough_data(examples: list[TrainingExample]) -> bool:
    if len(examples) < MIN_TRANSACTIONS:
        return False
    return len({e.category_id for e in examples}) >= MIN_DISTINCT_CATEGORIES


def suggest_categories(
    examples: list[TrainingExample], query_text: str, top_k: int = 3
) -> list[CategorySuggestion]:
    """Train on `examples` and rank candidate categories for `query_text`.

    Returns an empty list if there isn't enough data to train a meaningful
    classifier (see `has_enough_data`) — callers should treat that as "no
    suggestion available" rather than falling back to a low-confidence guess.
    """
    if not has_enough_data(examples):
        return []

    texts = [e.text for e in examples]
    labels = [str(e.category_id) for e in examples]

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("classifier", MultinomialNB()),
        ]
    )
    pipeline.fit(texts, labels)

    probabilities = pipeline.predict_proba([query_text])[0]
    class_labels = pipeline.classes_

    ranked = sorted(zip(class_labels, probabilities, strict=True), key=lambda p: -p[1])
    return [
        CategorySuggestion(category_id=uuid.UUID(label), confidence=round(float(prob), 4))
        for label, prob in ranked[:top_k]
    ]
