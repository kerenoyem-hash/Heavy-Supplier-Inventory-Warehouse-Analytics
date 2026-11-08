"""Week 2 cleaning pipeline: raw warehouse.duckdb -> data/processed/*.parquet

Run from the project folder (the one that contains warehouse.duckdb):

    python -m src.cleaning

The raw database is opened read-only and is never modified. Rows are never
deleted: problems are marked with flag columns so every decision stays visible
and reversible (see the Week 2 issue log).
"""
import os
from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = os.environ.get("WAREHOUSE_DB", "warehouse.duckdb")
OUT_DIR = Path(os.environ.get("PROCESSED_DIR", "data/processed"))
MONEY_TOLERANCE = 0.01

ALL_TABLES = [
    "branches", "products", "inventory_master", "suppliers", "customers",
    "invoices", "payments", "purchase_orders_header", "purchase_orders_lines",
    "sales_orders_header", "sales_orders_lines", "stock_ledger",
]

CATEGORICAL_COLUMNS = {
    "branches": ["warehouse_type"],
    "products": ["category", "machine_type"],
    "suppliers": ["supplier_type"],
    "customers": ["customer_type"],
    "invoices": ["payment_status"],
    "purchase_orders_header": ["po_status"],
    "sales_orders_header": ["order_status", "sales_channel"],
    "payments": ["payment_method"],
    "stock_ledger": ["movement_type"],
}

DATE_COLUMNS = {
    "products": ["last_purchase_date"],
    "customers": ["customer_since", "last_purchase_date"],
    "invoices": ["invoice_date", "due_date"],
    "payments": ["payment_date"],
    "purchase_orders_header": ["order_date", "expected_delivery_date", "received_date"],
    "sales_orders_header": ["order_date", "delivery_date"],
    "stock_ledger": ["movement_date"],
}

FK_RELATIONSHIPS = [  # (parent_table, parent_key, child_table, child_key)
    ("branches", "branch_id", "inventory_master", "branch_id"),
    ("products", "product_id", "inventory_master", "product_id"),
    ("suppliers", "supplier_id", "purchase_orders_header", "supplier_id"),
    ("branches", "branch_id", "purchase_orders_header", "branch_id"),
    ("purchase_orders_header", "po_id", "purchase_orders_lines", "po_id"),
    ("products", "product_id", "purchase_orders_lines", "product_id"),
    ("customers", "customer_id", "sales_orders_header", "customer_id"),
    ("branches", "branch_id", "sales_orders_header", "branch_id"),
    ("sales_orders_header", "so_id", "sales_orders_lines", "so_id"),
    ("products", "product_id", "sales_orders_lines", "product_id"),
    ("sales_orders_header", "so_id", "invoices", "so_id"),
    ("customers", "customer_id", "invoices", "customer_id"),
    ("branches", "branch_id", "invoices", "branch_id"),
    ("invoices", "invoice_id", "payments", "invoice_id"),
    ("products", "product_id", "stock_ledger", "product_id"),
    ("branches", "branch_id", "stock_ledger", "branch_id"),
    ("branches", "branch_id", "customers", "branch_id"),
]

PRIMARY_KEYS = {
    "branches": ["branch_id"],
    "products": ["product_id"],
    "inventory_master": ["product_id", "branch_id"],
    "suppliers": ["supplier_id"],
    "customers": ["customer_id"],
    "invoices": ["invoice_id"],
    "payments": ["payment_id"],
    "purchase_orders_header": ["po_id"],
    "purchase_orders_lines": ["po_id", "line_number"],
    "sales_orders_header": ["so_id"],
    "sales_orders_lines": ["so_id", "line_number"],
    "stock_ledger": ["movement_id"],
}

CANCELLED = "('cancelled', 'canceled')"


