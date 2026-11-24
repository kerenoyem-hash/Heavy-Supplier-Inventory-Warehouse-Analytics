"""Week 4 helper: product performance, ABC-XYZ, velocity, trend and seasonality.

Used by notebooks/04_product_performance.ipynb. You never run this file
directly: the notebook imports it with

    import src.product_analysis as pa

Business logic lives here; the notebook calls the functions and explains results.

Key assumptions (also stated in the notebook):
  * Cancelled sales orders are excluded everywhere (is_cancelled = True).
  * Revenue = sales_orders_lines.line_total (before GST).
  * Cost of goods = quantity x products.unit_cost.
  * Gross margin = revenue - cost of goods.
  * Branch = sales_orders_header.branch_id (label = branches.city).
  * Demand = units sold (quantity) per calendar month by order_date.
"""
from __future__ import annotations

import calendar
import math
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path("data/processed")
SALES_TABLES = ("sales_orders_header", "sales_orders_lines", "products",
                "branches", "inventory_master")
ABC_LABELS = ["A", "B", "C"]
XYZ_LABELS = ["X", "Y", "Z"]


# --------------------------------------------------------------------------
# 1. Loading and the base dataset
# --------------------------------------------------------------------------
def load_tables(processed_dir=PROCESSED_DIR) -> dict:
    """Read the Week 2 Parquet files we need into pandas DataFrames."""
    import duckdb                      # same engine used in Weeks 1-2

    folder = Path(processed_dir)
    con = duckdb.connect()
    try:
        tables = {}
        for name in SALES_TABLES:
            path = (folder / f"{name}.parquet").as_posix()
            tables[name] = con.execute(f"SELECT * FROM read_parquet('{path}')").df()
    finally:
        con.close()
    return tables


def build_sales_base(tables: dict) -> pd.DataFrame:
    """One row per sales-order line, delivered orders only, with product and branch info.

    Adds: order_month, year, month, revenue, cogs, gross_margin, branch.
    """
    header = tables["sales_orders_header"][
        ["so_id", "customer_id", "branch_id", "order_date", "is_cancelled"]]
    lines = tables["sales_orders_lines"][
        ["so_id", "line_number", "product_id", "quantity", "unit_price",
         "gst_rate", "line_total"]]
    products = tables["products"][
        ["product_id", "product_name", "category", "machine_type", "brand", "unit_cost"]]
    branches = tables["branches"][["branch_id", "city"]].rename(columns={"city": "branch"})

    base = (lines.merge(header, on="so_id", how="inner", validate="m:1")
                 .merge(products, on="product_id", how="left", validate="m:1")
                 .merge(branches, on="branch_id", how="left", validate="m:1"))
    base = base[~base["is_cancelled"].astype(bool)].copy()

    base["order_date"] = pd.to_datetime(base["order_date"]).dt.normalize()
    base["order_month"] = base["order_date"].dt.to_period("M").dt.to_timestamp()
    base["year"] = base["order_date"].dt.year
    base["month"] = base["order_date"].dt.month
    base["revenue"] = base["line_total"].astype(float)
    base["cogs"] = base["quantity"].astype(float) * base["unit_cost"].astype(float)
    base["gross_margin"] = base["revenue"] - base["cogs"]
    return base.reset_index(drop=True)


def reconcile_base(base: pd.DataFrame, tables: dict, tol: float = 1.0) -> pd.DataFrame:
    """Check that the base dataset agrees with the order headers (Week 2 totals)."""
    h = tables["sales_orders_header"]
    h_ok = h[~h["is_cancelled"].astype(bool)]
    l = tables["sales_orders_lines"]
    l_ok = l[l["so_id"].isin(h_ok["so_id"])]

    rows = [
        ("Delivered orders: base vs header", base["so_id"].nunique(), len(h_ok)),
        ("Order lines: base vs lines table", len(base), len(l_ok)),
        ("Revenue before GST: base vs header total_order_value",
         float(base["revenue"].sum()), float(h_ok["total_order_value"].sum())),
        ("Lines with no product match", int(base["product_name"].isna().sum()), 0),
        ("Lines with no branch match", int(base["branch"].isna().sum()), 0),
    ]
    out = pd.DataFrame(rows, columns=["check", "base_value", "expected_value"])
    out["difference"] = out["base_value"] - out["expected_value"]
    out["status"] = np.where(out["difference"].abs() <= tol, "PASS", "CHECK")
    return out


