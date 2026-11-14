# Sprint Notes: Week 03

| Field | Detail |
|---|---|
| **Sprint** | Week 3 |
| **Dates** | Fri 6 Nov - Thu 12 Nov 2026 (Days 15-21) |
| **Scrum Master** | Timothy (per rotation plan); sprint run solo by Keren Oyem |
| **Phase** | Phase 1: Foundation & Exploration (final week) |
| **Project** | Heavy Supplier, Inventory & Warehouse Analytics |

## Team

| Member | Role | This sprint |
|---|---|---|
| Keren Oyem | Data Analyst / Data Scientist | Worked alone and owned every task, covering both the analyst and the data scientist work |
| Thomars | Data Scientist | Not involved this sprint |
| Timothy | Data Analyst | Not involved this sprint |

## Sprint goal

Integrate the clean tables into an analytical star schema, engineer reusable features, finish the data dictionary and publish baseline KPI values.

## Selected tasks

| Code | Task | Role performed | Estimate (h) | Status |
|---|---|---|---:|---|
| A3 | Data Integration & Dataset Merging (star schema) | DA | [fill in] | Done |
| A4 | Feature Engineering for Analytics | DS | [fill in] | Done |
| A6 | Data Dictionary & Documentation | DA | [fill in] | Done |
| n/a | Baseline KPIs and Phase 1 summary | DA | [fill in] | Done |

Planned effort: about 60 h (one member, about 20 h per week in the plan; the whole scope was completed by one person).

## Daily stand-ups

The Done / Next entries follow the sprint plan. **Edit them to match what you actually did each day and add any blockers.**

| Date | Done | Next | Blockers |
|---|---|---|---|
| Fri 6 Nov | Sprint 3 planning | Star schema | [fill in] |
| Sat 7 Nov | Star schema design | Build and validate schema | [fill in] |
| Sun 8 Nov | [fill in] | Feature engineering | [fill in] |
| Mon 9 Nov | [fill in] | Features, data dictionary | [fill in] |
| Tue 10 Nov | [fill in] | Data dictionary, baseline KPIs | [fill in] |
| Wed 11 Nov | [fill in] | Phase 1 summary, review and retro | [fill in] |
| Thu 12 Nov | [fill in] | Sprint notes, README, tag, submit | [fill in] |

## Review

**What was delivered**

- **A3 Star schema:** `sql/schema.sql` builds 5 dimensions and 4 facts in schema `star`; `sql/validate_star.sql` and `03_star_schema.ipynb` reconcile each fact to its source (row counts, totals, grain, foreign keys). All checks passed.
- **A4 Features:** `src/features.py` builds 8 feature tables in schema `feat` (supplier delay and on-time flag, order-to-delivery days, days-to-pay, credit utilisation, monthly demand with lags, demand variability and demand class). Every column is described. All checks passed.
- **A6 Data dictionary:** `docs/data_dictionary.xlsx` and `.docx` cover every column of the raw, clean, star and feature layers (29 tables), with measured values, null counts and quality notes.
- **Baseline KPIs:** `docs/kpi_tracker.csv` and `.xlsx` hold 48 KPIs for 2019-2024 and the latest year; `reports/phase1_summary.docx` summarises them.

**Key results (baseline)**

| Result | Value |
|---|---|
| Delivered revenue 2024 (before GST) | INR 367.8 crore (5.0% below 2019) |
| Gross margin | 21.6%, steady |
| Collection rate | 79.7% |
| Supplier on-time delivery | 84.9% |
| Receipts-to-issues ratio | 18.0 to 1 |
| Closing inventory value 2024 | INR 27,877 crore, 99.7% above maximum stock level |
| Inventory turnover 2024 | 0.011 times a year |

**KPI changes:** this sprint establishes the baseline, so there is no earlier value to compare with.

**Links:** `week-03/README.md`, `docs/kpi_tracker.xlsx`, `docs/data_dictionary.docx`, `reports/phase1_summary.docx`

## Retrospective

| Keep | Improve | Try |
|---|---|---|
| Validation after every build step (row counts, totals, grain, keys) that stops the notebook if a check fails | Confirm dates and sprint capacity at the start of the week, since one person carries all tasks | Start Week 4 from `feat_demand_variability` and `fact_sales_line` instead of rebuilding measures |
| Description of every table and column stored in the database, reused for the dictionary | Reconcile inferred field definitions with the official Fields Documentation once it arrives | Ask the coordinator about stock adjustment direction early, before the Week 11 shrinkage work |
| Flag columns instead of deleting rows | Record real stand-up notes and hours day by day | Keep the KPI tracker as the single source for later reports |

**Next Scrum Master:** Keren Oyem (Week 4).

## Definition of done

- [x] Each fact table reconciles to source row counts and totals
- [ ] Phase 1 checkpoint: foundation signed off before analytics begins
- [ ] All 3 catalogue tasks marked complete in `sprint_review.docx`
- [ ] Sprint notes and README week entry pushed
- [ ] Git tag `week-03` pushed
- [ ] Link submitted in the portal

## Carry-over

None. A3, A4 and A6 are complete.

Open items for later weeks (not sprint carry-over): direction of stock adjustments; cause of 52 overpaid invoices; 14 product-branch pairs where recorded and ledger stock differ; reconciliation of inferred field definitions with the Fields Documentation.

## Contribution tracker

| Member | Tasks | Commits | Pull requests | Stand-ups attended |
|---|---:|---:|---:|---:|
| Keren Oyem | 4 (A3, A4, A6, baseline KPIs) | [fill in] | [fill in] | [fill in] |
| Thomars | 0 | 0 | 0 | 0 |
| Timothy | 0 | 0 | 0 | 0 |

## Submission

| Item | Detail |
|---|---|
| Commit hash | [fill in] |
| Tag | `week-03` |
| Portal submission time | [fill in] |
