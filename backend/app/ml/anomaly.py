"""Unusual-spending detection via Tukey's fences.

Statistics, not machine learning: a transaction is "unusual" for a
category if its amount clears the classic IQR-based outlier threshold
(Q3 + 1.5 * IQR) computed from that user's own prior transactions in the
same category. This is a well-established, fully explainable test —
appropriate for flagging outliers without dressing up simple arithmetic
as AI.
"""

import statistics
from decimal import Decimal

MIN_HISTORY = 5
IQR_MULTIPLIER = 1.5


def detect_unusual_amount(amount: Decimal, historical_amounts: list[Decimal]) -> bool:
    """Whether `amount` is an outlier relative to `historical_amounts`.

    Requires at least MIN_HISTORY prior data points — below that there's
    no meaningful distribution to compare against, so nothing is flagged.
    """
    if len(historical_amounts) < MIN_HISTORY:
        return False

    values = sorted(float(v) for v in historical_amounts)
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1

    # A flat history (iqr == 0) has no spread to build a fence from; fall
    # back to flagging anything more than double the constant prior value.
    threshold = q3 + IQR_MULTIPLIER * iqr if iqr > 0 else q3 * 2

    return float(amount) > threshold