def month_range(base: pd.DataFrame) -> pd.DatetimeIndex:
    """Every calendar month from the first to the last order (so zero-demand months count)."""
    return pd.date_range(base["order_month"].min(), base["order_month"].max(), freq="MS")


def overall_kpis(base: pd.DataFrame) -> pd.DataFrame:
    revenue, margin = base["revenue"].sum(), base["gross_margin"].sum()
    orders = base["so_id"].nunique()
    vals = {
        "first_order_date": base["order_date"].min().date(),
        "last_order_date": base["order_date"].max().date(),
        "delivered_orders": orders,
        "order_lines": len(base),
        "units_sold": int(base["quantity"].sum()),
        "revenue_inr": revenue,
        "gross_margin_inr": margin,
        "gross_margin_pct": margin / revenue * 100,
        "avg_order_value_inr": revenue / orders,
        "products_sold": base["product_id"].nunique(),
        "branches": base["branch_id"].nunique(),
    }
    return pd.Series(vals, name="value").to_frame()


# --------------------------------------------------------------------------
# 2. Performance summaries and Pareto (B1)
# --------------------------------------------------------------------------
def summarise_by(base: pd.DataFrame, by) -> pd.DataFrame:
    """Revenue, units, margin, margin %, orders, AOV and revenue share for any grouping."""
    by = [by] if isinstance(by, str) else list(by)
    g = base.groupby(by, dropna=False).agg(
        revenue=("revenue", "sum"),
        units=("quantity", "sum"),
        gross_margin=("gross_margin", "sum"),
        orders=("so_id", "nunique"),
        order_lines=("line_number", "size"),
    ).reset_index()
    g["margin_pct"] = g["gross_margin"] / g["revenue"] * 100
    g["aov"] = g["revenue"] / g["orders"]
    total = g["revenue"].sum()
    g["revenue_share_pct"] = g["revenue"] / total * 100 if total else np.nan
    return g.sort_values("revenue", ascending=False).reset_index(drop=True)


def pareto_table(summary: pd.DataFrame, value_col: str = "revenue") -> pd.DataFrame:
    """Sort descending and add rank, share and cumulative share (%)."""
    t = summary.sort_values(value_col, ascending=False).reset_index(drop=True).copy()
    v = t[value_col].clip(lower=0)
    t["rank"] = np.arange(1, len(t) + 1)
    t["share_pct"] = v / v.sum() * 100
    t["cum_share_pct"] = t["share_pct"].cumsum()
    t["cum_items_pct"] = t["rank"] / len(t) * 100
    return t


def items_for_share(pareto: pd.DataFrame, share: float = 80) -> int:
    """How many top items are needed to reach `share` % of the total."""
    return int((pareto["cum_share_pct"].shift(fill_value=0) < share).sum())


# --------------------------------------------------------------------------
# 3. Monthly demand matrix, ABC and XYZ (B7)
# --------------------------------------------------------------------------
def _key_index(universe: pd.DataFrame, by: list):
    if len(by) == 1:
        return pd.Index(universe[by[0]].values, name=by[0])
    return pd.MultiIndex.from_frame(universe[by])


def monthly_matrix(base: pd.DataFrame, by, value: str = "quantity",
                   months=None, universe: pd.DataFrame | None = None) -> pd.DataFrame:
    """Rows = items (e.g. product), columns = every month, values = sum of `value`.

    Missing months are filled with 0. `universe` (optional) lists every item that
    should appear, so items that never sold show up as all zeros.
    """
    by = [by] if isinstance(by, str) else list(by)
    if months is None:
        months = month_range(base)
    m = (base.groupby(by + ["order_month"])[value].sum()
             .unstack("order_month").reindex(columns=months).fillna(0.0))
    if universe is not None:
        m = m.reindex(m.index.union(_key_index(universe, by))).fillna(0.0)
    m.columns = pd.DatetimeIndex(m.columns)
    return m.sort_index()


