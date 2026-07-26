from retirement_planner.calculators.federal_tax import calculate_federal_tax

def test_progressive_tax():
    brackets=[{"upper":10000,"rate":0.10},{"upper":40000,"rate":0.20},{"upper":None,"rate":0.30}]
    assert calculate_federal_tax(50000,brackets)==10000.00
