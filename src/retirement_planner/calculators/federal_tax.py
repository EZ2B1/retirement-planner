import math
from numbers import Real


def _validate_brackets(brackets: list[dict]) -> None:
    """Validate a progressive federal tax bracket schedule.

    A valid schedule contains one or more brackets, has strictly increasing
    finite upper bounds, and ends with exactly one open-ended bracket whose
    ``upper`` value is ``None``. Rates must be finite numeric values between
    0 and 1, inclusive.
    """
    if not brackets:
        raise ValueError("Federal tax bracket schedule must not be empty.")

    previous_upper = 0.0
    open_ended_count = 0

    for index, bracket in enumerate(brackets):
        if not isinstance(bracket, dict):
            raise ValueError(f"Bracket {index} must be a dictionary.")

        if "rate" not in bracket:
            raise ValueError(f"Bracket {index} is missing a rate.")

        rate = bracket["rate"]
        if (
            isinstance(rate, bool)
            or not isinstance(rate, Real)
            or not math.isfinite(rate)
            or rate < 0
            or rate > 1
        ):
            raise ValueError(
                f"Bracket {index} rate must be a finite numeric value from 0 through 1."
            )

        upper = bracket.get("upper")
        if upper is None:
            open_ended_count += 1
            if index != len(brackets) - 1:
                raise ValueError("The open-ended bracket must be the final bracket.")
            continue

        if (
            isinstance(upper, bool)
            or not isinstance(upper, Real)
            or not math.isfinite(upper)
        ):
            raise ValueError(f"Bracket {index} upper bound must be finite and numeric.")

        if upper <= previous_upper:
            raise ValueError("Finite bracket upper bounds must be strictly increasing.")

        previous_upper = float(upper)

    if open_ended_count != 1:
        raise ValueError("The schedule must end with exactly one open-ended bracket.")


def calculate_federal_tax(taxable_income: float, brackets: list[dict]) -> float:
    _validate_brackets(brackets)

    tax = 0.0
    previous = 0.0
    for bracket in brackets:
        upper = bracket.get("upper")
        rate = bracket["rate"]
        if upper is None:
            tax += max(0.0, taxable_income - previous) * rate
            break
        taxable = max(0.0, min(taxable_income, upper) - previous)
        tax += taxable * rate
        if taxable_income <= upper:
            break
        previous = upper
    return round(tax, 2)
