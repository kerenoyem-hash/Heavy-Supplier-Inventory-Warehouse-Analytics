# Week 02: Data Cleaning, Validation & Integrity Checks

**Project:** Heavy Supplier, Inventory & Warehouse Analytics · CadetX Virtual Work Experience
**Author:** Keren Oyem (Data Analyst)
**Sprint:** Fri 30 Oct – Thu 5 Nov 2026
**Catalogue tasks:** A2 Data Cleaning & Quality Improvement · A5 Data Validation & Consistency Checks · G4 Data Integrity & Error Detection

---

## 1. Overview

Week 1 profiled the 12 warehouse tables and listed the first data-quality concerns. Week 2 turns those concerns into evidence and decisions. The result is a **validated, reproducible clean data layer** that later weeks (star schema, KPIs, forecasting, dashboards) can trust.

**Data:** 12 tables in `warehouse.duckdb` (about 605,000 rows; Jan 2019 – Jan 2025; INR; GST 18% and 28%). The raw database is opened **read-only** and is never modified.

## 2. What was done

All six tasks are in one notebook, `notebooks/02_cleaning_validation.ipynb`. Each task has an explanation, a note on every code output and a summary.

| Task | Work | Result |
|---|---|---|
| 1. Type casting and standardisation | Capacity text → numeric sqft; dimensions split and volume (m³) calculated; postal codes → text; date and label review | Done |
| 2. Stock reconstruction | Opening + IN − OUT ± ADJUSTMENT compared with `running_balance` and `current_stock` | Ledger consistent for 180 / 180 pairs; differences flagged |
| 3. Financial reconciliation | Line arithmetic, GST, header vs lines, invoices vs payments, customer purchase value | Arithmetic clean; payment and customer-value exceptions flagged |
| 4. Integrity and business rules | Primary keys, 17 foreign keys, cancelled POs, delivery dates, customer regions | All foreign keys valid; reused invoice and payment IDs flagged |
| 5. Automation and export | Pytest suite, reusable `src/cleaning.py`, Parquet export | 12 Parquet files; tests run on every refresh |
| 6. Issue log | 28 issues, each with a decision: Fix · Flag · Accept · Exclude | `docs/dq_issue_log_v2.csv` |

## 3. Key findings

* **Structure is sound.** All 17 foreign keys resolve (0 orphans, 0 nulls). Header totals equal line totals (sales 20,000; purchase 24,000). GST is exactly 18% or 28%.
* **Missing `received_date` (2,370) is valid.** Every blank belongs to a cancelled purchase order.
* **Reused IDs.** `invoice_id` (197 surplus rows) and `payment_id` (202 surplus rows) appear on *different* records, not exact copies. 393 invoices are therefore ambiguous for payment matching.
* **Payments.** 52 invoices are overpaid and 67 invoices stored as `Paid` were only partly paid, so the stored `payment_status` cannot be trusted.
* **Customer value.** `customers.total_purchase_value` does not match transactions (stored ≈ 5% of recomputed).
* **Stock.** The ledger is internally consistent. `current_stock` equals the ledger balance for 166 / 180 pairs. All 2,454 adjustments are positive numbers, so gain vs loss is unknown. Stock inflow is about 18× outflow.
* **Cancelled orders.** 1,967 cancelled sales orders have no invoice, yet still carry a delivery date (a placeholder).
* **Regions.** 22 customers sit in regions with no local branch; other branches serve them.
* **Correction.** An early check reported 179 of 180 stock mismatches. That came from text-sorted `movement_id` and unsigned adjustments, not bad data.

## 4. Decisions adopted

1. The raw database is never modified.
2. **No row is deleted.** Problems are carried by flag columns: `is_cancelled`, `invoice_id_duplicated`, `payment_id_duplicated`, `current_above_max_flag`, `purchase_value_mismatch_flag`.
3. Use `payment_status_derived`, not the stored `payment_status`.
4. Use `recalc_purchase_value_with_gst`, not `total_purchase_value`.
5. Join invoices to orders on `so_id`, not `invoice_id`.
6. Treat the ledger as the stock source of truth.
7. Exclude cancelled orders from revenue, lead-time and order-to-delivery measures (via flags).

## 5. Open questions

| Question | Needed for |
|---|---|
| Direction (gain or loss) of ADJUSTMENT movements | Shrinkage analysis, Week 11 |
| Cause of the 52 overpayments | Receivables accuracy |
| Genuine `current_stock` differences (notebook section 2.4) | Stock health, Week 5 |

## 6. Deliverables

```
.
├── README.md
├── notebooks/
│   └── 02_cleaning_validation.ipynb     # Tasks 1–6
├── src/
│   ├── __init__.py
│   └── cleaning.py                      # raw -> cleaned tables -> Parquet
├── tests/
│   ├── conftest.py                      # read-only database fixture
│   └── test_data_quality.py             # automated checks
├── data/processed/                      # 12 cleaned Parquet files
├── docs/
│   └── dq_issue_log_v2.csv              # issue log with decisions
└── week-02/
    └── sprint_notes_week02.md
```

## 7. How to run

**Requirements:** Python 3.10+, `duckdb`, `pandas`, `pytest` (`openpyxl` optional, for the Excel issue log).

```bash
pip install duckdb pandas pytest openpyxl
```

Run from the folder that contains `warehouse.duckdb`:

```bash
# 1. Rebuild the cleaned layer from the raw database
python -m src.cleaning

# 2. Run the automated checks
python -m pytest tests -q

# Or both, stopping if the build fails
python -m src.cleaning && python -m pytest tests -q
```

To read the full analysis, open `notebooks/02_cleaning_validation.ipynb` and run it top to bottom.

Optional environment variables: `WAREHOUSE_DB` (database path) and `PROCESSED_DIR` (output folder).

## 8. Automated tests

* **Rule tests** assert zero exceptions: row counts, unexpected nulls, date types, label spellings, key uniqueness, foreign keys, finance arithmetic, business rules, stock consistency and the Parquet layer. A failure means a new data problem.
* **Known-issue tests** pin a documented problem to its recorded size (for example 197 surplus invoice IDs). They pass today and fail if the problem changes, forcing a review.

## 9. Cleaned data layer (`data/processed/`)

Every raw column is kept; changes are additions only.

| Table | Added or changed |
|---|---|
| `branches` | `warehouse_capacity_sqft` |
| `products` | `length_cm`, `width_cm`, `height_cm`, `volume_m3` |
| `customers`, `suppliers` | `pincode` as 6-character text; customers also get recomputed purchase value and a mismatch flag |
| `invoices` | `total_paid`, `payment_count`, `outstanding_balance`, `invoice_id_duplicated`, `payment_status_derived` |
| `payments` | `payment_id_duplicated` |
| `sales_orders_header` | `is_cancelled`, `days_to_deliver` |
| `purchase_orders_header` | `is_cancelled` |
| `inventory_master` | `current_above_max_flag` |
| other tables | unchanged (labels trimmed) |

## 10. Limitations

* The official *Fields Documentation* was not available, so field meanings (such as adjustment direction) are inferred from the data.
* The data appears synthetic (for example, strongly one-sided stock flows), so findings describe this dataset, not a real company.

## 11. Next step

**Week 3:** build the star schema, engineer features and publish baseline KPIs on top of this clean layer.
