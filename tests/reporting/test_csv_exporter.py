from datetime import date
import csv

from retirement_planner.calculators.rmd_compliance import RmdAccountInput
from retirement_planner.engines.projection_engine import project_rmd_year
from retirement_planner.reporting.csv_exporter import export_rmd_accounts_csv


def _result():
    return project_rmd_year(
        2026,
        (
            RmdAccountInput(
                account_id="IRA-1",
                owner_id="owner-1",
                account_type="traditional_ira",
                prior_year_end_balance=274000.0,
                divisor=27.4,
                life_expectancy_table="Uniform Lifetime",
                distributions_taken=4000.0,
                qcd_requested=6000.0,
                qcd_direct_transfer=True,
                owner_date_of_birth=date(1950, 1, 1),
                qcd_distribution_date=date(2026, 2, 1),
            ),
        ),
        qcd_annual_limit=108000.0,
    )


def test_export_rmd_accounts_csv_writes_audit_fields(tmp_path):
    path = export_rmd_accounts_csv(_result(), tmp_path / "rmd_accounts.csv")

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert row["projection_year"] == "2026"
    assert row["account_id"] == "IRA-1"
    assert float(row["calculated_rmd"]) == 10000.0
    assert float(row["qualified_qcd"]) == 6000.0
    assert float(row["account_remaining_rmd"]) == 0.0


def test_export_rmd_accounts_csv_requires_csv_extension(tmp_path):
    try:
        export_rmd_accounts_csv(_result(), tmp_path / "rmd_accounts.txt")
    except ValueError as exc:
        assert ".csv" in str(exc)
    else:
        raise AssertionError("non-csv export should be rejected")
