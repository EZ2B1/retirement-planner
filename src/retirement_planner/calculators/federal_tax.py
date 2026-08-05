"""Federal income tax calculation helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from numbers import Real


def _coerce_finite_number(value: object, field_name: str) -> float:
    """Return a finite real number or raise a clear configuration error."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")

    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")

    return number


def _validate_brackets(brackets: Sequence[Mapping[str, object]]) -> None:
    """Validate a progressive tax-bracket schedule before calculation."""

    if not brackets:
        raise ValueError("At least one tax bracket is required")

    previous_upper = 0.0
    for index, bracket in enumerate(brackets):
        bracket_number = index + 1
        if not isinstance(bracket, Mapping):
            raise TypeError(f"Bracket {bracket_number} must be a mapping")
        if "rate" not in bracket:
            raise ValueError(f"Bracket {bracket_number} is missing rate")

        rate = _coerce_finite_number(
            bracket["rate"], f"Bracket {bracket_number} rate"
        )
        if not 0.0 <= rate <= 1.0:
            raise ValueError(
                f"Bracket {bracket_number} rate must be between 0 and 1"
            )

        upper = bracket.get("upper")
        if upper is None:
            if index != len(brackets) - 1:
                raise ValueError("The open-ended tax bracket must be last")
            continue

        upper_value = _coerce_finite_number(
            upper, f"Bracket {bracket_number} upper bound"
        )
        if upper_value <= previous_upper:
            raise ValueError("Tax bracket upper bounds must increase strictly")
        previous_upper = upper_value

    if brackets[-1].get("upper") is not None:
        raise ValueError("The final tax bracket must be open-ended")


def calculate_federal_tax(
    taxable_income: float,
    brackets: Sequence[Mapping[str, object]],
) -> float:
    """Calculate progressive federal tax from a validated bracket schedule.

    Negative taxable income is treated as zero. Malformed schedules are rejected
    instead of silently leaving income untaxed or applying brackets out of order.
    """

    income = _coerce_finite_number(taxable_income, "Taxable income")
    _validate_brackets(brackets)

    if income <= 0.0:
        return 0.0

    tax = 0.0
    previous_upper = 0.0

    for bracket in brackets:
        upper = bracket.get("upper")
        rate = float(bracket["rate"])

        if upper is None:
            tax += (income - previous_upper) * rate
            break

        upper_value = float(upper)
        taxable_at_rate = min(income, upper_value) - previous_upper
        tax += taxable_at_rate * rate

        if income <= upper_value:
            break
        previous_upper = upper_value

    return round(tax, 2)
