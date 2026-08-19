import uuid

from app.ml.categorization import (
    MIN_DISTINCT_CATEGORIES,
    MIN_TRANSACTIONS,
    TrainingExample,
    build_text,
    has_enough_data,
    suggest_categories,
)

GROCERIES = uuid.uuid4()
DINING = uuid.uuid4()


def make_examples(count_per_category: int) -> list[TrainingExample]:
    examples = []
    for _ in range(count_per_category):
        examples.append(TrainingExample(text="Whole Foods weekly groceries", category_id=GROCERIES))
        examples.append(TrainingExample(text="Chipotle lunch burrito", category_id=DINING))
    return examples


def test_build_text_combines_payee_and_description():
    assert build_text("Whole Foods", "weekly shop") == "Whole Foods weekly shop"


def test_build_text_falls_back_to_payee_only():
    assert build_text("Whole Foods", None) == "Whole Foods"
    assert build_text("Whole Foods", "") == "Whole Foods"


def test_has_enough_data_requires_minimum_transactions():
    examples = make_examples(1)
    assert len(examples) < MIN_TRANSACTIONS
    assert has_enough_data(examples) is False


def test_has_enough_data_requires_multiple_categories():
    examples = [
        TrainingExample(text="Whole Foods", category_id=GROCERIES) for _ in range(MIN_TRANSACTIONS)
    ]
    assert has_enough_data(examples) is False


def test_has_enough_data_true_once_thresholds_met():
    examples = make_examples(MIN_TRANSACTIONS)
    assert len(examples) >= MIN_TRANSACTIONS
    assert len({e.category_id for e in examples}) >= MIN_DISTINCT_CATEGORIES
    assert has_enough_data(examples) is True


def test_suggest_categories_returns_empty_when_insufficient_data():
    examples = make_examples(1)
    assert suggest_categories(examples, "Whole Foods") == []


def test_suggest_categories_ranks_correct_category_first():
    examples = make_examples(15)
    suggestions = suggest_categories(examples, "Whole Foods grocery run")

    assert suggestions
    assert suggestions[0].category_id == GROCERIES
    assert 0.0 < suggestions[0].confidence <= 1.0


def test_suggest_categories_confidences_are_sorted_descending():
    examples = make_examples(15)
    suggestions = suggest_categories(examples, "Chipotle takeout")

    confidences = [s.confidence for s in suggestions]
    assert confidences == sorted(confidences, reverse=True)


def test_suggest_categories_respects_top_k():
    examples = make_examples(15)
    suggestions = suggest_categories(examples, "Whole Foods", top_k=1)
    assert len(suggestions) == 1
