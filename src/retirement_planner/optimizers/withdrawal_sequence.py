"""Withdrawal sequencing controls for RMD-aware strategies."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from retirement_planner.calculators.rmd_compliance import RmdComplianceResult


@dataclass(frozen=True)
class WithdrawalSequenceResult:
    """RMD-first sequencing result for one annual strategy."""

    required_rmd_distribution: float
    planned_tax_deferred_withdrawal: float
    excess_tax_deferred_withdrawal: float
    remaining_rmd_shortfall: float
    roth_conversion_eligible_amount: float
    compliant: bool
    warnings: tuple[str, ...]


def _nonnegative(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError(f"{field_name} must be a nonnegative finite number")
    return number


def sequence_rmd_first(
    compliance: RmdComplianceResult,
    *,
    planned_tax_deferred_withdrawal: float,
) -> WithdrawalSequenceResult:
    """Apply tax-deferred withdrawals to RMDs before discretionary uses."""

    planned = _nonnegative(
        planned_tax_deferred_withdrawal, "planned_tax_deferred_withdrawal"
    )
    required = float(compliance.total_calculated_rmd)
    remaining_shortfall = max(0.0, required - planned)
    excess = max(0.0, planned - required)

    warnings: list[str] = []
    if remaining_shortfall > 0:
        warnings.append("Planned tax-deferred withdrawals do not satisfy the current-year RMD.")
    if any(
        account.ineligible_rollover_or_conversion > 0
        for account in compliance.account_results
    ):
        warnings.append("The underlying account plan attempts to roll over or convert RMD dollars.")

    compliant = remaining_shortfall == 0.0 and not warnings
    return WithdrawalSequenceResult(
        required_rmd_distribution=required,
        planned_tax_deferred_withdrawal=planned,
        excess_tax_deferred_withdrawal=excess,
        remaining_rmd_shortfall=remaining_shortfall,
        roth_conversion_eligible_amount=excess if compliant else 0.0,
        compliant=compliant,
        warnings=tuple(warnings),
    )
