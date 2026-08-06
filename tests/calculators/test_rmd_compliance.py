from datetime import date

import pytest

from retirement_planner.calculators.rmd_compliance import (
    RmdAccountInput,
    build_first_rmd_timing,
    evaluate_rmd_compliance,
)


def _account(**overrides):
    values = {
        "account_id": "ira-1",
        "owner_id": "owner-1",
        "account_type": "traditional_ira",
        "prior_year_end_balance": 274000.0,
        "divisor": 27.4,
        "life_expectancy_table": "uniform_lifetime",
    }
    values.update(overrides)
    return RmdAccountInput(**values)


def test_first_rmd_paid_by_december_31_does_not_create_double_year():
    result = build_first_rmd_timing(2026, defer_to_april_1=False)

    assert result.due_items[0].due_date == date(2026, 12, 31)
    assert result.due_items[1].due_date == date(2027, 12, 31)
    assert result.double_rmd_calendar_year is None
    assert result.warning is None


def test_first_rmd_deferred_to_april_1_creates_double_rmd_warning():
    result = build_first_rmd_timing(2026, defer_to_april_1=True)

    assert result.due_items[0].due_date == date(2027, 4, 1)
    assert result.due_items[1].due_date == date(2027, 12, 31)
    assert result.double_rmd_calendar_year == 2027
    assert "two RMD deadlines" in result.warning


def test_account_level_trail_calculates_rmd_and_shortfall():
    result = evaluate_rmd_compliance(
        [_account(distributions_taken=6000.0)], qcd_annual_limit=108000.0
    )

    account = result.account_results[0]
    assert account.calculated_rmd == pytest.approx(10000.0)
    assert account.account_remaining_rmd == pytest.approx(4000.0)
    assert account.prior_year_end_balance == 274000.0
    assert account.divisor == 27.4
    assert account.life_expectancy_table == "uniform_lifetime"
    assert result.total_remaining_shortfall == pytest.approx(4000.0)
    assert not result.compliant


def test_multiple_iras_for_same_owner_may_be_aggregated():
    accounts = [
        _account(account_id="ira-1", prior_year_end_balance=137000.0, distributions_taken=10000.0),
        _account(account_id="ira-2", prior_year_end_balance=137000.0, distributions_taken=0.0),
    ]

    result = evaluate_rmd_compliance(accounts, qcd_annual_limit=108000.0)

    assert len(result.group_results) == 1
    group = result.group_results[0]
    assert group.calculated_rmd == pytest.approx(10000.0)
    assert group.qualifying_distributions == pytest.approx(10000.0)
    assert group.remaining_shortfall == 0.0
    assert group.compliant


def test_401k_obligations_cannot_be_aggregated_across_plans():
    accounts = [
        _account(
            account_id="plan-a",
            account_type="401k",
            prior_year_end_balance=137000.0,
            distributions_taken=10000.0,
        ),
        _account(
            account_id="plan-b",
            account_type="401k",
            prior_year_end_balance=137000.0,
            distributions_taken=0.0,
        ),
    ]

    result = evaluate_rmd_compliance(accounts, qcd_annual_limit=108000.0)

    assert len(result.group_results) == 2
    by_id = {group.account_ids[0]: group for group in result.group_results}
    assert by_id["plan-a"].remaining_shortfall == 0.0
    assert by_id["plan-b"].remaining_shortfall == pytest.approx(5000.0)
    assert not result.compliant


def test_403b_contracts_for_same_owner_may_be_aggregated():
    accounts = [
        _account(
            account_id="403b-a",
            account_type="403b",
            prior_year_end_balance=137000.0,
            distributions_taken=10000.0,
        ),
        _account(
            account_id="403b-b",
            account_type="403b",
            prior_year_end_balance=137000.0,
            distributions_taken=0.0,
        ),
    ]

    result = evaluate_rmd_compliance(accounts, qcd_annual_limit=108000.0)

    assert len(result.group_results) == 1
    assert result.group_results[0].remaining_shortfall == 0.0


