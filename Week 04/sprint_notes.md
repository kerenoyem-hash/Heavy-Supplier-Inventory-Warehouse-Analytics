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
| B1 | Product Performance Analysis | DA | 18 | Done |
| B7 | ABC / Pareto Classification with XYZ | DA | 14 | Done |
| B2 | Fast-Moving Product Identification (velocity) | DA/DS | 12 | Done |
| B9 | Product Demand Trend Analysis | DA/DS | 16 | Done |

Planned effort: about 60 h. Actual: about 60 h `[adjust if your real hours differ]`.

## Daily stand-ups

| Date | Done | Next | Blockers |
|---|---|---|---|
| Fri 13 Nov | Sprint planning; set up helper module and sales base dataset | B1 | None |
| Sat 14 Nov | B1: performance by product, category, brand, machine type, branch, year; Pareto charts | B7 | None |
| Sun 15 Nov | B7: ABC and XYZ; exported abc_xyz_classification.csv | B2 | XYZ cut-offs gave one class (all X) |
| Mon 16 Nov | B2: velocity scores; exported product_velocity.csv | B9 | None |
| Tue 17 Nov | B9: STL, Mann-Kendall, seasonality, growth | Insight brief | None |
| Wed 18 Nov | Insight brief, sprint review, retrospective | Notes, submission | None |

## Review

**Delivered:** notebook and helper module; abc_xyz_classification.csv, product_velocity.csv and product-branch versions; trend, seasonality and growth tables; 12 charts; insight brief.

**Key results**
- 10 of 30 products generate 80% of revenue (81.5%); 12 generate 80% of margin. Volume per product is almost equal, so revenue differences come from price.
- Top product P015 Engine Block EB-600: 21.2% of revenue; top branch Chennai: 20.4%; same 10 core products in all six branches.
- All 30 products steady (CV 0.14 to 0.19): AX 10, BX 7, CX 13.
- Total demand slowly decreasing (p = 0.004, CAGR -0.8%; 2024 revenue -3.8%). 9 products decreasing, 2 increasing. Seasonal strength 0.56, peak July, weakest February.

**KPI changes:** revenue INR 22,959.0 M, gross margin INR 4,950.0 M (21.6%), 18,033 delivered orders, AOV INR 1.27 M.

## Retrospective

| Keep | Improve | Try |
|---|---|---|
| Reusable logic in the helper module | Check data spread before choosing cut-offs | Use days of stock cover in Week 5 |
| Reconciling the base to headers first | Do not report tercile counts as findings | Rank velocity within each branch |
| Chart takeaways computed from data | Run the full notebook before writing the brief | Start Week 5 with the declining-product list |

**Next Scrum Master:** Keren Oyem (Week 5, working solo).

## Carry-over

None planned.

## Contribution tracker

| Member | Tasks | Commits | Pull requests | Stand-ups |
|---|---|---|---|---|
| Keren Oyem | B1, B7, B2, B9 (4 of 4) | [git count] | [number] | 6 of 6 |

