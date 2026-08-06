"""Medicare IRMAA reference-data and tier calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from math import isfinite
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_TABLE = files("retirement_planner").joinpath("data/irmaa_2026.yml")
_SUPPORTED_STATUSES = {
    "single",
    "married_filing_jointly",
    "married_filing_separately_lived_with_spouse",
}


@dataclass(frozen=True)
class IrmaaProvenance:
    source_citation: str
    source_url: str
    source_revision_date: date
    retrieved_on: date
    verification_status: str


@dataclass(frozen=True)
class IrmaaTier:
    tier: int
    lower_bound: float | None
    lower_inclusive: bool
    upper_bound: float | None
    upper_inclusive: bool
    part_b_irmaa_monthly: float
    part_d_irmaa_monthly: float

    def matches(self, magi: float) -> bool:
        if self.lower_bound is not None:
            if self.lower_inclusive and magi < self.lower_bound:
                return False
            if not self.lower_inclusive and magi <= self.lower_bound:
                return False
        if self.upper_bound is not None:
            if self.upper_inclusive and magi > self.upper_bound:
                return False
            if not self.upper_inclusive and magi >= self.upper_bound:
                return False
        return True


@dataclass(frozen=True)
class IrmaaTable:
    premium_year: int
    ordinary_income_year: int
    fallback_income_year: int
    standard_part_b_monthly_premium: float
    provenance: IrmaaProvenance
    filing_status_tables: dict[str, tuple[IrmaaTier, ...]]


@dataclass(frozen=True)
class IrmaaResult:
    income_year: int
    premium_year: int
    lookback_years: int
    filing_status: str
    agi: float
    tax_exempt_interest: float
    irmaa_magi: float
    tier: int
    next_threshold: float | None
    distance_to_next_threshold: float | None
    standard_part_b_monthly_premium: float
    part_b_irmaa_monthly: float
    part_d_plan_monthly_premium: float
    part_d_irmaa_monthly: float
    beneficiary_count: int
    household_monthly_cost: float
    household_annual_cost: float


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _parse_date(value: Any, name: str) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD format") from exc


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not isfinite(result) or result < 0:
        raise ValueError(f"{name} must be a nonnegative finite number")
    return result


def load_irmaa_table(path: str | Path | None = None) -> IrmaaTable:
    source = Path(path) if path is not None else _DEFAULT_TABLE
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported IRMAA table schema")
    provenance_raw = payload.get("provenance")
    if not isinstance(provenance_raw, dict):
        raise ValueError("IRMAA provenance is required")
    status = _required_text(provenance_raw.get("verification_status"), "verification_status").lower()
    if status != "verified":
        raise ValueError("IRMAA reference data must be verified")
    provenance = IrmaaProvenance(
        source_citation=_required_text(provenance_raw.get("source_citation"), "source_citation"),
        source_url=_required_text(provenance_raw.get("source_url"), "source_url"),
        source_revision_date=_parse_date(provenance_raw.get("source_revision_date"), "source_revision_date"),
        retrieved_on=_parse_date(provenance_raw.get("retrieved_on"), "retrieved_on"),
        verification_status=status,
    )
    raw_tables = payload.get("filing_status_tables")
    if not isinstance(raw_tables, dict):
        raise ValueError("filing_status_tables is required")
    tables: dict[str, tuple[IrmaaTier, ...]] = {}
    for filing_status, raw_tiers in raw_tables.items():
        if filing_status not in _SUPPORTED_STATUSES or not isinstance(raw_tiers, list) or not raw_tiers:
            raise ValueError("invalid IRMAA filing-status table")
        tiers = tuple(
            IrmaaTier(
                tier=int(item["tier"]),
                lower_bound=None if item.get("lower_bound") is None else _number(item["lower_bound"], "lower_bound"),
                lower_inclusive=bool(item.get("lower_inclusive")),
                upper_bound=None if item.get("upper_bound") is None else _number(item["upper_bound"], "upper_bound"),
                upper_inclusive=bool(item.get("upper_inclusive")),
                part_b_irmaa_monthly=_number(item["part_b_irmaa_monthly"], "part_b_irmaa_monthly"),
                part_d_irmaa_monthly=_number(item["part_d_irmaa_monthly"], "part_d_irmaa_monthly"),
            )
            for item in raw_tiers
        )
        tables[filing_status] = tiers
    return IrmaaTable(
        premium_year=int(payload["premium_year"]),
        ordinary_income_year=int(payload["ordinary_income_year"]),
        fallback_income_year=int(payload["fallback_income_year"]),
        standard_part_b_monthly_premium=_number(payload["standard_part_b_monthly_premium"], "standard_part_b_monthly_premium"),
        provenance=provenance,
        filing_status_tables=tables,
    )


def calculate_irmaa_magi(agi: float, tax_exempt_interest: float) -> float:
    return _number(agi, "agi") + _number(tax_exempt_interest, "tax_exempt_interest")


def calculate_irmaa(
    *,
    income_year: int,
    filing_status: str,
    agi: float,
    tax_exempt_interest: float,
    beneficiary_count: int,
    part_d_plan_monthly_premium: float = 0.0,
    table: IrmaaTable | None = None,
) -> IrmaaResult:
    reference = table or load_irmaa_table()
    if income_year not in {reference.ordinary_income_year, reference.fallback_income_year}:
        raise ValueError("income_year is not supported by this premium-year table")
    if filing_status not in reference.filing_status_tables:
        raise ValueError("unsupported IRMAA filing status")
    if isinstance(beneficiary_count, bool) or beneficiary_count not in {0, 1, 2}:
        raise ValueError("beneficiary_count must be 0, 1, or 2")
    magi = calculate_irmaa_magi(agi, tax_exempt_interest)
    matches = [tier for tier in reference.filing_status_tables[filing_status] if tier.matches(magi)]
    if len(matches) != 1:
        raise ValueError("IRMAA MAGI must match exactly one tier")
    tier = matches[0]
    later = [item.lower_bound for item in reference.filing_status_tables[filing_status] if item.lower_bound is not None and item.lower_bound > magi]
    next_threshold = min(later) if later else None
    part_d_plan = _number(part_d_plan_monthly_premium, "part_d_plan_monthly_premium")
    per_beneficiary = reference.standard_part_b_monthly_premium + tier.part_b_irmaa_monthly + part_d_plan + tier.part_d_irmaa_monthly
    household_monthly = per_beneficiary * beneficiary_count
    return IrmaaResult(
        income_year=income_year,
        premium_year=reference.premium_year,
        lookback_years=reference.premium_year - income_year,
        filing_status=filing_status,
        agi=float(agi),
        tax_exempt_interest=float(tax_exempt_interest),
        irmaa_magi=magi,
        tier=tier.tier,
        next_threshold=next_threshold,
        distance_to_next_threshold=None if next_threshold is None else next_threshold - magi,
        standard_part_b_monthly_premium=reference.standard_part_b_monthly_premium,
        part_b_irmaa_monthly=tier.part_b_irmaa_monthly,
        part_d_plan_monthly_premium=part_d_plan,
        part_d_irmaa_monthly=tier.part_d_irmaa_monthly,
        beneficiary_count=beneficiary_count,
        household_monthly_cost=household_monthly,
        household_annual_cost=household_monthly * 12,
    )
