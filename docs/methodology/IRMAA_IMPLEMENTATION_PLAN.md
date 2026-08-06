# Medicare IRMAA Enhancement Implementation Plan

Source: `Retirement_Planner_Potential_Improvements_Register_v1.2.pdf`.

## Register-label reconciliation

Two v1.2 source variants use different labels for IRMAA-14 and IRMAA-15. To avoid losing either requirement, the implementation adopts the functional superset:

- IRMAA-14A: annual strategy output.
- IRMAA-14B: reference-data governance.
- IRMAA-15A: source provenance.
- IRMAA-15B: annual decision and stewardship record.

This preserves every requirement while making the numbering discrepancy explicit and auditable.

## Group 1 — Reference-data foundation

IRMAA-03, IRMAA-14B, and IRMAA-15A establish annual, filing-status-specific threshold and premium tables with exact boundary metadata, premium-year and income-year labels, official citations, revision dates, retrieval dates, and verification status.

Status: Implemented. Pending CI verification.

## Group 2 — Calculation and household engine

IRMAA-01, IRMAA-02, IRMAA-04, IRMAA-05, IRMAA-06, IRMAA-10, and IRMAA-11 cover lookback mapping, independent IRMAA MAGI, beneficiary-level costs, component separation, threshold distance, source diagnostics, and survivor transitions.

Status: Implemented. Pending CI verification.

## Group 3 — Strategy and optimizer integration

IRMAA-07, IRMAA-08, IRMAA-09, and IRMAA-14A add tier guardrails, planning buffers, deliberate threshold-crossing analysis, combined marginal-cost evaluation, and annual strategy output rather than treating IRMAA as an automatic prohibition.

Status: Implemented. Pending CI verification.

## Group 4 — Operational stewardship

IRMAA-12, IRMAA-13, and IRMAA-15B add SSA-44 screening, amended-return or corrected-tax-data tracking, evidence controls, workflow status, source review, and an auditable annual decision record.

Status: Implemented. Pending CI verification.

## Group 5 — Projection and reporting integration

The implementation includes annual projection records, validation-candidate workbook output, Medicare IRMAA, Audit, Validation, Advisor Report, Recommendations, and household-level CSV audit output.

Status: Implemented. Pending CI verification.

## Baseline protection

All workbook outputs are written as separate validation candidates. The approved base workbook is not overwritten or renamed.

## Completion gate

The enhancement group is eligible for closure only after:

1. The complete automated test suite passes in GitHub Actions.
2. Temporary CI scheduling is removed.
3. Issues #10 through #14 are closed as completed.
4. Issue #9 receives a final implementation summary.
5. The user explicitly approves the completed Medicare IRMAA enhancement group.
