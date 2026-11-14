"""Week 3 (A4): feature library. Builds the `feat` schema from the `star` schema.

Usage (from the project folder that contains warehouse.duckdb):

    import duckdb
    from src.features import build_features
    con = duckdb.connect("warehouse.duckdb")
    summary = build_features(con)

Each feature table is one SQL statement (FEATURE_SQL), documented by
TABLE_DESCRIPTIONS and COLUMN_DESCRIPTIONS. Descriptions are stored inside the
database (COMMENT ON) and feed the data dictionary (A6).

Rules carried from Week 2: cancelled orders/POs are kept but excluded from
delay, lead-time and delivery features; invoices are keyed on so_id;
ambiguous invoices (re-issued invoice_id) get no payment-timing features.
"""
REF_DATE = "2024-12-31"        # reference date for recency / overdue measures
DEMAND_START = "2019-01-01"    # monthly demand grid: Jan 2019 ...
DEMAND_END = "2024-12-31"      # ... to Dec 2024

FEATURE_SQL = {}

# --------------------------------------------------------------------------
FEATURE_SQL["feat_purchase_order"] = """
CREATE OR REPLACE TABLE feat.feat_purchase_order AS
WITH po AS (
    SELECT po_id, supplier_id, branch_id, order_date_key, expected_date_key,
           received_date_key, po_status, is_cancelled,
           COUNT(*)              AS line_count,
           SUM(quantity)         AS units,
           SUM(line_total)       AS spend_before_gst,
           SUM(line_grand_total) AS spend_incl_gst
    FROM star.fact_purchase_line
    GROUP BY ALL
)
SELECT
    po.po_id, po.supplier_id, po.branch_id,
    od.full_date          AS order_date,
    ed.full_date          AS expected_date,
    rd.full_date          AS received_date,
    od.calendar_year      AS order_year,
    po.po_status, po.is_cancelled, po.line_count, po.units,
    po.spend_before_gst, po.spend_incl_gst,
    date_diff('day', od.full_date, ed.full_date) AS planned_lead_time_days,
    date_diff('day', od.full_date, rd.full_date) AS actual_lead_time_days,
    date_diff('day', ed.full_date, rd.full_date) AS delay_days,
    CASE WHEN po.is_cancelled THEN NULL
         WHEN rd.full_date <= ed.full_date THEN TRUE ELSE FALSE END AS is_on_time,
    sup.lead_time_days AS stated_lead_time_days,
    date_diff('day', od.full_date, rd.full_date) - sup.lead_time_days AS lead_time_gap_days
FROM po
JOIN star.dim_date od ON po.order_date_key = od.date_key
JOIN star.dim_date ed ON po.expected_date_key = ed.date_key
LEFT JOIN star.dim_date rd ON po.received_date_key = rd.date_key
JOIN star.dim_supplier sup ON po.supplier_id = sup.supplier_id
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_supplier"] = """
CREATE OR REPLACE TABLE feat.feat_supplier AS
WITH agg AS (
    SELECT s.supplier_id, s.supplier_name,
           s.lead_time_days AS stated_lead_time_days,
           s.reliability_score AS stated_reliability_score,
           s.import_duty_rate,
           COUNT(p.po_id)                                  AS pos_placed,
           COUNT(*) FILTER (WHERE p.is_cancelled)          AS pos_cancelled,
           COUNT(*) FILTER (WHERE NOT p.is_cancelled)      AS pos_received,
           AVG(p.actual_lead_time_days)                    AS avg_actual_lead_time_days,
           STDDEV_SAMP(p.actual_lead_time_days)            AS lead_time_std_days,
           AVG(p.delay_days)                               AS avg_delay_days,
           quantile_cont(p.delay_days, 0.9)                AS p90_delay_days,
           AVG(p.is_on_time::INT)                          AS on_time_rate,
           SUM(p.spend_before_gst) FILTER (WHERE NOT p.is_cancelled) AS spend_before_gst
    FROM star.dim_supplier s
    LEFT JOIN feat.feat_purchase_order p ON s.supplier_id = p.supplier_id
    GROUP BY s.supplier_id, s.supplier_name, s.lead_time_days,
             s.reliability_score, s.import_duty_rate
)
SELECT supplier_id, supplier_name, stated_lead_time_days, stated_reliability_score,
       import_duty_rate, pos_placed, pos_cancelled,
       pos_cancelled * 1.0 / NULLIF(pos_placed, 0) AS cancellation_rate,
       pos_received, avg_actual_lead_time_days, lead_time_std_days,
       avg_delay_days, p90_delay_days, on_time_rate, spend_before_gst,
       spend_before_gst / SUM(spend_before_gst) OVER () AS spend_share
