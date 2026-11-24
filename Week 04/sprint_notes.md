# Sprint 4 Notes

| | |
|---|---|
| **Sprint / dates** | Week 4, Fri 13 Nov to Thu 19 Nov 2026 |
| **Scrum Master** | Keren Oyem |
| **Team** | Keren Oyem (solo: Data Analyst and Data Scientist roles) |

## Sprint goal

Explain which products drive revenue, margin and volume, classify them, and characterise demand trends and seasonality.

## Selected tasks

| Code | Description | Role | Estimate (h) | Status |
|---|---|---|---|---|
| B1 | Product Performance Analysis | DA | `[fill]` | Done |
| B7 | ABC / Pareto Classification with XYZ | DA | `[fill]` | Done |
| B2 | Fast-Moving Product Identification (velocity) | DA/DS | `[fill]` | Done |
| B9 | Product Demand Trend Analysis | DA/DS | `[fill]` | Done |

Planned effort: about 60 h. Actual: `[fill]`.

## Daily stand-ups

| Date | Done | Next | Blockers |
|---|---|---|---|
| Fri 13 Nov | Sprint planning | Base dataset and B1 | `[fill]` |
| Sat 14 Nov | `[fill]` | `[fill]` | `[fill]` |
| Sun 15 Nov | `[fill]` | `[fill]` | `[fill]` |
| Mon 16 Nov | `[fill]` | `[fill]` | `[fill]` |
| Tue 17 Nov | `[fill]` | `[fill]` | `[fill]` |
| Wed 18 Nov | `[fill]` | `[fill]` | `[fill]` |

## Review

**Delivered**

- `04_product_performance.ipynb` and the helper module `src/product_analysis.py`
- `abc_xyz_classification.csv`, `product_velocity.csv` and the product-branch versions
- Demand trend, seasonality and growth tables; 12 charts
- Product insight brief (`reports/week04_product_insights.md`)

**Key results**

- 10 of 30 products generate 80% of revenue (81.5%); 12 generate 80% of margin. Volume per product is almost equal, so revenue differences come from price.
- Top product P015 Engine Block EB-600 brings 21.2% of revenue; top branch Chennai 20.4%; the same 10 products are the core in all six branches.
- All 30 products have steady demand (CV 0.14 to 0.19): ABC-XYZ gives AX 10, BX 7, CX 13.
- Total demand is slowly decreasing (p = 0.004, CAGR -0.8%; 2024 revenue -3.8%). 9 products decreasing, 2 increasing. Seasonal strength 0.56, peak July, weakest February.

**KPI changes:** baseline revenue INR 22,959.0 M, gross margin INR 4,950.0 M (21.6%), 18,033 delivered orders, average order value INR 1.27 M.

**Links:** notebook, CSV files and charts as listed in `week-04/README.md`.

## Retrospective

| Keep | Improve | Try |
|---|---|---|
| Reusable logic in `src/product_analysis.py` with the notebook calling it | Check the spread of the data before choosing classification cut-offs (all CV values were 0.14 to 0.19, so XYZ gave one class) | In Week 5, use days of stock cover rather than velocity class to judge slow stock |
| Reconciling the sales base to the order headers before analysis (all checks passed) | Do not report tercile counts (10 / 10 / 10) as a finding | Rank product-branch velocity within each branch, so branch size does not dominate |
| Computing chart takeaways from the data | Run the whole notebook top to bottom before writing the brief; numbers changed several statements in the first draft | Use the declining-product list (P019, P010, P001, ...) as the start of the Week 5 slow-stock review |

`[Edit this table to match your own reflections.]`

**Next Scrum Master:** Keren Oyem (Week 5, working solo).

## Carry-over

None planned. `[Add any unfinished item and the reason.]`

## Contribution tracker

| Member | Tasks | Commits | Pull requests | Stand-ups |
|---|---|---|---|---|
| Keren Oyem | B1, B7, B2, B9 (4 of 4) | `[fill]` | `[fill]` | `[fill]` |

## Submission

| Item | Value |
|---|---|
| Commit hash | `[fill]` |
| Git tag | `week-04` |
| Portal submission time | `[fill]` (deadline Thu 19 Nov 2026, 20:00 IST) |
