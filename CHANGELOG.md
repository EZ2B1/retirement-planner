# Changelog

## [Unreleased]

### Added

- Added date-of-birth-driven RMD applicable-age rules with versioned source-year selection and verified provenance metadata.
- Added first-RMD timing comparisons for December 31 versus April 1, including double-RMD calendar-year warnings.
- Added account-level RMD calculation and compliance trails with prior-year balances, life-expectancy tables, divisors, distributions, QCDs, and shortfalls.
- Added legal aggregation controls for IRAs and 403(b) contracts while preserving plan-by-plan employer-account compliance.
- Added QCD eligibility, direct-transfer, chronological ordering, annual-limit, and RMD-offset controls.
- Added safeguards preventing current-year RMD amounts from being rolled over or converted to Roth.
- Added owner and household projection reconciliation, RMD-aware optimizer controls, Excel validation-candidate reporting, and CSV audit exports.
- Added automated tests for RMD/QCD boundaries, compliance, reconciliation, optimizer integration, and reporting output.
- Added the repaired `Retirement_Planner_v3.1_RC2.xlsx` baseline workbook.
- Added RC2 workbook-integrity documentation.
- Added repository setup guides in DOCX and PDF.
- Added initial-population instructions.
- Initial modular repository structure.
- Workbook generator scaffold.
- Tax, RMD, IRMAA, ACA, Social Security, and Roth conversion modules.
- Scenario configuration and test framework.

### Documentation

- Added `docs/methodology/RMD_QCD_COMPLIANCE_ENGINE.md` describing RMD-02 through RMD-06 implementation, controls, integration, and verification.
