"""Account-level RMD and QCD compliance calculations.

This module implements the core controls described by RMD-02 through RMD-06.
It is deliberately independent of workbook rendering so the calculation rules can
be tested before they are connected to projections, optimizers, and reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Iterable

IRA_ACCOUNT_TYPES = frozenset({"traditional_ira", "sep_ira", "simple_ira"})
QCD_ELIGIBLE_ACCOUNT_TYPES = IRA_ACCOUNT_TYPES
AGGREGATABLE_403B_TYPES = frozenset({"403b"})
SUPPORTED_ACCOUNT_TYPES = IRA_ACCOUNT_TYPES | AGGREGATABLE_403B_TYPES | frozenset(
    {"401k", "457b", "profit_sharing", "other_employer_plan"}
)


@dataclass(frozen=True)
class RmdDueItem:
    """One RMD year's statutory payment deadline."""

    rmd_year: int
    due_date: date


@dataclass(frozen=True)
class FirstRmdTimingResult:
    """First-RMD timing comparison and double-RMD warning."""

    first_rmd_year: int
    deferred_to_april_1: bool
    due_items: tuple[RmdDueItem, ...]
    double_rmd_calendar_year: int | None
    warning: str | None


@dataclass(frozen=True)
class RmdAccountInput:
    """Annual activity and required inputs for one retirement account."""

    account_id: str
    owner_id: str
    account_type: str
    prior_year_end_balance: float
    divisor: float
    life_expectancy_table: str
    distributions_taken: float = 0.0
    qcd_requested: float = 0.0
    qcd_direct_transfer: bool = False
    owner_date_of_birth: date | None = None
    qcd_distribution_date: date | None = None
    rollover_or_conversion_amount: float = 0.0


@dataclass(frozen=True)
class RmdAccountResult:
    """Complete annual calculation and compliance trail for one account."""

    account_id: str
    owner_id: str
    account_type: str
    aggregation_group: str
    prior_year_end_balance: float
    life_expectancy_table: str
    divisor: float
    calculated_rmd: float
    qcd_requested: float
    qualified_qcd: float
    qcd_applied_to_rmd: float
    distributions_taken: float
    account_remaining_rmd: float
    rollover_or_conversion_amount: float
    ineligible_rollover_or_conversion: float
    violations: tuple[str, ...]


@dataclass(frozen=True)
class RmdGroupResult:
    """Compliance result for one legally permitted aggregation group."""

    owner_id: str
    aggregation_group: str
    account_ids: tuple[str, ...]
    calculated_rmd: float
    qualifying_distributions: float
    remaining_shortfall: float
    compliant: bool


@dataclass(frozen=True)
class RmdComplianceResult:
    """Account, aggregation-group, owner, and household reconciliation."""

    account_results: tuple[RmdAccountResult, ...]
    group_results: tuple[RmdGroupResult, ...]
    total_calculated_rmd: float
    total_qualified_qcd: float
    total_distributions_taken: float
    total_remaining_shortfall: float
    compliant: bool


def build_first_rmd_timing(first_rmd_year: int, defer_to_april_1: bool) -> FirstRmdTimingResult:
    """Return first- and second-year deadlines and identify a double-RMD year."""

    if isinstance(first_rmd_year, bool) or not isinstance(first_rmd_year, int):
        raise TypeError("first_rmd_year must be an integer")
    if first_rmd_year < 1900:
        raise ValueError("first_rmd_year is outside the supported range")

    first_due = (
        date(first_rmd_year + 1, 4, 1)
        if defer_to_april_1
        else date(first_rmd_year, 12, 31)
    )
    second_due = date(first_rmd_year + 1, 12, 31)
    double_year = first_rmd_year + 1 if defer_to_april_1 else None
    warning = (
        f"Deferral creates two RMD deadlines in calendar year {double_year}."
        if double_year is not None
        else None
    )
    return FirstRmdTimingResult(
        first_rmd_year=first_rmd_year,
        deferred_to_april_1=defer_to_april_1,
        due_items=(
            RmdDueItem(rmd_year=first_rmd_year, due_date=first_due),
            RmdDueItem(rmd_year=first_rmd_year + 1, due_date=second_due),
        ),
        double_rmd_calendar_year=double_year,
        warning=warning,
    )


