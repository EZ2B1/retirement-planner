def calculate_federal_tax(taxable_income: float, brackets: list[dict]) -> float:
    tax = 0.0
    previous = 0.0
    for bracket in brackets:
        upper = bracket.get("upper")
        rate = bracket["rate"]
        if upper is None:
            tax += max(0.0, taxable_income - previous) * rate
            break
        taxable = max(0.0, min(taxable_income, upper) - previous)
        tax += taxable * rate
        if taxable_income <= upper:
            break
        previous = upper
    return round(tax, 2)
