"""Roth conversion optimizer safeguards.

The full tax optimization engine will build on these controls. This module makes
RMD ordering explicit: current-year RMD amounts must be distributed first and
cannot be converted to Roth.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from retirement_planner.calculators.rmd_compliance import RmdComplianceResult


@dataclass(frozen=True)
class RothConversionCapacity:
    """Maximum conversion capacity after current-year RMD obligations."""

    proposed_conversion: float
    eligible_conversion_capacity: float
    approved_conversion: float
    blocked_rmd_amount: float
    compliant: bool
    message: str | None


def _nonnegative(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError(f"{field_name} must be a nonnegative finite number")
    return number


def evaluate_roth_conversion_capacity(
    compliance: RmdComplianceResult,
    *,
    proposed_conversion: float,
    available_eligible_distribution: float,
) -> RothConversionCapacity:
    """Validate a proposed Roth conversion against current-year RMD rules.

    ``available_eligible_distribution`` is the amount distributed from eligible
    retirement accounts that remains after legally required RMD amounts have
    been satisfied. It may be converted, subject to other tax and plan rules.
    """

    proposed = _nonnegative(proposed_conversion, "proposed_conversion")
    eligible = _nonnegative(
        available_eligible_distribution, "available_eligible_distribution"
    )

    if compliance.total_remaining_shortfall > 0:
        return RothConversionCapacity(
            proposed_conversion=proposed,
            eligible_conversion_capacity=0.0,
            approved_conversion=0.0,
            blocked_rmd_amount=proposed,
            compliant=False,
            message=(
                "Roth conversion is blocked until all current-year RMD "
                "obligations are satisfied."
            ),
        )

    approved = min(proposed, eligible)
    blocked = max(0.0, proposed - approved)
    return RothConversionCapacity(
        proposed_conversion=proposed,
        eligible_conversion_capacity=eligible,
        approved_conversion=approved,
        blocked_rmd_amount=blocked,
        compliant=blocked == 0.0,
        message=(
            None
            if blocked == 0.0
            else "Proposed conversion exceeds distributions eligible after RMD satisfaction."
        ),
    )
