# Sprint Notes: Week 05

| | |
|---|---|
| **Sprint** | Week 5, Fri 20 Nov to Thu 26 Nov 2026 (submitted late) |
| **Scrum Master** | Keren Oyem (solo sprint; the plan listed Thomars, but the work was done alone) |
| **Team** | Keren Oyem (Data Analyst / Data Scientist) |
| **Reference date** | 31 December 2024 |

## Sprint goal

Quantify inventory health for every product-branch pair, the capital tied up in excess stock, and the stock that is old or not moving, and explain why stock keeps building up.

## Selected tasks

| Code | Task | Role | Status |
|---|---|---|---|
| B4 | Inventory Turnover Analysis | DA | Done |
| B5 | Stock Health Assessment | DA | Done |
| B8 | Overstock & Understock Detection | DA | Done |
| B6 | Inventory Aging Analysis (FIFO) | DS | Done |
| B3 | Slow-Moving & Dead Stock Identification | DA/DS | Done |
| (plan, Tue) | Inflow vs outflow root-cause analysis | DA/DS | Done |

Completion: 5 of 5 catalogue tasks closed (100%). Cumulative target for the plan: 16 of 59 (27%), subject to Week 4 being completed.

## Daily stand-ups (solo, reconstructed from the work log; edit if dates differ)

| Date | Done | Next | Blockers |
|---|---|---|---|
| Mon 23 Nov | Sprint planned; the Week 5 plan was compressed into a 4-day solo schedule | Build the notebook | Week 4 not finished, so velocity is computed directly from sales lines |
| Wed 25 Nov | `05_inventory_health.ipynb` built (turnover, stock health, ageing, dead stock, root cause) and tested on a synthetic copy of the tables | Run on real data | None |
| Sat 28 Nov | Notebook run on real data with no errors; results checked; conclusions written; insight brief written | Sprint notes, README, repo push, submission | Deadline (Thu 26 Nov, 20:00 IST) already passed |

## Review: what was delivered

| Deliverable | Where |
|---|---|
| Inventory health notebook | `notebooks/05_inventory_health.ipynb` |
| Turnover and DOH tables | `week-05/turnover_doh.csv` |
| Stock health status of all 180 pairs | `week-05/stock_health_status.csv` |
| FIFO ageing buckets per pair | `week-05/inventory_ageing.csv` |
| Dead-stock list and full slow/dead classification | `week-05/dead_stock_list.csv`, `week-05/slow_dead_classification.csv` |
| Headline metrics | `week-05/week05_headline_metrics.csv` |
| Charts | `reports/figures/w05_*.png` |
| Insight brief | `reports/week05_inventory_insights.docx` (and `.md`) |

### Key results

| Measure | Value |
|---|---|
| Pairs in Overstock | 180 of 180; none at or below reorder point |
| Total stock value (at unit cost) | INR 278.77 billion (19,130,292 units) |
| Excess above max levels | INR 277.93 billion (99.70%) |
| Inventory turnover 2024 / DOH | 0.01 times a year / 32,334 days |
| Stock older than 365 days | 82.72% of value (INR 230.60 billion) |
| Dead stock (no sales in 12 months) | 0 pairs; all 180 have more than 24 months of cover |
| Median months of cover | 1,153 (minimum 757) |
| IN : OUT ratio | 18.03 |
| Purchase vs sales units per line | 159.85 vs 10.50 (15.23 times); lines ratio 1.18 |
| Months to sell the excess | 1,141 (95 years) |
| Purchase orders in last 12 months on overstocked pairs | INR 50.83 billion before GST (3,657,914 units) |

### Assumptions (Definition of Done)

- Stock rebuilt from the ledger (opening + IN - OUT) as of 31 Dec 2024; `current_stock` is not used (issue I11).
- ADJUSTMENT movements excluded (issue I08): 66,990 units, 0.33% of IN.
- Valuation at standard `unit_cost`; FIFO is used for ageing only.
- COGS from delivered sales; cancelled orders excluded.
- Opening stock assumed dated 1 Jan 2019.
- Branch-level reorder, safety and max levels from `inventory_master`.

## Retrospective

| Keep | Improve | Try |
|---|---|---|
| Testing the notebook on a synthetic copy of the tables before running on real data | Do not write expected numbers into "Reading the output" notes before seeing the results (one note about opening stock was wrong) | Start each sprint earlier so the Thursday deadline is met |
| Built-in checks (`assert`) that the yearly path and FIFO layers reconcile to the Section 1 position | Check document-to-ledger reconciliation before calling the ledger a complete record | Finish the previous sprint before starting the next |
| Generating headline numbers live in one table | | Ask the coordinator about the purchasing rule and adjustment direction |

## Carry-over

| Item | Reason |
|---|---|
| Week 4 (B1, B2, B7, B9) | Not finished; Week 4 deadline passed on Thu 19 Nov |
| Ledger completeness check (new issue I29) | The ledger holds about 8.9% fewer units than the purchase and sales documents, and only about 55% of orders match exactly. Both sources give the same 18:1 ratio, so the conclusions hold. The cause is still to be investigated |
| Pull request review | Solo sprint, so no second member could review |

## Contribution tracker

| Member | Tasks | Commits | Pull requests | Stand-ups |
|---|---|---|---|---|
| Keren Oyem | B3, B4, B5, B6, B8, root-cause analysis, insight brief | [fill in] | [fill in] | 3 (reconstructed) |

## Submission

| Item | Value |
|---|---|
| Commit hash | [fill in] |
| Tag | `week-05` |
| Portal submission time | [fill in] (late; deadline was Thu 26 Nov 2026, 20:00 IST) |
