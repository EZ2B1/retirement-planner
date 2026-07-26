# Retirement Planner

Professional retirement-planning model and workbook generator supporting federal tax, Social Security taxation, RMDs, Roth conversions, Medicare IRMAA, ACA premium-tax-credit interactions, healthcare costs, portfolio projections, scenario comparison, and Excel workbook generation.

## Current scope

- Federal income-tax calculations
- Social Security claiming and taxation
- Pension and ordinary income
- Traditional and Roth IRA modeling
- Required Minimum Distributions
- Roth conversion optimization
- Medicare IRMAA analysis
- ACA premium-tax-credit analysis for a younger spouse
- Healthcare-cost projections
- Portfolio growth and withdrawals
- Asset-class assumptions and correlations
- Year-by-year taxes, cash flow, and net worth
- Excel, CSV, and report outputs

## Setup

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m pip install -e .
pytest
python scripts/build_workbook.py
```

Generated files belong in `outputs/`; approved release packages belong in `releases/`.