FROM agg
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_sales_order"] = """
CREATE OR REPLACE TABLE feat.feat_sales_order AS
WITH o AS (
    SELECT so_id, customer_id, branch_id, order_date_key, order_status,
           is_cancelled, sales_channel, payment_terms, days_to_deliver,
           COUNT(*)              AS line_count,
           SUM(quantity)         AS units,
           SUM(line_total)       AS revenue_before_gst,
           SUM(line_grand_total) AS revenue_incl_gst,
           SUM(gross_margin)     AS gross_margin
    FROM star.fact_sales_line
    GROUP BY ALL
)
SELECT o.so_id, o.customer_id, o.branch_id, o.order_status, o.is_cancelled,
       o.sales_channel, o.payment_terms, o.line_count, o.units,
       o.revenue_before_gst, o.revenue_incl_gst, o.gross_margin,
       d.full_date AS order_date, d.calendar_year AS order_year,
       d.calendar_month AS order_month,
       CASE WHEN o.is_cancelled THEN NULL ELSE o.days_to_deliver END AS order_to_delivery_days
FROM o
JOIN star.dim_date d ON o.order_date_key = d.date_key
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_invoice"] = """
CREATE OR REPLACE TABLE feat.feat_invoice AS
WITH base AS (
    SELECT f.so_id, f.invoice_id, f.customer_id, f.branch_id,
           i.full_date AS invoice_date, u.full_date AS due_date,
           i.calendar_year AS invoice_year,
           f.grand_total, f.total_paid, f.outstanding_balance,
           f.payment_status_derived, f.invoice_id_duplicated,
           fp.full_date AS first_payment_date, lp.full_date AS last_payment_date
    FROM star.fact_invoice_payment f
    JOIN star.dim_date i ON f.invoice_date_key = i.date_key
    JOIN star.dim_date u ON f.due_date_key = u.date_key
    LEFT JOIN star.dim_date fp ON f.first_payment_date_key = fp.date_key
    LEFT JOIN star.dim_date lp ON f.last_payment_date_key = lp.date_key
), flagged AS (
    SELECT *,
           (NOT invoice_id_duplicated AND outstanding_balance > 0.01
            AND due_date < DATE '__REF__') AS is_overdue
    FROM base
)
SELECT so_id, invoice_id, customer_id, branch_id, invoice_date, due_date,
       invoice_year, grand_total, total_paid, outstanding_balance,
       payment_status_derived, invoice_id_duplicated,
       date_diff('day', invoice_date, due_date)          AS credit_days,
       date_diff('day', invoice_date, first_payment_date) AS days_to_first_payment,
       date_diff('day', invoice_date, last_payment_date)  AS days_to_last_payment,
       CASE WHEN payment_status_derived = 'Fully paid'
            THEN date_diff('day', invoice_date, last_payment_date) END AS days_to_pay,
       CASE WHEN payment_status_derived = 'Fully paid'
            THEN last_payment_date > due_date END                      AS is_paid_late,
       CASE WHEN payment_status_derived = 'Fully paid'
            THEN GREATEST(date_diff('day', due_date, last_payment_date), 0) END AS days_late_when_paid,
       is_overdue,
       CASE WHEN is_overdue THEN date_diff('day', due_date, DATE '__REF__') END AS days_overdue
