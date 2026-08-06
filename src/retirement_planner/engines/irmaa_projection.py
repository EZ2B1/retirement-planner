"""Annual Medicare IRMAA projection and reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from retirement_planner.calculators.irmaa import IrmaaResult
from retirement_planner.calculators.irmaa_appeals import (
    IrmaaReviewRequest,
    validate_review_request,
)
from retirement_planner.calculators.irmaa_strategy import (
    IrmaaIncomeDiagnostic,
    IrmaaStrategyDecision,
    IrmaaSurvivorTransition,
)


@dataclass(frozen=True)
class IrmaaAnnualProjectionResult:
    projection_year: int
    premium_result: IrmaaResult
    income_diagnostic: IrmaaIncomeDiagnostic | None = None
    strategy_decision: IrmaaStrategyDecision | None = None
    survivor_transition: IrmaaSurvivorTransition | None = None
    review_requests: tuple[IrmaaReviewRequest, ...] = ()

    @property
    def annual_household_cost(self) -> float:
        return self.premium_result.household_annual_cost

    @property
    def threshold_warning(self) -> str | None:
        if self.strategy_decision is None:
            return None
        return self.strategy_decision.warning

    @property
    def open_review_count(self) -> int:
        return sum(
            request.status in {"draft", "submitted"}
            for request in self.review_requests
        )

    def validate_reconciliation(self) -> None:
        if self.projection_year != self.premium_result.premium_year:
            raise ValueError("projection year must equal the IRMAA premium year")
        if self.income_diagnostic is not None:
            diagnostic = self.income_diagnostic.result
            if diagnostic != self.premium_result:
                raise ValueError("income diagnostic does not reconcile to premium result")
        if self.strategy_decision is not None:
            if self.strategy_decision.baseline != self.premium_result:
                raise ValueError("strategy baseline does not reconcile to premium result")
        for request in self.review_requests:
            errors = validate_review_request(request)
            if errors:
                raise ValueError(
                    f"invalid IRMAA review request {request.request_id}: "
                    + "; ".join(errors)
                )
            if request.premium_year != self.projection_year:
                raise ValueError("review request premium year does not reconcile")


def project_irmaa_year(
    *,
    premium_result: IrmaaResult,
    income_diagnostic: IrmaaIncomeDiagnostic | None = None,
    strategy_decision: IrmaaStrategyDecision | None = None,
    survivor_transition: IrmaaSurvivorTransition | None = None,
    review_requests: Iterable[IrmaaReviewRequest] = (),
) -> IrmaaAnnualProjectionResult:
    """Build and validate one premium-year IRMAA projection record."""

    result = IrmaaAnnualProjectionResult(
        projection_year=premium_result.premium_year,
        premium_result=premium_result,
        income_diagnostic=income_diagnostic,
        strategy_decision=strategy_decision,
        survivor_transition=survivor_transition,
        review_requests=tuple(review_requests),
    )
    result.validate_reconciliation()
    return result
