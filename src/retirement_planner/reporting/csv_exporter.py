"""CSV output generation for retirement-planner results."""

from __future__ import annotations

import csv
from pathlib import Path

from retirement_planner.models.results import RmdAnnualProjectionResult


def export_rmd_accounts_csv(
    result: RmdAnnualProjectionResult,
    output_path: str | Path,
) -> Path:
    """Export the account-level RMD/QCD audit trail to CSV."""

    result.validate_reconciliation()
    path = Path(output_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("RMD account export must use the .csv extension")
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "projection_year", "owner_id", "account_id", "account_type",
        "aggregation_group", "prior_year_end_balance", "life_expectancy_table",
        "divisor", "calculated_rmd", "qcd_requested", "qualified_qcd",
        "qcd_applied_to_rmd", "distributions_taken", "account_remaining_rmd",
        "rollover_or_conversion_amount", "ineligible_rollover_or_conversion",
        "violations",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for account in result.account_results:
            writer.writerow(
                {
                    "projection_year": result.projection_year,
                    "owner_id": account.owner_id,
                    "account_id": account.account_id,
                    "account_type": account.account_type,
                    "aggregation_group": account.aggregation_group,
                    "prior_year_end_balance": account.prior_year_end_balance,
                    "life_expectancy_table": account.life_expectancy_table,
                    "divisor": account.divisor,
                    "calculated_rmd": account.calculated_rmd,
                    "qcd_requested": account.qcd_requested,
                    "qualified_qcd": account.qualified_qcd,
                    "qcd_applied_to_rmd": account.qcd_applied_to_rmd,
                    "distributions_taken": account.distributions_taken,
                    "account_remaining_rmd": account.account_remaining_rmd,
                    "rollover_or_conversion_amount": account.rollover_or_conversion_amount,
                    "ineligible_rollover_or_conversion": account.ineligible_rollover_or_conversion,
                    "violations": "; ".join(account.violations),
                }
            )
    return path
