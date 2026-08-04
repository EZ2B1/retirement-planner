# Reporting Restoration Plan

Tracks GitHub Issue #1: Restore reporting and optimization worksheets in the Formula-Driven Base workbook.

## Baseline and deliverable

- Protected baseline: `Retirement_Planner_v3.2_Formula_Driven_Base.xlsx`
- Reporting reference: `Retirement_Planner_v3.1_RC1.xlsx`, or the latest validated release-candidate equivalent
- New deliverable: a separately named validation candidate derived from the v3.2 formula-driven base
- The baseline workbook, legacy Python programs, and approved documentation remain unchanged until the validation candidate is approved.

## Implementation phases

### Phase 1 — Inventory and mapping

1. Record every worksheet in both source workbooks.
2. Map each reference worksheet's inputs, formulas, named ranges, tables, charts, validations, print settings, and external links.
3. Classify each worksheet as calculation, strategy, report, audit, support, or obsolete.
4. Document every dependency on v3.1 cell addresses that must be remapped to v3.2 formulas or named outputs.

### Phase 2 — Structural restoration

1. Create the missing worksheets in the approved user-workflow order.
2. Transfer layout, labels, chart definitions, print settings, and formatting without importing stale hard-coded values.
3. Replace fragile cross-sheet cell addresses with documented named ranges or structured references where practical.
4. Add workbook version, calculation version, tax year, and validation status to the Cover and Dashboard.

### Phase 3 — Formula integration

1. Connect each restored report to the v3.2 formula-driven calculation model.
2. Rebuild scenario selection and comparison controls.
3. Reconnect Roth-conversion, tax, withdrawal, Social Security, and other strategy outputs to annual calculations.
4. Reconcile ACA and IRMAA calculations to their applicable MAGI definitions.
5. Enforce the rule that RMD amounts are neither Roth conversions nor eligible rollover amounts.

### Phase 4 — Analysis and reporting

1. Restore Lifetime Cash Flow and account-balance reconciliations.
2. Restore Sensitivity Analysis and Monte Carlo result presentation.
3. Restore charitable, estate, and healthcare planning reports.
4. Generate Recommendations and Advisor Report exclusively from selected-scenario live values.

### Phase 5 — Audit and validation

The candidate must automatically test:

- required sheets and approved sheet order;
- broken formulas and Excel error values;
- external workbook links;
- undefined or duplicate named ranges;
- invalid or missing required inputs;
- annual cash-flow reconciliation;
- account roll-forward reconciliation;
- tax-calculation reconciliation;
- ACA and IRMAA MAGI reconciliation;
- RMD calculation and rollover restrictions;
- scenario and optimizer result reconciliation;
- report values changing when relevant assumptions change.

### Phase 6 — Release candidate

1. Save the workbook under a new validation-candidate name.
2. Run automated structure and regression tests.
3. Complete a manual Excel review of formulas, charts, print areas, protection, and user navigation.
4. Record test evidence and unresolved limitations.
5. Do not replace the protected baseline until explicit validation and approval are recorded.

## Definition of done

The reporting restoration is complete only when all Issue #1 acceptance criteria pass, the workbook contains no unexplained hard-coded report outputs, and the validation candidate is explicitly approved for promotion.
