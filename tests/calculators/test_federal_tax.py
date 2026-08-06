import math

import pytest

from retirement_planner.calculators.federal_tax import calculate_federal_tax


VALID_BRACKETS = [
    {"upper": 10_000, "rate": 0.10},
    {"upper": 40_000, "rate": 0.20},
    {"upper": None, "rate": 0.30},
]


def test_progressive_tax_preserves_existing_result():
    assert calculate_federal_tax(50_000, VALID_BRACKETS) == 10_000.00


@pytest.mark.parametrize(
    ("taxable_income", "expected"),
    [
        (0, 0.00),
        (10_000, 1_000.00),
        (40_000, 7_000.00),
        (40_001, 7_000.30),
        (-1, 0.00),
    ],
)
def test_tax_bracket_boundaries(taxable_income, expected):
    assert calculate_federal_tax(taxable_income, VALID_BRACKETS) == expected


def test_rejects_empty_schedule():
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_federal_tax(50_000, [])


@pytest.mark.parametrize(
    "brackets",
    [
        [{"upper": 10_000, "rate": 0.10}],
        [
            {"upper": None, "rate": 0.10},
            {"upper": 40_000, "rate": 0.20},
        ],
        [
            {"upper": 10_000, "rate": 0.10},
            {"upper": None, "rate": 0.20},
            {"upper": None, "rate": 0.30},
        ],
    ],
)
def test_rejects_missing_nonfinal_or_multiple_open_ended_brackets(brackets):
    with pytest.raises(ValueError, match="open-ended bracket"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize(
    "brackets",
    [
        [
            {"upper": 10_000, "rate": 0.10},
            {"upper": 10_000, "rate": 0.20},
            {"upper": None, "rate": 0.30},
        ],
        [
            {"upper": 40_000, "rate": 0.10},
            {"upper": 10_000, "rate": 0.20},
            {"upper": None, "rate": 0.30},
        ],
        [
            {"upper": 0, "rate": 0.10},
            {"upper": None, "rate": 0.30},
        ],
    ],
)
def test_rejects_non_increasing_finite_thresholds(brackets):
    with pytest.raises(ValueError, match="strictly increasing"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize(
    "invalid_rate",
    ["0.10", None, True, math.nan, math.inf, -0.01, 1.01],
)
def test_rejects_invalid_rates(invalid_rate):
    brackets = [
        {"upper": 10_000, "rate": invalid_rate},
        {"upper": None, "rate": 0.30},
    ]

    with pytest.raises(ValueError, match="rate must be a finite numeric value"):
        calculate_federal_tax(50_000, brackets)


@pytest.mark.parametrize("valid_rate", [0, 1, 0.25])
def test_accepts_rate_boundaries(valid_rate):
    brackets = [{"upper": None, "rate": valid_rate}]
    assert calculate_federal_tax(100, brackets) == round(100 * valid_rate, 2)


@pytest.mark.parametrize("invalid_upper", ["10000", True, math.nan, math.inf])
def test_rejects_nonfinite_or_nonnumeric_finite_thresholds(invalid_upper):
    brackets = [
        {"upper": invalid_upper, "rate": 0.10},
        {"upper": None, "rate": 0.30},
    ]

    with pytest.raises(ValueError, match="upper bound must be finite and numeric"):
        calculate_federal_tax(50_000, brackets)
