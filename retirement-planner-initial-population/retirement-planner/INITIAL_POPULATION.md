# Initial Repository Population

This package is ready to be copied into an empty, locally cloned GitHub
repository.

## Included baseline assets

- Modular Python source scaffold
- Automated test and validation structure
- Workbook and system specifications
- Reference household scenario
- `Retirement_Planner_v3.1_RC2.xlsx`
- GitHub Repository Setup Guide in DOCX and PDF
- RC2 workbook-integrity note

## First commit

Recommended commit:

```bash
git add .
git commit -m "Initialize Retirement Planner repository with v3.1 RC2 baseline"
git push -u origin main
```

## Development branch

```bash
git checkout -b develop
git push -u origin develop
```

## Important

The reference workbook is intentionally committed because it establishes the
approved baseline for the Version 3.1 design review. Generated workbooks should
continue to be written to `outputs/`, which remains ignored by Git.
