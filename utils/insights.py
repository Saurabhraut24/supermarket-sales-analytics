import pandas as pd
import numpy as np


def generate_insights(df: pd.DataFrame) -> list:
    """
    Dynamically generate text business insights from the filtered DataFrame.
    Returns a list of insight strings.
    """
    insights = []

    if df.empty:
        return ["No data available for the selected filters."]

    def safe(col):
        return col in df.columns and df[col].notna().any()

    # ── Sales insights ───────────────────────────────────────────────────────
    if safe("Product line") and safe("Sales"):
        top_pl = df.groupby("Product line")["Sales"].sum().idxmax()
        top_pl_val = df.groupby("Product line")["Sales"].sum().max()
        low_pl = df.groupby("Product line")["Sales"].sum().idxmin()
        insights.append(
            f"**{top_pl}** is the highest-selling product line "
            f"with total sales of **${top_pl_val:,.2f}**."
        )
        insights.append(
            f"**{low_pl}** is the lowest-selling product line."
        )

    if safe("Branch") and safe("Sales"):
        top_branch = df.groupby("Branch")["Sales"].sum().idxmax()
        top_branch_val = df.groupby("Branch")["Sales"].sum().max()
        insights.append(
            f"Branch **{top_branch}** generated the highest revenue of **${top_branch_val:,.2f}**."
        )

    if safe("City") and safe("Sales"):
        top_city = df.groupby("City")["Sales"].sum().idxmax()
        insights.append(f"**{top_city}** is the top-performing city by sales.")

    # ── Time insights ────────────────────────────────────────────────────────
    if safe("Hour") and safe("Sales"):
        peak_hour = df.groupby("Hour")["Sales"].sum().idxmax()
        am_pm = "AM" if peak_hour < 12 else "PM"
        hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
        hour_12 = 12 if hour_12 == 0 else hour_12
        insights.append(
            f"The peak sales hour is **{hour_12}:00 {am_pm}** ({peak_hour}:00)."
        )

    if safe("Day_Name") and safe("Sales"):
        best_day = df.groupby("Day_Name")["Sales"].sum().idxmax()
        insights.append(f"**{best_day}** is the best-performing day of the week by sales.")

    if safe("Month_Name") and safe("Sales") and df["Month_Name"].nunique() > 1:
        best_month = df.groupby("Month_Name")["Sales"].sum().idxmax()
        insights.append(f"**{best_month}** recorded the highest monthly sales.")

    # ── Customer insights ────────────────────────────────────────────────────
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

    # ── Payment insights ─────────────────────────────────────────────────────
    if safe("Payment") and safe("Sales"):
        top_pay = df.groupby("Payment")["Sales"].sum().idxmax()
        insights.append(
            f"**{top_pay}** is the most popular payment method by total sales."
        )

    # ── Price insights ───────────────────────────────────────────────────────
    if safe("Product line") and safe("Unit price"):
        top_price_pl = df.groupby("Product line")["Unit price"].mean().idxmax()
        top_price_val = df.groupby("Product line")["Unit price"].mean().max()
        insights.append(
            f"**{top_price_pl}** has the highest average unit price of **${top_price_val:,.2f}**."
        )

    # ── Gross Income insights ────────────────────────────────────────────────
    if safe("Product line") and safe("gross income"):
        top_gi_pl = df.groupby("Product line")["gross income"].sum().idxmax()
        top_gi_val = df.groupby("Product line")["gross income"].sum().max()
        insights.append(
            f"**{top_gi_pl}** is the most profitable product line with gross income of **${top_gi_val:,.2f}**."
        )

    # ── Rating insights ──────────────────────────────────────────────────────
    if safe("Product line") and safe("Rating"):
        top_rated = df.groupby("Product line")["Rating"].mean().idxmax()
        top_rated_val = df.groupby("Product line")["Rating"].mean().max()
        low_rated = df.groupby("Product line")["Rating"].mean().idxmin()
        low_rated_val = df.groupby("Product line")["Rating"].mean().min()
        insights.append(
            f"**{top_rated}** has the highest average customer rating ({top_rated_val:.2f}/10)."
        )
        insights.append(
            f"**{low_rated}** has the lowest average customer rating ({low_rated_val:.2f}/10)."
        )

    if safe("Branch") and safe("Rating"):
        top_branch_rating = df.groupby("Branch")["Rating"].mean().idxmax()
        insights.append(
            f"Branch **{top_branch_rating}** has the highest average customer satisfaction rating."
        )

    # ── Quantity insights ────────────────────────────────────────────────────
    if safe("Product line") and safe("Quantity"):
        top_qty_pl = df.groupby("Product line")["Quantity"].sum().idxmax()
        top_qty_val = int(df.groupby("Product line")["Quantity"].sum().max())
        insights.append(
            f"**{top_qty_pl}** had the highest quantity sold ({top_qty_val:,} units)."
        )

    return insights if insights else ["Not enough data to generate insights."]