FROM flagged
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_customer"] = """
CREATE OR REPLACE TABLE feat.feat_customer AS
WITH s AS (
    SELECT customer_id,
           COUNT(*)                                          AS orders_placed,
           COUNT(*) FILTER (WHERE NOT is_cancelled)          AS delivered_orders,
           SUM(revenue_before_gst) FILTER (WHERE NOT is_cancelled) AS revenue_before_gst,
           MIN(order_date) FILTER (WHERE NOT is_cancelled)   AS first_order_date,
           MAX(order_date) FILTER (WHERE NOT is_cancelled)   AS last_order_date
    FROM feat.feat_sales_order
    GROUP BY customer_id
), pay AS (
    SELECT customer_id,
           AVG(days_to_pay) AS avg_days_to_pay,
           AVG(CASE WHEN is_paid_late THEN 1.0 ELSE 0.0 END)
               FILTER (WHERE is_paid_late IS NOT NULL) AS late_payment_rate
    FROM feat.feat_invoice
    GROUP BY customer_id
)
SELECT c.customer_id, c.customer_type, c.industry_segment, c.region, c.branch_id,
       c.customer_since, c.credit_limit, c.current_balance,
       c.current_balance * 1.0 / NULLIF(c.credit_limit, 0) AS credit_utilisation,
       COALESCE(s.orders_placed, 0)     AS orders_placed,
       COALESCE(s.delivered_orders, 0)  AS delivered_orders,
       COALESCE(s.revenue_before_gst, 0) AS revenue_before_gst,
       s.revenue_before_gst / NULLIF(s.delivered_orders, 0) AS avg_order_value,
       s.first_order_date, s.last_order_date,
       date_diff('day', s.last_order_date, DATE '__REF__') AS recency_days,
       date_diff('day', c.customer_since, DATE '__REF__') / 365.25 AS tenure_years,
       pay.avg_days_to_pay, pay.late_payment_rate
FROM star.dim_customer c
LEFT JOIN s   ON c.customer_id = s.customer_id
LEFT JOIN pay ON c.customer_id = pay.customer_id
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_product"] = """
CREATE OR REPLACE TABLE feat.feat_product AS
SELECT product_id, product_name, category, machine_type, brand, criticality_level,
       unit_cost, unit_price,
       unit_price - unit_cost AS unit_margin,
       (unit_price - unit_cost) * 100.0 / NULLIF(unit_price, 0) AS margin_pct_calc,
       (unit_price - unit_cost) * 100.0 / NULLIF(unit_cost, 0)  AS markup_pct,
       margin_percentage AS margin_pct_stored,
       weight_kg, length_cm, width_cm, height_cm, volume_m3,
       weight_kg / NULLIF(volume_m3, 0)  AS density_kg_per_m3,
       unit_price / NULLIF(weight_kg, 0) AS price_per_kg,
       lead_time_days AS master_lead_time_days
