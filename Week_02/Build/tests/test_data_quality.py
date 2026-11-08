"""Week 2 automated data-quality tests (pytest).

Run on every data refresh:   python -m pytest tests -v

Two kinds of test:
  * RULE tests assert zero exceptions (a failure is a new data problem).
  * KNOWN-ISSUE tests pin a documented problem to its recorded size, so the
    suite stays green today but fails if the problem grows or changes.
    These are marked KNOWN ISSUE and map to the issue log (Task 6).
"""
import pytest

from src.cleaning import (
    ALL_TABLES, CANCELLED, CATEGORICAL_COLUMNS, DATE_COLUMNS,
    FK_RELATIONSHIPS, PRIMARY_KEYS,
)

TOL = 0.01

EXPECTED_ROWS = {
    "branches": 6, "products": 30, "inventory_master": 180, "suppliers": 8,
    "customers": 500, "invoices": 18033, "payments": 19257,
    "purchase_orders_header": 24000, "purchase_orders_lines": 155495,
    "sales_orders_header": 20000, "sales_orders_lines": 130402,
    "stock_ledger": 237230,
}
ALLOWED_NULLS = {("purchase_orders_header", "received_date")}   # cancelled POs

# Recorded sizes of documented (not yet fixed) issues - see the issue log.
KNOWN_DUPLICATE_KEYS = {"invoices": 197, "payments": 202}       # surplus rows
KNOWN_UNMATCHED_REGION_CUSTOMERS = 22
KNOWN_CURRENT_STOCK_NOT_REACHABLE = 9


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


# --------------------------------------------------------------- structure
@pytest.mark.parametrize("table", ALL_TABLES)
def test_raw_row_count(con, table):
    assert scalar(con, f"SELECT COUNT(*) FROM {table}") == EXPECTED_ROWS[table]


@pytest.mark.parametrize("table", ALL_TABLES)
def test_no_unexpected_nulls(con, table):
    cols = [r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()]
    bad = {c: scalar(con, f"SELECT COUNT(*) - COUNT({c}) FROM {table}")
           for c in cols if (table, c) not in ALLOWED_NULLS}
    assert {c: n for c, n in bad.items() if n} == {}


@pytest.mark.parametrize("table,col", [(t, c) for t, cs in DATE_COLUMNS.items() for c in cs])
def test_date_columns_are_dates(con, table, col):
    types = {row[0]: row[1] for row in con.execute(f"DESCRIBE {table}").fetchall()}
    assert types[col] == "DATE"


@pytest.mark.parametrize("table,col", [(t, c) for t, cs in CATEGORICAL_COLUMNS.items() for c in cs])
def test_categorical_values_have_one_spelling(con, table, col):
    distinct_raw = scalar(con, f"SELECT COUNT(DISTINCT {col}) FROM {table}")
    distinct_clean = scalar(con, f"SELECT COUNT(DISTINCT LOWER(TRIM({col}))) FROM {table}")
    assert distinct_raw == distinct_clean


# -------------------------------------------------------------------- keys
UNIQUE_TABLES = [t for t in PRIMARY_KEYS if t not in KNOWN_DUPLICATE_KEYS]


@pytest.mark.parametrize("table", UNIQUE_TABLES)
def test_primary_key_unique(con, table):
    cols = ", ".join(PRIMARY_KEYS[table])
    total = scalar(con, f"SELECT COUNT(*) FROM {table}")
    distinct = scalar(con, f"SELECT COUNT(*) FROM (SELECT DISTINCT {cols} FROM {table})")
    assert total == distinct


@pytest.mark.parametrize("table", list(KNOWN_DUPLICATE_KEYS))
def test_known_issue_duplicate_ids_not_growing(con, table):
    """KNOWN ISSUE: invoice_id / payment_id are reused by different records."""
    key = PRIMARY_KEYS[table][0]
    total = scalar(con, f"SELECT COUNT(*) FROM {table}")
    distinct = scalar(con, f"SELECT COUNT(DISTINCT {key}) FROM {table}")
    assert total - distinct == KNOWN_DUPLICATE_KEYS[table]


@pytest.mark.parametrize("parent,pkey,child,ckey", FK_RELATIONSHIPS)
def test_foreign_key_has_no_orphans_or_nulls(con, parent, pkey, child, ckey):
    bad = scalar(con, f"""
        SELECT COUNT(*) FROM {child} c
        WHERE c.{ckey} IS NULL
           OR NOT EXISTS (SELECT 1 FROM {parent} p WHERE p.{pkey} = c.{ckey})
    """)
    assert bad == 0