def test_qualified_qcd_is_applied_before_other_distributions():
    account = _account(
        qcd_requested=7000.0,
        qcd_direct_transfer=True,
        owner_date_of_birth=date(1950, 1, 1),
        qcd_distribution_date=date(2026, 1, 15),
        distributions_taken=3000.0,
    )

    result = evaluate_rmd_compliance([account], qcd_annual_limit=108000.0)
    trail = result.account_results[0]

    assert trail.qualified_qcd == 7000.0
    assert trail.qcd_applied_to_rmd == 7000.0
    assert trail.account_remaining_rmd == 0.0
    assert result.compliant


def test_qcd_requires_age_70_and_one_half_on_distribution_date():
    account = _account(
        qcd_requested=5000.0,
        qcd_direct_transfer=True,
        owner_date_of_birth=date(1956, 1, 1),
        qcd_distribution_date=date(2026, 6, 30),
    )

    result = evaluate_rmd_compliance([account], qcd_annual_limit=108000.0)
    trail = result.account_results[0]

    assert trail.qualified_qcd == 0.0
    assert any("70 1/2" in message for message in trail.violations)
    assert not result.compliant


def test_qcd_requires_direct_transfer_and_eligible_account_type():
    indirect = _account(
        qcd_requested=5000.0,
        qcd_direct_transfer=False,
        owner_date_of_birth=date(1950, 1, 1),
        qcd_distribution_date=date(2026, 1, 15),
    )
    employer_plan = _account(
        account_id="plan-1",
        account_type="401k",
        qcd_requested=5000.0,
        qcd_direct_transfer=True,
        owner_date_of_birth=date(1950, 1, 1),
        qcd_distribution_date=date(2026, 1, 15),
    )

    result = evaluate_rmd_compliance(
        [indirect, employer_plan], qcd_annual_limit=108000.0
    )
    by_id = {item.account_id: item for item in result.account_results}

    assert any("directly" in message for message in by_id["ira-1"].violations)
    assert any("account type" in message for message in by_id["plan-1"].violations)


def test_qcd_annual_limit_is_applied_per_owner_in_date_order():
    accounts = [
        _account(
            account_id="later",
            qcd_requested=70000.0,
            qcd_direct_transfer=True,
            owner_date_of_birth=date(1950, 1, 1),
            qcd_distribution_date=date(2026, 6, 1),
        ),
        _account(
            account_id="earlier",
            qcd_requested=70000.0,
            qcd_direct_transfer=True,
            owner_date_of_birth=date(1950, 1, 1),
            qcd_distribution_date=date(2026, 2, 1),
        ),
    ]

    result = evaluate_rmd_compliance(accounts, qcd_annual_limit=108000.0)
    by_id = {item.account_id: item for item in result.account_results}

    assert by_id["earlier"].qualified_qcd == 70000.0
    assert by_id["later"].qualified_qcd == 38000.0
    assert any("annual limit" in message for message in by_id["later"].violations)
    assert result.total_qualified_qcd == 108000.0


def test_current_year_rmd_cannot_be_rolled_or_converted():
    account = _account(
        distributions_taken=10000.0,
        rollover_or_conversion_amount=10000.0,
    )

    result = evaluate_rmd_compliance([account], qcd_annual_limit=108000.0)
    trail = result.account_results[0]

    assert trail.ineligible_rollover_or_conversion == pytest.approx(10000.0)
    assert any("not eligible" in message for message in trail.violations)
    assert not result.compliant


def test_distribution_above_rmd_may_leave_only_excess_eligible_for_rollover():
    account = _account(
        distributions_taken=15000.0,
        rollover_or_conversion_amount=6000.0,
    )

    result = evaluate_rmd_compliance([account], qcd_annual_limit=108000.0)
    trail = result.account_results[0]

    assert trail.ineligible_rollover_or_conversion == pytest.approx(1000.0)


def test_duplicate_accounts_and_invalid_amounts_are_rejected():
    duplicate = [_account(), _account()]
    with pytest.raises(ValueError, match="duplicate account_id"):
        evaluate_rmd_compliance(duplicate, qcd_annual_limit=108000.0)

    with pytest.raises(ValueError, match="greater than zero"):
        evaluate_rmd_compliance([_account(divisor=0)], qcd_annual_limit=108000.0)
