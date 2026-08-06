"""Projection and strategy result models."""

from __future__ import annotations

from dataclasses import dataclass

from retirement_planner.calculators.rmd_compliance import (
    RmdAccountResult,
    RmdGroupResult,
)


@dataclass(frozen=True)
class RmdOwnerSummary:
    """Reconciled annual RMD/QCD totals for one account owner."""

    owner_id: str
    calculated_rmd: float
    qualified_qcd: float
    distributions_taken: float
    remaining_shortfall: float
    compliant: bool


@dataclass(frozen=True)
class RmdAnnualProjectionResult:
    """Projection-ready annual RMD/QCD output for reports and optimizers."""

    projection_year: int
    account_results: tuple[RmdAccountResult, ...]
    group_results: tuple[RmdGroupResult, ...]
    owner_summaries: tuple[RmdOwnerSummary, ...]
    household_calculated_rmd: float
    household_qualified_qcd: float
    household_distributions_taken: float
    household_remaining_shortfall: float
    compliant: bool

    def validate_reconciliation(self, tolerance: float = 0.01) -> None:
        """Raise when account, group, owner, and household totals do not agree."""

        if tolerance < 0:
            raise ValueError("tolerance must be nonnegative")

        account_rmd = sum(item.calculated_rmd for item in self.account_results)
        account_qcd = sum(item.qualified_qcd for item in self.account_results)
        account_distributions = sum(item.distributions_taken for item in self.account_results)
        group_shortfall = sum(item.remaining_shortfall for item in self.group_results)
        owner_rmd = sum(item.calculated_rmd for item in self.owner_summaries)
        owner_qcd = sum(item.qualified_qcd for item in self.owner_summaries)
        owner_distributions = sum(item.distributions_taken for item in self.owner_summaries)
        owner_shortfall = sum(item.remaining_shortfall for item in self.owner_summaries)

        checks = (
            (account_rmd, self.household_calculated_rmd, "account RMD"),
            (owner_rmd, self.household_calculated_rmd, "owner RMD"),
            (account_qcd, self.household_qualified_qcd, "account QCD"),
            (owner_qcd, self.household_qualified_qcd, "owner QCD"),
            (
                account_distributions,
                self.household_distributions_taken,
                "account distributions",
            ),
            (
                owner_distributions,
                self.household_distributions_taken,
                "owner distributions",
            ),
            (group_shortfall, self.household_remaining_shortfall, "group shortfall"),
            (owner_shortfall, self.household_remaining_shortfall, "owner shortfall"),
        )
        for actual, expected, label in checks:
            if abs(actual - expected) > tolerance:
                raise ValueError(f"RMD reconciliation failed for {label}")
