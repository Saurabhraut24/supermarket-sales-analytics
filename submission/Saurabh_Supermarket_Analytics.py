# =============================================================================
# SUPERMARKET SALES ANALYTICS DASHBOARD
# =============================================================================
# Student  : Saurabh Raut
# Institute: Walchand Institute of Technology, Solapur
# Dept     : Electronics and Computer Engineering
# Programme: AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026
#            BharatCares
#
# Submission File: Saurabh_Supermarket_Analytics.py
# Description    : Single self-contained Streamlit dashboard combining all
#                  project modules (data_loader, data_cleaning, analytics,
#                  insights, visualizations, app).
#
# Run with: streamlit run Saurabh_Supermarket_Analytics.py
# =============================================================================

# =============================================================================
# SECTION 1 — IMPORTS
# =============================================================================
import sys
import os
import io

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================================================
# SECTION 2 — CONFIGURATION
# =============================================================================

# ── Default dataset path (relative to this file's directory) ─────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(_THIS_DIR, "..", "data", "SuperMarket Analysis.csv")

# ── Minimum required columns for schema validation ───────────────────────────
REQUIRED_COLUMNS = {"Invoice ID", "Branch", "Sales", "Quantity", "Rating", "Date"}

# ── Numeric columns to coerce on load ────────────────────────────────────────
NUMERIC_COLS = [
    "Unit price", "Quantity", "Tax 5%", "Sales",
    "cogs", "gross margin percentage", "gross income", "Rating",
]

# ── Column name aliases: alternate name → canonical name ─────────────────────
COLUMN_ALIASES = {
    "Customer Type":  "Customer type",
    "customertype":   "Customer type",
    "customer_type":  "Customer type",
    "Unit Price":     "Unit price",
    "unit_price":     "Unit price",
    "UnitPrice":      "Unit price",
    "Price":          "Unit price",
    "Category":       "Product line",
    "category":       "Product line",
    "Product Line":   "Product line",
    "product_line":   "Product line",
    "product line":   "Product line",
    "Payment Method": "Payment",
    "payment_method": "Payment",
    "Total":          "Sales",
    "Revenue":        "Sales",
    "total_sales":    "Sales",
    "Qty":            "Quantity",
    "quantity":       "Quantity",
}

# ── Chart colour palette ──────────────────────────────────────────────────────
PALETTE   = px.colors.qualitative.Vivid
BLUE_SEQ  = px.colors.sequential.Blues
GREEN_SEQ = px.colors.sequential.Greens
PURPLE    = "#7C3AED"
TEAL      = "#0D9488"
ORANGE    = "#EA580C"
PINK      = "#DB2777"
GOLD      = "#D97706"

