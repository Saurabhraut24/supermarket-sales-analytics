import pandas as pd
import numpy as np


def safe_col(df, col):
    """Return True if column exists and has non-null values."""
    return col in df.columns and df[col].notna().any()


def calc_kpis(df: pd.DataFrame) -> dict:
    """Calculate all top-level KPIs from the filtered dataframe."""
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
    if "Date" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    daily = df.groupby("Date")["Sales"].sum().reset_index()
    daily.columns = ["Date", "Sales"]
    daily.sort_values("Date", inplace=True)
    return daily


def sales_by_col(df: pd.DataFrame, col: str, value_col: str = "Sales") -> pd.DataFrame:
    if col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    out = df.groupby(col)[value_col].sum().reset_index().sort_values(value_col, ascending=False)
    return out


def quantity_by_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col not in df.columns or "Quantity" not in df.columns:
        return pd.DataFrame()
    return df.groupby(col)["Quantity"].sum().reset_index().sort_values("Quantity", ascending=False)


def avg_by_col(df: pd.DataFrame, col: str, value_col: str) -> pd.DataFrame:
    if col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    return df.groupby(col)[value_col].mean().reset_index().sort_values(value_col, ascending=False)


def price_distribution(df: pd.DataFrame) -> pd.Series:
    if "Unit price" not in df.columns:
        return pd.Series(dtype=float)
    return df["Unit price"].dropna()


def rating_distribution(df: pd.DataFrame) -> pd.Series:
    if "Rating" not in df.columns:
        return pd.Series(dtype=float)
    return df["Rating"].dropna()


def sales_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    if "Hour" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    return df.groupby("Hour")["Sales"].sum().reset_index().sort_values("Hour")


def sales_by_day_name(df: pd.DataFrame) -> pd.DataFrame:
    if "Day_Name" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grp = df.groupby("Day_Name")["Sales"].sum().reindex(
        [d for d in day_order if d in df["Day_Name"].unique()]
    ).reset_index()
    grp.columns = ["Day_Name", "Sales"]
    return grp


def sales_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if "Month" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby(["Month", "Month_Name"])["Sales"].sum().reset_index()
    grp.sort_values("Month", inplace=True)
    return grp


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = ["Unit price", "Quantity", "Tax 5%", "Sales", "cogs", "gross income", "Rating"]
    existing = [c for c in num_cols if c in df.columns]
    if len(existing) < 2:
        return pd.DataFrame()
    return df[existing].corr()


def payment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "Payment" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby("Payment").agg(
        Total_Sales=("Sales", "sum"),
        Transaction_Count=("Sales", "count"),
        Avg_Transaction=("Sales", "mean"),
    ).reset_index().sort_values("Total_Sales", ascending=False)
    return grp


def customer_type_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "Customer type" not in df.columns or "Sales" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby("Customer type").agg(
        Total_Sales=("Sales", "sum"),
        Transactions=("Sales", "count"),
        Avg_Transaction=("Sales", "mean"),
        Total_Quantity=("Quantity", "sum") if "Quantity" in df.columns else ("Sales", "count"),
    ).reset_index()
    return grp


def branch_analysis(df: pd.DataFrame) -> pd.DataFrame:
    agg = {"Sales": "sum"}
    if "gross income" in df.columns:
        agg["gross income"] = "sum"
    if "Quantity" in df.columns:
        agg["Quantity"] = "sum"
    if "Rating" in df.columns:
        agg["Rating"] = "mean"
    if "Branch" not in df.columns:
        return pd.DataFrame()
    return df.groupby("Branch").agg(agg).reset_index()


def product_line_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "Product line" not in df.columns:
        return pd.DataFrame()
    agg = {"Sales": "sum"}
    if "gross income" in df.columns:
        agg["gross income"] = "sum"
    if "Quantity" in df.columns:
        agg["Quantity"] = "sum"
    if "Unit price" in df.columns:
        agg["Unit price"] = "mean"
    return df.groupby("Product line").agg(agg).reset_index().sort_values("Sales", ascending=False)
