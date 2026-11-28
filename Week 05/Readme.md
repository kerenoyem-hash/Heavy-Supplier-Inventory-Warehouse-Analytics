
# Heavy Supplier, Inventory & Warehouse Analytics

CadetX Virtual Work Experience (Data Analytics & Data Science). A 12-week analytics programme on warehouse, supplier, sales and finance data for a heavy-machinery spare-parts business with six branches in India.

**Author:** Keren Oyem (Data Analyst / Data Scientist)
**Plan window:** 23 October 2026 to 21 January 2027

## Business problem

Warehouses handling heavy-machinery spare parts run reactively, with excess inventory, stockouts, poor space use and slow decisions. The goal is a unified analytics framework that uses historical warehouse, supplier, sales and finance data to analyse, predict and optimise product movement, inventory levels and warehouse performance.

## Dataset

12 tables, about 605,000 rows, transactions Jan 2019 to Jan 2025: 6 branches, 30 products, 8 suppliers, 500 customers, plus sales orders, purchase orders, invoices, payments and a stock ledger. Currency is INR (GST 18% and 28%). Reference date for as-of measures is 31 December 2024.

## Weekly log

| Week | Focus | Status | Main outputs |
|---|---|---|---|
| 1 | Project set-up, data profiling | Notebook complete | `01_data_profiling.ipynb` |
| 2 | Data cleaning, validation, integrity checks | Notebook complete | `02_cleaning_validation.ipynb`, `src/cleaning.py`, `tests/`, `data/processed/`, issue log v2 |
| 3 | Integration, feature engineering, baseline KPIs | [update status] | |
| 4 | Product performance and demand patterns | In progress | |
| 5 | Inventory health, turnover and ageing | Notebook complete; submitted late | `05_inventory_health.ipynb`, `week-05/`, `reports/week05_inventory_insights` |
| 6 to 12 | Warehouse, supplier, customer, forecasting, optimisation, dashboards, strategy | Not started | |

### Week 5 summary: inventory health, turnover and ageing

- All 180 product-branch pairs are above their branch maximum; INR 277.93 billion (99.70%) of INR 278.77 billion of stock is excess.
- Inventory turnover in 2024 was 0.01 times a year (32,334 days on hand); the excess would take about 95 years to sell at current sales.
- 82.72% of stock value is older than 365 days.
- Stock in is 18.03 times stock out. Purchase lines average 159.85 units against 10.50 for sales lines, which accounts for about 94% of the gap.
- INR 50.83 billion of purchase orders (before GST) were placed in the last 12 months for pairs already above maximum.
- Known limitation: the ledger holds about 8.9% fewer units than the purchase and sales documents (issue I29, under investigation); both sources give the same 18:1 ratio.

## How to run

Run everything from the repository root (the folder that contains `warehouse.duckdb`).

```bash
pip install duckdb pandas numpy matplotlib pytest pyarrow

python -m src.cleaning          # raw database -> data/processed/*.parquet
python -m pytest tests -q       # data-quality tests (107 cases)
jupyter lab                     # then run notebooks in order
```

`05_inventory_health.ipynb` reads `data/processed/*.parquet` and writes its outputs to `week-05/` and `reports/figures/`. Use Kernel, Restart & Run All.

## Data-quality notes (from Week 2)

- All 17 foreign keys are valid and order-level money fields reconcile.
- `invoice_id` and `payment_id` are re-issued on different records: join invoices on `so_id`, and use the derived payment status, not the stored one.
- Use the recomputed customer purchase value, not `customers.total_purchase_value`.
- Exclude cancelled orders (`is_cancelled`) from revenue, invoice and lead-time measures.
- ADJUSTMENT quantities have no direction (issue I08).
- Full issue log: `docs/dq_issue_log_v2.csv`.

## Tools

Python (pandas, NumPy, matplotlib), SQL on DuckDB, pytest, Parquet, Git/GitHub. Power BI, statsmodels, scikit-learn, LightGBM and others are planned for later weeks.