FROM star.dim_product
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_monthly_demand"] = """
CREATE OR REPLACE TABLE feat.feat_monthly_demand AS
WITH months AS (
    SELECT DISTINCT CAST(date_trunc('month', full_date) AS DATE) AS month_start
    FROM star.dim_date
    WHERE full_date BETWEEN DATE '__DSTART__' AND DATE '__DEND__'
), grid AS (
    SELECT p.product_id, b.branch_id, m.month_start
    FROM star.dim_product p
    CROSS JOIN star.dim_branch b
    CROSS JOIN months m
), act AS (
    SELECT f.product_id, f.branch_id,
           CAST(date_trunc('month', d.full_date) AS DATE) AS month_start,
           SUM(f.quantity)        AS units_sold,
           SUM(f.line_total)      AS revenue,
           COUNT(*)               AS order_lines,
           COUNT(DISTINCT f.so_id) AS orders
    FROM star.fact_sales_line f
    JOIN star.dim_date d ON f.order_date_key = d.date_key
    WHERE NOT f.is_cancelled
    GROUP BY ALL
), base AS (
    SELECT g.product_id, g.branch_id, g.month_start,
           COALESCE(a.units_sold, 0)  AS units_sold,
           COALESCE(a.revenue, 0)     AS revenue,
           COALESCE(a.order_lines, 0) AS order_lines,
           COALESCE(a.orders, 0)      AS orders
    FROM grid g
    LEFT JOIN act a ON g.product_id = a.product_id
                   AND g.branch_id = a.branch_id
                   AND g.month_start = a.month_start
)
SELECT product_id, branch_id, month_start,
       year(month_start)    AS calendar_year,
       month(month_start)   AS calendar_month,
       quarter(month_start) AS calendar_quarter,
       CASE WHEN month(month_start) >= 4 THEN year(month_start) + 1
            ELSE year(month_start) END AS fiscal_year,
       day(last_day(month_start)) AS days_in_month,
       units_sold, revenue, order_lines, orders,
       LAG(units_sold, 1)  OVER w AS units_lag_1,
       LAG(units_sold, 12) OVER w AS units_lag_12,
       AVG(units_sold) OVER (PARTITION BY product_id, branch_id
                             ORDER BY month_start
                             ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS units_roll_mean_3
FROM base
WINDOW w AS (PARTITION BY product_id, branch_id ORDER BY month_start)
"""

# --------------------------------------------------------------------------
FEATURE_SQL["feat_demand_variability"] = """
CREATE OR REPLACE TABLE feat.feat_demand_variability AS
WITH s AS (
    SELECT product_id, branch_id,
           COUNT(*)                                   AS months_observed,
           SUM(units_sold)                            AS total_units,
           AVG(units_sold)                            AS mean_monthly_units,
           STDDEV_SAMP(units_sold)                    AS std_monthly_units,
           COUNT(*) FILTER (WHERE units_sold > 0)     AS demand_months,
           COUNT(*) FILTER (WHERE units_sold = 0)     AS zero_demand_months,
           AVG(units_sold) FILTER (WHERE units_sold > 0)         AS mean_nonzero_units,
           STDDEV_SAMP(units_sold) FILTER (WHERE units_sold > 0) AS std_nonzero_units
    FROM feat.feat_monthly_demand
    GROUP BY product_id, branch_id
), m AS (
    SELECT *,
           std_monthly_units / NULLIF(mean_monthly_units, 0)    AS demand_cv,
           zero_demand_months * 1.0 / months_observed           AS zero_demand_share,
           months_observed * 1.0 / NULLIF(demand_months, 0)     AS adi,
           COALESCE(POWER(std_nonzero_units / NULLIF(mean_nonzero_units, 0), 2), 0) AS cv2_nonzero
    FROM s
)
SELECT product_id, branch_id, months_observed, total_units, mean_monthly_units,
       std_monthly_units, demand_cv, demand_months, zero_demand_months,
       zero_demand_share, adi, cv2_nonzero,
       CASE WHEN demand_months = 0              THEN 'No demand'
            WHEN adi < 1.32 AND cv2_nonzero < 0.49  THEN 'Smooth'
            WHEN adi < 1.32                     THEN 'Erratic'
            WHEN cv2_nonzero < 0.49             THEN 'Intermittent'
            ELSE 'Lumpy' END AS demand_class
FROM m
"""

BUILD_ORDER = ["feat_purchase_order", "feat_supplier", "feat_sales_order", "feat_invoice",
               "feat_customer", "feat_product", "feat_monthly_demand",
               "feat_demand_variability"]

TABLE_DESCRIPTIONS = {
    "feat_purchase_order": "Grain: one purchase order (24,000). Planned vs actual lead time, delay and on-time flag. Delay fields are NULL for cancelled POs.",
    "feat_supplier": "Grain: one supplier (8). Stated vs actual performance: lead time, delay, on-time rate, cancellation, spend share.",
    "feat_sales_order": "Grain: one sales order (20,000). Order totals and order-to-delivery days. Delivery days are NULL for cancelled orders.",
    "feat_invoice": "Grain: one invoice (so_id, 18,033). Payment timing, late and overdue flags. Payment timing is NULL for ambiguous invoices.",
    "feat_customer": "Grain: one customer (500). Credit utilisation, order value, recency, tenure and payment behaviour.",
    "feat_product": "Grain: one product (30). Margin, markup, volume, weight and density measures.",
    "feat_monthly_demand": "Grain: product x branch x month (30 x 6 x 72 = 12,960). Delivered sales per month with zero months filled, calendar fields and lag features.",
    "feat_demand_variability": "Grain: product x branch (180). Demand variability (CV), intermittency (ADI) and demand pattern class.",
}

COLUMN_DESCRIPTIONS = {
 "feat_purchase_order": {
  "po_id": "Purchase order ID.", "supplier_id": "FK to dim_supplier.", "branch_id": "FK to dim_branch (receiving branch).",
  "order_date": "Date the PO was placed.", "expected_date": "Promised delivery date.",
  "received_date": "Actual receipt date. NULL for cancelled POs.", "order_year": "Calendar year of the order date.",
  "po_status": "Received or Cancelled.", "is_cancelled": "TRUE for cancelled POs; exclude from delay and lead-time measures.",
  "line_count": "Number of lines on the PO.", "units": "Total units ordered.",
  "spend_before_gst": "PO value before GST, INR.", "spend_incl_gst": "PO value including GST, INR.",
  "planned_lead_time_days": "expected_date - order_date.", "actual_lead_time_days": "received_date - order_date. NULL if cancelled.",
  "delay_days": "received_date - expected_date. Positive = late, negative = early. NULL if cancelled.",
  "is_on_time": "TRUE if received on or before the expected date. NULL if cancelled.",
  "stated_lead_time_days": "Lead time promised in the supplier master.",
  "lead_time_gap_days": "actual_lead_time_days - stated_lead_time_days."},
 "feat_supplier": {
  "supplier_id": "Supplier ID.", "supplier_name": "Supplier name.",
  "stated_lead_time_days": "Lead time stated in the supplier master.", "stated_reliability_score": "Reliability score stated in the supplier master.",
  "import_duty_rate": "Import duty rate from the supplier master.", "pos_placed": "All POs placed with the supplier.",
  "pos_cancelled": "Cancelled POs.", "cancellation_rate": "pos_cancelled / pos_placed (0-1).", "pos_received": "Non-cancelled POs.",
  "avg_actual_lead_time_days": "Mean order-to-receipt days.", "lead_time_std_days": "Standard deviation of actual lead time (variability).",
  "avg_delay_days": "Mean delay vs expected date.", "p90_delay_days": "90th percentile of delay days.",
  "on_time_rate": "Share of received POs on time (0-1).", "spend_before_gst": "Spend on non-cancelled POs, INR before GST.",
  "spend_share": "Supplier share of total spend (0-1)."},
 "feat_sales_order": {
  "so_id": "Sales order ID.", "customer_id": "FK to dim_customer.", "branch_id": "FK to dim_branch.",
  "order_status": "Delivered or Cancelled.", "is_cancelled": "TRUE for cancelled orders.", "sales_channel": "Sales channel.",
  "payment_terms": "Payment terms.", "line_count": "Lines on the order.", "units": "Units on the order.",
  "revenue_before_gst": "Order value before GST, INR.", "revenue_incl_gst": "Order value including GST, INR.",
  "gross_margin": "Order value minus cost at master unit cost, INR.", "order_date": "Order date.",
  "order_year": "Calendar year of the order.", "order_month": "Calendar month of the order (1-12).",
  "order_to_delivery_days": "delivery date - order date. NULL for cancelled orders (placeholder date)."},
 "feat_invoice": {
  "so_id": "Sales order ID; the reliable invoice key.", "invoice_id": "Invoice ID (not unique).", "customer_id": "FK to dim_customer.",
  "branch_id": "FK to dim_branch.", "invoice_date": "Invoice date.", "due_date": "Payment due date.", "invoice_year": "Calendar year of the invoice.",
  "grand_total": "Invoice value incl. GST, INR.", "total_paid": "Payments received, INR.", "outstanding_balance": "grand_total - total_paid. Negative = overpaid.",
  "payment_status_derived": "Status derived from payments.", "invoice_id_duplicated": "TRUE if invoice_id is shared; payment timing is not computed.",
  "credit_days": "due_date - invoice_date.", "days_to_first_payment": "First payment date - invoice date.",
  "days_to_last_payment": "Last payment date - invoice date.", "days_to_pay": "Days from invoice to last payment, only for Fully paid invoices.",
  "is_paid_late": "TRUE if a fully paid invoice was settled after the due date.", "days_late_when_paid": "Days after due date at final payment (0 if on time).",
  "is_overdue": "TRUE if still unpaid at the reference date (2024-12-31) and past due.", "days_overdue": "Reference date - due date for overdue invoices."},
 "feat_customer": {
  "customer_id": "Customer ID.", "customer_type": "Customer type.", "industry_segment": "Industry segment.", "region": "Customer region.",
  "branch_id": "Serving branch.", "customer_since": "Date the customer joined.", "credit_limit": "Credit limit, INR.",
  "current_balance": "Current balance, INR.", "credit_utilisation": "current_balance / credit_limit.",
  "orders_placed": "All orders including cancelled.", "delivered_orders": "Delivered orders.", "revenue_before_gst": "Delivered revenue before GST, INR.",
  "avg_order_value": "revenue_before_gst / delivered_orders.", "first_order_date": "First delivered order date.", "last_order_date": "Last delivered order date.",
  "recency_days": "Reference date (2024-12-31) minus last delivered order.", "tenure_years": "Years from customer_since to the reference date.",
  "avg_days_to_pay": "Mean days to pay on fully paid invoices.", "late_payment_rate": "Share of fully paid invoices settled late (0-1)."},
 "feat_product": {
  "product_id": "Product ID.", "product_name": "Product name.", "category": "Category.", "machine_type": "Machine type.", "brand": "Brand.",
  "criticality_level": "Criticality level.", "unit_cost": "Unit cost, INR.", "unit_price": "Unit price, INR.", "unit_margin": "unit_price - unit_cost.",
  "margin_pct_calc": "(price - cost) / price x 100, recalculated.", "markup_pct": "(price - cost) / cost x 100.",
  "margin_pct_stored": "Margin percentage as stored in the product master.", "weight_kg": "Unit weight, kg.", "length_cm": "Length, cm.",
  "width_cm": "Width, cm.", "height_cm": "Height, cm.", "volume_m3": "Unit volume, cubic metres.", "density_kg_per_m3": "weight_kg / volume_m3.",
  "price_per_kg": "unit_price / weight_kg.", "master_lead_time_days": "Lead time in the product master."},
 "feat_monthly_demand": {
  "product_id": "FK to dim_product.", "branch_id": "FK to dim_branch.", "month_start": "First day of the month.",
  "calendar_year": "Calendar year.", "calendar_month": "Month number 1-12.", "calendar_quarter": "Calendar quarter 1-4.",
  "fiscal_year": "Indian fiscal year (April-March).", "days_in_month": "Days in the month.",
  "units_sold": "Units sold on delivered orders; 0 when none.", "revenue": "Revenue before GST, INR; 0 when none.",
  "order_lines": "Sales lines in the month.", "orders": "Distinct orders in the month.",
  "units_lag_1": "units_sold one month earlier.", "units_lag_12": "units_sold twelve months earlier.",
  "units_roll_mean_3": "Mean units_sold of the previous 3 months (current month excluded)."},
 "feat_demand_variability": {
  "product_id": "FK to dim_product.", "branch_id": "FK to dim_branch.", "months_observed": "Months in the series (72).",
  "total_units": "Total delivered units.", "mean_monthly_units": "Mean monthly units.", "std_monthly_units": "Standard deviation of monthly units.",
  "demand_cv": "std / mean of monthly units (demand variability).", "demand_months": "Months with demand.", "zero_demand_months": "Months with no demand.",
  "zero_demand_share": "zero_demand_months / months_observed.", "adi": "Average demand interval: months_observed / demand_months.",
  "cv2_nonzero": "Squared CV of non-zero monthly demand.",
  "demand_class": "Syntetos-Boylan class: Smooth, Erratic, Intermittent, Lumpy (ADI 1.32, CV2 0.49)."},
}


def _sql(name: str) -> str:
    return (FEATURE_SQL[name]
            .replace("__REF__", REF_DATE)
            .replace("__DSTART__", DEMAND_START)
            .replace("__DEND__", DEMAND_END))


def _esc(text: str) -> str:
    return text.replace("'", "''")


def build_features(con):
    """Create schema `feat`, build all feature tables, attach descriptions.

    Returns a DataFrame: table, rows, columns.
    """
    import pandas as pd
    con.execute("CREATE SCHEMA IF NOT EXISTS feat")
    rows = []
    for name in BUILD_ORDER:
        con.execute(_sql(name))
        con.execute(f"COMMENT ON TABLE feat.{name} IS '{_esc(TABLE_DESCRIPTIONS[name])}'")
        for col, text in COLUMN_DESCRIPTIONS[name].items():
            con.execute(f"COMMENT ON COLUMN feat.{name}.{col} IS '{_esc(text)}'")
        n = con.execute(f"SELECT COUNT(*) FROM feat.{name}").fetchone()[0]
        c = con.execute(f"SELECT COUNT(*) FROM duckdb_columns() "
                        f"WHERE schema_name='feat' AND table_name='{name}'").fetchone()[0]
        rows.append({"table": name, "rows": n, "columns": c})
    return pd.DataFrame(rows)


def undocumented_columns(con):
    """Feature columns that have no description (expected: none)."""
    return con.execute("""
        SELECT table_name, column_name FROM duckdb_columns()
        WHERE schema_name = 'feat' AND comment IS NULL
        ORDER BY table_name, column_index""").df()