def cv_table(matrix: pd.DataFrame) -> pd.DataFrame:
    """Mean, standard deviation and coefficient of variation of monthly demand."""
    mean = matrix.mean(axis=1)
    std = matrix.std(axis=1, ddof=0)
    out = pd.DataFrame({"mean_monthly_units": mean, "std_monthly_units": std,
                        "cv": std / mean.replace(0, np.nan),
                        "months_with_demand": (matrix > 0).sum(axis=1)})
    return out.reset_index()


def assign_abc(values: pd.Series, a_cut: float = 80, b_cut: float = 95) -> pd.Series:
    """A = items that bring cumulative share to a_cut %, B = up to b_cut %, C = the rest.

    An item is A if the cumulative share BEFORE it is still below a_cut, so the item
    that crosses the line is included in the class.
    """
    v = values.reset_index(drop=True).clip(lower=0)
    order = v.sort_values(ascending=False, kind="mergesort").index
    share = v.loc[order] / v.sum() * 100
    before = share.cumsum() - share
    cls = np.where(before < a_cut, "A", np.where(before < b_cut, "B", "C"))
    return pd.Series(cls, index=order).sort_index().set_axis(values.index)


def classify_xyz(cv: pd.Series, x_cut: float = 0.5, y_cut: float = 1.0) -> pd.Series:
    """X = steady (cv < x_cut), Y = variable (< y_cut), Z = erratic or no demand."""
    return pd.Series(np.where(cv < x_cut, "X", np.where(cv < y_cut, "Y", "Z")),
                     index=cv.index)


def classify_abc_xyz(base: pd.DataFrame, by=("product_id",), universe=None,
                     x_cut: float = 0.5, y_cut: float = 1.0,
                     a_cut: float = 80, b_cut: float = 95, months=None) -> pd.DataFrame:
    """ABC (revenue and margin) combined with XYZ (CV of monthly units)."""
    by = list(by)
    s = summarise_by(base, by)[by + ["revenue", "units", "gross_margin", "revenue_share_pct"]]
    if universe is not None:
        s = universe[by].drop_duplicates().merge(s, on=by, how="left")
        for c in ["revenue", "units", "gross_margin", "revenue_share_pct"]:
            s[c] = s[c].fillna(0)
    s = s.sort_values("revenue", ascending=False).reset_index(drop=True)
    s["abc_revenue"] = assign_abc(s["revenue"], a_cut, b_cut)
    s["abc_margin"] = assign_abc(s["gross_margin"], a_cut, b_cut)

    matrix = monthly_matrix(base, by, "quantity", months, universe)
    out = s.merge(cv_table(matrix), on=by, how="left")
    out["xyz"] = classify_xyz(out["cv"], x_cut, y_cut)       # NaN cv (no demand) -> Z
    out["abc_xyz"] = out["abc_revenue"] + out["xyz"]
    out["abc_margin_xyz"] = out["abc_margin"] + out["xyz"]
    return out


def abc_xyz_matrix(df: pd.DataFrame, abc_col: str = "abc_revenue",
                   xyz_col: str = "xyz") -> pd.DataFrame:
    """3 x 3 count of items per ABC-XYZ cell (always shows all nine cells)."""
    return (pd.crosstab(df[abc_col], df[xyz_col])
              .reindex(index=ABC_LABELS, columns=XYZ_LABELS, fill_value=0))