def connect(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Open the raw warehouse read-only."""
    return duckdb.connect(db_path, read_only=True)


def _pincode_text(series: pd.Series) -> pd.Series:
    """Postal codes are identifiers, not numbers: store as 6-character text."""
    return series.astype("Int64").astype(str).str.zfill(6)


def _trim_categoricals(table: str, df: pd.DataFrame) -> pd.DataFrame:
    for col in CATEGORICAL_COLUMNS.get(table, []):
        df[col] = df[col].str.strip()
    return df


def build_clean_tables(con: duckdb.DuckDBPyConnection) -> dict:
    """Return {table_name: cleaned DataFrame} for all 12 tables.

    Every original column is kept. New columns are additions only.
    """
    tables = {t: con.execute(f"SELECT * FROM {t}").df() for t in ALL_TABLES}

    # ---- Task 1: type casting and standardisation ------------------------
    b = tables["branches"]
    b["warehouse_capacity_sqft"] = (
        b["warehouse_capacity"].str.replace("sqft", "", regex=False).str.strip().astype(int)
    )

    p = tables["products"]
    dims = p["dimensions_cm"].str.extract(
        r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)"
    )
    dims.columns = ["length_cm", "width_cm", "height_cm"]
    p = pd.concat([p, dims.astype(float)], axis=1)
    p["volume_m3"] = p["length_cm"] * p["width_cm"] * p["height_cm"] / 1_000_000

    tables["products"] = p

    tables["suppliers"]["pincode"] = _pincode_text(tables["suppliers"]["pincode"])

    c = tables["customers"]
    c["pincode"] = _pincode_text(c["pincode"])
    # Task 3: recomputed purchase value (delivered orders only); original kept.
    recalc = con.execute("""
        SELECT customer_id,
               SUM(grand_total)       AS recalc_purchase_value_with_gst,
               SUM(total_order_value) AS recalc_purchase_value_before_gst
        FROM sales_orders_header
        WHERE LOWER(TRIM(order_status)) = 'delivered'
        GROUP BY customer_id
    """).df()
    c = c.merge(recalc, on="customer_id", how="left")
    for col in ["recalc_purchase_value_with_gst", "recalc_purchase_value_before_gst"]:
        c[col] = c[col].fillna(0.0)
    c["purchase_value_mismatch_flag"] = (
        (c["total_purchase_value"] - c["recalc_purchase_value_with_gst"]).abs()
        >= MONEY_TOLERANCE
    )
    tables["customers"] = c

    # ---- Task 3 / 4: flags that carry the issue-log decisions -------------
    tables["invoices"] = con.execute(f"""
        WITH paid AS (
            SELECT invoice_id, SUM(payment_amount) AS total_paid, COUNT(*) AS payment_count
            FROM payments GROUP BY invoice_id
        ), dup AS (
            SELECT invoice_id, COUNT(*) AS invoice_rows FROM invoices GROUP BY invoice_id
        )
        SELECT i.*,
               COALESCE(p.total_paid, 0)    AS total_paid,
               COALESCE(p.payment_count, 0) AS payment_count,
               i.grand_total - COALESCE(p.total_paid, 0) AS outstanding_balance,
               d.invoice_rows > 1 AS invoice_id_duplicated,
               CASE
                 WHEN d.invoice_rows > 1 THEN 'Ambiguous (duplicate invoice_id)'
                 WHEN COALESCE(p.total_paid, 0) <= {MONEY_TOLERANCE} THEN 'Unpaid'
                 WHEN i.grand_total - COALESCE(p.total_paid, 0) >  {MONEY_TOLERANCE} THEN 'Partially paid'
                 WHEN i.grand_total - COALESCE(p.total_paid, 0) < -{MONEY_TOLERANCE} THEN 'Overpaid'
                 ELSE 'Fully paid'
               END AS payment_status_derived
        FROM invoices i
        LEFT JOIN paid p ON i.invoice_id = p.invoice_id
        JOIN dup d       ON i.invoice_id = d.invoice_id
    """).df()

    tables["payments"] = con.execute("""
        SELECT p.*, d.payment_rows > 1 AS payment_id_duplicated
        FROM payments p
        JOIN (SELECT payment_id, COUNT(*) AS payment_rows
              FROM payments GROUP BY payment_id) d
          ON p.payment_id = d.payment_id
    """).df()

    s = tables["sales_orders_header"]
    s["is_cancelled"] = s["order_status"].str.strip().str.lower().isin(["cancelled", "canceled"])
    s["days_to_deliver"] = (
        pd.to_datetime(s["delivery_date"]) - pd.to_datetime(s["order_date"])
    ).dt.days

    po = tables["purchase_orders_header"]
    po["is_cancelled"] = po["po_status"].str.strip().str.lower().isin(["cancelled", "canceled"])

    im = tables["inventory_master"]
    im["current_above_max_flag"] = im["current_stock"] > im["max_stock"]

    # ---- Task 1: categorical clean-up (trim only; no spelling clashes found)
    for name in list(tables):
        tables[name] = _trim_categoricals(name, tables[name])
    return tables


def export_parquet(tables: dict, out_dir=OUT_DIR) -> pd.DataFrame:
    """Write each table to <out_dir>/<table>.parquet and return a summary."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mem = duckdb.connect()          # separate in-memory connection: raw DB untouched
    rows = []
    for name, df in tables.items():
        path = out_dir / f"{name}.parquet"
        mem.register("tmp_table", df)
        mem.execute(f"COPY tmp_table TO '{path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        mem.unregister("tmp_table")
        rows.append({"table": name, "rows": len(df), "columns": df.shape[1],
                     "file_size_kb": round(path.stat().st_size / 1024, 1)})
    return pd.DataFrame(rows)


def run_pipeline(db_path: str = DB_PATH, out_dir=OUT_DIR) -> pd.DataFrame:
    con = connect(db_path)
    try:
        return export_parquet(build_clean_tables(con), out_dir)
    finally:
        con.close()


if __name__ == "__main__":
    print(run_pipeline().to_string(index=False))
