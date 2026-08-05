"""Tests for the formula-driven workbook structure manifest."""

from retirement_planner.reporting.excel_builder import (
    REQUIRED_WORKSHEET_ORDER,
    RESTORED_REPORTING_SHEETS,
    create_workbook_shell,
    validate_sheet_structure,
)


def test_workbook_shell_uses_required_user_workflow_order() -> None:
    workbook = create_workbook_shell()

    assert tuple(workbook.sheetnames) == REQUIRED_WORKSHEET_ORDER
    assert validate_sheet_structure(workbook.sheetnames) == []


def test_manifest_contains_all_issue_1_reporting_sheets() -> None:
    assert RESTORED_REPORTING_SHEETS.issubset(set(REQUIRED_WORKSHEET_ORDER))


def test_validation_reports_missing_required_sheet() -> None:
    sheet_names = [
        name for name in REQUIRED_WORKSHEET_ORDER if name != "Scenario Comparison"
    ]

    errors = validate_sheet_structure(sheet_names)

    assert any("Scenario Comparison" in error for error in errors)


def test_validation_reports_misordered_required_sheets() -> None:
    sheet_names = list(REQUIRED_WORKSHEET_ORDER)
    sheet_names[0], sheet_names[1] = sheet_names[1], sheet_names[0]

    errors = validate_sheet_structure(sheet_names)

    assert "Required worksheets are not in the approved user-workflow order" in errors


def test_validation_allows_nonrequired_support_sheet_without_reordering() -> None:
    sheet_names = list(REQUIRED_WORKSHEET_ORDER)
    sheet_names.append("Temporary QA Notes")

    assert validate_sheet_structure(sheet_names) == []
