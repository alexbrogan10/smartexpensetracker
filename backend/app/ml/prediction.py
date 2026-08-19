"""Trend-based spending forecasting.

Fits a simple linear regression over a user's own trailing monthly totals
and extrapolates one or more months ahead. Like app/ml/categorization.py,
nothing is persisted: the datasets involved (at most a couple dozen months)
make retraining on every request trivial, so there's no model to keep in
sync with new transactions.
"""

from decimal import Decimal

from sklearn.linear_model import LinearRegression

MIN_DATA_POINTS = 3


def has_enough_data(values: list[Decimal]) -> bool:
    """At least MIN_DATA_POINTS months must show real activity.

    A window padded mostly with zero months (e.g. a brand new account)
    isn't a trend — it's an absence of data.
    """
    return sum(1 for v in values if v > 0) >= MIN_DATA_POINTS


def forecast_next(values: list[Decimal], steps_ahead: int = 1) -> Decimal:
    """Extrapolate `steps_ahead` points past the end of `values`.

    `values` is oldest-to-newest with one entry per consecutive month.
    Callers should check `has_enough_data` first — this always fits and
    predicts, without judging whether the result is meaningful.
    """
    x = [[i] for i in range(len(values))]
    y = [float(v) for v in values]

    model = LinearRegression().fit(x, y)
    future_index = len(values) - 1 + steps_ahead
    predicted = model.predict([[future_index]])[0]

    return Decimal(str(round(max(predicted, 0.0), 2)))
