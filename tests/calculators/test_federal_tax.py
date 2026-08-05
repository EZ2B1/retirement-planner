import math

import pytest

from retirement_planner.calculators.federal_tax import calculate_federal_tax


VALID_BRACKETS = [
    {"upper": 10_000, "rate": 0.10},
    {"upper": 40_000, "rate": 0.20},
    {"upper": None, "rate": 0.30},
]


def test_progressive_tax() -> None:
    assert calculate_federal_tax(50_000, VALID_BRACKETS) == 10_000.00


@pytest.mark.parametrize(
    ("taxable_income", "expected_tax"),
    [
        (-1_000, 0.00),
        (0, 0.00),
        (10_000, 1_000.00),
        (40_000, 7_000.00),
    ],
)
def test_income_boundaries(taxable_income: float, expected_tax: float) -> None:
    assert calculate_federal_tax(taxable_income, VALID_BRACKETS) == expected_tax


def test_rejects_empty_bracket_schedule() -> None:
    with pytest.raises(ValueError, match="At least one tax bracket"):
        calculate_federal_tax(50_000, [])


def test_rejects_schedule_without_open_ended_bracket() -> None:
    brackets = [
        {"upper": 10_000, "rate": 0.10},
        {"upper": 40_000, "rate": 0.20},
    ]

    with pytest.raises(ValueError, match="final tax bracket must be open-ended"):
        calculate_federal_tax(50_000, brackets)


def test_rejects_open_ended_bracket_before_final_position() -> None:
    brackets = [
        {"upper": None, "rate": 0.10},
        {"upper": 40_000, "rate": 0.20},
    ]

    with pytest.raises(ValueError, match="open-ended tax bracket must be last"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize(
    "brackets",
    [
        [
            {"upper": 40_000, "rate": 0.10},
            {"upper": 10_000, "rate": 0.20},
            {"upper": None, "rate": 0.30},
        ],
        [
            {"upper": 10_000, "rate": 0.10},
            {"upper": 10_000, "rate": 0.20},
            {"upper": None, "rate": 0.30},
        ],
    ],
)
def test_rejects_non_increasing_thresholds(brackets: list[dict]) -> None:
    with pytest.raises(ValueError, match="upper bounds must increase strictly"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize("rate", [-0.01, 1.01])
def test_rejects_rate_outside_zero_to_one(rate: float) -> None:
    brackets = [
        {"upper": 10_000, "rate": rate},
        {"upper": None, "rate": 0.20},
    ]

    with pytest.raises(ValueError, match="rate must be between 0 and 1"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize("rate", ["0.10", True])
def test_rejects_nonnumeric_rate(rate: object) -> None:
    brackets = [
        {"upper": 10_000, "rate": rate},
        {"upper": None, "rate": 0.20},
    ]

    with pytest.raises(TypeError, match="rate must be a real number"):
        calculate_federal_tax(50_000, brackets)


def test_rejects_nonfinite_values() -> None:
    brackets = [
        {"upper": math.inf, "rate": 0.10},
        {"upper": None, "rate": 0.20},
    ]

    with pytest.raises(ValueError, match="upper bound must be finite"):
        calculate_federal_tax(50_000, brackets)

    with pytest.raises(ValueError, match="Taxable income must be finite"):
        calculate_federal_tax(math.nan, VALID_BRACKETS)
