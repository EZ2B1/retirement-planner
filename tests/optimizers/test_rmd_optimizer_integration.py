from retirement_planner.calculators.rmd_compliance import (
    RmdAccountInput,
    evaluate_rmd_compliance,
)
from retirement_planner.optimizers.roth_conversion import (
    evaluate_roth_conversion_capacity,
)
from retirement_planner.optimizers.withdrawal_sequence import sequence_rmd_first


def _compliance(*, distribution=4_000.0, conversion=0.0):
    return evaluate_rmd_compliance(
        (
            RmdAccountInput(
                account_id="ira-1",
                owner_id="owner-1",
                account_type="traditional_ira",
                prior_year_end_balance=100_000.0,
                divisor=25.0,
                life_expectancy_table="uniform_lifetime",
                distributions_taken=distribution,
                rollover_or_conversion_amount=conversion,
            ),
        ),
        qcd_annual_limit=0.0,
    )


def test_withdrawal_sequence_satisfies_rmd_before_discretionary_amounts():
    result = sequence_rmd_first(
        _compliance(), planned_tax_deferred_withdrawal=10_000.0
    )

    assert result.required_rmd_distribution == 4_000.0
    assert result.excess_tax_deferred_withdrawal == 6_000.0
    assert result.roth_conversion_eligible_amount == 6_000.0
    assert result.compliant


def test_withdrawal_sequence_blocks_conversion_when_rmd_is_underfunded():
    compliance = _compliance(distribution=0.0)
    result = sequence_rmd_first(
        compliance, planned_tax_deferred_withdrawal=3_000.0
    )

    assert result.remaining_rmd_shortfall == 1_000.0
    assert result.roth_conversion_eligible_amount == 0.0
    assert not result.compliant


def test_roth_conversion_is_blocked_until_rmd_shortfall_is_satisfied():
    result = evaluate_roth_conversion_capacity(
        _compliance(distribution=0.0),
        proposed_conversion=5_000.0,
        available_eligible_distribution=5_000.0,
    )

    assert result.approved_conversion == 0.0
    assert result.blocked_rmd_amount == 5_000.0
    assert not result.compliant


def test_roth_conversion_uses_only_distribution_excess_after_rmd():
    result = evaluate_roth_conversion_capacity(
        _compliance(),
        proposed_conversion=7_000.0,
        available_eligible_distribution=6_000.0,
    )

    assert result.approved_conversion == 6_000.0
    assert result.blocked_rmd_amount == 1_000.0
    assert not result.compliant


def test_compliant_roth_conversion_within_excess_distribution():
    result = evaluate_roth_conversion_capacity(
        _compliance(),
        proposed_conversion=5_000.0,
        available_eligible_distribution=6_000.0,
    )

    assert result.approved_conversion == 5_000.0
    assert result.blocked_rmd_amount == 0.0
    assert result.compliant


def test_underlying_attempt_to_convert_rmd_dollars_invalidates_sequence():
    compliance = _compliance(distribution=4_000.0, conversion=4_000.0)
    result = sequence_rmd_first(
        compliance, planned_tax_deferred_withdrawal=10_000.0
    )

    assert result.roth_conversion_eligible_amount == 0.0
    assert not result.compliant
    assert any("RMD dollars" in warning for warning in result.warnings)
