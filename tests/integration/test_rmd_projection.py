from datetime import date

import pytest

from retirement_planner.calculators.rmd_compliance import RmdAccountInput
from retirement_planner.engines.projection_engine import project_rmd_year
from retirement_planner.models.results import RmdAnnualProjectionResult


def _ira(account_id, owner_id, balance, divisor, distributions=0, qcd=0):
    return RmdAccountInput(
        account_id=account_id,
        owner_id=owner_id,
        account_type="traditional_ira",
        prior_year_end_balance=balance,
        divisor=divisor,
        life_expectancy_table="uniform_lifetime",
        distributions_taken=distributions,
        qcd_requested=qcd,
        qcd_direct_transfer=qcd > 0,
        owner_date_of_birth=date(1950, 1, 1),
        qcd_distribution_date=date(2026, 3, 1) if qcd > 0 else None,
    )


def test_projection_reconciles_accounts_owners_groups_and_household():
    result = project_rmd_year(
        2026,
        (
            _ira("h-ira-1", "husband", 274_000, 27.4, distributions=4_000, qcd=6_000),
            _ira("h-ira-2", "husband", 137_000, 27.4, distributions=5_000),
            _ira("w-ira-1", "wife", 274_000, 27.4, distributions=10_000),
        ),
        qcd_annual_limit=108_000,
    )

    assert result.household_calculated_rmd == pytest.approx(25_000)
    assert result.household_qualified_qcd == pytest.approx(6_000)
    assert result.household_distributions_taken == pytest.approx(19_000)
    assert result.household_remaining_shortfall == pytest.approx(0)
    assert result.compliant is True
    assert [item.owner_id for item in result.owner_summaries] == ["husband", "wife"]
    assert result.owner_summaries[0].calculated_rmd == pytest.approx(15_000)
    assert result.owner_summaries[1].calculated_rmd == pytest.approx(10_000)
    result.validate_reconciliation()


def test_projection_preserves_plan_by_plan_shortfall():
    accounts = (
        RmdAccountInput(
            account_id="plan-a",
            owner_id="husband",
            account_type="401k",
            prior_year_end_balance=274_000,
            divisor=27.4,
            life_expectancy_table="uniform_lifetime",
            distributions_taken=20_000,
        ),
        RmdAccountInput(
            account_id="plan-b",
            owner_id="husband",
            account_type="401k",
            prior_year_end_balance=274_000,
            divisor=27.4,
            life_expectancy_table="uniform_lifetime",
            distributions_taken=0,
        ),
    )

    result = project_rmd_year(2026, accounts, qcd_annual_limit=108_000)

    assert len(result.group_results) == 2
    assert result.household_remaining_shortfall == pytest.approx(10_000)
    assert result.compliant is False
    assert result.owner_summaries[0].remaining_shortfall == pytest.approx(10_000)


def test_reconciliation_detects_tampered_household_total():
    result = project_rmd_year(
        2026,
        (_ira("ira-1", "owner", 274_000, 27.4, distributions=10_000),),
        qcd_annual_limit=108_000,
    )
    tampered = RmdAnnualProjectionResult(
        projection_year=result.projection_year,
        account_results=result.account_results,
        group_results=result.group_results,
        owner_summaries=result.owner_summaries,
        household_calculated_rmd=result.household_calculated_rmd + 1,
        household_qualified_qcd=result.household_qualified_qcd,
        household_distributions_taken=result.household_distributions_taken,
        household_remaining_shortfall=result.household_remaining_shortfall,
        compliant=result.compliant,
    )

    with pytest.raises(ValueError, match="account RMD"):
        tampered.validate_reconciliation()


@pytest.mark.parametrize("year", [True, 2026.0, "2026"])
def test_projection_year_must_be_integer(year):
    with pytest.raises(TypeError, match="projection_year must be an integer"):
        project_rmd_year(year, (_ira("ira-1", "owner", 274_000, 27.4),), qcd_annual_limit=0)
