# Week 5 Insight Brief: Inventory Health, Turnover & Ageing

| | |
|---|---|
| **Project** | Heavy Supplier, Inventory & Warehouse Analytics (CadetX) |
| **Prepared by** | Keren Oyem |
| **Sprint** | Week 5, Fri 20 Nov to Thu 26 Nov 2026 |
| **Catalogue tasks** | B3, B4, B5, B6, B8 |
| **Reference date** | 31 December 2024 |

## 1. Question addressed and data used

How healthy is the stock in each of the 180 product-branch pairs, how much capital is tied up in excess stock, how old is that stock, and why does it keep building up?

Stock was rebuilt from the stock ledger (opening stock + IN - OUT) and valued at the product unit cost. It was compared with the branch-level reorder, safety and maximum levels in the inventory master. Demand comes from delivered sales orders and purchasing from received purchase orders, all taken from the cleaned Week 2 data layer.

## 2. Key findings

**Finding 1: every pair is overstocked.** All 180 pairs are above their branch maximum and none is at or below its reorder point. Stock is 19,130,292 units worth INR 278.77 billion, of which INR 277.93 billion (99.70%) is above the maximum levels. The combined maximum levels total only 57,916 units, so stock is about 330 times what the maximum levels allow. The excess is spread evenly: each branch holds INR 44.09 to INR 47.31 billion of it (99.60% to 99.77% of that branch's stock). Four categories hold 90.10% of the excess: Engine (33.48%), Hydraulic (27.37%), Transmission (16.10%) and Undercarriage (13.15%).

**Finding 2: stock almost does not turn.** Inventory turnover in 2024 was 0.01 times a year, which is 32,334 days of inventory on hand (about 89 years). At the sales rate of the last 12 months (200,562 units) the excess would take 1,141 months (95 years) to sell. No pair is dead stock, because every pair still sells, but all 180 pairs hold more than 24 months of cover. The shortest cover is 757 months and the median is 1,153 months.

**Finding 3: most of the capital is old.** 82.72% of stock value (INR 230.60 billion, 15.82 million units) is older than 365 days. Only 4.26% (INR 11.87 billion) arrived in the last 90 days, 4.48% in 91 to 180 days and 8.54% in 181 to 365 days.

**Finding 4: the cause is the size of purchase lines, not the number of orders.** Stock coming in is 18.03 times stock going out. Purchase lines average 159.85 units against 10.50 for sales lines (15.23 times larger), while purchases have only 1.18 times as many lines as sales. On a log scale, about 94% of the gap comes from line size. The same ratio appears in the source documents (18.02), so the imbalance is in the purchase and sales records themselves.

**Finding 5: purchasing is still going on.** In the last 12 months, purchase orders for pairs already above maximum covered 3,657,914 units worth INR 50.83 billion before GST. That is 18.2 times the 200,562 units sold in the same period. Ten pairs account for INR 15.67 billion (30.8%) of it: Engine Block EB-600 (P015) in all six branches, and Transmission Assembly TA-800 (P014) in four.

## 3. Recommendations, expected impact and priority

| Recommendation | Expected impact | Priority |
|---|---|---|
| Freeze new purchase orders for all pairs above maximum, starting with P015 and P014. | Avoids up to INR 50.83 billion a year of purchasing (based on the last 12 months, before GST). | High |
| Set purchase quantities from demand and months of cover instead of lines of about 160 units. | Removes the main cause of the 18:1 imbalance (about 94% of the gap). | High |
| Review stock older than 365 days for supplier returns, resale or write-down, starting with Engine and Hydraulic. | Targets INR 230.60 billion of aged stock and 60.85% of the excess. Branch-to-branch transfers will not help because all six branches are overstocked. | Medium |
| Check the branch maximum and reorder levels (Week 10 recalculation). | Maximum levels total 57,916 units against 19.13 million on hand, so they do not control purchasing today. | Medium |
| Add stock-to-max and months-of-cover alerts to the risk monitoring rules (Week 11). | Stops the build-up from recurring unnoticed. | Low |

## 4. Limitations and assumptions

- **Ledger completeness.** The ledger holds about 8.9% fewer units than the documents (IN 20.40 million against 22.39 million, OUT 1.12 million against 1.23 million). Only 11,692 of 21,391 matched purchase orders and 9,716 of 17,871 matched sales orders agree exactly, and 1,098 ledger purchase IDs and 895 sales IDs are not in the live documents. Both sources give the same 18:1 ratio, so the conclusions hold, but true stock may be higher than shown. This is being investigated and is logged as a new issue (I29).
- **Adjustments excluded.** ADJUSTMENT movements (66,990 units, 0.33% of IN) are left out because their direction is unknown (issue I08).
- **Valuation.** Stock is valued at the standard unit cost, with FIFO used only for ageing. The average stock cost (INR 14,572 a unit) is broadly in line with recent purchase prices (INR 13,895 a unit).
- **Opening date.** Opening stock is assumed to be dated 1 January 2019. This does not change the share older than 365 days, provided the opening stock is older than that.
- **Stock source.** The ledger stock at 31 December 2024 is used, not the stored `current_stock` (issue I11). Movements after the reference date are excluded.
- **Data realism.** The figures are extreme (95 years of cover) and the data appears synthetic, so the results are for analysis practice and should not be read as real business performance.

## 5. Links to notebook, charts and outputs

- Notebook: `05_inventory_health.ipynb`
- Tables (`week-05/`): `turnover_doh.csv`, `stock_health_status.csv`, `inventory_ageing.csv`, `dead_stock_list.csv`, `slow_dead_classification.csv`, `week05_headline_metrics.csv`
- Charts (`reports/figures/`): `w05_inflow_outflow_by_year.png`, `w05_excess_by_branch.png`, `w05_ageing_profile.png`, `w05_doh_by_year.png`
