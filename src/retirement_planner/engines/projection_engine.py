"""Year-by-year household projection engine."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from retirement_planner.calculators.rmd_compliance import (
    RmdAccountInput,
    evaluate_rmd_compliance,
)
from retirement_planner.models.results import (
    RmdAnnualProjectionResult,
    RmdOwnerSummary,
)


def project_rmd_year(
    projection_year: int,
    accounts: Iterable[RmdAccountInput],
    *,
    qcd_annual_limit: float,
) -> RmdAnnualProjectionResult:
    """Calculate and reconcile one projection year's RMD/QCD compliance output."""

    if isinstance(projection_year, bool) or not isinstance(projection_year, int):
        raise TypeError("projection_year must be an integer")
    if projection_year < 1900:
        raise ValueError("projection_year is outside the supported range")

    compliance = evaluate_rmd_compliance(
        accounts,
        qcd_annual_limit=qcd_annual_limit,
    )

    by_owner: dict[str, dict[str, float | bool]] = defaultdict(
        lambda: {
            "calculated_rmd": 0.0,
            "qualified_qcd": 0.0,
            "distributions_taken": 0.0,
            "remaining_shortfall": 0.0,
            "compliant": True,
        }
    )

    for account in compliance.account_results:
        owner = by_owner[account.owner_id]
        owner["calculated_rmd"] = float(owner["calculated_rmd"]) + account.calculated_rmd
        owner["qualified_qcd"] = float(owner["qualified_qcd"]) + account.qualified_qcd
        owner["distributions_taken"] = (
            float(owner["distributions_taken"]) + account.distributions_taken
        )
        if account.violations:
            owner["compliant"] = False

    for group in compliance.group_results:
        owner = by_owner[group.owner_id]
        owner["remaining_shortfall"] = (
            float(owner["remaining_shortfall"]) + group.remaining_shortfall
        )
        if not group.compliant:
            owner["compliant"] = False

    owner_summaries = tuple(
        RmdOwnerSummary(
            owner_id=owner_id,
            calculated_rmd=float(values["calculated_rmd"]),
            qualified_qcd=float(values["qualified_qcd"]),
            distributions_taken=float(values["distributions_taken"]),
            remaining_shortfall=float(values["remaining_shortfall"]),
            compliant=bool(values["compliant"]),
        )
        for owner_id, values in sorted(by_owner.items())
    )

    result = RmdAnnualProjectionResult(
        projection_year=projection_year,
        account_results=compliance.account_results,
        group_results=compliance.group_results,
        owner_summaries=owner_summaries,
        household_calculated_rmd=compliance.total_calculated_rmd,
        household_qualified_qcd=compliance.total_qualified_qcd,
        household_distributions_taken=compliance.total_distributions_taken,
        household_remaining_shortfall=compliance.total_remaining_shortfall,
        compliant=compliance.compliant,
    )
    result.validate_reconciliation()
    return result
