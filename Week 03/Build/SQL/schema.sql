-- =============================================================================
-- WEEK 3 | A3 DATA INTEGRATION & DATASET MERGING | STAR SCHEMA
-- Project : Heavy Supplier, Inventory & Warehouse Analytics (CadetX)
-- Author  : Keren Oyem (Data Analyst / Data Scientist)
-- Run from: the project folder (contains warehouse.duckdb and data/processed/)
--           python -m src.build_star_schema
--
-- PURPOSE
--   Integrates the 12 cleaned Week 2 tables (data/processed/*.parquet) into an
--   analytical star schema: 4 fact tables + 5 dimension tables.
--
-- DESIGN RULES
--   1. Everything is created in the separate schema `star`; the raw tables in
--      `main` are never touched.
--   2. No row is dropped. Week 2 flags (is_cancelled, invoice_id_duplicated,
--      payment_status_derived, ...) are carried into the facts so analysts
--      filter explicitly instead of losing data silently.
--   3. Natural keys are used (product_id, branch_id, ...). They are unique and
--      small (6 branches, 30 products, 8 suppliers, 500 customers), so
--      surrogate keys would add complexity for no benefit.
--   4. Dates become integer keys YYYYMMDD that join to star.dim_date.
--   5. Join rules from the Week 2 issue log:
--        - invoices are identified by so_id, NOT invoice_id (197 re-issued IDs)
--        - use payment_status_derived, not the stored payment_status
--        - use lifetime_value_with_gst, not total_purchase_value_stored
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS star;

-- Helper: DATE -> integer key YYYYMMDD (NULL stays NULL)
CREATE OR REPLACE MACRO star.date_key(d) AS
    year(d) * 10000 + month(d) * 100 + day(d);


-- =============================================================================
-- DIMENSIONS
-- =============================================================================

-- ---- dim_date ---------------------------------------------------------------
-- Calendar covering all order dates (2019-2024) and ledger/finance dates that
-- extend into early 2025. Fiscal year follows the Indian April-March year.
CREATE OR REPLACE TABLE star.dim_date AS
SELECT
    star.date_key(d)                                AS date_key,
    d                                               AS full_date,
    year(d)                                         AS calendar_year,
    quarter(d)                                      AS calendar_quarter,
    month(d)                                        AS calendar_month,
    strftime(d, '%B')                               AS month_name,
    strftime(d, '%Y-%m')                            AS year_month,
    weekofyear(d)                                   AS week_of_year,
    isodow(d)                                       AS day_of_week,
    strftime(d, '%A')                               AS day_name,
    isodow(d) >= 6                                  AS is_weekend,
    CASE WHEN month(d) >= 4 THEN year(d) + 1 ELSE year(d) END AS fiscal_year,
    ((month(d) + 8) % 12) // 3 + 1                  AS fiscal_quarter
FROM (
    SELECT CAST(range AS DATE) AS d
    FROM range(DATE '2019-01-01', DATE '2026-01-01', INTERVAL 1 DAY)
);

-- ---- dim_product -------------------------------------------------------------
-- 30 heavy-machinery spare parts. Company-level reorder/safety/max parameters
-- live here; branch-level ones live in fact-adjacent inventory_master (Week 5).
CREATE OR REPLACE TABLE star.dim_product AS
SELECT
    p.*,
    p.unit_price - p.unit_cost AS unit_margin
FROM read_parquet('data/processed/products.parquet') p;

-- ---- dim_branch --------------------------------------------------------------
-- 6 branches / warehouses; includes numeric warehouse_capacity_sqft from Week 2.
CREATE OR REPLACE TABLE star.dim_branch AS
SELECT * FROM read_parquet('data/processed/branches.parquet');

-- ---- dim_customer ------------------------------------------------------------
-- 500 customers. The stored purchase value is kept but renamed so nobody uses
-- it by accident (it is only ~4% of real sales and uncorrelated with them).
CREATE OR REPLACE TABLE star.dim_customer AS
SELECT
    * EXCLUDE (total_purchase_value,
               recalc_purchase_value_with_gst,
               recalc_purchase_value_before_gst),
    total_purchase_value              AS total_purchase_value_stored,
    recalc_purchase_value_with_gst    AS lifetime_value_with_gst,
    recalc_purchase_value_before_gst  AS lifetime_value_before_gst
FROM read_parquet('data/processed/customers.parquet');

-- ---- dim_supplier ------------------------------------------------------------
-- 8 China-based suppliers (pincode stored as 6-character text).
CREATE OR REPLACE TABLE star.dim_supplier AS
SELECT * FROM read_parquet('data/processed/suppliers.parquet');


-- =============================================================================
-- FACTS
-- =============================================================================

-- ---- fact_sales_line ---------------------------------------------------------
-- GRAIN: one row per sales order line (so_id + line_number). 130,402 rows.
-- Header attributes are denormalised onto each line. Cancelled orders are KEPT
-- and marked with is_cancelled; exclude them from revenue measures.
CREATE OR REPLACE TABLE star.fact_sales_line AS
SELECT
    l.so_id,
    l.line_number,
    h.customer_id,
    h.branch_id,
    l.product_id,
    star.date_key(h.order_date)     AS order_date_key,
    star.date_key(h.delivery_date)  AS delivery_date_key,
    h.order_status,
    h.is_cancelled,
    h.sales_channel,
    h.payment_terms,
    l.quantity,
    l.unit_price,
    l.gst_rate,
    l.line_total,
    l.gst_amount,
    l.line_grand_total,
    p.unit_cost                              AS unit_cost_master,
    l.quantity * p.unit_cost                 AS cogs,
    l.line_total - l.quantity * p.unit_cost  AS gross_margin,
    h.days_to_deliver
FROM read_parquet('data/processed/sales_orders_lines.parquet')  l
JOIN read_parquet('data/processed/sales_orders_header.parquet') h ON l.so_id = h.so_id
LEFT JOIN read_parquet('data/processed/products.parquet')       p ON l.product_id = p.product_id;

-- ---- fact_purchase_line ------------------------------------------------------
-- GRAIN: one row per purchase order line (po_id + line_number). 155,495 rows.
-- received_date_key is NULL for the 2,370 cancelled POs (valid, not an error).
CREATE OR REPLACE TABLE star.fact_purchase_line AS
SELECT
    l.po_id,
    l.line_number,
    h.supplier_id,
    h.branch_id,
    l.product_id,
    star.date_key(h.order_date)             AS order_date_key,
    star.date_key(h.expected_delivery_date) AS expected_date_key,
    star.date_key(h.received_date)          AS received_date_key,
    h.po_status,
    h.is_cancelled,
    l.quantity,
    l.unit_cost,
    l.gst_rate,
    l.line_total,
    l.gst_amount,
    l.line_grand_total
FROM read_parquet('data/processed/purchase_orders_lines.parquet')  l
JOIN read_parquet('data/processed/purchase_orders_header.parquet') h ON l.po_id = h.po_id;

-- ---- fact_stock_movement -----------------------------------------------------
-- GRAIN: one row per stock ledger movement (movement_id). 237,230 rows.
-- signed_quantity: IN positive, OUT negative, ADJUSTMENT NULL because the data
-- stores adjustments as positive numbers with no direction (issue I08).
-- Row order within a day is not stored, so running_balance cannot be re-sorted.
CREATE OR REPLACE TABLE star.fact_stock_movement AS
SELECT
    movement_id,
    product_id,
    branch_id,
    star.date_key(movement_date) AS movement_date_key,
    movement_type,
    quantity,
    CASE movement_type WHEN 'IN'  THEN quantity
                       WHEN 'OUT' THEN -quantity
                       ELSE NULL END       AS signed_quantity,
    movement_type <> 'ADJUSTMENT'          AS direction_known,
    reference_type,
    reference_id,
    running_balance
FROM read_parquet('data/processed/stock_ledger.parquet');

-- ---- fact_invoice_payment ----------------------------------------------------
-- GRAIN: one row per invoice, identified by so_id (invoice_id is re-issued on
-- 197 invoices, so it is NOT unique). 18,033 rows. Payments are pre-aggregated
-- onto the invoice in Week 2. Invoices with a duplicated invoice_id are kept
-- and labelled 'Ambiguous' because their payments cannot be assigned safely.
CREATE OR REPLACE TABLE star.fact_invoice_payment AS
SELECT
    i.so_id,
    i.invoice_id,
    i.customer_id,
    i.branch_id,
    star.date_key(i.invoice_date)  AS invoice_date_key,
    star.date_key(i.due_date)      AS due_date_key,
    i.total_order_value,
    i.total_gst_amount,
    i.grand_total,
    i.payment_status               AS payment_status_stored,
    i.payment_status_derived,
    i.total_paid,
    i.payment_count,
    i.outstanding_balance,
    i.invoice_id_duplicated,
    star.date_key(pay.first_payment_date) AS first_payment_date_key,
    star.date_key(pay.last_payment_date)  AS last_payment_date_key
FROM read_parquet('data/processed/invoices.parquet') i
LEFT JOIN (
    SELECT invoice_id,
           MIN(payment_date) AS first_payment_date,
           MAX(payment_date) AS last_payment_date
    FROM read_parquet('data/processed/payments.parquet')
    GROUP BY invoice_id
) pay
  ON i.invoice_id = pay.invoice_id
 AND NOT i.invoice_id_duplicated;     -- never attach payments to a re-issued ID


-- =============================================================================
-- DESCRIPTIONS (visible with: SELECT * FROM duckdb_columns() WHERE comment IS NOT NULL)
-- These feed the Week 3 data dictionary (A6).
-- =============================================================================

COMMENT ON TABLE star.dim_date IS 'Calendar dimension, one row per day 2019-01-01 to 2025-12-31. Key: date_key (YYYYMMDD).';
COMMENT ON TABLE star.dim_product IS 'Product dimension, one row per spare part (30). Key: product_id.';
COMMENT ON TABLE star.dim_branch IS 'Branch/warehouse dimension, one row per branch (6). Key: branch_id.';
COMMENT ON TABLE star.dim_customer IS 'Customer dimension, one row per customer (500). Key: customer_id.';
COMMENT ON TABLE star.dim_supplier IS 'Supplier dimension, one row per supplier (8). Key: supplier_id.';
COMMENT ON TABLE star.fact_sales_line IS 'Grain: one sales order line (so_id, line_number). Revenue, GST, cost and margin per line. Exclude is_cancelled for revenue.';
COMMENT ON TABLE star.fact_purchase_line IS 'Grain: one purchase order line (po_id, line_number). Procurement quantity, cost and dates.';
COMMENT ON TABLE star.fact_stock_movement IS 'Grain: one stock ledger movement (movement_id). IN / OUT / ADJUSTMENT with running balance.';
COMMENT ON TABLE star.fact_invoice_payment IS 'Grain: one invoice, keyed by so_id (invoice_id is not unique). Invoice value, payments received and derived status.';

-- dim_date
COMMENT ON COLUMN star.dim_date.date_key IS 'Integer date key YYYYMMDD; joins to every *_date_key column.';
COMMENT ON COLUMN star.dim_date.full_date IS 'Calendar date.';
COMMENT ON COLUMN star.dim_date.calendar_year IS 'Calendar year.';
COMMENT ON COLUMN star.dim_date.calendar_quarter IS 'Calendar quarter 1-4 (Jan-Mar = 1).';
COMMENT ON COLUMN star.dim_date.calendar_month IS 'Month number 1-12.';
COMMENT ON COLUMN star.dim_date.month_name IS 'Full month name.';
COMMENT ON COLUMN star.dim_date.year_month IS 'Year and month as text YYYY-MM, for monthly series.';
COMMENT ON COLUMN star.dim_date.week_of_year IS 'ISO week number.';
COMMENT ON COLUMN star.dim_date.day_of_week IS 'ISO day of week, Monday = 1 ... Sunday = 7.';
COMMENT ON COLUMN star.dim_date.day_name IS 'Full day name.';
COMMENT ON COLUMN star.dim_date.is_weekend IS 'TRUE for Saturday and Sunday.';
COMMENT ON COLUMN star.dim_date.fiscal_year IS 'Indian fiscal year (April-March) labelled by the year it ends, e.g. Apr 2023 = FY2024.';
COMMENT ON COLUMN star.dim_date.fiscal_quarter IS 'Fiscal quarter 1-4 (Apr-Jun = 1).';

-- dim_product (added column; other columns are documented in the data dictionary)
COMMENT ON COLUMN star.dim_product.unit_margin IS 'Derived: unit_price - unit_cost, in INR per unit.';

-- dim_customer (renamed columns)
COMMENT ON COLUMN star.dim_customer.total_purchase_value_stored IS 'ORIGINAL stored value. Unreliable (about 4% of real sales, correlation -0.08). Do not use.';
COMMENT ON COLUMN star.dim_customer.lifetime_value_with_gst IS 'Recomputed: sum of grand_total over delivered orders, INR incl. GST. Use this one.';
COMMENT ON COLUMN star.dim_customer.lifetime_value_before_gst IS 'Recomputed: sum of total_order_value over delivered orders, INR before GST.';

-- fact_sales_line
COMMENT ON COLUMN star.fact_sales_line.so_id IS 'Sales order ID (with line_number forms the grain).';
COMMENT ON COLUMN star.fact_sales_line.line_number IS 'Line number within the sales order.';
COMMENT ON COLUMN star.fact_sales_line.customer_id IS 'FK to dim_customer.';
COMMENT ON COLUMN star.fact_sales_line.branch_id IS 'FK to dim_branch (fulfilling branch).';
COMMENT ON COLUMN star.fact_sales_line.product_id IS 'FK to dim_product.';
COMMENT ON COLUMN star.fact_sales_line.order_date_key IS 'FK to dim_date: order date.';
COMMENT ON COLUMN star.fact_sales_line.delivery_date_key IS 'FK to dim_date: delivery date. Placeholder for cancelled orders.';
COMMENT ON COLUMN star.fact_sales_line.order_status IS 'Delivered or Cancelled.';
COMMENT ON COLUMN star.fact_sales_line.is_cancelled IS 'TRUE for cancelled orders; exclude from revenue and delivery measures.';
COMMENT ON COLUMN star.fact_sales_line.sales_channel IS 'Sales channel of the order.';
COMMENT ON COLUMN star.fact_sales_line.payment_terms IS 'Payment terms agreed on the order.';
COMMENT ON COLUMN star.fact_sales_line.quantity IS 'Units sold on the line.';
COMMENT ON COLUMN star.fact_sales_line.unit_price IS 'Selling price per unit, INR before GST.';
COMMENT ON COLUMN star.fact_sales_line.gst_rate IS 'GST rate in percent (18 or 28).';
COMMENT ON COLUMN star.fact_sales_line.line_total IS 'quantity x unit_price, INR before GST.';
COMMENT ON COLUMN star.fact_sales_line.gst_amount IS 'GST on the line, INR.';
COMMENT ON COLUMN star.fact_sales_line.line_grand_total IS 'line_total + gst_amount, INR.';
COMMENT ON COLUMN star.fact_sales_line.unit_cost_master IS 'Unit cost from the product master (assumed cost basis for margin).';
COMMENT ON COLUMN star.fact_sales_line.cogs IS 'Derived: quantity x unit_cost_master, INR.';
COMMENT ON COLUMN star.fact_sales_line.gross_margin IS 'Derived: line_total - cogs, INR before GST.';
COMMENT ON COLUMN star.fact_sales_line.days_to_deliver IS 'delivery_date - order_date in days.';

-- fact_purchase_line
COMMENT ON COLUMN star.fact_purchase_line.po_id IS 'Purchase order ID (with line_number forms the grain).';
COMMENT ON COLUMN star.fact_purchase_line.line_number IS 'Line number within the purchase order.';
COMMENT ON COLUMN star.fact_purchase_line.supplier_id IS 'FK to dim_supplier.';
COMMENT ON COLUMN star.fact_purchase_line.branch_id IS 'FK to dim_branch (receiving branch).';
COMMENT ON COLUMN star.fact_purchase_line.product_id IS 'FK to dim_product.';
COMMENT ON COLUMN star.fact_purchase_line.order_date_key IS 'FK to dim_date: PO order date.';
COMMENT ON COLUMN star.fact_purchase_line.expected_date_key IS 'FK to dim_date: promised delivery date.';
COMMENT ON COLUMN star.fact_purchase_line.received_date_key IS 'FK to dim_date: actual receipt date. NULL for cancelled POs.';
COMMENT ON COLUMN star.fact_purchase_line.po_status IS 'Received or Cancelled.';
COMMENT ON COLUMN star.fact_purchase_line.is_cancelled IS 'TRUE for cancelled POs; exclude from lead-time, delay and on-time measures.';
COMMENT ON COLUMN star.fact_purchase_line.quantity IS 'Units ordered.';
COMMENT ON COLUMN star.fact_purchase_line.unit_cost IS 'Purchase price per unit, INR before GST.';
COMMENT ON COLUMN star.fact_purchase_line.gst_rate IS 'GST rate in percent.';
COMMENT ON COLUMN star.fact_purchase_line.line_total IS 'quantity x unit_cost, INR before GST.';
COMMENT ON COLUMN star.fact_purchase_line.gst_amount IS 'GST on the line, INR.';
COMMENT ON COLUMN star.fact_purchase_line.line_grand_total IS 'line_total + gst_amount, INR.';

-- fact_stock_movement
COMMENT ON COLUMN star.fact_stock_movement.movement_id IS 'Unique ledger movement ID (the grain). Sorts as text, not by time.';
COMMENT ON COLUMN star.fact_stock_movement.product_id IS 'FK to dim_product.';
COMMENT ON COLUMN star.fact_stock_movement.branch_id IS 'FK to dim_branch.';
COMMENT ON COLUMN star.fact_stock_movement.movement_date_key IS 'FK to dim_date: movement date.';
COMMENT ON COLUMN star.fact_stock_movement.movement_type IS 'IN, OUT or ADJUSTMENT.';
COMMENT ON COLUMN star.fact_stock_movement.quantity IS 'Units moved. Always positive in the source.';
COMMENT ON COLUMN star.fact_stock_movement.signed_quantity IS 'Derived: +quantity for IN, -quantity for OUT, NULL for ADJUSTMENT (direction unknown).';
COMMENT ON COLUMN star.fact_stock_movement.direction_known IS 'FALSE for ADJUSTMENT rows.';
COMMENT ON COLUMN star.fact_stock_movement.reference_type IS 'Source document type (PO, SO or ADJ).';
COMMENT ON COLUMN star.fact_stock_movement.reference_id IS 'Source document ID.';
COMMENT ON COLUMN star.fact_stock_movement.running_balance IS 'Balance recorded after the movement. Order within a day is ambiguous.';

-- fact_invoice_payment
COMMENT ON COLUMN star.fact_invoice_payment.so_id IS 'Sales order ID. Unique per invoice: this is the reliable invoice key.';
COMMENT ON COLUMN star.fact_invoice_payment.invoice_id IS 'Invoice ID. NOT unique (197 re-issued IDs); do not join on it alone.';
COMMENT ON COLUMN star.fact_invoice_payment.customer_id IS 'FK to dim_customer.';
COMMENT ON COLUMN star.fact_invoice_payment.branch_id IS 'FK to dim_branch.';
COMMENT ON COLUMN star.fact_invoice_payment.invoice_date_key IS 'FK to dim_date: invoice date.';
COMMENT ON COLUMN star.fact_invoice_payment.due_date_key IS 'FK to dim_date: payment due date.';
COMMENT ON COLUMN star.fact_invoice_payment.total_order_value IS 'Invoice value before GST, INR.';
COMMENT ON COLUMN star.fact_invoice_payment.total_gst_amount IS 'GST on the invoice, INR.';
COMMENT ON COLUMN star.fact_invoice_payment.grand_total IS 'Invoice value including GST, INR.';
COMMENT ON COLUMN star.fact_invoice_payment.payment_status_stored IS 'ORIGINAL stored status. 67 stored as Paid are only partly paid. Do not use.';
COMMENT ON COLUMN star.fact_invoice_payment.payment_status_derived IS 'Status derived from payments: Unpaid, Partially paid, Fully paid, Overpaid or Ambiguous. Use this one.';
COMMENT ON COLUMN star.fact_invoice_payment.total_paid IS 'Sum of payments received against the invoice_id, INR.';
COMMENT ON COLUMN star.fact_invoice_payment.payment_count IS 'Number of payments received against the invoice_id.';
COMMENT ON COLUMN star.fact_invoice_payment.outstanding_balance IS 'grand_total - total_paid, INR. Negative means overpaid.';
COMMENT ON COLUMN star.fact_invoice_payment.invoice_id_duplicated IS 'TRUE when the invoice_id is shared with another invoice; payments for these are ambiguous.';
COMMENT ON COLUMN star.fact_invoice_payment.first_payment_date_key IS 'FK to dim_date: first payment. NULL if unpaid or ambiguous.';
COMMENT ON COLUMN star.fact_invoice_payment.last_payment_date_key IS 'FK to dim_date: last payment. NULL if unpaid or ambiguous.';
