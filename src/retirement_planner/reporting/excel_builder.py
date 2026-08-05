"""Excel workbook structure and validation helpers.

This module defines the required user-facing worksheet order for the formula-driven
validation candidate. It deliberately does not modify or replace the approved base
workbook. Workbook generation and formula wiring will be added incrementally against
this manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from openpyxl import Workbook


@dataclass(frozen=True)
class WorksheetDefinition:
    """Metadata for a required worksheet."""

    name: str
    section: str
    required: bool = True


WORKSHEET_MANIFEST: tuple[WorksheetDefinition, ...] = (
    WorksheetDefinition("Cover", "Orientation and control"),
    WorksheetDefinition("Instructions", "Orientation and control"),
    WorksheetDefinition("Dashboard", "Orientation and control"),
    WorksheetDefinition("Scenario Manager", "Orientation and control"),
    WorksheetDefinition("Household Inputs", "Household and planning inputs"),
    WorksheetDefinition("Economic Assumptions", "Household and planning inputs"),
    WorksheetDefinition("Asset-Class Assumptions", "Household and planning inputs"),
    WorksheetDefinition("Tax Assumptions", "Household and planning inputs"),
    WorksheetDefinition("Social Security", "Household and planning inputs"),
    WorksheetDefinition("Pension and Other Income", "Household and planning inputs"),
    WorksheetDefinition("Account Balances", "Household and planning inputs"),
    WorksheetDefinition("Spending and Cash Needs", "Household and planning inputs"),
    WorksheetDefinition("Annual Projection", "Core annual calculations"),
    WorksheetDefinition("Lifetime Cash Flow", "Core annual calculations"),
    WorksheetDefinition("Federal Tax Calculation", "Core annual calculations"),
    WorksheetDefinition("RMD Analysis", "Core annual calculations"),
    WorksheetDefinition("Medicare IRMAA", "Core annual calculations"),
    WorksheetDefinition("ACA Analysis", "Core annual calculations"),
    WorksheetDefinition("Healthcare Planning", "Core annual calculations"),
    WorksheetDefinition("Roth Conversion Optimizer", "Strategy and optimization"),
    WorksheetDefinition("Tax Optimizer", "Strategy and optimization"),
    WorksheetDefinition("Withdrawal Strategy", "Strategy and optimization"),
    WorksheetDefinition("Social Security Claiming", "Strategy and optimization"),
    WorksheetDefinition("Charitable Planning", "Strategy and optimization"),
    WorksheetDefinition("Estate Planning", "Strategy and optimization"),
    WorksheetDefinition("Scenario Comparison", "Comparison and risk analysis"),
    WorksheetDefinition("Sensitivity Analysis", "Comparison and risk analysis"),
    WorksheetDefinition("Monte Carlo Analysis", "Comparison and risk analysis"),
    WorksheetDefinition("Optimizer Results", "Comparison and risk analysis"),
    WorksheetDefinition("Recommendations", "Decision reports"),
    WorksheetDefinition("Advisor Report", "Decision reports"),
    WorksheetDefinition("Audit", "Validation and support"),
    WorksheetDefinition("Validation", "Validation and support"),
    WorksheetDefinition("Data Tables", "Validation and support"),
    WorksheetDefinition("Documentation", "Validation and support"),
    WorksheetDefinition("Change Log", "Validation and support"),
)

REQUIRED_WORKSHEET_ORDER: tuple[str, ...] = tuple(
    definition.name for definition in WORKSHEET_MANIFEST if definition.required
)

RESTORED_REPORTING_SHEETS: frozenset[str] = frozenset(
    {
        "Scenario Comparison",
        "Roth Conversion Optimizer",
        "Tax Optimizer",
        "Lifetime Cash Flow",
        "Sensitivity Analysis",
        "Monte Carlo Analysis",
        "ACA Analysis",
        "Medicare IRMAA",
        "Charitable Planning",
        "Estate Planning",
        "Healthcare Planning",
        "RMD Analysis",
        "Audit",
        "Validation",
        "Advisor Report",
        "Recommendations",
    }
)


def create_workbook_shell() -> Workbook:
    """Create an empty workbook with sheets in the approved user-workflow order.

    The returned workbook is a structural shell only. It contains no financial
    formulas and must not be represented as a validated retirement-planning model.
    """

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    for definition in WORKSHEET_MANIFEST:
        workbook.create_sheet(definition.name)

    return workbook


def validate_sheet_structure(sheet_names: Sequence[str] | Iterable[str]) -> list[str]:
    """Return human-readable errors for missing, duplicate, or misordered sheets."""

    names = list(sheet_names)
    errors: list[str] = []

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append(f"Duplicate worksheets: {', '.join(duplicates)}")

    missing = [name for name in REQUIRED_WORKSHEET_ORDER if name not in names]
    if missing:
        errors.append(f"Missing required worksheets: {', '.join(missing)}")

    present_required = [name for name in names if name in REQUIRED_WORKSHEET_ORDER]
    expected_present_order = [
        name for name in REQUIRED_WORKSHEET_ORDER if name in present_required
    ]
    if present_required != expected_present_order:
        errors.append("Required worksheets are not in the approved user-workflow order")

    return errors
