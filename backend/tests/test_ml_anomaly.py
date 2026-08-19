from decimal import Decimal

from app.ml.anomaly import MIN_HISTORY, detect_unusual_amount

TIGHT_CLUSTER = [Decimal(v) for v in ("10", "11", "12", "12", "13")]
FLAT_HISTORY = [Decimal("20")] * 5


def test_requires_minimum_history():
    short_history = TIGHT_CLUSTER[: MIN_HISTORY - 1]
    assert len(short_history) < MIN_HISTORY
    assert detect_unusual_amount(Decimal("1000"), short_history) is False


def test_flags_amount_far_above_cluster():
    assert detect_unusual_amount(Decimal("100"), TIGHT_CLUSTER) is True


def test_does_not_flag_amount_within_cluster():
    assert detect_unusual_amount(Decimal("12"), TIGHT_CLUSTER) is False


def test_flat_history_flags_amount_more_than_double():
    assert detect_unusual_amount(Decimal("50"), FLAT_HISTORY) is True


def test_flat_history_does_not_flag_amount_at_double():
    assert detect_unusual_amount(Decimal("40"), FLAT_HISTORY) is False


def test_flat_history_does_not_flag_similar_amount():
    assert detect_unusual_amount(Decimal("22"), FLAT_HISTORY) is False
