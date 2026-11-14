# Week 03: Data Integration, Feature Engineering & Baseline KPIs

**Project:** Heavy Supplier, Inventory & Warehouse Analytics (CadetX Virtual Work Experience)
**Sprint:** Week 3, Fri 6 Nov - Thu 12 Nov 2026 (Phase 1: Foundation & Exploration)
**Author:** Keren Oyem (Data Analyst / Data Scientist)
**Catalogue tasks:** A3 Data Integration & Dataset Merging, A4 Feature Engineering for Analytics, A6 Data Dictionary & Documentation

## 1. Goal

Turn the 12 clean tables from Week 2 into an analytical model that Weeks 4-12 can reuse: a star schema, a library of derived features, a documented data dictionary and a baseline KPI tracker. This closes Phase 1.

## 2. Deliverables

| Task | Deliverable | File |
|---|---|---|
| A3 | Star schema (5 dimensions, 4 facts) | `sql/schema.sql` |
| A3 | Star schema validation | `sql/validate_star.sql` |
| A3 | Notebook that builds and validates the schema | `03_star_schema.ipynb` |
| A4 | Feature library (8 feature tables, every column described) | `src/features.py` |
| A4 | Notebook that builds, inspects and validates the features | `03_feature_engineering.ipynb` |
| A6 | Data dictionary notebook | `03_data_dictionary.ipynb` |
| A6 | Data dictionary (Excel) | `docs/data_dictionary.xlsx` |
| A6 | Data dictionary (Word) | `docs/data_dictionary.docx` |
| A6 | Library used to write the dictionary files | `src/dictionary_writers.py` |
| KPIs | Baseline KPI notebook | `03_kpi_baseline.ipynb` |
| KPIs | Baseline KPI tracker (48 KPIs) | `docs/kpi_tracker.csv`, `docs/kpi_tracker.xlsx` |
| Summary | Phase 1 summary report | `reports/phase1_summary.docx` |
| Admin | Sprint notes | `week-03/sprint_notes.md` |

## 3. How the pieces fit together

```
data/processed/*.parquet   (Week 2 clean layer)
        |
        v   03_star_schema.ipynb  (sql/schema.sql, sql/validate_star.sql)
schema star   : dim_date, dim_product, dim_branch, dim_customer, dim_supplier
                fact_sales_line, fact_purchase_line, fact_stock_movement, fact_invoice_payment
        |
        v   03_feature_engineering.ipynb  (src/features.py)
schema feat   : feat_purchase_order, feat_supplier, feat_sales_order, feat_invoice,
                feat_customer, feat_product, feat_monthly_demand, feat_demand_variability
        |
        +--> 03_kpi_baseline.ipynb   -> docs/kpi_tracker.csv / .xlsx
        +--> 03_data_dictionary.ipynb -> docs/data_dictionary.xlsx / .docx
```

All new tables live in the schemas `star`, `feat` and `kpi` inside `warehouse.duckdb`. The raw tables in `main` are never modified, and no row is dropped anywhere.

## 4. How to reproduce

Run everything from the project folder (the one that contains `warehouse.duckdb`, `sql/`, `src/` and `data/processed/`).

1. Make sure the Week 2 clean layer exists: `python -m src.cleaning`
2. Run `03_star_schema.ipynb` (builds `star` and validates it)
3. Run `03_feature_engineering.ipynb` (writes `src/features.py`, builds `feat`)
4. Run `03_kpi_baseline.ipynb` (writes `docs/kpi_tracker.*`)
5. Run `03_data_dictionary.ipynb` (writes `docs/data_dictionary.*`)

Requirements: Python 3, `duckdb`, `pandas`, `matplotlib`, `openpyxl`, `python-docx`. Close any other notebook that has the database open for writing, because DuckDB allows only one writing connection.

## 5. Design decisions

- **Natural keys** (`product_id`, `branch_id`, ...) are used; they are unique and small, so surrogate keys add nothing.
- **Dates** are integer keys `YYYYMMDD` joining to `dim_date` (fiscal year follows the Indian April-March year).
- **Invoices are keyed on `so_id`**, not `invoice_id`, because 197 invoice IDs were re-issued in the source data. Payments are never attached to those ambiguous invoices.
- **Derived fields replace unreliable stored ones:** `payment_status_derived` (not `payment_status`) and `lifetime_value_with_gst` (not `total_purchase_value`).
- **Cancelled orders and POs are kept and flagged** with `is_cancelled`; they are excluded from revenue, delay and lead-time measures.
- **Stock adjustments** have no stored direction, so `signed_quantity` is empty for them and they are left out of stock KPIs.
- **Every table and column is described** inside the database (`COMMENT ON`), which feeds the data dictionary.

## 6. Validation

| Check | Result |
|---|---|
| Star schema: row counts, totals, grain, foreign keys | All checks passed |
| Feature tables: row counts, totals, Week 2 rules, documentation | All checks passed |
| Data dictionary: every column defined, files valid | All checks passed |
| KPI notebook: pooled revenue equals the sum of the six years | Passed |

## 7. Headline results (baseline, 2019-2024)

| KPI | 2019 | 2024 | 2019-2024 |
|---|---:|---:|---:|
| Delivered revenue (INR crore, before GST) | 387.0 | 367.8 | 2,295.9 |
| Gross margin % | 21.6 | 21.6 | 21.6 |
| Collection rate % | 80.8 | 79.9 | 79.7 |
| Supplier on-time delivery % | 84.5 | 84.9 | 84.9 |
| Closing inventory value (INR crore) | 4,520 | 27,877 | n/a (average 16,242) |
| Inventory turnover (times a year) | 0.133 | 0.011 | n/a (average 0.041) |
| Receipts-to-issues ratio | 17.4 | 18.1 | n/a (average 18.0) |

The dominant finding is **overstock**: stock received is 18 times stock issued, and 99.7% of 2024 inventory value (INR 27,793 crore) sits above the maximum stock level. The full set of six findings is in `reports/phase1_summary.docx`.

## 8. Known limitations and open questions

- DSO is a proxy (outstanding divided by invoiced, times 365).
- Stock KPIs leave out adjustments; branch operating cost is assumed constant across years.
- Definitions of master-table fields are inferred (marked "Inferred" in the data dictionary) because `Fields Documentation.docx` was not available.
- Open business questions: direction of stock adjustments, cause of the 52 overpaid invoices, and the genuine differences between recorded and ledger stock.

## 9. Next: Week 4, Product Performance & Demand Patterns

Revenue, margin and units by product, category, brand and branch; Pareto (80/20) classification; ABC-XYZ matrix using `feat_demand_variability`; fast-mover identification; demand trend and seasonality analysis.

