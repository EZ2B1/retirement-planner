"""Medicare IRMAA appeal, corrected-tax-data, and stewardship workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

SSA44_EVENTS = frozenset(
    {
        "marriage",
        "divorce_or_annulment",
        "death_of_spouse",
        "work_stoppage",
        "work_reduction",
        "loss_of_income_producing_property",
        "loss_of_pension_income",
        "employer_settlement_payment",
    }
)
WORKFLOW_STATUSES = frozenset(
    {"draft", "submitted", "approved", "denied", "withdrawn"}
)
REVIEW_TYPES = frozenset({"ssa44_life_changing_event", "corrected_tax_data"})


@dataclass(frozen=True)
class IrmaaReviewRequest:
    request_id: str
    beneficiary_id: str
    review_type: str
    status: str
    premium_year: int
    original_income_year: int
    requested_income_year: int
    projected_agi: float
    projected_tax_exempt_interest: float
    event_type: str | None = None
    event_date: date | None = None
    evidence_items: tuple[str, ...] = ()
    required_evidence_items: tuple[str, ...] = ()
    submitted_on: date | None = None
    decided_on: date | None = None
    decision_notes: str | None = None

    @property
    def projected_magi(self) -> float:
        return self.projected_agi + self.projected_tax_exempt_interest

    @property
    def missing_evidence(self) -> tuple[str, ...]:
        provided = {item.strip().lower() for item in self.evidence_items if item.strip()}
        return tuple(
            item
            for item in self.required_evidence_items
            if item.strip().lower() not in provided
        )

    @property
    def ready_to_submit(self) -> bool:
        return not self.missing_evidence and self.status == "draft"


@dataclass(frozen=True)
class IrmaaStewardshipRecord:
    premium_year: int
    source_citation: str
    source_url: str
    reviewer: str
    reviewed_on: date
    next_review_due: date
    verification_status: str
    notes: str = ""


def _nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    number = float(value)
    if number < 0:
        raise ValueError(f"{name} must be nonnegative")
    return number


def validate_review_request(request: IrmaaReviewRequest) -> tuple[str, ...]:
    """Return validation errors without mutating the workflow request."""

    errors: list[str] = []
    if not request.request_id.strip():
        errors.append("request_id is required")
    if not request.beneficiary_id.strip():
        errors.append("beneficiary_id is required")
    if request.review_type not in REVIEW_TYPES:
        errors.append("unsupported review_type")
    if request.status not in WORKFLOW_STATUSES:
        errors.append("unsupported workflow status")
    if request.premium_year < 1900:
        errors.append("premium_year is outside the supported range")
    if request.original_income_year >= request.premium_year:
        errors.append("original_income_year must precede premium_year")
    if request.requested_income_year >= request.premium_year:
        errors.append("requested_income_year must precede premium_year")

    try:
        _nonnegative(request.projected_agi, "projected_agi")
        _nonnegative(
            request.projected_tax_exempt_interest,
            "projected_tax_exempt_interest",
        )
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))

    if request.review_type == "ssa44_life_changing_event":
        if request.event_type not in SSA44_EVENTS:
            errors.append("SSA-44 review requires a supported life-changing event")
        if request.event_date is None:
            errors.append("SSA-44 review requires an event_date")
    elif request.event_type is not None or request.event_date is not None:
        errors.append("corrected-tax-data review must not be labeled as an SSA-44 event")

    if request.status in {"submitted", "approved", "denied"}:
        if request.missing_evidence:
            errors.append("required evidence is incomplete")
        if request.submitted_on is None:
            errors.append("submitted_on is required after submission")

    if request.status in {"approved", "denied"}:
        if request.decided_on is None:
            errors.append("decided_on is required for a completed decision")
        if not (request.decision_notes or "").strip():
            errors.append("decision_notes are required for a completed decision")

    if request.status == "withdrawn" and request.decided_on is None:
        errors.append("withdrawn requests require the withdrawal date in decided_on")

    return tuple(errors)


def create_review_request(
    *,
    request_id: str,
    beneficiary_id: str,
    review_type: str,
    premium_year: int,
    original_income_year: int,
    requested_income_year: int,
    projected_agi: float,
    projected_tax_exempt_interest: float,
    event_type: str | None = None,
    event_date: date | None = None,
    evidence_items: Iterable[str] = (),
    required_evidence_items: Iterable[str] = (),
) -> IrmaaReviewRequest:
    request = IrmaaReviewRequest(
        request_id=request_id,
        beneficiary_id=beneficiary_id,
        review_type=review_type,
        status="draft",
        premium_year=premium_year,
        original_income_year=original_income_year,
        requested_income_year=requested_income_year,
        projected_agi=_nonnegative(projected_agi, "projected_agi"),
        projected_tax_exempt_interest=_nonnegative(
            projected_tax_exempt_interest,
            "projected_tax_exempt_interest",
        ),
        event_type=event_type,
        event_date=event_date,
        evidence_items=tuple(evidence_items),
        required_evidence_items=tuple(required_evidence_items),
    )
    errors = validate_review_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    return request


def validate_stewardship_record(record: IrmaaStewardshipRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if record.premium_year < 1900:
        errors.append("premium_year is outside the supported range")
    if not record.source_citation.strip():
        errors.append("source_citation is required")
    if not record.source_url.strip():
        errors.append("source_url is required")
    if not record.reviewer.strip():
        errors.append("reviewer is required")
    if record.next_review_due <= record.reviewed_on:
        errors.append("next_review_due must be after reviewed_on")
    if record.verification_status not in {"verified", "pending", "superseded"}:
        errors.append("unsupported verification_status")
    return tuple(errors)