def _nonnegative_number(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError(f"{field_name} must be a nonnegative finite number")
    return number


def _positive_number(value: float, field_name: str) -> float:
    number = _nonnegative_number(value, field_name)
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return number


def _qcd_eligibility_date(date_of_birth: date) -> date:
    """Return the date on which an owner reaches age 70 1/2."""

    try:
        age_70 = date(date_of_birth.year + 70, date_of_birth.month, date_of_birth.day)
    except ValueError:
        age_70 = date(date_of_birth.year + 70, 2, 28)

    month_index = age_70.month - 1 + 6
    year = age_70.year + month_index // 12
    month = month_index % 12 + 1
    day = age_70.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1


def _aggregation_group(account: RmdAccountInput) -> str:
    if account.account_type in IRA_ACCOUNT_TYPES:
        return f"{account.owner_id}:ira"
    if account.account_type in AGGREGATABLE_403B_TYPES:
        return f"{account.owner_id}:403b"
    return f"{account.owner_id}:{account.account_id}"


def _validate_account(account: RmdAccountInput) -> None:
    if not account.account_id.strip():
        raise ValueError("account_id is required")
    if not account.owner_id.strip():
        raise ValueError("owner_id is required")
    if account.account_type not in SUPPORTED_ACCOUNT_TYPES:
        raise ValueError(f"unsupported account_type: {account.account_type}")
    if not account.life_expectancy_table.strip():
        raise ValueError("life_expectancy_table is required")
    _nonnegative_number(account.prior_year_end_balance, "prior_year_end_balance")
    _positive_number(account.divisor, "divisor")
    _nonnegative_number(account.distributions_taken, "distributions_taken")
    _nonnegative_number(account.qcd_requested, "qcd_requested")
    _nonnegative_number(
        account.rollover_or_conversion_amount, "rollover_or_conversion_amount"
    )


def evaluate_rmd_compliance(
    accounts: Iterable[RmdAccountInput],
    *,
    qcd_annual_limit: float,
) -> RmdComplianceResult:
    """Calculate annual RMD obligations and enforce QCD/aggregation controls.

    QCD requests are processed chronologically by distribution date and then by
    account ID. The annual QCD limit is applied separately to each owner.
    """

    annual_limit = _nonnegative_number(qcd_annual_limit, "qcd_annual_limit")
    account_list = tuple(accounts)
    if not account_list:
        raise ValueError("at least one retirement account is required")

    seen_ids: set[str] = set()
    for account in account_list:
        _validate_account(account)
        if account.account_id in seen_ids:
            raise ValueError(f"duplicate account_id: {account.account_id}")
        seen_ids.add(account.account_id)

    qcd_used_by_owner: dict[str, float] = {}
    result_by_id: dict[str, RmdAccountResult] = {}
    processing_order = sorted(
        account_list,
        key=lambda item: (item.qcd_distribution_date or date.max, item.account_id),
    )

    for account in processing_order:
        balance = float(account.prior_year_end_balance)
        divisor = float(account.divisor)
        rmd = balance / divisor
        distributions = float(account.distributions_taken)
        requested_qcd = float(account.qcd_requested)
        violations: list[str] = []
        qualified_qcd = 0.0

        if requested_qcd > 0:
            if account.account_type not in QCD_ELIGIBLE_ACCOUNT_TYPES:
                violations.append("QCD is not permitted from this account type")
            elif not account.qcd_direct_transfer:
                violations.append("QCD must be paid directly to an eligible charity")
            elif account.owner_date_of_birth is None or account.qcd_distribution_date is None:
                violations.append("QCD requires owner birth date and distribution date")
            elif account.qcd_distribution_date < _qcd_eligibility_date(
                account.owner_date_of_birth
            ):
                violations.append("Owner had not reached age 70 1/2 on the QCD date")
            else:
                used = qcd_used_by_owner.get(account.owner_id, 0.0)
                remaining_limit = max(0.0, annual_limit - used)
                qualified_qcd = min(requested_qcd, remaining_limit)
                qcd_used_by_owner[account.owner_id] = used + qualified_qcd
                if qualified_qcd < requested_qcd:
                    violations.append("QCD request exceeds the owner's annual limit")

        qcd_applied = min(rmd, qualified_qcd)
        remaining_after_qcd = max(0.0, rmd - qcd_applied)
        account_remaining = max(0.0, remaining_after_qcd - distributions)

        eligible_rollover_or_conversion = max(0.0, distributions - remaining_after_qcd)
        requested_rollover = float(account.rollover_or_conversion_amount)
        ineligible_rollover = max(0.0, requested_rollover - eligible_rollover_or_conversion)
        if ineligible_rollover > 0:
            violations.append("Current-year RMD is not eligible for rollover or Roth conversion")

        result_by_id[account.account_id] = RmdAccountResult(
            account_id=account.account_id,
            owner_id=account.owner_id,
            account_type=account.account_type,
            aggregation_group=_aggregation_group(account),
            prior_year_end_balance=balance,
            life_expectancy_table=account.life_expectancy_table,
            divisor=divisor,
            calculated_rmd=rmd,
            qcd_requested=requested_qcd,
            qualified_qcd=qualified_qcd,
            qcd_applied_to_rmd=qcd_applied,
            distributions_taken=distributions,
            account_remaining_rmd=account_remaining,
            rollover_or_conversion_amount=requested_rollover,
            ineligible_rollover_or_conversion=ineligible_rollover,
            violations=tuple(violations),
        )

    account_results = tuple(result_by_id[item.account_id] for item in account_list)
    grouped: dict[str, list[RmdAccountResult]] = {}
    for result in account_results:
        grouped.setdefault(result.aggregation_group, []).append(result)

    group_results: list[RmdGroupResult] = []
    for group_name, members in grouped.items():
        obligation = sum(item.calculated_rmd for item in members)
        qualifying = sum(item.qualified_qcd + item.distributions_taken for item in members)
        shortfall = max(0.0, obligation - qualifying)
        group_results.append(
            RmdGroupResult(
                owner_id=members[0].owner_id,
                aggregation_group=group_name,
                account_ids=tuple(item.account_id for item in members),
                calculated_rmd=obligation,
                qualifying_distributions=qualifying,
                remaining_shortfall=shortfall,
                compliant=shortfall == 0.0 and not any(item.violations for item in members),
            )
        )

    total_rmd = sum(item.calculated_rmd for item in account_results)
    total_qcd = sum(item.qualified_qcd for item in account_results)
    total_distributions = sum(item.distributions_taken for item in account_results)
    total_shortfall = sum(item.remaining_shortfall for item in group_results)
    compliant = all(item.compliant for item in group_results)

    return RmdComplianceResult(
        account_results=account_results,
        group_results=tuple(group_results),
        total_calculated_rmd=total_rmd,
        total_qualified_qcd=total_qcd,
        total_distributions_taken=total_distributions,
        total_remaining_shortfall=total_shortfall,
        compliant=compliant,
    )
