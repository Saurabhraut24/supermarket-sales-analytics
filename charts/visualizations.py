import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Colour palette ────────────────────────────────────────────────────────────
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


def _apply(fig):
    fig.update_layout(**LAYOUT)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.15)", zeroline=False)
    return fig


def _empty_fig(message: str = "No data available") -> go.Figure:
    """Return a styled empty figure with a centred message instead of blank axes."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{message}</b>",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=15, color="rgba(255,255,255,0.4)", family="Inter, sans-serif"),
    )
    fig.update_layout(
        **LAYOUT,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Sales charts
# ═══════════════════════════════════════════════════════════════════════════════

def sales_trend(daily: pd.DataFrame) -> go.Figure:
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


def sales_by_category(df: pd.DataFrame, col: str, value_col: str = "Sales",
                       title: str = None, horizontal: bool = True) -> go.Figure:
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
            df, x=col, y=value_col,
            title=title,
            labels={value_col: f"{value_col} ($)", col: col},
            color=col, color_discrete_sequence=PALETTE,
            text_auto=".2s",
        )
    fig.update_traces(textposition="outside" if not horizontal else "inside")
    return _apply(fig)


def sales_by_hour_chart(hourly: pd.DataFrame) -> go.Figure:
    if hourly.empty:
        return _empty_fig("⏰ Hourly data not available\n(No Time column in dataset)")
    fig = px.bar(
        hourly, x="Hour", y="Sales",
        title="Hourly Sales Pattern",
        labels={"Sales": "Total Sales ($)", "Hour": "Hour of Day"},
        color="Sales", color_continuous_scale=BLUE_SEQ,
        text_auto=".2s",
    )
    fig.update_xaxes(tickmode="linear", tick0=0, dtick=1)
    return _apply(fig)


def sales_by_day_chart(daily_name: pd.DataFrame) -> go.Figure:
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


def sales_by_month_chart(monthly: pd.DataFrame) -> go.Figure:
    if monthly.empty:
        return _empty_fig()
    fig = px.line(
        monthly, x="Month_Name", y="Sales",
        title="Monthly Sales",
        labels={"Sales": "Total Sales ($)", "Month_Name": "Month"},
        markers=True,
        color_discrete_sequence=[TEAL],
    )
    fig.update_traces(line_width=3, marker_size=9)
    return _apply(fig)


# ═══════════════════════════════════════════════════════════════════════════════
# Price charts
# ═══════════════════════════════════════════════════════════════════════════════

def price_histogram(prices: pd.Series) -> go.Figure:
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


def price_vs_quantity(df: pd.DataFrame) -> go.Figure:
    if "Unit price" not in df.columns or "Quantity" not in df.columns:
        return _empty_fig()
    color_col = "Product line" if "Product line" in df.columns else None
    fig = px.scatter(
        df, x="Unit price", y="Quantity",
        title="Unit Price vs Quantity Sold",
        labels={"Unit price": "Unit Price ($)", "Quantity": "Quantity"},
        color=color_col,
        color_discrete_sequence=PALETTE,
        opacity=0.6,
        hover_data=["Invoice ID"] if "Invoice ID" in df.columns else None,
    )
    return _apply(fig)


def price_vs_sales(df: pd.DataFrame) -> go.Figure:
    if "Unit price" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    color_col = "Product line" if "Product line" in df.columns else None
    fig = px.scatter(
        df, x="Unit price", y="Sales",
        title="Unit Price vs Total Sales",
        labels={"Unit price": "Unit Price ($)", "Sales": "Total Sales ($)"},
        color=color_col,
        color_discrete_sequence=PALETTE,
        opacity=0.6,
    )
    return _apply(fig)


# ═══════════════════════════════════════════════════════════════════════════════
# Product charts
# ═══════════════════════════════════════════════════════════════════════════════

def product_line_sunburst(df: pd.DataFrame) -> go.Figure:
    if "Product line" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    grp = df.groupby(["Product line"])["Sales"].sum().reset_index()
    fig = px.pie(
        grp, names="Product line", values="Sales",
        title="Sales Share by Product Line",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def gender_pie(df: pd.DataFrame) -> go.Figure:
    if "Gender" not in df.columns or "Sales" not in df.columns:
        return _empty_fig()
    grp = df.groupby("Gender")["Sales"].sum().reset_index()
    fig = px.pie(
        grp, names="Gender", values="Sales",
        title="Sales by Gender",
        color_discrete_sequence=[PURPLE, PINK],
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def customer_type_grouped(ct_df: pd.DataFrame) -> go.Figure:
    if ct_df.empty:
        return _empty_fig()
    fig = px.bar(
        ct_df, x="Customer type",
        y=["Total_Sales", "Avg_Transaction"],
        barmode="group",
        title="Customer Type: Total Sales vs Avg Transaction",
        labels={"value": "Amount ($)", "variable": "Metric"},
        color_discrete_sequence=[TEAL, ORANGE],
    )
    return _apply(fig)


def payment_donut(pay_df: pd.DataFrame) -> go.Figure:
    if pay_df.empty:
        return _empty_fig()
    fig = px.pie(
        pay_df, names="Payment", values="Total_Sales",
        title="Sales by Payment Method",
        color_discrete_sequence=PALETTE,
        hole=0.5,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def payment_bar(pay_df: pd.DataFrame) -> go.Figure:
    if pay_df.empty:
        return _empty_fig()
    fig = px.bar(
        pay_df, x="Payment", y="Transaction_Count",
        title="Transaction Count by Payment Method",
        labels={"Transaction_Count": "Transactions", "Payment": "Payment Method"},
        color="Payment", color_discrete_sequence=PALETTE,
        text_auto=True,
    )
    return _apply(fig)


def branch_radar(branch_df: pd.DataFrame) -> go.Figure:
    if branch_df.empty or "Branch" not in branch_df.columns:
        return _empty_fig()
    metrics = [c for c in ["Sales", "gross income", "Quantity", "Rating"] if c in branch_df.columns]
    if len(metrics) < 2:
        return _empty_fig()
    from sklearn.preprocessing import MinMaxScaler
    try:
        scaler = MinMaxScaler()
        scaled = branch_df[metrics].copy()
        scaled[metrics] = scaler.fit_transform(scaled[metrics])
    except Exception:
        scaled = branch_df.copy()

    fig = go.Figure()
    for _, row in branch_df.iterrows():
        vals = [row[m] for m in metrics]
        fig.add_trace(go.Bar(
            name=str(row["Branch"]),
            x=metrics,
            y=vals,
        ))
    fig.update_layout(
        title="Branch Performance Comparison",
        barmode="group",
        **LAYOUT,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.15)")
    return fig


def rating_histogram(ratings: pd.Series) -> go.Figure:
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


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    if corr.empty:
        return _empty_fig()
    fig = px.imshow(
        corr,
        title="Feature Correlation Matrix",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        text_auto=".2f",
        aspect="auto",
    )
    return _apply(fig)


def pareto_chart(df: pd.DataFrame, col: str = "Product line",
                 value: str = "Sales") -> go.Figure:
    if col not in df.columns or value not in df.columns:
        return _empty_fig()
    grp = df.groupby(col)[value].sum().sort_values(ascending=False).reset_index()
    grp["Cumulative %"] = grp[value].cumsum() / grp[value].sum() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=grp[col], y=grp[value], name=value,
               marker_color=TEAL, text=grp[value].apply(lambda x: f"${x:,.0f}"),
               textposition="outside"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=grp[col], y=grp["Cumulative %"], name="Cumulative %",
                   mode="lines+markers", line_color=ORANGE, marker_size=7),
        secondary_y=True,
    )
    fig.update_layout(title=f"Pareto Chart: {value} by {col}", **LAYOUT)
    fig.update_yaxes(title_text=f"{value} ($)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True)
    fig.update_xaxes(showgrid=False)
    return fig


def gross_income_trend(df: pd.DataFrame) -> go.Figure:
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
