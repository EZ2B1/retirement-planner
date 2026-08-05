# Workbook Specification

## Workbook governance

`Retirement_Planner_v3.2_Formula_Driven_Base.xlsx` is the validated calculation foundation. Reporting restoration must be performed in a new validation candidate. The approved base workbook, existing Python programs, and existing documentation must not be overwritten or renamed during this work.

The workbook is intended for annual use to compare retirement strategies and evaluate each strategy's benefits, costs, tradeoffs, and long-term consequences.

## Required worksheet order

The worksheet order follows the user's natural workflow: orientation, data entry, calculations, strategy design, comparison, specialized planning, reporting, and quality control.

### 1. Orientation and control

1. Cover
2. Instructions
3. Dashboard
4. Scenario Manager

### 2. Household and planning inputs

5. Household Inputs
6. Economic Assumptions
7. Asset-Class Assumptions
8. Tax Assumptions
9. Social Security
10. Pension and Other Income
11. Account Balances
12. Spending and Cash Needs

### 3. Core annual calculations

13. Annual Projection
14. Lifetime Cash Flow
15. Federal Tax Calculation
16. RMD Analysis
17. Medicare IRMAA
18. ACA Analysis
19. Healthcare Planning

### 4. Strategy and optimization

20. Roth Conversion Optimizer
21. Tax Optimizer
22. Withdrawal Strategy
23. Social Security Claiming
24. Charitable Planning
25. Estate Planning

### 5. Comparison and risk analysis

26. Scenario Comparison
27. Sensitivity Analysis
28. Monte Carlo Analysis
29. Optimizer Results

### 6. Decision reports

30. Recommendations
31. Advisor Report

### 7. Validation and support

32. Audit
33. Validation
34. Data Tables
35. Documentation
36. Change Log

## Restored reporting requirements

The validation candidate must include and connect these previously missing capabilities:

- Scenario Comparison
- Roth Conversion Optimizer
- Tax Optimizer
- Lifetime Cash Flow
- Sensitivity Analysis
- Monte Carlo Analysis
- ACA Analysis
- Medicare IRMAA Analysis
- Charitable Planning
- Estate Planning
- Healthcare Planning
- RMD Analysis
- Audit
- Validation
- Advisor Report
- Recommendations

Every restored sheet must use live formula-driven assumptions and calculation outputs. Report values must not be hard-coded.

## Calculation and reconciliation rules

- Core assumption changes must flow through every applicable report, optimizer, and recommendation.
- Scenario, Roth-conversion, and tax-optimization outputs must reconcile to detailed annual calculations.
- ACA and IRMAA results must reconcile to the applicable MAGI calculations.
- Lifetime cash flow and net worth must reconcile to annual account balances and transaction flows.
- RMD amounts must not be classified as Roth conversions and must not be treated as eligible rollover amounts.
- Advisor Report and Recommendations must summarize the selected scenario using live workbook values.
- Audit and Validation must identify broken formulas, external links, invalid inputs, missing sheets, and reconciliation differences.

## Workbook standards

- Distinguish user inputs, formulas, calculated outputs, and warnings visually.
- Protect formula ranges while leaving intended inputs editable.
- Use documented named ranges or structured references for cross-sheet dependencies.
- Avoid unexplained hard-coded tax, benefit, healthcare, or market values.
- Record the source and effective year for tax and benefit assumptions.
- Include workbook version, calculation version, tax year, and validation status on the Cover or Dashboard.
- Do not label a workbook production-ready until all acceptance tests pass and the validation candidate is explicitly approved.
