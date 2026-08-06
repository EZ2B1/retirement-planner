from dataclasses import replace
from datetime import date

import pytest

from retirement_planner.calculators.irmaa_appeals import (
    IrmaaStewardshipRecord,
    create_review_request,
    validate_review_request,
    validate_stewardship_record,
)


def test_ssa44_draft_tracks_missing_evidence() -> None:
    request = create_review_request(
        request_id="A-1",
        beneficiary_id="spouse-1",
        review_type="ssa44_life_changing_event",
        premium_year=2026,
        original_income_year=2024,
        requested_income_year=2025,
        projected_agi=90000,
        projected_tax_exempt_interest=1000,
        event_type="work_stoppage",
        event_date=date(2025, 6, 30),
        evidence_items=("employment termination letter",),
        required_evidence_items=(
            "employment termination letter",
            "income estimate",
        ),
    )

    assert request.projected_magi == 91000
    assert request.missing_evidence == ("income estimate",)
    assert not request.ready_to_submit


def test_ssa44_rejects_unsupported_event() -> None:
    with pytest.raises(ValueError, match="supported life-changing event"):
        create_review_request(
            request_id="A-2",
            beneficiary_id="spouse-1",
            review_type="ssa44_life_changing_event",
            premium_year=2026,
            original_income_year=2024,
            requested_income_year=2025,
            projected_agi=90000,
            projected_tax_exempt_interest=0,
            event_type="large_medical_expense",
            event_date=date(2025, 1, 1),
        )


def test_corrected_tax_data_remains_separate_from_ssa44() -> None:
    request = create_review_request(
        request_id="C-1",
        beneficiary_id="spouse-2",
        review_type="corrected_tax_data",
        premium_year=2026,
        original_income_year=2024,
        requested_income_year=2024,
        projected_agi=105000,
        projected_tax_exempt_interest=500,
        evidence_items=("amended federal return",),
        required_evidence_items=("amended federal return",),
    )

    assert request.event_type is None
    assert request.ready_to_submit

    mislabeled = replace(
        request,
        event_type="marriage",
        event_date=date(2024, 5, 1),
    )
    assert any("must not be labeled" in error for error in validate_review_request(mislabeled))


def test_submitted_request_requires_complete_evidence_and_date() -> None:
    request = create_review_request(
        request_id="A-3",
        beneficiary_id="spouse-1",
        review_type="ssa44_life_changing_event",
        premium_year=2026,
        original_income_year=2024,
        requested_income_year=2025,
        projected_agi=80000,
        projected_tax_exempt_interest=0,
        event_type="death_of_spouse",
        event_date=date(2025, 2, 10),
        required_evidence_items=("death certificate",),
    )
    submitted = replace(request, status="submitted")

    errors = validate_review_request(submitted)
    assert "required evidence is incomplete" in errors
    assert "submitted_on is required after submission" in errors


def test_approved_request_requires_decision_controls() -> None:
    request = create_review_request(
        request_id="C-2",
        beneficiary_id="spouse-2",
        review_type="corrected_tax_data",
        premium_year=2026,
        original_income_year=2024,
        requested_income_year=2024,
        projected_agi=100000,
        projected_tax_exempt_interest=0,
        evidence_items=("corrected IRS transcript",),
        required_evidence_items=("corrected IRS transcript",),
    )
    approved = replace(
        request,
        status="approved",
        submitted_on=date(2026, 2, 1),
    )

    errors = validate_review_request(approved)
    assert "decided_on is required for a completed decision" in errors
    assert "decision_notes are required for a completed decision" in errors


def test_stewardship_record_requires_future_review_and_verified_metadata() -> None:
    valid = IrmaaStewardshipRecord(
        premium_year=2026,
        source_citation="CMS 2026 Medicare premiums",
        source_url="https://www.cms.gov/example",
        reviewer="Tax Data Steward",
        reviewed_on=date(2025, 11, 14),
        next_review_due=date(2026, 11, 1),
        verification_status="verified",
    )
    assert validate_stewardship_record(valid) == ()

    invalid = replace(valid, next_review_due=date(2025, 11, 14), reviewer="")
    errors = validate_stewardship_record(invalid)
    assert "reviewer is required" in errors
    assert "next_review_due must be after reviewed_on" in errors
