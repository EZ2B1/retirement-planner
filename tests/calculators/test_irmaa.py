from retirement_planner.calculators.irmaa import calculate_irmaa, calculate_irmaa_magi, load_irmaa_table


def test_irmaa_magi_is_agi_plus_tax_exempt_interest():
    assert calculate_irmaa_magi(200000, 18000) == 218000


def test_2026_mfj_boundary_logic_and_lookback_mapping():
    base = calculate_irmaa(
        income_year=2024,
        filing_status="married_filing_jointly",
        agi=218000,
        tax_exempt_interest=0,
        beneficiary_count=2,
    )
    next_tier = calculate_irmaa(
        income_year=2024,
        filing_status="married_filing_jointly",
        agi=218000.01,
        tax_exempt_interest=0,
        beneficiary_count=2,
    )
    assert base.premium_year == 2026
    assert base.lookback_years == 2
    assert base.tier == 0
    assert next_tier.tier == 1


def test_components_reconcile_for_two_beneficiaries():
    result = calculate_irmaa(
        income_year=2024,
        filing_status="married_filing_jointly",
        agi=300000,
        tax_exempt_interest=0,
        beneficiary_count=2,
        part_d_plan_monthly_premium=45,
    )
    expected_per_person = 202.90 + 202.90 + 45 + 37.50
    assert result.household_monthly_cost == expected_per_person * 2
    assert result.household_annual_cost == expected_per_person * 2 * 12


def test_threshold_distance_is_reported():
    result = calculate_irmaa(
        income_year=2024,
        filing_status="single",
        agi=100000,
        tax_exempt_interest=0,
        beneficiary_count=1,
    )
    assert result.next_threshold == 109000
    assert result.distance_to_next_threshold == 9000


def test_reference_data_is_verified():
    table = load_irmaa_table()
    assert table.premium_year == 2026
    assert table.ordinary_income_year == 2024
    assert table.provenance.verification_status == "verified"
