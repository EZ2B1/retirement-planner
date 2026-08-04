# Git commands — v3.2 formula-driven base

```bash
git clone https://github.com/EZ2B1/retirement-planner.git
cd retirement-planner
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch feature/v3.2-formula-driven-base

# Extract the implementation ZIP over the repository root, then review:
git status
git diff --stat
git add scripts src config data tests docs .github README.md CHANGELOG.md GIT_COMMANDS_V3.2.md
git diff --cached --stat
git commit -m "Implement v3.2 formula-driven workbook generator"
git push -u origin feature/v3.2-formula-driven-base

python -m pip install -r requirements.txt
python -m pip install -e .
pytest
python scripts/build_workbook.py

# After opening, recalculating, and validating in Microsoft Excel:
mkdir -p workbooks/reference
cp outputs/excel/Retirement_Planner_v3.2_Formula_Driven_Base.xlsx workbooks/reference/
git add workbooks/reference/Retirement_Planner_v3.2_Formula_Driven_Base.xlsx
git commit -m "Add validated v3.2 formula-driven reference workbook"
git push
```

Open a pull request from `feature/v3.2-formula-driven-base` into `develop`. Merge into `main` only after tax-year review, CI success, and workbook approval.
