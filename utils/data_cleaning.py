import pandas as pd
import numpy as np

def clean_dataframe(df: pd.DataFrame):
    """Clean the dataframe. Returns (cleaned_df, cleaning_report)."""
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

    # 3. Parse Time column (only when real time data exists)
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
    """Return data quality metrics for the raw dataframe."""
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
