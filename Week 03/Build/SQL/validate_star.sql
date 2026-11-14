-- =============================================================================
-- WEEK 3 | STAR SCHEMA VALIDATION  (Definition of Done: "each fact table
-- reconciles to source row counts and totals")
-- Returns one row per check: check_name, expected, actual, status.
-- Run after schema.sql:  python -m src.build_star_schema
-- Sections: 1 row counts | 2 totals | 3 grain uniqueness | 4 orphan keys
-- =============================================================================
WITH checks AS (

-- 1. ROW COUNTS: fact rows must equal source rows (no row lost or duplicated)
SELECT 'rows: fact_sales_line = sales_orders_lines' AS check_name,
       (SELECT COUNT(*) FROM read_parquet('data/processed/sales_orders_lines.parquet'))::DOUBLE AS expected,
       (SELECT COUNT(*) FROM star.fact_sales_line)::DOUBLE AS actual
UNION ALL SELECT 'rows: fact_purchase_line = purchase_orders_lines',
       (SELECT COUNT(*) FROM read_parquet('data/processed/purchase_orders_lines.parquet')),
       (SELECT COUNT(*) FROM star.fact_purchase_line)
UNION ALL SELECT 'rows: fact_stock_movement = stock_ledger',
       (SELECT COUNT(*) FROM read_parquet('data/processed/stock_ledger.parquet')),
       (SELECT COUNT(*) FROM star.fact_stock_movement)
UNION ALL SELECT 'rows: fact_invoice_payment = invoices',
       (SELECT COUNT(*) FROM read_parquet('data/processed/invoices.parquet')),
       (SELECT COUNT(*) FROM star.fact_invoice_payment)
UNION ALL SELECT 'rows: dim_product = products', 30, (SELECT COUNT(*) FROM star.dim_product)
UNION ALL SELECT 'rows: dim_branch = branches', 6, (SELECT COUNT(*) FROM star.dim_branch)
UNION ALL SELECT 'rows: dim_customer = customers', 500, (SELECT COUNT(*) FROM star.dim_customer)
UNION ALL SELECT 'rows: dim_supplier = suppliers', 8, (SELECT COUNT(*) FROM star.dim_supplier)

-- 2. TOTALS: money and quantity sums must equal the source
UNION ALL SELECT 'total: sales line_grand_total',
       (SELECT SUM(line_grand_total) FROM read_parquet('data/processed/sales_orders_lines.parquet')),
       (SELECT SUM(line_grand_total) FROM star.fact_sales_line)
UNION ALL SELECT 'total: sales header grand_total = fact (all orders)',
       (SELECT SUM(grand_total) FROM read_parquet('data/processed/sales_orders_header.parquet')),
       (SELECT SUM(line_grand_total) FROM star.fact_sales_line)
UNION ALL SELECT 'total: purchase line_grand_total',
       (SELECT SUM(line_grand_total) FROM read_parquet('data/processed/purchase_orders_lines.parquet')),
       (SELECT SUM(line_grand_total) FROM star.fact_purchase_line)
UNION ALL SELECT 'total: purchase header grand_total = fact (all POs)',
       (SELECT SUM(grand_total) FROM read_parquet('data/processed/purchase_orders_header.parquet')),
       (SELECT SUM(line_grand_total) FROM star.fact_purchase_line)
UNION ALL SELECT 'total: stock quantity',
       (SELECT SUM(quantity) FROM read_parquet('data/processed/stock_ledger.parquet')),
       (SELECT SUM(quantity) FROM star.fact_stock_movement)
UNION ALL SELECT 'total: invoice grand_total',
       (SELECT SUM(grand_total) FROM read_parquet('data/processed/invoices.parquet')),
       (SELECT SUM(grand_total) FROM star.fact_invoice_payment)
UNION ALL SELECT 'total: invoice total_paid',
       (SELECT SUM(total_paid) FROM read_parquet('data/processed/invoices.parquet')),
       (SELECT SUM(total_paid) FROM star.fact_invoice_payment)

-- 3. GRAIN: the stated grain must be unique (0 surplus rows expected)
UNION ALL SELECT 'grain: fact_sales_line (so_id, line_number) unique', 0,
       (SELECT COUNT(*) - COUNT(DISTINCT so_id || '|' || line_number) FROM star.fact_sales_line)
UNION ALL SELECT 'grain: fact_purchase_line (po_id, line_number) unique', 0,
       (SELECT COUNT(*) - COUNT(DISTINCT po_id || '|' || line_number) FROM star.fact_purchase_line)
UNION ALL SELECT 'grain: fact_stock_movement movement_id unique', 0,
       (SELECT COUNT(*) - COUNT(DISTINCT movement_id) FROM star.fact_stock_movement)
UNION ALL SELECT 'grain: fact_invoice_payment so_id unique', 0,
       (SELECT COUNT(*) - COUNT(DISTINCT so_id) FROM star.fact_invoice_payment)

-- 4. ORPHAN KEYS: every fact key must exist in its dimension (0 expected;
--    nullable date keys are only checked when present)
UNION ALL SELECT 'fk: sales -> dim_product', 0, (SELECT COUNT(*) FROM star.fact_sales_line f LEFT JOIN star.dim_product d USING (product_id) WHERE d.product_id IS NULL)
UNION ALL SELECT 'fk: sales -> dim_customer', 0, (SELECT COUNT(*) FROM star.fact_sales_line f LEFT JOIN star.dim_customer d USING (customer_id) WHERE d.customer_id IS NULL)
UNION ALL SELECT 'fk: sales -> dim_branch', 0, (SELECT COUNT(*) FROM star.fact_sales_line f LEFT JOIN star.dim_branch d USING (branch_id) WHERE d.branch_id IS NULL)
UNION ALL SELECT 'fk: sales order_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_sales_line f LEFT JOIN star.dim_date d ON f.order_date_key = d.date_key WHERE d.date_key IS NULL)
UNION ALL SELECT 'fk: sales delivery_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_sales_line f LEFT JOIN star.dim_date d ON f.delivery_date_key = d.date_key WHERE f.delivery_date_key IS NOT NULL AND d.date_key IS NULL)
UNION ALL SELECT 'fk: purchase -> dim_product', 0, (SELECT COUNT(*) FROM star.fact_purchase_line f LEFT JOIN star.dim_product d USING (product_id) WHERE d.product_id IS NULL)
UNION ALL SELECT 'fk: purchase -> dim_supplier', 0, (SELECT COUNT(*) FROM star.fact_purchase_line f LEFT JOIN star.dim_supplier d USING (supplier_id) WHERE d.supplier_id IS NULL)
UNION ALL SELECT 'fk: purchase -> dim_branch', 0, (SELECT COUNT(*) FROM star.fact_purchase_line f LEFT JOIN star.dim_branch d USING (branch_id) WHERE d.branch_id IS NULL)
UNION ALL SELECT 'fk: purchase order_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_purchase_line f LEFT JOIN star.dim_date d ON f.order_date_key = d.date_key WHERE d.date_key IS NULL)
UNION ALL SELECT 'fk: purchase received_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_purchase_line f LEFT JOIN star.dim_date d ON f.received_date_key = d.date_key WHERE f.received_date_key IS NOT NULL AND d.date_key IS NULL)
UNION ALL SELECT 'fk: stock -> dim_product', 0, (SELECT COUNT(*) FROM star.fact_stock_movement f LEFT JOIN star.dim_product d USING (product_id) WHERE d.product_id IS NULL)
UNION ALL SELECT 'fk: stock -> dim_branch', 0, (SELECT COUNT(*) FROM star.fact_stock_movement f LEFT JOIN star.dim_branch d USING (branch_id) WHERE d.branch_id IS NULL)
UNION ALL SELECT 'fk: stock movement_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_stock_movement f LEFT JOIN star.dim_date d ON f.movement_date_key = d.date_key WHERE d.date_key IS NULL)
UNION ALL SELECT 'fk: invoice -> dim_customer', 0, (SELECT COUNT(*) FROM star.fact_invoice_payment f LEFT JOIN star.dim_customer d USING (customer_id) WHERE d.customer_id IS NULL)
UNION ALL SELECT 'fk: invoice -> dim_branch', 0, (SELECT COUNT(*) FROM star.fact_invoice_payment f LEFT JOIN star.dim_branch d USING (branch_id) WHERE d.branch_id IS NULL)
UNION ALL SELECT 'fk: invoice_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_invoice_payment f LEFT JOIN star.dim_date d ON f.invoice_date_key = d.date_key WHERE d.date_key IS NULL)
UNION ALL SELECT 'fk: invoice due_date -> dim_date', 0, (SELECT COUNT(*) FROM star.fact_invoice_payment f LEFT JOIN star.dim_date d ON f.due_date_key = d.date_key WHERE d.date_key IS NULL)
)
SELECT check_name, expected, actual,
       CASE WHEN ABS(expected - actual) < 0.01 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM checks;
