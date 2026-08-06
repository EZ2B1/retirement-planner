from datetime import date

import pytest
import yaml

from retirement_planner.calculators.rmd import (
    ApplicableAgeRule,
    ApplicableAgeRuleSet,
    RuleTableProvenance,
    determine_applicable_rmd_age,
    load_applicable_age_rule_sets,
)


def _verified_provenance(**overrides):
    values = {
        "source_citation": "Treasury Decision 10001, 89 FR 58886",
        "source_url": "https://www.irs.gov/irb/2024-33_IRB",
        "source_revision_date": date(2024, 7, 19),
        "verification_status": "verified",
        "verified_on": date(2026, 8, 6),
    }
    values.update(overrides)
    return RuleTableProvenance(**values)


def _write_rule_table(tmp_path, *, provenance=None):
    payload = {
        "schema_version": 1,
        "rule_sets": [
            {
                "effective_year": 2023,
                "provenance": provenance
                if provenance is not None
                else {
                    "source_citation": "Treasury Decision 10001, 89 FR 58886",
                    "source_url": "https://www.irs.gov/irb/2024-33_IRB",
                    "source_revision_date": "2024-07-19",
                    "verification_status": "verified",
                    "verified_on": "2026-08-06",
                },
                "rules": [
                    {
                        "born_on_or_after": None,
                        "born_on_or_before": None,
                        "applicable_age": 73,
                    }
                ],
            }
        ],
    }
    path = tmp_path / "rmd_rules.yml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


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


def test_default_rule_table_loads_with_verified_provenance():
    rule_sets = load_applicable_age_rule_sets()

    assert [rule_set.effective_year for rule_set in rule_sets] == [2019, 2020, 2023]
    assert all(rule_set.provenance.verification_status == "verified" for rule_set in rule_sets)
    assert all(rule_set.provenance.source_citation for rule_set in rule_sets)
    assert all(rule_set.provenance.source_revision_date for rule_set in rule_sets)


def test_overlapping_or_gapped_rules_cannot_produce_a_result():
    malformed = (
        ApplicableAgeRuleSet(
            effective_year=2023,
            provenance=_verified_provenance(),
            rules=(
                ApplicableAgeRule(None, date(1950, 12, 31), 72.0),
                ApplicableAgeRule(date(1950, 12, 31), None, 73.0),
            ),
        ),
    )

    with pytest.raises(ValueError, match="contiguous and non-overlapping"):
        determine_applicable_rmd_age(date(1950, 12, 31), 2026, malformed)


def test_custom_rule_sets_preserve_valid_result():
    custom = (
        ApplicableAgeRuleSet(
            effective_year=2023,
            provenance=_verified_provenance(),
            rules=(ApplicableAgeRule(None, None, 73.0),),
        ),
    )

    assert determine_applicable_rmd_age(date(1955, 5, 5), 2026, custom) == 73.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_citation", "", "source_citation"),
        ("source_url", "", "source_url"),
        ("source_revision_date", None, "source_revision_date"),
        ("verification_status", None, "verification_status"),
        ("verified_on", None, "verified_on"),
    ],
)
def test_missing_provenance_fields_are_rejected(tmp_path, field, value, message):
    provenance = {
        "source_citation": "Treasury Decision 10001, 89 FR 58886",
        "source_url": "https://www.irs.gov/irb/2024-33_IRB",
        "source_revision_date": "2024-07-19",
        "verification_status": "verified",
        "verified_on": "2026-08-06",
    }
    provenance[field] = value

    with pytest.raises(ValueError, match=message):
        load_applicable_age_rule_sets(_write_rule_table(tmp_path, provenance=provenance))


@pytest.mark.parametrize("status", ["pending", "draft", "rejected", "VERIFIED-PENDING"])
def test_unverified_rule_tables_are_rejected(tmp_path, status):
    provenance = {
        "source_citation": "Treasury Decision 10001, 89 FR 58886",
        "source_url": "https://www.irs.gov/irb/2024-33_IRB",
        "source_revision_date": "2024-07-19",
        "verification_status": status,
        "verified_on": "2026-08-06",
    }

    with pytest.raises(ValueError, match="must be 'verified'"):
        load_applicable_age_rule_sets(_write_rule_table(tmp_path, provenance=provenance))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_revision_date", "07/19/2024"),
        ("verified_on", "August 6, 2026"),
    ],
)
def test_provenance_dates_require_iso_format(tmp_path, field, value):
    provenance = {
        "source_citation": "Treasury Decision 10001, 89 FR 58886",
        "source_url": "https://www.irs.gov/irb/2024-33_IRB",
        "source_revision_date": "2024-07-19",
        "verification_status": "verified",
        "verified_on": "2026-08-06",
    }
    provenance[field] = value

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        load_applicable_age_rule_sets(_write_rule_table(tmp_path, provenance=provenance))


def test_source_url_must_be_absolute(tmp_path):
    provenance = {
        "source_citation": "Treasury Decision 10001, 89 FR 58886",
        "source_url": "irs.gov/irb/2024-33_IRB",
        "source_revision_date": "2024-07-19",
        "verification_status": "verified",
        "verified_on": "2026-08-06",
    }

    with pytest.raises(ValueError, match="absolute HTTP or HTTPS URL"):
        load_applicable_age_rule_sets(_write_rule_table(tmp_path, provenance=provenance))
