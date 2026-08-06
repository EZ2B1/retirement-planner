# RMD and QCD Calculation and Compliance Engine

## Scope

This document records the implemented design for Issue #8, covering RMD-02 through RMD-06.

## First-RMD Timing

The engine supports both statutory first-RMD timing choices:

- Payment by December 31 of the first RMD year.
- Deferral to April 1 of the following calendar year.

When deferral is selected, the engine reports the two RMD deadlines falling in the following calendar year and presents a double-RMD warning.

## Account-Level Calculation Trail

Each retirement account records:

- Owner and account identifiers.
- Account type.
- Prior-year-end balance.
- Life-expectancy table selection.
- Divisor.
- Calculated RMD.
- QCD requested and qualified QCD.
- QCD applied toward the RMD.
- Other distributions taken.
- Remaining RMD obligation.
- Proposed rollover or Roth conversion amount.
- Ineligible rollover or conversion amount.
- Compliance violations.

The annual RMD calculation is the prior-year-end balance divided by the applicable divisor.

## Aggregation Controls

Aggregation is controlled by account type and owner:

- Traditional, SEP, and SIMPLE IRAs may be aggregated for the same owner.
- 403(b) contracts may be aggregated for the same owner.
- 401(k), 457(b), profit-sharing, and other employer-plan accounts remain separate obligations.
- Accounts owned by different individuals are never aggregated.

Compliance is evaluated at the legally permitted aggregation-group level and then reconciled to owner and household totals.

## QCD Controls

QCD processing enforces:

- Eligible IRA account types.
- Owner age of at least 70 1/2 on the distribution date.
- Direct payment to an eligible charity.
- Chronological processing of QCD requests.
- A per-owner annual QCD limit supplied from authoritative tax-year reference data.
- Application of qualified QCD amounts toward the remaining RMD.

Requests exceeding the annual limit are capped and flagged.

## Rollover and Roth-Conversion Controls

Current-year RMD amounts are not eligible for rollover or Roth conversion. The optimizer integration therefore:

1. Satisfies the applicable RMD obligation first.
2. Determines the excess eligible distribution remaining after RMD satisfaction.
3. Limits conversion recommendations to that excess.
4. Rejects strategies that attempt to convert RMD dollars or proceed while an RMD shortfall remains.

## Projection and Reporting Integration

The projection layer produces reconciled account, aggregation-group, owner, and household results. Reconciliation validation fails when calculated RMD, qualified QCD, distributions, or shortfall totals disagree across layers.

The reporting layer can generate:

- A separately named Excel validation candidate.
- An RMD Analysis worksheet.
- Audit and Validation worksheet outputs.
- An account-level CSV audit trail.

The validation-candidate process does not overwrite the approved baseline workbook.

## Verification

Automated tests cover first-RMD timing, double-RMD years, account calculations, legal and prohibited aggregation, QCD eligibility and limits, RMD-offset treatment, rollover and conversion blocking, projection reconciliation, optimizer safeguards, workbook output, and CSV audit exports.