# --------------------------------------------------------------------------
# 4. Velocity (B2)
# --------------------------------------------------------------------------
def velocity_table(base: pd.DataFrame, by=("product_id",), universe=None) -> pd.DataFrame:
    """Units per month, order lines per month, days with demand, and a 0-100 velocity score.

    Score = average percentile rank of the three measures x 100.
    Class: top third = Fast, middle third = Medium, bottom third = Slow,
    and items with no sales at all = No sales.
    """
    by = list(by)
    n_months = len(month_range(base))
    n_days = (base["order_date"].max() - base["order_date"].min()).days + 1

    g = base.groupby(by).agg(
        units=("quantity", "sum"),
        order_lines=("line_number", "size"),
        days_with_demand=("order_date", "nunique"),
        months_with_demand=("order_month", "nunique"),
    ).reset_index()
    if universe is not None:
        g = universe[by].drop_duplicates().merge(g, on=by, how="left").fillna(0)

    g["units_per_month"] = g["units"] / n_months
    g["order_lines_per_month"] = g["order_lines"] / n_months
    g["pct_days_with_demand"] = g["days_with_demand"] / n_days * 100
    parts = [g[c].rank(pct=True) for c in
             ("units_per_month", "order_lines_per_month", "days_with_demand")]
    g["velocity_score"] = sum(parts) / len(parts) * 100

    pct = g["velocity_score"].rank(pct=True, method="first")
    g["velocity_class"] = np.where(pct > 2 / 3, "Fast", np.where(pct > 1 / 3, "Medium", "Slow"))
    g.loc[g["units"] == 0, "velocity_class"] = "No sales"
    return g.sort_values("velocity_score", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# 5. Trend, seasonality, growth (B9)
# --------------------------------------------------------------------------
def mann_kendall(x, alpha: float = 0.05) -> dict:
    """Mann-Kendall trend test (with tie correction) and Sen's slope."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 4:
        return {"mk_trend": "n/a", "mk_p": np.nan, "mk_tau": np.nan, "sen_slope": np.nan}
    i, j = np.triu_indices(n, 1)
    diff = x[j] - x[i]
    s = np.sign(diff).sum()
    _, counts = np.unique(x, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5) - (counts * (counts - 1) * (2 * counts + 5)).sum()) / 18
    if var_s <= 0:
        return {"mk_trend": "no trend", "mk_p": 1.0, "mk_tau": 0.0, "sen_slope": 0.0}
    z = (s - 1) / math.sqrt(var_s) if s > 0 else (s + 1) / math.sqrt(var_s) if s < 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    label = "no trend" if p >= alpha else ("increasing" if z > 0 else "decreasing")
    return {"mk_trend": label, "mk_p": p, "mk_tau": s / (n * (n - 1) / 2),
            "sen_slope": float(np.median(diff / (j - i)))}


def stl_components(series: pd.Series, period: int = 12, robust: bool = True) -> pd.DataFrame:
    """STL decomposition into trend, seasonal and residual (needs statsmodels)."""
    from statsmodels.tsa.seasonal import STL

    idx = pd.date_range(start=pd.Timestamp(series.index[0]), periods=len(series), freq="MS")
    y = pd.Series(np.asarray(series, dtype=float), index=idx)
    res = STL(y, period=period, robust=robust).fit()
    return pd.DataFrame({"observed": y, "trend": res.trend,
                         "seasonal": res.seasonal, "resid": res.resid})


def _strength(resid: pd.Series, other: pd.Series) -> float:
    total = (other + resid).var()
    return float(max(0.0, 1 - resid.var() / total)) if total > 0 else np.nan


def trend_stats(series: pd.Series, period: int = 12, alpha: float = 0.05) -> dict:
    """STL strengths plus a Mann-Kendall test on the de-seasonalised series."""
    y = series.astype(float)
    out = {"months": len(y), "total_units": y.sum(), "mean_monthly_units": y.mean()}
    comps = None
    if len(y) >= 2 * period and y.std() > 0:
        try:
            comps = stl_components(y, period)
        except Exception:                      # e.g. too few non-zero points
            comps = None
    if comps is not None:
        deseason = comps["trend"] + comps["resid"]
        out["trend_strength"] = _strength(comps["resid"], comps["trend"])
        out["seasonal_strength"] = _strength(comps["resid"], comps["seasonal"])
        by_month = comps["seasonal"].groupby(comps.index.month).mean()
        out["peak_month"] = calendar.month_abbr[int(by_month.idxmax())]
        out["low_month"] = calendar.month_abbr[int(by_month.idxmin())]
    else:
        deseason = y
        out.update(trend_strength=np.nan, seasonal_strength=np.nan,
                   peak_month=None, low_month=None)
    mk = mann_kendall(deseason.values, alpha)
    out.update(mk)
    mean = y.mean()
    out["trend_pct_per_year"] = mk["sen_slope"] * 12 / mean * 100 if mean else np.nan
    return out


def trend_table(matrix: pd.DataFrame, period: int = 12, alpha: float = 0.05) -> pd.DataFrame:
    """Run trend_stats on every row of a monthly matrix."""
    names = list(matrix.index.names)
    rows = []
    for key, row in matrix.iterrows():
        key = key if isinstance(key, tuple) else (key,)
        d = dict(zip(names, key))
        d.update(trend_stats(row, period, alpha))
        rows.append(d)
    return pd.DataFrame(rows)


def seasonal_profile(series: pd.Series) -> pd.Series:
    """Average demand per calendar month as an index (100 = average month)."""
    by_month = series.groupby(series.index.month).mean()
    return by_month / series.mean() * 100


def growth_table(matrix: pd.DataFrame) -> pd.DataFrame:
    """Yearly units, last year-on-year growth % and CAGR % per row."""
    yearly = matrix.T.groupby(matrix.columns.year).sum().T
    years = list(yearly.columns)
    first, last = yearly[years[0]], yearly[years[-1]]
    n = len(years) - 1
    out = yearly.copy()
    out.columns = [f"units_{y}" for y in years]
    out["yoy_last_pct"] = (last / yearly[years[-2]].replace(0, np.nan) - 1) * 100
    ok = (first > 0) & (last > 0)
    out["cagr_pct"] = np.where(ok, ((last / first.where(first > 0)) ** (1 / n) - 1) * 100, np.nan)
    return out.reset_index()


def attach_labels(df: pd.DataFrame, tables: dict) -> pd.DataFrame:
    """Add product name/category/brand and branch city next to the key columns."""
    out = df.copy()
    added = []
    if "product_id" in out.columns:
        lab = tables["products"][["product_id", "product_name", "category", "brand",
                                  "machine_type"]]
        new = [c for c in lab.columns if c == "product_id" or c not in out.columns]
        out = out.merge(lab[new], on="product_id", how="left")
        added += [c for c in new if c != "product_id"]
    if "branch_id" in out.columns and "branch" not in out.columns:
        lab = tables["branches"][["branch_id", "city"]].rename(columns={"city": "branch"})
        out = out.merge(lab, on="branch_id", how="left")
        added.append("branch")
    keys = [c for c in ("product_id", "branch_id") if c in out.columns]
    rest = [c for c in out.columns if c not in keys + added]
    return out[keys + added + rest]


# --------------------------------------------------------------------------
# 6. Charts (every chart gets a title, units and a one-line takeaway)
# --------------------------------------------------------------------------
def _plt():
    import matplotlib.pyplot as plt
    return plt


def inr_m(x: float) -> str:
    """Format rupees in millions for text."""
    return f"INR {x / 1e6:,.1f} M"


def save_chart(fig, name: str, takeaway: str, out_dir) -> Path:
    """Add the one-line takeaway under the chart, save a PNG, then show it."""
    plt = _plt()
    note = textwrap.fill("Takeaway: " + takeaway, 110)
    fig.tight_layout()
    fig.text(0.01, -0.01, note, fontsize=9, style="italic", ha="left", va="top")
    path = Path(out_dir) / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return path


def plot_pareto(t: pd.DataFrame, label_col: str, value_col: str, title: str, ylabel: str):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(t[label_col].astype(str), t[value_col] / 1e6, color="#4C72B0")
    ax.set_ylabel(ylabel)
    ax.set_xlabel(label_col.replace("_", " ").title())
    ax.tick_params(axis="x", rotation=90)
    ax2 = ax.twinx()
    ax2.plot(range(len(t)), t["cum_share_pct"], color="#C44E52", marker="o", ms=4)
    ax2.axhline(80, color="grey", ls="--", lw=1)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative share (%)")
    ax2.grid(False)
    ax.set_title(title)
    return fig


def plot_bar_panel(panels: list, value_col: str = "revenue", xlabel: str = "Revenue (INR million)"):
    """panels = [(title, DataFrame, label_col), ...] drawn as horizontal bars (up to 4)."""
    plt = _plt()
    rows = int(np.ceil(len(panels) / 2))
    fig, axes = plt.subplots(rows, 2, figsize=(12, 4.2 * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax, (title, df, label) in zip(axes, panels):
        d = df.sort_values(value_col)
        ax.barh(d[label].astype(str), d[value_col] / 1e6, color="#55A868")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
    for ax in axes[len(panels):]:
        ax.axis("off")
    return fig


def plot_year_bars(yr: pd.DataFrame):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(yr["year"].astype(str), yr["revenue"] / 1e6, color="#4C72B0", label="Revenue")
    ax.set_xlabel("Year")
    ax.set_ylabel("Revenue (INR million)")
    ax2 = ax.twinx()
    ax2.plot(yr["year"].astype(str), yr["margin_pct"], color="#C44E52", marker="o",
             label="Gross margin %")
    ax2.set_ylabel("Gross margin (%)")
    ax2.grid(False)
    ax.set_title("Revenue and gross margin % by year")
    return fig


def plot_hist(values: pd.Series, cuts: tuple, title: str, xlabel: str):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(values.dropna(), bins=20, color="#8172B2", edgecolor="white")
    for c in cuts:
        ax.axvline(c, color="#C44E52", ls="--")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of items")
    return fig


def plot_matrices(items: list, cbar_label: str = "Number of items"):
    """items = [(title, 3x3 DataFrame), ...] drawn side by side as annotated heatmaps."""
    plt = _plt()
    fig, axes = plt.subplots(1, len(items), figsize=(5.2 * len(items), 4.4))
    axes = np.atleast_1d(axes)
    for ax, (title, m) in zip(axes, items):
        im = ax.imshow(m.values, cmap="Blues")
        ax.set_xticks(range(3), ["X (steady)", "Y (variable)", "Z (erratic)"])
        ax.set_yticks(range(3), ["A", "B", "C"])
        ax.set_title(title)
        ax.grid(False)
        top = m.values.max() if m.values.max() else 1
        for r in range(3):
            for c in range(3):
                v = m.values[r, c]
                ax.text(c, r, int(v), ha="center", va="center",
                        color="white" if v > top / 2 else "black", fontsize=13)
    return fig


def plot_velocity(vel: pd.DataFrame, label_col: str = "product_id"):
    plt = _plt()
    colors = {"Fast": "#55A868", "Medium": "#CCB974", "Slow": "#C44E52", "No sales": "#7f7f7f"}
    d = vel.sort_values("velocity_score")
    fig, ax = plt.subplots(figsize=(9, 0.28 * len(d) + 2))
    ax.barh(d[label_col].astype(str), d["velocity_score"],
            color=[colors[c] for c in d["velocity_class"]])
    ax.set_xlabel("Velocity score (0-100)")
    ax.set_title("Product velocity score (green = Fast, yellow = Medium, red = Slow)")
    return fig


def plot_monthly(series: pd.Series, title: str, ylabel: str, scale: float = 1.0):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(series.index, series / scale, color="#4C72B0", lw=1.2, label="Monthly")
    ax.plot(series.index, series.rolling(12).mean() / scale, color="#C44E52", lw=2,
            label="12-month average")
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.legend()
    return fig


def plot_seasonal_index(profile: pd.Series, title: str):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar([calendar.month_abbr[m] for m in profile.index], profile.values, color="#8172B2")
    ax.axhline(100, color="grey", ls="--")
    ax.set_title(title)
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Seasonal index (100 = average month)")
    return fig


def plot_stl(comps: pd.DataFrame, title: str, ylabel: str = "Units"):
    plt = _plt()
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    for ax, col in zip(axes, ["observed", "trend", "seasonal", "resid"]):
        ax.plot(comps.index, comps[col], color="#4C72B0", lw=1.1)
        ax.set_ylabel(f"{col.title()}\n({ylabel.lower()})")
    axes[0].set_title(title)
    axes[-1].set_xlabel("Month")
    return fig