# ----------------------------------------------------------------- finance
@pytest.mark.parametrize("lines,price", [("sales_orders_lines", "unit_price"),
                                         ("purchase_orders_lines", "unit_cost")])
def test_line_arithmetic(con, lines, price):
    bad = scalar(con, f"""
        SELECT COUNT(*) FROM {lines}
        WHERE ABS(line_total - quantity * {price}) >= {TOL}
           OR ABS(gst_amount - line_total * gst_rate / 100.0) >= {TOL}
           OR ABS(line_grand_total - (line_total + gst_amount)) >= {TOL}
    """)
    assert bad == 0


def test_sales_gst_rates_are_18_or_28(con):
    assert scalar(con, "SELECT COUNT(*) FROM sales_orders_lines WHERE gst_rate NOT IN (18, 28)") == 0


@pytest.mark.parametrize("header,lines,key,h_base,h_gst,h_grand", [
    ("sales_orders_header", "sales_orders_lines", "so_id",
     "total_order_value", "total_gst_amount", "grand_total"),
    ("purchase_orders_header", "purchase_orders_lines", "po_id",
     "total_cost", "total_gst_amount", "grand_total"),
])
def test_header_totals_equal_line_totals(con, header, lines, key, h_base, h_gst, h_grand):
    bad = scalar(con, f"""
        SELECT COUNT(*) FROM {header} h
        LEFT JOIN (SELECT {key}, SUM(line_total) b, SUM(gst_amount) g, SUM(line_grand_total) t
                   FROM {lines} GROUP BY {key}) l ON h.{key} = l.{key}
        WHERE l.t IS NULL
           OR ABS(h.{h_base} - l.b) >= {TOL}
           OR ABS(h.{h_gst} - l.g) >= {TOL}
           OR ABS(h.{h_grand} - l.t) >= {TOL}
    """)
    assert bad == 0


def test_no_invoice_for_a_cancelled_order(con):
    bad = scalar(con, f"""
        SELECT COUNT(*) FROM invoices i
        JOIN sales_orders_header h ON i.so_id = h.so_id
        WHERE LOWER(TRIM(h.order_status)) IN {CANCELLED}
    """)
    assert bad == 0


# ---------------------------------------------------------- business rules
def test_cancelled_pos_have_no_received_date(con):
    assert scalar(con, f"""SELECT COUNT(*) FROM purchase_orders_header
        WHERE LOWER(TRIM(po_status)) IN {CANCELLED} AND received_date IS NOT NULL""") == 0


def test_active_pos_have_a_received_date(con):
    assert scalar(con, f"""SELECT COUNT(*) FROM purchase_orders_header
        WHERE LOWER(TRIM(po_status)) NOT IN {CANCELLED} AND received_date IS NULL""") == 0


def test_po_dates_are_in_order(con):
    assert scalar(con, """SELECT COUNT(*) FROM purchase_orders_header
        WHERE received_date < order_date OR expected_delivery_date < order_date""") == 0


def test_delivery_not_before_order(con):
    assert scalar(con, "SELECT COUNT(*) FROM sales_orders_header WHERE delivery_date < order_date") == 0


def test_known_issue_customers_in_regions_without_branch(con):
    """KNOWN ISSUE (accepted): customers in regions with no local branch."""
    n = scalar(con, """
        SELECT COUNT(*) FROM customers c
        WHERE c.region IS NOT NULL AND TRIM(c.region) <> ''
          AND NOT EXISTS (SELECT 1 FROM branches b
                          WHERE LOWER(TRIM(b.region)) = LOWER(TRIM(c.region)))""")
    assert n <= KNOWN_UNMATCHED_REGION_CUSTOMERS


# ------------------------------------------------------------------- stock
def test_stock_movement_types_and_quantities(con):
    types = {r[0] for r in con.execute("SELECT DISTINCT movement_type FROM stock_ledger").fetchall()}
    assert types == {"IN", "OUT", "ADJUSTMENT"}
    assert scalar(con, "SELECT COUNT(*) FROM stock_ledger WHERE quantity <= 0") == 0
    assert scalar(con, "SELECT COUNT(*) FROM inventory_master WHERE opening_stock < 0 OR current_stock < 0") == 0


_EXPECTED_CTE = """
WITH exp AS (
    SELECT i.product_id, i.branch_id, i.current_stock,
           CAST(i.opening_stock
                + COALESCE(SUM(CASE WHEN s.movement_type = 'IN'  THEN s.quantity END), 0)
                - COALESCE(SUM(CASE WHEN s.movement_type = 'OUT' THEN s.quantity END), 0) AS BIGINT) AS expected,
           CAST(COALESCE(SUM(CASE WHEN s.movement_type = 'ADJUSTMENT' THEN s.quantity END), 0) AS BIGINT) AS adj
    FROM inventory_master i
    LEFT JOIN stock_ledger s ON i.product_id = s.product_id AND i.branch_id = s.branch_id
    GROUP BY i.product_id, i.branch_id, i.opening_stock, i.current_stock
)
"""

