import io, os
import pandas as pd
import streamlit as st

# ── Minimum required columns (flexible set) ───────────────────────────────────
REQUIRED_COLUMNS = {"Invoice ID", "Branch", "Sales", "Quantity", "Rating", "Date"}

# ── Numeric columns to coerce ─────────────────────────────────────────────────
NUMERIC_COLS = [
    "Unit price", "Quantity", "Tax 5%", "Sales",
    "cogs", "gross margin percentage", "gross income", "Rating",
]

# ── Column name aliases: alternate name → canonical name ─────────────────────
COLUMN_ALIASES = {
    # Customer type variants
    "Customer Type":  "Customer type",
    "customertype":   "Customer type",
    "customer_type":  "Customer type",
    # Unit price variants
    "Unit Price":     "Unit price",
    "unit_price":     "Unit price",
    "UnitPrice":      "Unit price",
    "Price":          "Unit price",
    # Product line variants
    "Category":       "Product line",
    "category":       "Product line",
    "Product Line":   "Product line",
    "product_line":   "Product line",
    "product line":   "Product line",
    # Payment variants
    "Payment Method": "Payment",
    "payment_method": "Payment",
    # Sales variants
    "Total":          "Sales",
    "Revenue":        "Sales",
    "total_sales":    "Sales",
    # Quantity variants
    "Qty":            "Quantity",
    "quantity":       "Quantity",
}

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "SuperMarket Analysis.csv"
)

@st.cache_data(show_spinner=False)
def load_default_csv():
    if not os.path.exists(DEFAULT_CSV_PATH):
        raise FileNotFoundError(f"Default dataset not found at: {DEFAULT_CSV_PATH}")
    return _read_csv(DEFAULT_CSV_PATH)

def load_uploaded_csv(uploaded_file):
    content = uploaded_file.read()
    return _read_csv(io.BytesIO(content))

def _read_csv(source):
    try:
        df = pd.read_csv(source)
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    # 1. Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # 2. Normalize column names via alias map
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    # 3. Coerce numeric columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Derive missing financial/structural columns
    df = _derive_missing_columns(df)

    return df


def _derive_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Safely derive columns that are absent in alternate CSV formats.
    Only derives when source columns are available.
    """
    has_sales = "Sales" in df.columns and df["Sales"].notna().any()
    has_qty   = "Quantity" in df.columns and df["Quantity"].notna().any()
    has_price = "Unit price" in df.columns and df["Unit price"].notna().any()

    # Compute Sales if missing but Quantity + Unit price available
    if not has_sales and has_qty and has_price:
        df["Sales"] = df["Quantity"] * df["Unit price"]
        has_sales = True

    if has_sales:
        # Tax 5%: back-calculate from Sales (Sales already includes tax)
        if "Tax 5%" not in df.columns:
            df["Tax 5%"] = (df["Sales"] * 5 / 105).round(4)
        # gross income = Tax amount
        if "gross income" not in df.columns:
            df["gross income"] = df["Tax 5%"].round(4)
        # cogs = Sales minus gross income
        if "cogs" not in df.columns:
            df["cogs"] = (df["Sales"] - df["gross income"]).round(4)
        # gross margin percentage is always fixed
        if "gross margin percentage" not in df.columns:
            df["gross margin percentage"] = 4.761904762

    # Time: insert None if absent (time analysis will be skipped gracefully)
    if "Time" not in df.columns:
        df["Time"] = None

    # Invoice ID: generate if absent
    if "Invoice ID" not in df.columns:
        df["Invoice ID"] = [f"INV{str(i+1).zfill(5)}" for i in range(len(df))]

    # City: fall back to Branch label if absent
    if "City" not in df.columns and "Branch" in df.columns:
        df["City"] = df["Branch"].astype(str)

    # Product line: fall back to "General" if still absent after alias mapping
    if "Product line" not in df.columns:
        df["Product line"] = "General"

    # Gender: fill missing with "Unknown"
    if "Gender" not in df.columns:
        df["Gender"] = "Unknown"

    # Customer type: fill missing with "Normal"
    if "Customer type" not in df.columns:
        df["Customer type"] = "Normal"

    # Payment: fill missing with "Unknown"
    if "Payment" not in df.columns:
        df["Payment"] = "Unknown"

    return df


def validate_schema(df: pd.DataFrame):
    """
    Validate minimum required columns after normalization.
    Returns (is_valid: bool, missing_cols: list).
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return len(missing) == 0, missing
