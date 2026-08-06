"""Required Minimum Distribution calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from math import isfinite
from pathlib import Path
from typing import Any, Iterable

import yaml

_DEFAULT_RULE_TABLE = files("retirement_planner").joinpath("data/rmd_applicable_age.yml")


@dataclass(frozen=True)
class ApplicableAgeRule:
    """One date-of-birth range and its applicable RMD age."""

    born_on_or_after: date | None
    born_on_or_before: date | None
    applicable_age: float

    def matches(self, date_of_birth: date) -> bool:
        if self.born_on_or_after is not None and date_of_birth < self.born_on_or_after:
            return False
        if self.born_on_or_before is not None and date_of_birth > self.born_on_or_before:
            return False
        return True


@dataclass(frozen=True)
class ApplicableAgeRuleSet:
    """RMD applicable-age rules effective for a source year."""

    effective_year: int
    rules: tuple[ApplicableAgeRule, ...]


def _parse_date(value: Any, field_name: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an ISO date string or null")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc


def _parse_age(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("applicable_age must be numeric")
    age = float(value)
    if not isfinite(age) or age <= 0:
        raise ValueError("applicable_age must be a positive finite number")
    return age


def _validate_rules(rules: Iterable[ApplicableAgeRule]) -> tuple[ApplicableAgeRule, ...]:
    validated = tuple(rules)
    if not validated:
        raise ValueError("each RMD applicable-age rule set must contain at least one rule")

    previous_end: date | None = None
    for index, rule in enumerate(validated):
        start = rule.born_on_or_after
        end = rule.born_on_or_before

        if start is not None and end is not None and start > end:
            raise ValueError("born_on_or_after cannot be later than born_on_or_before")

        if index == 0 and start is not None:
            raise ValueError("the first rule must be open-ended for earlier birth dates")

        if index > 0:
            if start is None:
                raise ValueError("only the first rule may omit born_on_or_after")
            if previous_end is None:
                raise ValueError("an open-ended rule must be last")
            if start.toordinal() != previous_end.toordinal() + 1:
                raise ValueError("birth-date rules must be contiguous and non-overlapping")

        previous_end = end

    if validated[-1].born_on_or_before is not None:
        raise ValueError("the final rule must be open-ended for later birth dates")

    return validated


def load_applicable_age_rule_sets(
    path: str | Path | None = None,
) -> tuple[ApplicableAgeRuleSet, ...]:
    """Load and validate version-controlled RMD applicable-age rules."""

    source = Path(path) if path is not None else _DEFAULT_RULE_TABLE
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    if not isinstance(payload, dict):
        raise ValueError("RMD applicable-age rule table must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported RMD applicable-age rule-table schema version")

    raw_rule_sets = payload.get("rule_sets")
    if not isinstance(raw_rule_sets, list) or not raw_rule_sets:
        raise ValueError("RMD applicable-age rule table must contain rule_sets")

    parsed: list[ApplicableAgeRuleSet] = []
    previous_effective_year: int | None = None

    for raw_rule_set in raw_rule_sets:
        if not isinstance(raw_rule_set, dict):
            raise ValueError("each rule set must be a mapping")

        effective_year = raw_rule_set.get("effective_year")
        if isinstance(effective_year, bool) or not isinstance(effective_year, int):
            raise ValueError("effective_year must be an integer")
        if previous_effective_year is not None and effective_year <= previous_effective_year:
            raise ValueError("rule-set effective years must increase strictly")

        raw_rules = raw_rule_set.get("rules")
        if not isinstance(raw_rules, list):
            raise ValueError("rules must be a list")

        rules = _validate_rules(
            ApplicableAgeRule(
                born_on_or_after=_parse_date(
                    raw_rule.get("born_on_or_after"), "born_on_or_after"
                ),
                born_on_or_before=_parse_date(
                    raw_rule.get("born_on_or_before"), "born_on_or_before"
                ),
                applicable_age=_parse_age(raw_rule.get("applicable_age")),
            )
            for raw_rule in raw_rules
            if isinstance(raw_rule, dict)
        )
        if len(rules) != len(raw_rules):
            raise ValueError("each rule must be a mapping")

        parsed.append(ApplicableAgeRuleSet(effective_year=effective_year, rules=rules))
        previous_effective_year = effective_year

    return tuple(parsed)


def determine_applicable_rmd_age(
    date_of_birth: date,
    source_year: int,
    rule_sets: Iterable[ApplicableAgeRuleSet] | None = None,
) -> float:
    """Return the applicable RMD age for a birth date and source year.

    ``source_year`` selects the latest rule set whose effective year is not
    later than the requested source year. This prevents a universal hard-coded
    RMD age from leaking into calculations and supports historical rule sets.
    """

    if not isinstance(date_of_birth, date):
        raise TypeError("date_of_birth must be a datetime.date")
    if isinstance(source_year, bool) or not isinstance(source_year, int):
        raise TypeError("source_year must be an integer")

    available = tuple(rule_sets) if rule_sets is not None else load_applicable_age_rule_sets()
    selected = [rule_set for rule_set in available if rule_set.effective_year <= source_year]
    if not selected:
        raise ValueError(f"no RMD applicable-age rules are available for source year {source_year}")

    rule_set = max(selected, key=lambda item: item.effective_year)
    matches = [rule for rule in rule_set.rules if rule.matches(date_of_birth)]
    if len(matches) != 1:
        raise ValueError("birth date must match exactly one applicable-age rule")

    return matches[0].applicable_age
