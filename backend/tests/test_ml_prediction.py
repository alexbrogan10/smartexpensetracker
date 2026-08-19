from decimal import Decimal

from app.ml.prediction import MIN_DATA_POINTS, forecast_next, has_enough_data


def test_has_enough_data_requires_minimum_nonzero_months():
    values = [Decimal("0"), Decimal("0"), Decimal("10")]
    assert len([v for v in values if v > 0]) < MIN_DATA_POINTS
    assert has_enough_data(values) is False


def test_has_enough_data_ignores_zero_months():
    values = [Decimal("0"), Decimal("10"), Decimal("20"), Decimal("30")]
    assert has_enough_data(values) is True


def test_forecast_next_extrapolates_linear_trend():
    values = [Decimal(v) for v in (10, 20, 30, 40, 50, 60)]

    assert forecast_next(values, steps_ahead=1) == Decimal("70.00")
    assert forecast_next(values, steps_ahead=2) == Decimal("80.00")


def test_forecast_next_clips_negative_predictions_to_zero():
    values = [Decimal(v) for v in (100, 50, 0)]

    predicted = forecast_next(values, steps_ahead=1)

    assert predicted == Decimal("0.00")


def test_forecast_next_returns_flat_value_for_constant_series():
    values = [Decimal("25.00")] * 4

    assert forecast_next(values, steps_ahead=1) == Decimal("25.00")
