from datetime import date

import pytest

from retirement_planner.calculators.rmd import (
    ApplicableAgeRule,
    ApplicableAgeRuleSet,
    determine_applicable_rmd_age,
    load_applicable_age_rule_sets,
)


@pytest.mark.parametrize(
    ("date_of_birth", "expected_age"),
    [
        (date(1949, 6, 30), 70.5),
        (date(1949, 7, 1), 72.0),
        (date(1950, 12, 31), 72.0),
        (date(1951, 1, 1), 73.0),
        (date(1959, 12, 31), 73.0),
        (date(1960, 1, 1), 75.0),
    ],
)
def test_secure_2_boundary_birth_dates(date_of_birth, expected_age):
    assert determine_applicable_rmd_age(date_of_birth, 2026) == expected_age


def test_source_year_selects_historical_rule_set():
    date_of_birth = date(1960, 1, 1)

    assert determine_applicable_rmd_age(date_of_birth, 2019) == 70.5
    assert determine_applicable_rmd_age(date_of_birth, 2020) == 72.0
    assert determine_applicable_rmd_age(date_of_birth, 2022) == 72.0
    assert determine_applicable_rmd_age(date_of_birth, 2023) == 75.0


def test_source_year_before_first_rule_set_is_rejected():
    with pytest.raises(ValueError, match="no RMD applicable-age rules"):
        determine_applicable_rmd_age(date(1960, 1, 1), 2018)


@pytest.mark.parametrize("source_year", [True, 2026.0, "2026", None])
def test_invalid_source_year_is_rejected(source_year):
    with pytest.raises(TypeError, match="source_year must be an integer"):
        determine_applicable_rmd_age(date(1960, 1, 1), source_year)


def test_invalid_date_of_birth_is_rejected():
    with pytest.raises(TypeError, match="date_of_birth must be a datetime.date"):
        determine_applicable_rmd_age("1960-01-01", 2026)


def test_default_rule_table_loads_in_effective_year_order():
    rule_sets = load_applicable_age_rule_sets()

    assert [rule_set.effective_year for rule_set in rule_sets] == [2019, 2020, 2023]


def test_overlapping_or_gapped_rules_cannot_produce_a_result():
    malformed = (
        ApplicableAgeRuleSet(
            effective_year=2023,
            rules=(
                ApplicableAgeRule(None, date(1950, 12, 31), 72.0),
                ApplicableAgeRule(date(1950, 12, 31), None, 73.0),
            ),
        ),
    )

    with pytest.raises(ValueError, match="exactly one"):
        determine_applicable_rmd_age(date(1950, 12, 31), 2026, malformed)


def test_custom_rule_sets_preserve_valid_result():
    custom = (
        ApplicableAgeRuleSet(
            effective_year=2023,
            rules=(ApplicableAgeRule(None, None, 73.0),),
        ),
    )

    assert determine_applicable_rmd_age(date(1955, 5, 5), 2026, custom) == 73.0