# A balance B is reachable when |B - expected| <= total adjustments and has the
# same parity (a signed sum of positive quantities).
_LEDGER_NOT_REACHABLE = _EXPECTED_CTE.rstrip() + """, last_day AS (
    SELECT s.product_id, s.branch_id, s.running_balance
    FROM stock_ledger s
    JOIN (SELECT product_id, branch_id, MAX(movement_date) AS d
          FROM stock_ledger GROUP BY product_id, branch_id) l
      ON s.product_id = l.product_id AND s.branch_id = l.branch_id AND s.movement_date = l.d
)
SELECT COUNT(*) FROM exp e
WHERE NOT EXISTS (
    SELECT 1 FROM last_day l
    WHERE l.product_id = e.product_id AND l.branch_id = e.branch_id
      AND ABS(l.running_balance - e.expected) <= e.adj
      AND (e.adj - ABS(l.running_balance - e.expected)) % 2 = 0)
"""

_CURRENT_NOT_REACHABLE = _EXPECTED_CTE + """
SELECT COUNT(*) FROM exp e
WHERE ABS(e.current_stock - e.expected) > e.adj
   OR (e.adj - ABS(e.current_stock - e.expected)) % 2 <> 0
"""


def test_ledger_balance_reachable_with_signed_adjustments(con):
    """Opening + IN - OUT +/- adjustments reaches the ledger balance (order-independent)."""
    assert scalar(con, _LEDGER_NOT_REACHABLE) == 0


def test_known_issue_current_stock_not_reachable(con):
    """KNOWN ISSUE: current_stock disagrees with the ledger for a few pairs."""
    assert scalar(con, _CURRENT_NOT_REACHABLE) <= KNOWN_CURRENT_STOCK_NOT_REACHABLE


# ------------------------------------------------------- processed (parquet)
def _parquet(processed_dir, table):
    path = processed_dir / f"{table}.parquet"
    assert path.exists(), f"{path} is missing - run `python -m src.cleaning` first"
    return path.as_posix()


@pytest.mark.parametrize("table", ALL_TABLES)
def test_processed_row_count_matches_raw(con, processed_dir, table):
    path = _parquet(processed_dir, table)
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{path}')") == EXPECTED_ROWS[table]


def test_processed_capacity_and_volume_are_numeric(con, processed_dir):
    b, p = _parquet(processed_dir, "branches"), _parquet(processed_dir, "products")
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{b}') "
                       "WHERE warehouse_capacity_sqft IS NULL OR warehouse_capacity_sqft <= 0") == 0
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{p}') "
                       "WHERE volume_m3 IS NULL OR volume_m3 <= 0") == 0


@pytest.mark.parametrize("table", ["customers", "suppliers"])
def test_processed_pincode_is_six_digit_text(con, processed_dir, table):
    path = _parquet(processed_dir, table)
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{path}') "
                       "WHERE NOT regexp_matches(CAST(pincode AS VARCHAR), '^[0-9]{6}$')") == 0


def test_processed_invoice_status_is_complete(con, processed_dir):
    path = _parquet(processed_dir, "invoices")
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{path}') "
                       "WHERE payment_status_derived IS NULL") == 0
    ambiguous = scalar(con, f"SELECT COUNT(*) FROM read_parquet('{path}') "
                            "WHERE payment_status_derived LIKE 'Ambiguous%'")
    flagged = scalar(con, f"SELECT COUNT(*) FROM read_parquet('{path}') WHERE invoice_id_duplicated")
    assert ambiguous == flagged


def test_processed_cancelled_flags_match_status(con, processed_dir):
    so = _parquet(processed_dir, "sales_orders_header")
    po = _parquet(processed_dir, "purchase_orders_header")
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{so}') WHERE is_cancelled") == \
        scalar(con, f"SELECT COUNT(*) FROM sales_orders_header WHERE LOWER(TRIM(order_status)) IN {CANCELLED}")
    assert scalar(con, f"SELECT COUNT(*) FROM read_parquet('{po}') WHERE is_cancelled") == \
        scalar(con, f"SELECT COUNT(*) FROM purchase_orders_header WHERE LOWER(TRIM(po_status)) IN {CANCELLED}")
