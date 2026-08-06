import pytest

from retirement_planner.calculators.irmaa_strategy import (
    IrmaaIncomeSource,
    analyze_irmaa_income_sources,
    compare_survivor_irmaa,
    evaluate_irmaa_strategy,
)


def test_income_sources_reconcile_and_identify_threshold_driver():
    diagnostic = analyze_irmaa_income_sources(
        income_year=2024,
        filing_status="married_filing_jointly",
        beneficiary_count=2,
        sources=(
            IrmaaIncomeSource("Pension and taxable income", 210000),
            IrmaaIncomeSource("Roth conversion", 10000),
            IrmaaIncomeSource("Municipal-bond interest", 2000, "tax_exempt_interest"),
        ),
    )

    assert diagnostic.agi_total == 220000
    assert diagnostic.tax_exempt_interest_total == 2000
    assert diagnostic.result.irmaa_magi == 222000
    assert diagnostic.result.tier == 1
    roth = next(item for item in diagnostic.source_impacts if item.name == "Roth conversion")
    assert roth.tier_without_source == 0
    assert roth.tier_with_source == 1
    assert roth.incremental_annual_cost > 0


def test_duplicate_income_source_names_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        analyze_irmaa_income_sources(
            income_year=2024,
            filing_status="single",
            beneficiary_count=1,
            sources=(
                IrmaaIncomeSource("Interest", 1000),
                IrmaaIncomeSource("Interest", 2000),
            ),
        )


def test_survivor_transition_uses_single_thresholds_and_one_beneficiary():
    transition = compare_survivor_irmaa(
        income_year=2024,
        agi=180000,
        tax_exempt_interest=0,
    )

    assert transition.joint_result.filing_status == "married_filing_jointly"
    assert transition.joint_result.beneficiary_count == 2
    assert transition.joint_result.tier == 0
    assert transition.survivor_result.filing_status == "single"
    assert transition.survivor_result.beneficiary_count == 1
    assert transition.survivor_result.tier == 3
    assert transition.tier_change == 3


def test_optimizer_blocks_silent_threshold_crossing():
    decision = evaluate_irmaa_strategy(
        income_year=2024,
        filing_status="married_filing_jointly",
        beneficiary_count=2,
        baseline_agi=215000,
        baseline_tax_exempt_interest=0,
        added_agi=10000,
    )

    assert decision.baseline.tier == 0
    assert decision.proposed.tier == 1
    assert decision.crossed_threshold is True
    assert decision.allowed is False
    assert decision.incremental_annual_cost > 0
    assert "without explicit approval" in decision.warning


def test_optimizer_allows_deliberate_crossing_with_rationale():
    decision = evaluate_irmaa_strategy(
        income_year=2024,
        filing_status="married_filing_jointly",
        beneficiary_count=2,
        baseline_agi=215000,
        baseline_tax_exempt_interest=0,
        added_agi=10000,
        allow_deliberate_crossing=True,
        rationale="Lifetime tax savings exceed the modeled Medicare surcharge.",
    )

    assert decision.crossed_threshold is True
    assert decision.allowed is True
    assert decision.rationale is not None
    assert "Deliberate" in decision.warning


def test_crossing_permission_without_rationale_is_still_blocked():
    decision = evaluate_irmaa_strategy(
        income_year=2024,
        filing_status="single",
        beneficiary_count=1,
        baseline_agi=108000,
        baseline_tax_exempt_interest=0,
        added_agi=2000,
        allow_deliberate_crossing=True,
        rationale="  ",
    )

    assert decision.crossed_threshold is True
    assert decision.allowed is False