LAYOUT = dict(
    font=dict(family="Inter, sans-serif", size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(255,255,255,0.05)", bordercolor="rgba(255,255,255,0.1)"),
)

# =============================================================================
# SECTION 3 — DATA LOADING
# =============================================================================

def _derive_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Derive financial/structural columns that may be absent in alternate CSVs."""
    has_sales = "Sales" in df.columns and df["Sales"].notna().any()
    has_qty   = "Quantity" in df.columns and df["Quantity"].notna().any()
    has_price = "Unit price" in df.columns and df["Unit price"].notna().any()

    if not has_sales and has_qty and has_price:
        df["Sales"] = df["Quantity"] * df["Unit price"]
        has_sales = True

    if has_sales:
        if "Tax 5%" not in df.columns:
            df["Tax 5%"] = (df["Sales"] * 5 / 105).round(4)
        if "gross income" not in df.columns:
            df["gross income"] = df["Tax 5%"].round(4)
        if "cogs" not in df.columns:
            df["cogs"] = (df["Sales"] - df["gross income"]).round(4)
        if "gross margin percentage" not in df.columns:
            df["gross margin percentage"] = (df["gross income"] / df["Sales"] * 100).round(6)

    if "Time" not in df.columns:
        df["Time"] = None
    if "Invoice ID" not in df.columns:
        df["Invoice ID"] = [f"INV{str(i+1).zfill(5)}" for i in range(len(df))]
    if "City" not in df.columns and "Branch" in df.columns:
        df["City"] = df["Branch"].astype(str)
    if "Product line" not in df.columns:
        df["Product line"] = "General"
    if "Gender" not in df.columns:
        df["Gender"] = "Unknown"
    if "Customer type" not in df.columns:
        df["Customer type"] = "Normal"
    if "Payment" not in df.columns:
        df["Payment"] = "Unknown"

    return df


def _read_csv(source) -> pd.DataFrame:
    """Core CSV reading with normalisation, coercion, and derivation."""
    try:
        df = pd.read_csv(source)
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    df.columns = df.columns.str.strip()
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = _derive_missing_columns(df)
    return df


@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    """Load the default bundled dataset with Streamlit caching."""
    if not os.path.exists(DEFAULT_CSV_PATH):
        raise FileNotFoundError(f"Default dataset not found at: {DEFAULT_CSV_PATH}")
    return _read_csv(DEFAULT_CSV_PATH)


def load_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Load a user-uploaded CSV file."""
    content = uploaded_file.read()
    return _read_csv(io.BytesIO(content))


def validate_schema(df: pd.DataFrame):
    """
    Validate minimum required columns after normalisation.
    Returns (is_valid: bool, missing_cols: list).
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return len(missing) == 0, missing

# =============================================================================
# SECTION 4 — DATA CLEANING
# =============================================================================

def clean_dataframe(df: pd.DataFrame):
    """
    Clean the dataframe. Returns (cleaned_df, cleaning_report).

    Steps:
      1. Remove fully empty rows
      2. Parse Date column; derive temporal features
      3. Parse Time column; derive Hour feature
      4. Remove duplicate Invoice IDs
      5. Drop rows with missing Sales / Unit price
      6. Strip string whitespace
    """
    report = []
    df = df.copy()

    # 1. Remove fully empty rows
    blank_before = df.shape[0]
    df.dropna(how="all", inplace=True)
    dropped_blank = blank_before - df.shape[0]
    if dropped_blank:
        report.append(f"Removed {dropped_blank} fully empty row(s).")

    # 2. Parse Date column
    if "Date" in df.columns:
        original_nulls = df["Date"].isna().sum()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        new_nulls = df["Date"].isna().sum()
        failed = int(new_nulls - original_nulls)
        if failed > 0:
            report.append(f"Could not parse {failed} Date value(s) - set to NaT.")
        df["Year"]       = df["Date"].dt.year
        df["Month"]      = df["Date"].dt.month
        df["Month_Name"] = df["Date"].dt.strftime("%b")
        df["Day"]        = df["Date"].dt.day
        df["Day_Name"]   = df["Date"].dt.strftime("%A")
        df["Week"]       = df["Date"].dt.isocalendar().week.astype(int)
        report.append("Parsed Date column; derived Year, Month, Day, Day_Name, Week.")

    # 3. Parse Time column
    if "Time" in df.columns and df["Time"].notna().any():
        df["Time_dt"] = pd.to_datetime(df["Time"], format="%I:%M:%S %p", errors="coerce")
        df["Hour"]    = df["Time_dt"].dt.hour
        nulls = int(df["Hour"].isna().sum())
        if nulls:
            report.append(f"Could not parse {nulls} Time value(s).")
        else:
            report.append("Parsed Time column; derived Hour feature.")
    else:
        report.append("No Time column found; hourly analysis skipped.")

    # 4. Remove duplicate Invoice IDs
    if "Invoice ID" in df.columns:
        dup_count = int(df.duplicated(subset=["Invoice ID"]).sum())
        if dup_count:
            df.drop_duplicates(subset=["Invoice ID"], keep="first", inplace=True)
            report.append(f"Removed {dup_count} duplicate Invoice ID(s).")
        else:
            report.append("No duplicate Invoice IDs found.")

    # 5. Drop rows with missing Sales / Unit price
    critical = [c for c in ["Sales", "Unit price"] if c in df.columns]
    if critical:
        before = df.shape[0]
        df.dropna(subset=critical, inplace=True)
        after = df.shape[0]
        if before != after:
            report.append(f"Removed {before - after} row(s) with missing Sales/Unit price.")

    # 6. Strip string whitespace
    str_cols = df.select_dtypes(include="object").columns.tolist()
    for col in str_cols:
        df[col] = df[col].str.strip()

    df.reset_index(drop=True, inplace=True)
    report.append(f"Final dataset: {df.shape[0]} rows x {df.shape[1]} columns.")
    return df, report


def get_quality_report(raw_df: pd.DataFrame) -> dict:
    """Return data quality metrics for the raw dataframe (pre-cleaning)."""
    return {
        "rows":           raw_df.shape[0],
        "columns":        raw_df.shape[1],
        "missing_cells":  int(raw_df.isna().sum().sum()),
        "missing_pct":    round(raw_df.isna().sum().sum() / max(raw_df.size, 1) * 100, 2),
        "duplicate_rows": int(raw_df.duplicated().sum()),
        "column_names":   raw_df.columns.tolist(),
        "dtypes":         raw_df.dtypes.astype(str).to_dict(),
        "null_by_col":    raw_df.isna().sum().to_dict(),
    }

# =============================================================================
# SECTION 5 — DATA VALIDATION (helper)
# =============================================================================

def safe_col(df: pd.DataFrame, col: str) -> bool:
    """Return True if column exists and has at least one non-null value."""
    return col in df.columns and df[col].notna().any()

# =============================================================================
# SECTION 6 — ANALYTICS FUNCTIONS
# =============================================================================

def calc_kpis(df: pd.DataFrame) -> dict:
    """Calculate all top-level KPIs from the (filtered) dataframe."""
    kpis = {}

    if safe_col(df, "Sales"):
        kpis["total_sales"]     = df["Sales"].sum()
        kpis["avg_order_value"] = df["Sales"].mean()

    if safe_col(df, "gross income"):
        kpis["total_gross_income"] = df["gross income"].sum()
        kpis["avg_gross_income"]   = df["gross income"].mean()

    if "Invoice ID" in df.columns:
        kpis["total_transactions"] = df["Invoice ID"].nunique()
    else:
        kpis["total_transactions"] = len(df)

    if safe_col(df, "Quantity"):
        kpis["total_quantity"] = int(df["Quantity"].sum())

    if safe_col(df, "Unit price"):
        kpis["avg_unit_price"] = df["Unit price"].mean()
        kpis["min_unit_price"] = df["Unit price"].min()
        kpis["max_unit_price"] = df["Unit price"].max()

    if safe_col(df, "Rating"):
        kpis["avg_rating"] = df["Rating"].mean()

    if safe_col(df, "gross income") and safe_col(df, "Sales"):
        total_sales = df["Sales"].sum()
        total_gi    = df["gross income"].sum()
        kpis["gross_margin_pct"] = (total_gi / total_sales * 100) if total_sales else 0

    if safe_col(df, "cogs"):
        kpis["total_cogs"] = df["cogs"].sum()

    return kpis


def sales_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Daily sales aggregation."""
    if "Date" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    daily = df.groupby("Date")["Sales"].sum().reset_index()
    daily.columns = ["Date", "Sales"]
    daily.sort_values("Date", inplace=True)
    return daily


def sales_by_col(df: pd.DataFrame, col: str, value_col: str = "Sales") -> pd.DataFrame:
    """Aggregate a value column by a grouping column."""
    if col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    out = df.groupby(col)[value_col].sum().reset_index().sort_values(value_col, ascending=False)
    return out


def quantity_by_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Total quantity grouped by a column."""
    if col not in df.columns or "Quantity" not in df.columns:
        return pd.DataFrame()
    return df.groupby(col)["Quantity"].sum().reset_index().sort_values("Quantity", ascending=False)


def avg_by_col(df: pd.DataFrame, col: str, value_col: str) -> pd.DataFrame:
    """Mean of a value column grouped by a column."""
    if col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    return df.groupby(col)[value_col].mean().reset_index().sort_values(value_col, ascending=False)


def price_distribution(df: pd.DataFrame) -> pd.Series:
    """Return non-null unit prices as a Series."""
    if "Unit price" not in df.columns:
        return pd.Series(dtype=float)
    return df["Unit price"].dropna()


def rating_distribution(df: pd.DataFrame) -> pd.Series:
    """Return non-null ratings as a Series."""
    if "Rating" not in df.columns:
        return pd.Series(dtype=float)
    return df["Rating"].dropna()


def sales_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales grouped by hour of day."""
    if "Hour" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    return df.groupby("Hour")["Sales"].sum().reset_index().sort_values("Hour")


def sales_by_day_name(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales grouped by day-of-week name, in calendar order."""
    if "Day_Name" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grp = (
        df.groupby("Day_Name")["Sales"]
        .sum()
        .reindex([d for d in day_order if d in df["Day_Name"].unique()])
        .reset_index()
    )
    grp.columns = ["Day_Name", "Sales"]
    return grp


def sales_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales grouped by month."""
    if "Month" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby(["Month", "Month_Name"])["Sales"].sum().reset_index()
    grp.sort_values("Month", inplace=True)
    return grp


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation matrix for key numeric columns."""
    num_cols = ["Unit price", "Quantity", "Tax 5%", "Sales", "cogs", "gross income", "Rating"]
    existing = [c for c in num_cols if c in df.columns]
    if len(existing) < 2:
        return pd.DataFrame()
    return df[existing].corr()


def payment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate payment-method metrics."""
    if "Payment" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    grp = (
        df.groupby("Payment")
        .agg(
            Total_Sales=("Sales", "sum"),
            Transaction_Count=("Sales", "count"),
            Avg_Transaction=("Sales", "mean"),
        )
        .reset_index()
        .sort_values("Total_Sales", ascending=False)
    )
    return grp


def customer_type_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customer-type metrics."""
    if "Customer type" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    agg_dict = {
        "Total_Sales":      ("Sales", "sum"),
        "Transactions":     ("Sales", "count"),
        "Avg_Transaction":  ("Sales", "mean"),
    }
    if "Quantity" in df.columns:
        agg_dict["Total_Quantity"] = ("Quantity", "sum")
    grp = df.groupby("Customer type").agg(**agg_dict).reset_index()
    return grp


def branch_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate branch-level metrics."""
    if "Branch" not in df.columns:
        return pd.DataFrame()
    agg = {"Sales": "sum"}
    if "gross income" in df.columns:
        agg["gross income"] = "sum"
    if "Quantity" in df.columns:
        agg["Quantity"] = "sum"
    if "Rating" in df.columns:
        agg["Rating"] = "mean"
    return df.groupby("Branch").agg(agg).reset_index()


def product_line_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product-line metrics."""
    if "Product line" not in df.columns:
        return pd.DataFrame()
    agg = {"Sales": "sum"}
    if "gross income" in df.columns:
        agg["gross income"] = "sum"
    if "Quantity" in df.columns:
        agg["Quantity"] = "sum"
    if "Unit price" in df.columns:
        agg["Unit price"] = "mean"
    return (
        df.groupby("Product line")
        .agg(agg)
        .reset_index()
        .sort_values("Sales", ascending=False)
    )

# =============================================================================
# SECTION 7 — BUSINESS INSIGHTS
# =============================================================================

def generate_insights(df: pd.DataFrame) -> list:
    """
    Dynamically generate plain-English business insights from the filtered
    DataFrame. Returns a list of markdown-formatted insight strings.
    """
    insights = []

    if df.empty:
        return ["No data available for the selected filters."]

    def safe(col):
        return col in df.columns and df[col].notna().any()

    # Sales insights
    if safe("Product line") and safe("Sales"):
        top_pl     = df.groupby("Product line")["Sales"].sum().idxmax()
        top_pl_val = df.groupby("Product line")["Sales"].sum().max()
        low_pl     = df.groupby("Product line")["Sales"].sum().idxmin()
        insights.append(
            f"**{top_pl}** is the highest-selling product line "
            f"with total sales of **${top_pl_val:,.2f}**."
        )
        insights.append(f"**{low_pl}** is the lowest-selling product line.")

    if safe("Branch") and safe("Sales"):
        top_branch     = df.groupby("Branch")["Sales"].sum().idxmax()
        top_branch_val = df.groupby("Branch")["Sales"].sum().max()
        insights.append(
            f"Branch **{top_branch}** generated the highest revenue of **${top_branch_val:,.2f}**."
        )

    if safe("City") and safe("Sales"):
        top_city = df.groupby("City")["Sales"].sum().idxmax()
        insights.append(f"**{top_city}** is the top-performing city by sales.")

    # Time insights
    if safe("Hour") and safe("Sales"):
        peak_hour = df.groupby("Hour")["Sales"].sum().idxmax()
        am_pm     = "AM" if peak_hour < 12 else "PM"
        hour_12   = peak_hour if peak_hour <= 12 else peak_hour - 12
        hour_12   = 12 if hour_12 == 0 else hour_12
        insights.append(
            f"The peak sales hour is **{hour_12}:00 {am_pm}** ({peak_hour}:00)."
        )

    if safe("Day_Name") and safe("Sales"):
        best_day = df.groupby("Day_Name")["Sales"].sum().idxmax()
        insights.append(f"**{best_day}** is the best-performing day of the week by sales.")

    if safe("Month_Name") and safe("Sales") and df["Month_Name"].nunique() > 1:
        best_month = df.groupby("Month_Name")["Sales"].sum().idxmax()
        insights.append(f"**{best_month}** recorded the highest monthly sales.")

    # Customer insights
    if safe("Customer type") and safe("Sales"):
        ct = df.groupby("Customer type")["Sales"].mean()
        if len(ct) == 2:
            higher, lower = ct.idxmax(), ct.idxmin()
            insights.append(
                f"**{higher}** customers generate a higher average transaction value "
                f"(${ct[higher]:,.2f}) compared to **{lower}** customers (${ct[lower]:,.2f})."
            )

    if safe("Gender") and safe("Sales"):
        top_gender = df.groupby("Gender")["Sales"].sum().idxmax()
        insights.append(
            f"**{top_gender}** customers account for the larger share of total sales."
        )

    # Payment insights
    if safe("Payment") and safe("Sales"):
        top_pay = df.groupby("Payment")["Sales"].sum().idxmax()
        insights.append(f"**{top_pay}** is the most popular payment method by total sales.")

    # Price insights
    if safe("Product line") and safe("Unit price"):
        top_price_pl  = df.groupby("Product line")["Unit price"].mean().idxmax()
        top_price_val = df.groupby("Product line")["Unit price"].mean().max()
        insights.append(
            f"**{top_price_pl}** has the highest average unit price of **${top_price_val:,.2f}**."
        )

    # Gross income insights
    if safe("Product line") and safe("gross income"):
        top_gi_pl  = df.groupby("Product line")["gross income"].sum().idxmax()
        top_gi_val = df.groupby("Product line")["gross income"].sum().max()
        insights.append(
            f"**{top_gi_pl}** is the top product line by gross income: **${top_gi_val:,.2f}**."
        )

    # Rating insights
    if safe("Product line") and safe("Rating"):
        top_rated     = df.groupby("Product line")["Rating"].mean().idxmax()
        top_rated_val = df.groupby("Product line")["Rating"].mean().max()
        low_rated     = df.groupby("Product line")["Rating"].mean().idxmin()
        low_rated_val = df.groupby("Product line")["Rating"].mean().min()
        insights.append(
            f"**{top_rated}** has the highest avg customer rating ({top_rated_val:.2f}/10)."
        )
        insights.append(
            f"**{low_rated}** has the lowest avg customer rating ({low_rated_val:.2f}/10)."
        )

    if safe("Branch") and safe("Rating"):
        top_br_rating = df.groupby("Branch")["Rating"].mean().idxmax()
        insights.append(
            f"Branch **{top_br_rating}** has the highest average customer satisfaction rating."
        )

    # Quantity insights
    if safe("Product line") and safe("Quantity"):
        top_qty_pl  = df.groupby("Product line")["Quantity"].sum().idxmax()
        top_qty_val = int(df.groupby("Product line")["Quantity"].sum().max())
        insights.append(
            f"**{top_qty_pl}** had the highest quantity sold ({top_qty_val:,} units)."
        )

    return insights if insights else ["Not enough data to generate insights."]

# =============================================================================
# SECTION 8 — VISUALIZATION FUNCTIONS
# =============================================================================

def _apply(fig: go.Figure) -> go.Figure:
    """Apply the standard transparent dark-theme layout to a Plotly figure."""
    fig.update_layout(**LAYOUT)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.15)", zeroline=False)
    return fig


def _empty_fig(message: str = "No data available") -> go.Figure:
    """Return a styled empty figure with a centred message."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{message}</b>",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=15, color="rgba(255,255,255,0.4)", family="Inter, sans-serif"),
    )
    fig.update_layout(**LAYOUT, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


# ── Sales charts ─────────────────────────────────────────────────────────────

def chart_sales_trend(daily: pd.DataFrame) -> go.Figure:
    if daily.empty:
        return _empty_fig()
    fig = px.area(
        daily, x="Date", y="Sales",
        title="Daily Sales Trend",
        labels={"Sales": "Total Sales ($)", "Date": "Date"},
        color_discrete_sequence=[TEAL],
    )
    fig.update_traces(fill="tozeroy", line_color=TEAL, fillcolor="rgba(13,148,136,0.15)")
    return _apply(fig)


def chart_sales_by_category(
    df: pd.DataFrame, col: str, value_col: str = "Sales",
    title: str = None, horizontal: bool = True
) -> go.Figure:
    if df.empty:
        return _empty_fig()
    title = title or f"{value_col} by {col}"
    if horizontal:
        fig = px.bar(
            df.sort_values(value_col), x=value_col, y=col,
            orientation="h", title=title,
            labels={value_col: f"{value_col} ($)", col: col},
            color=value_col, color_continuous_scale=BLUE_SEQ,
            text_auto=".2s",
        )
    else:
        fig = px.bar(
            df, x=col, y=value_col, title=title,
            labels={value_col: f"{value_col} ($)", col: col},
            color=col, color_discrete_sequence=PALETTE,
            text_auto=".2s",
        )
    fig.update_traces(textposition="outside" if not horizontal else "inside")
    return _apply(fig)


def chart_sales_by_hour(hourly: pd.DataFrame) -> go.Figure:
    if hourly.empty:
        return _empty_fig("Hourly data not available\n(No Time column in dataset)")
    fig = px.bar(
        hourly, x="Hour", y="Sales",
        title="Hourly Sales Pattern",
        labels={"Sales": "Total Sales ($)", "Hour": "Hour of Day"},
        color="Sales", color_continuous_scale=BLUE_SEQ,
        text_auto=".2s",
    )
    fig.update_xaxes(tickmode="linear", tick0=0, dtick=1)
    return _apply(fig)


def chart_sales_by_day(daily_name: pd.DataFrame) -> go.Figure:
    if daily_name.empty:
        return _empty_fig()
    fig = px.bar(
        daily_name, x="Day_Name", y="Sales",
        title="Sales by Day of Week",
        labels={"Sales": "Total Sales ($)", "Day_Name": "Day"},
        color="Sales", color_continuous_scale=BLUE_SEQ,
        text_auto=".2s",
    )
    return _apply(fig)


def chart_sales_by_month(monthly: pd.DataFrame) -> go.Figure:
    if monthly.empty:
        return _empty_fig()
    fig = px.line(
        monthly, x="Month_Name", y="Sales",
        title="Monthly Sales",
        labels={"Sales": "Total Sales ($)", "Month_Name": "Month"},
        markers=True, color_discrete_sequence=[TEAL],
    )
    fig.update_traces(line_width=3, marker_size=9)
    return _apply(fig)


# ── Price charts ─────────────────────────────────────────────────────────────

def chart_price_histogram(prices: pd.Series) -> go.Figure:
    if prices.empty:
        return _empty_fig()
    fig = px.histogram(
        prices, nbins=30,
        title="Unit Price Distribution",
        labels={"value": "Unit Price ($)", "count": "Frequency"},
        color_discrete_sequence=[PURPLE],
    )
    fig.update_layout(bargap=0.05)
    return _apply(fig)


def chart_price_vs_quantity(df: pd.DataFrame) -> go.Figure:
    if "Unit price" not in df.columns or "Quantity" not in df.columns:
        return _empty_fig()
    color_col = "Product line" if "Product line" in df.columns else None
    fig = px.scatter(
        df, x="Unit price", y="Quantity",
        title="Unit Price vs Quantity Sold",
        labels={"Unit price": "Unit Price ($)", "Quantity": "Quantity"},
        color=color_col, color_discrete_sequence=PALETTE, opacity=0.6,
        hover_data=["Invoice ID"] if "Invoice ID" in df.columns else None,
    )
    return _apply(fig)


def chart_price_vs_sales(df: pd.DataFrame) -> go.Figure:
    if "Unit price" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    color_col = "Product line" if "Product line" in df.columns else None
    fig = px.scatter(
        df, x="Unit price", y="Sales",
        title="Unit Price vs Total Sales",
        labels={"Unit price": "Unit Price ($)", "Sales": "Total Sales ($)"},
        color=color_col, color_discrete_sequence=PALETTE, opacity=0.6,
    )
    return _apply(fig)


# ── Product charts ────────────────────────────────────────────────────────────

def chart_product_line_sunburst(df: pd.DataFrame) -> go.Figure:
    if "Product line" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    grp = df.groupby("Product line")["Sales"].sum().reset_index()
    fig = px.pie(
        grp, names="Product line", values="Sales",
        title="Sales Share by Product Line",
        color_discrete_sequence=PALETTE, hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def chart_gender_pie(df: pd.DataFrame) -> go.Figure:
    if "Gender" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    grp = df.groupby("Gender")["Sales"].sum().reset_index()
    fig = px.pie(
        grp, names="Gender", values="Sales",
        title="Sales by Gender",
        color_discrete_sequence=[PURPLE, PINK], hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


# ── Payment charts ────────────────────────────────────────────────────────────

def chart_payment_donut(pay_df: pd.DataFrame) -> go.Figure:
    if pay_df.empty:
        return _empty_fig()
    fig = px.pie(
        pay_df, names="Payment", values="Total_Sales",
        title="Sales by Payment Method",
        color_discrete_sequence=PALETTE, hole=0.5,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def chart_payment_bar(pay_df: pd.DataFrame) -> go.Figure:
    if pay_df.empty:
        return _empty_fig()
    fig = px.bar(
        pay_df, x="Payment", y="Transaction_Count",
        title="Transaction Count by Payment Method",
        labels={"Transaction_Count": "Transactions", "Payment": "Payment Method"},
        color="Payment", color_discrete_sequence=PALETTE, text_auto=True,
    )
    return _apply(fig)


# ── Rating chart ──────────────────────────────────────────────────────────────

def chart_rating_histogram(ratings: pd.Series) -> go.Figure:
    if ratings.empty:
        return _empty_fig()
    fig = px.histogram(
        ratings, nbins=20,
        title="Customer Rating Distribution",
        labels={"value": "Rating", "count": "Frequency"},
        color_discrete_sequence=[GOLD],
    )
    fig.update_layout(bargap=0.05)
    return _apply(fig)


# ── Correlation heatmap ────────────────────────────────────────────────────────

def chart_correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    if corr.empty:
        return _empty_fig()
    fig = px.imshow(
        corr, title="Feature Correlation Matrix",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        text_auto=".2f", aspect="auto",
    )
    return _apply(fig)


# ── Pareto chart ───────────────────────────────────────────────────────────────

def chart_pareto(df: pd.DataFrame, col: str = "Product line", value: str = "Sales") -> go.Figure:
    if col not in df.columns or value not in df.columns:
        return _empty_fig()
    grp = df.groupby(col)[value].sum().sort_values(ascending=False).reset_index()
    grp["Cumulative %"] = grp[value].cumsum() / grp[value].sum() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=grp[col], y=grp[value], name=value,
            marker_color=TEAL,
            text=grp[value].apply(lambda x: f"${x:,.0f}"),
            textposition="outside",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=grp[col], y=grp["Cumulative %"], name="Cumulative %",
            mode="lines+markers", line_color=ORANGE, marker_size=7,
        ),
        secondary_y=True,
    )
    fig.update_layout(title=f"Pareto Chart: {value} by {col}", **LAYOUT)
    fig.update_yaxes(title_text=f"{value} ($)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True)
    fig.update_xaxes(showgrid=False)
    return fig


# ── Gross income trend ────────────────────────────────────────────────────────

def chart_gross_income_trend(df: pd.DataFrame) -> go.Figure:
    if "Date" not in df.columns or "gross income" not in df.columns:
        return _empty_fig()
    daily = df.groupby("Date")["gross income"].sum().reset_index()
    daily.sort_values("Date", inplace=True)
    fig = px.area(
        daily, x="Date", y="gross income",
        title="Daily Gross Income Trend",
        labels={"gross income": "Gross Income ($)", "Date": "Date"},
        color_discrete_sequence=[GOLD],
    )
    fig.update_traces(fill="tozeroy", line_color=GOLD, fillcolor="rgba(217,119,6,0.15)")
    return _apply(fig)

# =============================================================================
# SECTION 9 — STREAMLIT UI HELPERS
# =============================================================================

# ── Page config (called once at top-level, before any other st calls) ─────────
st.set_page_config(
    page_title="SuperMarket Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
.kpi-card {
    background: linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px; padding: 24px 20px; text-align: center;
    backdrop-filter: blur(12px);
    transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 8px;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.3); }
.kpi-label { font-size:12px; font-weight:600; letter-spacing:1.2px; text-transform:uppercase;
             color:rgba(255,255,255,0.6); margin-bottom:6px; }
.kpi-value { font-size:28px; font-weight:700; color:#ffffff; }
.kpi-icon  { font-size:22px; margin-bottom:6px; }
.section-header { font-size:22px; font-weight:700; color:#ffffff;
                  border-left:4px solid #7C3AED; padding-left:12px; margin:20px 0 16px 0; }
.insight-card { background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.3);
                border-radius:12px; padding:14px 18px; margin-bottom:10px;
                color:#e2e8f0; font-size:14px; line-height:1.6; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#1e1b4b,#312e81) !important; }
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
.stTabs [data-baseweb="tab-list"] { background:rgba(255,255,255,0.05); border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"] { border-radius:8px; padding:8px 18px; font-weight:500;
                                color:rgba(255,255,255,0.6) !important; }
.stTabs [aria-selected="true"] { background:rgba(124,58,237,0.4) !important; color:#ffffff !important; }
[data-testid="stPlotlyChart"] { border-radius:12px; border:1px solid rgba(255,255,255,0.08);
                                 background:rgba(255,255,255,0.03); }
hr { border-color:rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)


def kpi_card(icon: str, label: str, value: str) -> str:
    """Return HTML string for a glassmorphism KPI card."""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'</div>'
    )


def fmtfig(fig: go.Figure) -> go.Figure:
    """Apply transparent background and grid settings inline."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.15)", zeroline=False)
    return fig

# =============================================================================
# SECTION 10 — MAIN APPLICATION
# =============================================================================

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:30px 0 10px 0;">
  <div style="font-size:48px;margin-bottom:8px;">🛒</div>
  <h1 style="font-size:36px;font-weight:800;color:#ffffff;margin:0;letter-spacing:-1px;">
    SuperMarket Sales Analytics Dashboard
  </h1>
  <p style="font-size:16px;color:rgba(255,255,255,0.55);margin-top:8px;">
    Interactive business intelligence and sales performance analysis
  </p>
</div><hr/>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 SuperMarket Analytics")
    st.markdown("---")
    st.markdown("### 📂 Upload Dataset")
    uploaded_file = st.file_uploader(
        "Upload Supermarket CSV", type=["csv"],
        help="Upload a compatible supermarket CSV to replace the default dataset.",
        key="csv_upload",
    )
    st.markdown("---")

    raw_df      = None
    data_source = "Default Dataset"

    if uploaded_file is not None:
        try:
            raw_df      = load_uploaded_csv(uploaded_file)
            data_source = f"📤 {uploaded_file.name}"
            st.success(f"Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Could not load file: {e}")

    if raw_df is None:
        try:
            raw_df      = load_default_csv()
            data_source = "📦 Default Dataset"
        except FileNotFoundError:
            st.error("Default dataset not found. Please upload a CSV.")
            st.stop()
        except Exception as e:
            st.error(f"Error loading default dataset: {e}")
            st.stop()

    is_valid, missing_cols = validate_schema(raw_df)
    if not is_valid:
        st.warning(f"Non-standard CSV. Missing columns: {', '.join(missing_cols)}")

    if raw_df.empty:
        st.error("The loaded dataset is empty.")
        st.stop()

    quality_report = get_quality_report(raw_df)
    df, cleaning_log = clean_dataframe(raw_df)

    if df.empty:
        st.error("Dataset is empty after cleaning.")
        st.stop()

    st.markdown(f"**Source:** {data_source}")
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    filtered_df = df.copy()

    # Date range filter
    if "Date" in df.columns and df["Date"].notna().any():
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.date_input(
            "📅 Date Range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            d1 = pd.Timestamp(date_range[0])
            d2 = pd.Timestamp(date_range[1])
            filtered_df = filtered_df[
                (filtered_df["Date"] >= d1) & (filtered_df["Date"] <= d2)
            ]

    # Branch filter
    if "Branch" in df.columns:
        branches     = sorted(df["Branch"].dropna().unique().tolist())
        sel_branches = st.multiselect("🏪 Branch", branches, default=branches)
        if sel_branches:
            filtered_df = filtered_df[filtered_df["Branch"].isin(sel_branches)]

    # City filter
    if "City" in df.columns:
        cities     = sorted(df["City"].dropna().unique().tolist())
        sel_cities = st.multiselect("🏙️ City", cities, default=cities)
        if sel_cities:
            filtered_df = filtered_df[filtered_df["City"].isin(sel_cities)]

    # Customer type filter
    if "Customer type" in df.columns:
        ct_vals = sorted(df["Customer type"].dropna().unique().tolist())
        sel_ct  = st.multiselect("👤 Customer Type", ct_vals, default=ct_vals)
        if sel_ct:
            filtered_df = filtered_df[filtered_df["Customer type"].isin(sel_ct)]

    # Gender filter
    if "Gender" in df.columns:
        genders    = sorted(df["Gender"].dropna().unique().tolist())
        sel_gender = st.multiselect("⚧ Gender", genders, default=genders)
        if sel_gender:
            filtered_df = filtered_df[filtered_df["Gender"].isin(sel_gender)]

    # Product line filter
    if "Product line" in df.columns:
        products     = sorted(df["Product line"].dropna().unique().tolist())
        sel_products = st.multiselect("📦 Product Line", products, default=products)
        if sel_products:
            filtered_df = filtered_df[filtered_df["Product line"].isin(sel_products)]

    # Payment method filter
    if "Payment" in df.columns:
        payments     = sorted(df["Payment"].dropna().unique().tolist())
        sel_payments = st.multiselect("💳 Payment Method", payments, default=payments)
        if sel_payments:
            filtered_df = filtered_df[filtered_df["Payment"].isin(sel_payments)]

    st.markdown("---")
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.rerun()

    st.markdown(f"**Showing:** {len(filtered_df):,} / {len(df):,} records")
    st.markdown("---")
    st.caption("SuperMarket Analytics v1.0  |  Saurabh Raut")

# Guard: empty filtered dataset
if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your filters.")
    st.stop()

# ── Compute KPIs ──────────────────────────────────────────────────────────────
kpis = calc_kpis(filtered_df)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Overview",
    "📈 Sales Analytics",
    "📦 Product Analytics",
    "👥 Customer Analytics",
    "💰 Gross Income Analysis",
    "🕐 Time Analysis",
    "💳 Payment Analysis",
    "🏪 Branch & Location",
    "⭐ Ratings",
    "🔬 Advanced",
    "🗃️ Data Explorer",
])

# ═══ TAB 1: OVERVIEW ══════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if "total_sales" in kpis:
            st.markdown(kpi_card("💵", "Total Sales", f"${kpis['total_sales']:,.2f}"), unsafe_allow_html=True)
    with c2:
        if "total_gross_income" in kpis:
            st.markdown(kpi_card("💹", "Total Gross Income", f"${kpis['total_gross_income']:,.2f}"), unsafe_allow_html=True)
    with c3:
        if "total_transactions" in kpis:
            st.markdown(kpi_card("🧾", "Transactions", f"{kpis['total_transactions']:,}"), unsafe_allow_html=True)
    with c4:
        if "total_quantity" in kpis:
            st.markdown(kpi_card("📦", "Total Quantity Sold", f"{kpis['total_quantity']:,}"), unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        if "avg_order_value" in kpis:
            st.markdown(kpi_card("🛒", "Avg Order Value", f"${kpis['avg_order_value']:,.2f}"), unsafe_allow_html=True)
    with c6:
        if "avg_unit_price" in kpis:
            st.markdown(kpi_card("🏷️", "Avg Unit Price", f"${kpis['avg_unit_price']:,.2f}"), unsafe_allow_html=True)
    with c7:
        if "gross_margin_pct" in kpis:
            st.markdown(kpi_card("📊", "Gross Margin %", f"{kpis['gross_margin_pct']:.2f}%"), unsafe_allow_html=True)
    with c8:
        if "avg_rating" in kpis:
            st.markdown(kpi_card("⭐", "Avg Customer Rating", f"{kpis['avg_rating']:.2f}/10"), unsafe_allow_html=True)

    st.markdown("---")
    co1, co2 = st.columns(2)
    with co1:
        st.plotly_chart(chart_sales_trend(sales_over_time(filtered_df)), use_container_width=True, key="ov_1")
    with co2:
        st.plotly_chart(chart_product_line_sunburst(filtered_df), use_container_width=True, key="ov_2")

    co3, co4 = st.columns(2)
    with co3:
        branch_sales = sales_by_col(filtered_df, "Branch")
        st.plotly_chart(
            chart_sales_by_category(branch_sales, "Branch", "Sales", "Sales by Branch", horizontal=False),
            use_container_width=True, key="ov_3",
        )
    with co4:
        city_sales = sales_by_col(filtered_df, "City")
        st.plotly_chart(
            chart_sales_by_category(city_sales, "City", "Sales", "Sales by City", horizontal=False),
            use_container_width=True, key="ov_4",
        )

    st.markdown('<div class="section-header">💡 Business Insights</div>', unsafe_allow_html=True)
    insights = generate_insights(filtered_df)
    ins_cols = st.columns(2)
    for i, insight in enumerate(insights):
        with ins_cols[i % 2]:
            st.markdown(f'<div class="insight-card">💡 {insight}</div>', unsafe_allow_html=True)

# ═══ TAB 2: SALES ANALYTICS ═══════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-header">Sales Analytics</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_sales_trend(sales_over_time(filtered_df)), use_container_width=True, key="sa_1")

    sa1, sa2 = st.columns(2)
    with sa1:
        pl_sales = sales_by_col(filtered_df, "Product line")
        st.plotly_chart(
            chart_sales_by_category(pl_sales, "Product line", "Sales", "Sales by Product Line"),
            use_container_width=True, key="sa_2",
        )
    with sa2:
        branch_sales = sales_by_col(filtered_df, "Branch")
        st.plotly_chart(
            chart_sales_by_category(branch_sales, "Branch", "Sales", "Sales by Branch", horizontal=False),
            use_container_width=True, key="sa_3",
        )

    sa3, sa4 = st.columns(2)
    with sa3:
        ct_sales = sales_by_col(filtered_df, "Customer type")
        st.plotly_chart(
            chart_sales_by_category(ct_sales, "Customer type", "Sales", "Sales by Customer Type", horizontal=False),
            use_container_width=True, key="sa_4",
        )
    with sa4:
        st.plotly_chart(chart_gender_pie(filtered_df), use_container_width=True, key="sa_5")

    sa5, sa6 = st.columns(2)
    with sa5:
        pay_sales = sales_by_col(filtered_df, "Payment")
        st.plotly_chart(
            chart_sales_by_category(pay_sales, "Payment", "Sales", "Sales by Payment Method", horizontal=False),
            use_container_width=True, key="sa_6",
        )
    with sa6:
        qty_sales = quantity_by_col(filtered_df, "Product line")
        st.plotly_chart(
            chart_sales_by_category(qty_sales, "Product line", "Quantity", "Quantity Sold by Product Line"),
            use_container_width=True, key="sa_7",
        )

    st.markdown("---")
    sa7, sa8 = st.columns(2)
    with sa7:
        city_sales2 = sales_by_col(filtered_df, "City")
        st.plotly_chart(
            chart_sales_by_category(city_sales2, "City", "Sales", "Sales by City", horizontal=False),
            use_container_width=True, key="sa_8",
        )
    with sa8:
        avg_price_pl = avg_by_col(filtered_df, "Product line", "Unit price")
        st.plotly_chart(
            chart_sales_by_category(avg_price_pl, "Product line", "Unit price", "Avg Unit Price by Product Line"),
            use_container_width=True, key="sa_9",
        )

# ═══ TAB 3: PRODUCT ANALYTICS ══════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-header">Product Analytics</div>', unsafe_allow_html=True)
    prod_df = product_line_analysis(filtered_df)

    pa1, pa2 = st.columns(2)
    with pa1:
        st.plotly_chart(chart_product_line_sunburst(filtered_df), use_container_width=True, key="pa_1")
    with pa2:
        if not prod_df.empty and "Quantity" in prod_df.columns:
            st.plotly_chart(
                chart_sales_by_category(prod_df[["Product line", "Quantity"]], "Product line", "Quantity", "Units Sold by Product Line"),
                use_container_width=True, key="pa_2",
            )

    pa3, pa4 = st.columns(2)
    with pa3:
        if not prod_df.empty and "Sales" in prod_df.columns:
            top5 = prod_df.nlargest(5, "Sales")
            st.plotly_chart(
                chart_sales_by_category(top5, "Product line", "Sales", "Top Product Lines by Sales"),
                use_container_width=True, key="pa_3",
            )
    with pa4:
        if not prod_df.empty and "Sales" in prod_df.columns:
            bot5 = prod_df.nsmallest(5, "Sales")
            st.plotly_chart(
                chart_sales_by_category(bot5, "Product line", "Sales", "Lowest Product Lines by Sales"),
                use_container_width=True, key="pa_4",
            )

    pa5, pa6 = st.columns(2)
    with pa5:
        avg_price_pl = avg_by_col(filtered_df, "Product line", "Unit price")
        st.plotly_chart(
            chart_sales_by_category(avg_price_pl, "Product line", "Unit price", "Avg Unit Price by Product Line"),
            use_container_width=True, key="pa_5",
        )
    with pa6:
        if not prod_df.empty and "gross income" in prod_df.columns:
            st.plotly_chart(
                chart_sales_by_category(prod_df, "Product line", "gross income", "Gross Income by Product Line"),
                use_container_width=True, key="pa_6",
            )

    st.markdown('<div class="section-header">Pareto Analysis</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_pareto(filtered_df, "Product line", "Sales"), use_container_width=True, key="pa_7")

# ═══ TAB 4: CUSTOMER ANALYTICS ═════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-header">Customer Analytics</div>', unsafe_allow_html=True)

    ca1, ca2 = st.columns(2)
    with ca1:
        st.plotly_chart(chart_gender_pie(filtered_df), use_container_width=True, key="ca_1")
    with ca2:
        if "Customer type" in filtered_df.columns and "Sales" in filtered_df.columns:
            ct_grp = filtered_df.groupby("Customer type")["Sales"].sum().reset_index()
            fig = px.pie(
                ct_grp, names="Customer type", values="Sales",
                title="Sales by Customer Type",
                color_discrete_sequence=[PURPLE, TEAL], hole=0.45,
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ca_2")

    ca3, ca4 = st.columns(2)
    with ca3:
        ct_a = customer_type_analysis(filtered_df)
        if not ct_a.empty and "Avg_Transaction" in ct_a.columns:
            fig = px.bar(
                ct_a, x="Customer type", y="Avg_Transaction",
                title="Avg Transaction Value by Customer Type",
                color="Customer type", color_discrete_sequence=[PURPLE, TEAL],
                text_auto=".2f", labels={"Avg_Transaction": "Avg Transaction ($)"},
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ca_3")
    with ca4:
        if "Customer type" in filtered_df.columns and "Quantity" in filtered_df.columns:
            ct_qty = filtered_df.groupby("Customer type")["Quantity"].sum().reset_index()
            fig = px.bar(
                ct_qty, x="Customer type", y="Quantity",
                title="Total Quantity by Customer Type",
                color="Customer type", color_discrete_sequence=[PURPLE, TEAL], text_auto=True,
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ca_4")

    ca5, ca6 = st.columns(2)
    with ca5:
        if all(c in filtered_df.columns for c in ["Gender", "Product line", "Sales"]):
            gpl = filtered_df.groupby(["Gender", "Product line"])["Sales"].sum().reset_index()
            fig = px.bar(
                gpl, x="Product line", y="Sales", color="Gender", barmode="group",
                title="Sales by Gender and Product Line",
                color_discrete_sequence=[PURPLE, PINK],
            )
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ca_5")
    with ca6:
        if "Customer type" in filtered_df.columns and "Rating" in filtered_df.columns:
            ct_r = filtered_df.groupby("Customer type")["Rating"].mean().reset_index()
            fig = px.bar(
                ct_r, x="Customer type", y="Rating",
                title="Avg Rating by Customer Type",
                color="Customer type", color_discrete_sequence=[PURPLE, TEAL], text_auto=".2f",
            )
            fig.update_yaxes(range=[0, 10])
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ca_6")

# ═══ TAB 5: GROSS INCOME ANALYSIS ══════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-header">Gross Income Analysis</div>', unsafe_allow_html=True)
    if "gross income" not in filtered_df.columns:
        st.warning("Gross income column not found in the dataset.")
    else:
        gi1, gi2, gi3, gi4 = st.columns(4)
        with gi1:
            st.markdown(kpi_card("💹", "Total Gross Income", f"${filtered_df['gross income'].sum():,.2f}"), unsafe_allow_html=True)
        with gi2:
            st.markdown(kpi_card("📊", "Avg Gross Income", f"${filtered_df['gross income'].mean():,.2f}"), unsafe_allow_html=True)
        with gi3:
            if "Sales" in filtered_df.columns and filtered_df["Sales"].sum() > 0:
                margin = filtered_df["gross income"].sum() / filtered_df["Sales"].sum() * 100
                st.markdown(kpi_card("📈", "Gross Margin %", f"{margin:.2f}%"), unsafe_allow_html=True)
        with gi4:
            if "gross margin percentage" in filtered_df.columns:
                st.markdown(kpi_card("🎯", "Avg Margin %", f"{filtered_df['gross margin percentage'].mean():.2f}%"), unsafe_allow_html=True)

        pf1, pf2 = st.columns(2)
        with pf1:
            gi_pl = sales_by_col(filtered_df, "Product line", "gross income")
            st.plotly_chart(
                chart_sales_by_category(gi_pl, "Product line", "gross income", "Gross Income by Product Line"),
                use_container_width=True, key="gi_1",
            )
        with pf2:
            gi_branch = sales_by_col(filtered_df, "Branch", "gross income")
            st.plotly_chart(
                chart_sales_by_category(gi_branch, "Branch", "gross income", "Gross Income by Branch", horizontal=False),
                use_container_width=True, key="gi_2",
            )

        pf3, pf4 = st.columns(2)
        with pf3:
            st.plotly_chart(chart_gross_income_trend(filtered_df), use_container_width=True, key="gi_3")
        with pf4:
            if "Sales" in filtered_df.columns:
                fig = px.scatter(
                    filtered_df, x="Sales", y="gross income",
                    title="Gross Income vs Total Sales",
                    color="Product line" if "Product line" in filtered_df.columns else None,
                    color_discrete_sequence=PALETTE, opacity=0.6,
                )
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="gi_4")

        if "cogs" in filtered_df.columns and "Sales" in filtered_df.columns:
            pf5, pf6 = st.columns(2)
            with pf5:
                fig = px.scatter(
                    filtered_df, x="cogs", y="gross income",
                    title="COGS vs Gross Income",
                    color="Product line" if "Product line" in filtered_df.columns else None,
                    color_discrete_sequence=PALETTE, opacity=0.6,
                )
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="gi_5")
            with pf6:
                cogs_pl = sales_by_col(filtered_df, "Product line", "cogs")
                st.plotly_chart(
                    chart_sales_by_category(cogs_pl, "Product line", "cogs", "COGS by Product Line"),
                    use_container_width=True, key="gi_6",
                )

# ═══ TAB 6: TIME ANALYSIS ══════════════════════════════════════════════════════
with tabs[5]:
    st.markdown('<div class="section-header">Time Analysis</div>', unsafe_allow_html=True)
    tcols = st.columns(3)

    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "Sales" in filtered_df.columns:
        peak_hour = int(filtered_df.groupby("Hour")["Sales"].sum().idxmax())
        am_pm     = "AM" if peak_hour < 12 else "PM"
        h12       = peak_hour if 1 <= peak_hour <= 12 else (peak_hour - 12 if peak_hour > 12 else 12)
        with tcols[0]:
            st.markdown(kpi_card("⏰", "Peak Sales Hour", f"{h12}:00 {am_pm}"), unsafe_allow_html=True)

    if "Day_Name" in filtered_df.columns and "Sales" in filtered_df.columns:
        best_day = filtered_df.groupby("Day_Name")["Sales"].sum().idxmax()
        with tcols[1]:
            st.markdown(kpi_card("📅", "Best Sales Day", best_day), unsafe_allow_html=True)

    if "Month_Name" in filtered_df.columns and "Sales" in filtered_df.columns and filtered_df["Month_Name"].nunique() > 1:
        best_month = filtered_df.groupby("Month_Name")["Sales"].sum().idxmax()
        with tcols[2]:
            st.markdown(kpi_card("📆", "Best Sales Month", best_month), unsafe_allow_html=True)

    ta1, ta2 = st.columns(2)
    with ta1:
        st.plotly_chart(chart_sales_by_hour(sales_by_hour(filtered_df)), use_container_width=True, key="ta_1")
    with ta2:
        st.plotly_chart(chart_sales_by_day(sales_by_day_name(filtered_df)), use_container_width=True, key="ta_2")

    ta3, ta4 = st.columns(2)
    with ta3:
        st.plotly_chart(chart_sales_by_month(sales_by_month(filtered_df)), use_container_width=True, key="ta_3")
    with ta4:
        st.plotly_chart(chart_sales_trend(sales_over_time(filtered_df)), use_container_width=True, key="ta_4")

    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "Quantity" in filtered_df.columns:
        qty_h = filtered_df.groupby("Hour")["Quantity"].sum().reset_index()
        fig = px.bar(
            qty_h, x="Hour", y="Quantity", title="Quantity Sold by Hour",
            color="Quantity", color_continuous_scale=GREEN_SEQ, text_auto=True,
        )
        fig.update_xaxes(tickmode="linear", tick0=0, dtick=1)
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="ta_5")

    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "gross income" in filtered_df.columns:
        gi_h = filtered_df.groupby("Hour")["gross income"].sum().reset_index()
        fig = px.line(
            gi_h, x="Hour", y="gross income", title="Gross Income by Hour",
            markers=True, color_discrete_sequence=[GOLD],
        )
        fig.update_traces(line_width=2, marker_size=7)
        fig.update_xaxes(tickmode="linear", tick0=0, dtick=1)
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="ta_6")

# ═══ TAB 7: PAYMENT ANALYSIS ════════════════════════════════════════════════════
with tabs[6]:
    st.markdown('<div class="section-header">Payment Analysis</div>', unsafe_allow_html=True)
    pay_df = payment_analysis(filtered_df)

    if pay_df.empty:
        st.warning("Payment data not available.")
    else:
        pm1, pm2 = st.columns(2)
        with pm1:
            st.plotly_chart(chart_payment_donut(pay_df), use_container_width=True, key="pm_1")
        with pm2:
            st.plotly_chart(chart_payment_bar(pay_df), use_container_width=True, key="pm_2")

        pm3, pm4 = st.columns(2)
        with pm3:
            fig = px.bar(
                pay_df, x="Payment", y="Total_Sales",
                title="Total Sales by Payment Method",
                color="Payment", color_discrete_sequence=PALETTE, text_auto=".2s",
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="pm_3")
        with pm4:
            fig = px.bar(
                pay_df, x="Payment", y="Avg_Transaction",
                title="Avg Transaction by Payment Method",
                color="Payment", color_discrete_sequence=PALETTE, text_auto=".2f",
                labels={"Avg_Transaction": "Avg Transaction ($)"},
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="pm_4")

        with st.expander("📊 Payment Summary Table"):
            st.dataframe(
                pay_df.style.format({
                    "Total_Sales": "${:,.2f}",
                    "Avg_Transaction": "${:,.2f}",
                    "Transaction_Count": "{:,}",
                }),
                use_container_width=True,
            )

# ═══ TAB 8: BRANCH & LOCATION ══════════════════════════════════════════════════
with tabs[7]:
    st.markdown('<div class="section-header">Branch & Location Analysis</div>', unsafe_allow_html=True)
    branch_df = branch_analysis(filtered_df)

    if branch_df.empty:
        st.warning("Branch data not available.")
    else:
        if "Sales" in branch_df.columns:
            best_br     = branch_df.loc[branch_df["Sales"].idxmax(), "Branch"]
            best_br_val = branch_df["Sales"].max()
            st.markdown(
                f'<div class="insight-card">🏆 Best performing branch: <strong>{best_br}</strong> '
                f'with ${best_br_val:,.2f} in total sales.</div>',
                unsafe_allow_html=True,
            )

        bl1, bl2 = st.columns(2)
        with bl1:
            st.plotly_chart(
                chart_sales_by_category(branch_df, "Branch", "Sales", "Sales by Branch", horizontal=False),
                use_container_width=True, key="bl_1",
            )
        with bl2:
            if "gross income" in branch_df.columns:
                st.plotly_chart(
                    chart_sales_by_category(branch_df, "Branch", "gross income", "Gross Income by Branch", horizontal=False),
                    use_container_width=True, key="bl_2",
                )

        bl3, bl4 = st.columns(2)
        with bl3:
            if "Quantity" in branch_df.columns:
                st.plotly_chart(
                    chart_sales_by_category(branch_df, "Branch", "Quantity", "Quantity Sold by Branch", horizontal=False),
                    use_container_width=True, key="bl_3",
                )
        with bl4:
            if "Rating" in branch_df.columns:
                fig = px.bar(
                    branch_df, x="Branch", y="Rating",
                    title="Avg Rating by Branch",
                    color="Branch", color_discrete_sequence=PALETTE, text_auto=".2f",
                )
                fig.update_yaxes(range=[0, 10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="bl_4")

        if all(c in filtered_df.columns for c in ["Branch", "Product line", "Sales"]):
            bpl = filtered_df.groupby(["Branch", "Product line"])["Sales"].sum().reset_index()
            fig = px.bar(
                bpl, x="Product line", y="Sales", color="Branch", barmode="group",
                title="Product Line Sales by Branch",
                color_discrete_sequence=PALETTE,
            )
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="bl_5")

        if "City" in filtered_df.columns and "Sales" in filtered_df.columns:
            city_grp = (
                filtered_df.groupby("City")["Sales"]
                .sum()
                .reset_index()
                .sort_values("Sales", ascending=False)
            )
            fig = px.bar(
                city_grp, x="City", y="Sales", title="Sales by City",
                color="City", color_discrete_sequence=PALETTE, text_auto=".2s",
            )
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="bl_6")

# ═══ TAB 9: RATINGS ════════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown('<div class="section-header">Customer Rating Analysis</div>', unsafe_allow_html=True)
    if "Rating" not in filtered_df.columns:
        st.warning("Rating column not found.")
    else:
        rk1, rk2, rk3 = st.columns(3)
        with rk1:
            st.markdown(kpi_card("⭐", "Average Rating", f"{filtered_df['Rating'].mean():.2f}/10"), unsafe_allow_html=True)
        with rk2:
            st.markdown(kpi_card("🔺", "Max Rating", f"{filtered_df['Rating'].max():.1f}"), unsafe_allow_html=True)
        with rk3:
            st.markdown(kpi_card("🔻", "Min Rating", f"{filtered_df['Rating'].min():.1f}"), unsafe_allow_html=True)

        ra1, ra2 = st.columns(2)
        with ra1:
            st.plotly_chart(chart_rating_histogram(rating_distribution(filtered_df)), use_container_width=True, key="ra_1")
        with ra2:
            if "Product line" in filtered_df.columns:
                pl_r = (
                    filtered_df.groupby("Product line")["Rating"]
                    .mean()
                    .reset_index()
                    .sort_values("Rating", ascending=False)
                )
                fig = px.bar(
                    pl_r, x="Product line", y="Rating",
                    title="Avg Rating by Product Line",
                    color="Rating", color_continuous_scale=px.colors.sequential.Oranges, text_auto=".2f",
                )
                fig.update_yaxes(range=[0, 10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="ra_2")

        ra3, ra4 = st.columns(2)
        with ra3:
            if "Branch" in filtered_df.columns:
                br_r = (
                    filtered_df.groupby("Branch")["Rating"]
                    .mean()
                    .reset_index()
                    .sort_values("Rating", ascending=False)
                )
                fig = px.bar(
                    br_r, x="Branch", y="Rating", title="Avg Rating by Branch",
                    color="Branch", color_discrete_sequence=PALETTE, text_auto=".2f",
                )
                fig.update_yaxes(range=[0, 10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="ra_3")
        with ra4:
            if "Sales" in filtered_df.columns:
                fig = px.scatter(
                    filtered_df, x="Rating", y="Sales", title="Rating vs Sales",
                    color="Product line" if "Product line" in filtered_df.columns else None,
                    color_discrete_sequence=PALETTE, opacity=0.55,
                )
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="ra_4")

        if "Gender" in filtered_df.columns:
            gender_r = filtered_df.groupby("Gender")["Rating"].mean().reset_index()
            fig = px.bar(
                gender_r, x="Gender", y="Rating", title="Avg Rating by Gender",
                color="Gender", color_discrete_sequence=[PURPLE, PINK], text_auto=".2f",
            )
            fig.update_yaxes(range=[0, 10])
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="ra_5")

# ═══ TAB 10: ADVANCED ANALYTICS ════════════════════════════════════════════════
with tabs[9]:
    st.markdown('<div class="section-header">Advanced Analytics</div>', unsafe_allow_html=True)

    adv1, adv2 = st.columns(2)
    with adv1:
        st.plotly_chart(chart_price_histogram(price_distribution(filtered_df)), use_container_width=True, key="adv_1")
    with adv2:
        st.plotly_chart(chart_price_vs_quantity(filtered_df), use_container_width=True, key="adv_2")

    adv3, adv4 = st.columns(2)
    with adv3:
        st.plotly_chart(chart_price_vs_sales(filtered_df), use_container_width=True, key="adv_3")
    with adv4:
        corr = correlation_matrix(filtered_df)
        st.plotly_chart(chart_correlation_heatmap(corr), use_container_width=True, key="adv_4")

    st.markdown('<div class="section-header">Pareto Analysis</div>', unsafe_allow_html=True)
    par1, par2 = st.columns(2)
    with par1:
        st.plotly_chart(chart_pareto(filtered_df, "Product line", "Sales"), use_container_width=True, key="adv_5")
    with par2:
        if "gross income" in filtered_df.columns:
            st.plotly_chart(chart_pareto(filtered_df, "Product line", "gross income"), use_container_width=True, key="adv_6")

    if "Product line" in filtered_df.columns and "Sales" in filtered_df.columns:
        st.markdown('<div class="section-header">Sales Contribution %</div>', unsafe_allow_html=True)
        contrib = filtered_df.groupby("Product line")["Sales"].sum().reset_index()
        contrib["Contribution %"] = contrib["Sales"] / contrib["Sales"].sum() * 100
        contrib.sort_values("Contribution %", ascending=False, inplace=True)
        fig = px.bar(
            contrib, x="Product line", y="Contribution %",
            title="Sales Contribution by Product Line (%)",
            color="Contribution %", color_continuous_scale=px.colors.sequential.Purples,
            text=contrib["Contribution %"].apply(lambda x: f"{x:.1f}%"),
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="adv_7")

    if "Quantity" in filtered_df.columns and "Sales" in filtered_df.columns:
        st.markdown('<div class="section-header">Sales vs Quantity Relationship</div>', unsafe_allow_html=True)
        fig = px.scatter(
            filtered_df, x="Quantity", y="Sales",
            title="Sales vs Quantity Sold",
            color="Product line" if "Product line" in filtered_df.columns else None,
            color_discrete_sequence=PALETTE,
            size="Unit price" if "Unit price" in filtered_df.columns else None,
            opacity=0.65,
        )
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="adv_8")

# ═══ TAB 11: DATA EXPLORER ══════════════════════════════════════════════════════
with tabs[10]:
    st.markdown('<div class="section-header">Data Explorer</div>', unsafe_allow_html=True)
    qr = quality_report

    de1, de2, de3, de4 = st.columns(4)
    with de1:
        st.markdown(kpi_card("📋", "Total Rows (Raw)", f"{qr['rows']:,}"), unsafe_allow_html=True)
    with de2:
        st.markdown(kpi_card("📊", "Columns", f"{qr['columns']}"), unsafe_allow_html=True)
    with de3:
        st.markdown(kpi_card("❓", "Missing Cells", f"{qr['missing_cells']:,}"), unsafe_allow_html=True)
    with de4:
        st.markdown(kpi_card("📄", "Duplicate Rows", f"{qr['duplicate_rows']:,}"), unsafe_allow_html=True)

    with st.expander("🧹 Data Cleaning Log", expanded=False):
        for action in cleaning_log:
            st.markdown(f"✅ {action}")

    with st.expander("🔍 Missing Values by Column", expanded=False):
        null_df = pd.DataFrame.from_dict(qr["null_by_col"], orient="index", columns=["Missing"])
        null_df = null_df[null_df["Missing"] > 0]
        if null_df.empty:
            st.success("No missing values found!")
        else:
            st.dataframe(null_df, use_container_width=True)

    with st.expander("📌 Column Info & Data Types", expanded=False):
        dtype_df = pd.DataFrame.from_dict(qr["dtypes"], orient="index", columns=["Data Type"])
        st.dataframe(dtype_df, use_container_width=True)

    st.markdown(f"**Filtered Dataset: {len(filtered_df):,} rows × {len(filtered_df.columns)} columns**")
    st.dataframe(filtered_df, use_container_width=True, height=400)

    with st.expander("📊 Descriptive Statistics", expanded=False):
        num_cols_de = filtered_df.select_dtypes(include="number").columns.tolist()
        if num_cols_de:
            st.dataframe(filtered_df[num_cols_de].describe().round(4), use_container_width=True)

    with st.expander("🔢 Unique Values per Column", expanded=False):
        uniq_df = pd.DataFrame({
            "Column":        filtered_df.columns,
            "Unique Values": [filtered_df[c].nunique() for c in filtered_df.columns],
            "Sample Values": [
                str(filtered_df[c].dropna().unique()[:5].tolist())
                for c in filtered_df.columns
            ],
        })
        st.dataframe(uniq_df, use_container_width=True)

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered CSV",
        data=csv_bytes,
        file_name="filtered_supermarket_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
