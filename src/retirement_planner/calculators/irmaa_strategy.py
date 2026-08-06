"""IRMAA diagnostics, survivor transitions, and optimizer guardrails."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from retirement_planner.calculators.irmaa import IrmaaResult, IrmaaTable, calculate_irmaa


@dataclass(frozen=True)
class IrmaaIncomeSource:
    """One named component of IRMAA MAGI."""

    name: str
    amount: float
    category: str = "agi"


@dataclass(frozen=True)
class IrmaaSourceImpact:
    """Marginal premium effect of including one income source."""

    name: str
    amount: float
    category: str
    tier_without_source: int
    tier_with_source: int
    incremental_annual_cost: float


@dataclass(frozen=True)
class IrmaaIncomeDiagnostic:
    """Reconciled source-level IRMAA analysis."""

    result: IrmaaResult
    agi_total: float
    tax_exempt_interest_total: float
    source_impacts: tuple[IrmaaSourceImpact, ...]


@dataclass(frozen=True)
class IrmaaSurvivorTransition:
    """Before-and-after comparison for a survivor filing-status transition."""

    joint_result: IrmaaResult
    survivor_result: IrmaaResult
    annual_cost_change: float
    tier_change: int


@dataclass(frozen=True)
class IrmaaStrategyDecision:
    """Optimizer decision for proposed income that may cross an IRMAA threshold."""

    baseline: IrmaaResult
    proposed: IrmaaResult
    added_agi: float
    added_tax_exempt_interest: float
    crossed_threshold: bool
    incremental_annual_cost: float
    allowed: bool
    rationale: str | None
    warning: str | None


def _validate_sources(sources: Iterable[IrmaaIncomeSource]) -> tuple[IrmaaIncomeSource, ...]:
    items = tuple(sources)
    names: set[str] = set()
    for item in items:
        if not item.name.strip():
            raise ValueError("IRMAA income-source name is required")
        if item.name in names:
            raise ValueError(f"duplicate IRMAA income-source name: {item.name}")
        names.add(item.name)
        if item.category not in {"agi", "tax_exempt_interest"}:
            raise ValueError("IRMAA income-source category must be 'agi' or 'tax_exempt_interest'")
        if item.amount < 0:
            raise ValueError("IRMAA income-source amount must be nonnegative")
    return items


def analyze_irmaa_income_sources(
    *,
    income_year: int,
    filing_status: str,
    beneficiary_count: int,
    sources: Iterable[IrmaaIncomeSource],
    part_d_plan_monthly_premium: float = 0.0,
    table: IrmaaTable | None = None,
) -> IrmaaIncomeDiagnostic:
    """Calculate IRMAA and attribute marginal annual premium effects to sources."""

    items = _validate_sources(sources)
    agi_total = sum(item.amount for item in items if item.category == "agi")
    tax_exempt_total = sum(
        item.amount for item in items if item.category == "tax_exempt_interest"
    )
    full_result = calculate_irmaa(
        income_year=income_year,
        filing_status=filing_status,
        agi=agi_total,
        tax_exempt_interest=tax_exempt_total,
        beneficiary_count=beneficiary_count,
        part_d_plan_monthly_premium=part_d_plan_monthly_premium,
        table=table,
    )

    impacts: list[IrmaaSourceImpact] = []
    for source in items:
        without_agi = agi_total - source.amount if source.category == "agi" else agi_total
        without_tax_exempt = (
            tax_exempt_total - source.amount
            if source.category == "tax_exempt_interest"
            else tax_exempt_total
        )
        without_result = calculate_irmaa(
            income_year=income_year,
            filing_status=filing_status,
            agi=without_agi,
            tax_exempt_interest=without_tax_exempt,
            beneficiary_count=beneficiary_count,
            part_d_plan_monthly_premium=part_d_plan_monthly_premium,
            table=table,
        )
        impacts.append(
            IrmaaSourceImpact(
                name=source.name,
                amount=source.amount,
                category=source.category,
                tier_without_source=without_result.tier,
                tier_with_source=full_result.tier,
                incremental_annual_cost=(
                    full_result.household_annual_cost
                    - without_result.household_annual_cost
                ),
            )
        )

    return IrmaaIncomeDiagnostic(
        result=full_result,
        agi_total=agi_total,
        tax_exempt_interest_total=tax_exempt_total,
        source_impacts=tuple(impacts),
    )


def compare_survivor_irmaa(
    *,
    income_year: int,
    agi: float,
    tax_exempt_interest: float,
    joint_part_d_plan_monthly_premium: float = 0.0,
    survivor_part_d_plan_monthly_premium: float = 0.0,
    table: IrmaaTable | None = None,
) -> IrmaaSurvivorTransition:
    """Compare the same modeled income under joint and survivor/single treatment."""

    joint = calculate_irmaa(
        income_year=income_year,
        filing_status="married_filing_jointly",
        agi=agi,
        tax_exempt_interest=tax_exempt_interest,
        beneficiary_count=2,
        part_d_plan_monthly_premium=joint_part_d_plan_monthly_premium,
        table=table,
    )
    survivor = calculate_irmaa(
        income_year=income_year,
        filing_status="single",
        agi=agi,
        tax_exempt_interest=tax_exempt_interest,
        beneficiary_count=1,
        part_d_plan_monthly_premium=survivor_part_d_plan_monthly_premium,
        table=table,
    )
    return IrmaaSurvivorTransition(
        joint_result=joint,
        survivor_result=survivor,
        annual_cost_change=survivor.household_annual_cost - joint.household_annual_cost,
        tier_change=survivor.tier - joint.tier,
    )


def evaluate_irmaa_strategy(
    *,
    income_year: int,
    filing_status: str,
    beneficiary_count: int,
    baseline_agi: float,
    baseline_tax_exempt_interest: float,
    added_agi: float = 0.0,
    added_tax_exempt_interest: float = 0.0,
    part_d_plan_monthly_premium: float = 0.0,
    allow_deliberate_crossing: bool = False,
    rationale: str | None = None,
    table: IrmaaTable | None = None,
) -> IrmaaStrategyDecision:
    """Block silent IRMAA threshold crossings and price deliberate crossings."""

    baseline = calculate_irmaa(
        income_year=income_year,
        filing_status=filing_status,
        agi=baseline_agi,
        tax_exempt_interest=baseline_tax_exempt_interest,
        beneficiary_count=beneficiary_count,
        part_d_plan_monthly_premium=part_d_plan_monthly_premium,
        table=table,
    )
    proposed = calculate_irmaa(
        income_year=income_year,
        filing_status=filing_status,
        agi=baseline_agi + added_agi,
        tax_exempt_interest=baseline_tax_exempt_interest + added_tax_exempt_interest,
        beneficiary_count=beneficiary_count,
        part_d_plan_monthly_premium=part_d_plan_monthly_premium,
        table=table,
    )
    crossed = proposed.tier > baseline.tier
    clean_rationale = rationale.strip() if isinstance(rationale, str) and rationale.strip() else None
    allowed = not crossed or (allow_deliberate_crossing and clean_rationale is not None)
    warning = None
    if crossed and not allowed:
        warning = "Proposed strategy crosses an IRMAA threshold without explicit approval and rationale."
    elif crossed:
        warning = "Deliberate IRMAA threshold crossing approved; review the incremental Medicare cost."

    return IrmaaStrategyDecision(
        baseline=baseline,
        proposed=proposed,
        added_agi=added_agi,
        added_tax_exempt_interest=added_tax_exempt_interest,
        crossed_threshold=crossed,
        incremental_annual_cost=(
            proposed.household_annual_cost - baseline.household_annual_cost
        ),
        allowed=allowed,
        rationale=clean_rationale,
        warning=warning,
    )
