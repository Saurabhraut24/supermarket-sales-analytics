import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader   import load_default_csv, load_uploaded_csv, validate_schema
from utils.data_cleaning import clean_dataframe, get_quality_report
from utils import analytics as an
from utils.insights      import generate_insights
from charts.visualizations import (
    sales_trend, sales_by_category, sales_by_hour_chart, sales_by_day_chart,
    sales_by_month_chart, price_histogram, price_vs_quantity, price_vs_sales,
    product_line_sunburst, gender_pie, payment_donut, payment_bar,
    rating_histogram, correlation_heatmap, pareto_chart, gross_income_trend,
)

st.set_page_config(page_title="SuperMarket Analytics", page_icon="🛒", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
.kpi-card { background: linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.04)); border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:24px 20px; text-align:center; backdrop-filter:blur(12px); transition:transform 0.2s,box-shadow 0.2s; margin-bottom:8px; }
.kpi-card:hover { transform:translateY(-3px); box-shadow:0 12px 40px rgba(0,0,0,0.3); }
.kpi-label { font-size:12px; font-weight:600; letter-spacing:1.2px; text-transform:uppercase; color:rgba(255,255,255,0.6); margin-bottom:6px; }
.kpi-value { font-size:28px; font-weight:700; color:#ffffff; }
.kpi-icon { font-size:22px; margin-bottom:6px; }
.section-header { font-size:22px; font-weight:700; color:#ffffff; border-left:4px solid #7C3AED; padding-left:12px; margin:20px 0 16px 0; }
.insight-card { background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.3); border-radius:12px; padding:14px 18px; margin-bottom:10px; color:#e2e8f0; font-size:14px; line-height:1.6; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#1e1b4b,#312e81) !important; }
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
.stTabs [data-baseweb="tab-list"] { background:rgba(255,255,255,0.05); border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"] { border-radius:8px; padding:8px 18px; font-weight:500; color:rgba(255,255,255,0.6) !important; }
.stTabs [aria-selected="true"] { background:rgba(124,58,237,0.4) !important; color:#ffffff !important; }
[data-testid="stPlotlyChart"] { border-radius:12px; border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.03); }
hr { border-color:rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align:center;padding:30px 0 10px 0;">
<div style="font-size:48px;margin-bottom:8px;">🛒</div>
<h1 style="font-size:36px;font-weight:800;color:#ffffff;margin:0;letter-spacing:-1px;">SuperMarket Sales Analytics Dashboard</h1>
<p style="font-size:16px;color:rgba(255,255,255,0.55);margin-top:8px;">Interactive business intelligence and sales performance analysis</p>
</div><hr/>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 SuperMarket Analytics")
    st.markdown("---")
    st.markdown("### 📂 Upload Dataset")
    uploaded_file = st.file_uploader("Upload Supermarket CSV", type=["csv"],
        help="Upload a compatible supermarket CSV to replace the default dataset.", key="csv_upload")
    st.markdown("---")
    raw_df = None
    data_source = "Default Dataset"
    if uploaded_file is not None:
        try:
            raw_df = load_uploaded_csv(uploaded_file)
            data_source = f"📤 {uploaded_file.name}"
            st.success(f"✅ Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Could not load file: {e}")
    if raw_df is None:
        try:
            raw_df = load_default_csv()
            data_source = "📦 Default Dataset"
        except FileNotFoundError:
            st.error("❌ Default dataset not found. Please upload a CSV.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error loading default dataset: {e}")
            st.stop()
    is_valid, missing_cols = validate_schema(raw_df)
    if not is_valid:
        st.warning(f"⚠️ Non-standard CSV. Missing columns: {', '.join(missing_cols)}")
    if raw_df.empty:
        st.error("❌ The loaded dataset is empty.")
        st.stop()
    quality_report = get_quality_report(raw_df)
    df, cleaning_log = clean_dataframe(raw_df)
    if df.empty:
        st.error("❌ Dataset is empty after cleaning.")
        st.stop()
    st.markdown(f"**Source:** {data_source}")
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    filtered_df = df.copy()
    if "Date" in df.columns and df["Date"].notna().any():
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.date_input("📅 Date Range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            d1, d2 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
            filtered_df = filtered_df[(filtered_df["Date"] >= d1) & (filtered_df["Date"] <= d2)]
    if "Branch" in df.columns:
        branches = sorted(df["Branch"].dropna().unique().tolist())
        sel_branches = st.multiselect("🏪 Branch", branches, default=branches)
        if sel_branches: filtered_df = filtered_df[filtered_df["Branch"].isin(sel_branches)]
    if "City" in df.columns:
        cities = sorted(df["City"].dropna().unique().tolist())
        sel_cities = st.multiselect("🏙️ City", cities, default=cities)
        if sel_cities: filtered_df = filtered_df[filtered_df["City"].isin(sel_cities)]
    if "Customer type" in df.columns:
        ct_vals = sorted(df["Customer type"].dropna().unique().tolist())
        sel_ct = st.multiselect("👤 Customer Type", ct_vals, default=ct_vals)
        if sel_ct: filtered_df = filtered_df[filtered_df["Customer type"].isin(sel_ct)]
    if "Gender" in df.columns:
        genders = sorted(df["Gender"].dropna().unique().tolist())
        sel_gender = st.multiselect("⚧ Gender", genders, default=genders)
        if sel_gender: filtered_df = filtered_df[filtered_df["Gender"].isin(sel_gender)]
    if "Product line" in df.columns:
        products = sorted(df["Product line"].dropna().unique().tolist())
        sel_products = st.multiselect("📦 Product Line", products, default=products)
        if sel_products: filtered_df = filtered_df[filtered_df["Product line"].isin(sel_products)]
    if "Payment" in df.columns:
        payments = sorted(df["Payment"].dropna().unique().tolist())
        sel_payments = st.multiselect("💳 Payment Method", payments, default=payments)
        if sel_payments: filtered_df = filtered_df[filtered_df["Payment"].isin(sel_payments)]
    st.markdown("---")
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.rerun()
    st.markdown(f"**Showing:** {len(filtered_df):,} / {len(df):,} records")
    st.markdown("---")
    st.caption("SuperMarket Analytics v1.0")

if filtered_df.empty:
    st.warning("⚠️ No data matches the selected filters. Please adjust your filters.")
    st.stop()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def kpi_card(icon, label, value):
    return f"""<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>"""

def fmtfig(fig):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", size=13))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.15)", zeroline=False)
    return fig

kpis = an.calc_kpis(filtered_df)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 Overview","📈 Sales Analytics","📦 Product Analytics",
                "👥 Customer Analytics","💰 Profit Analysis","🕐 Time Analysis",
                "💳 Payment Analysis","🏪 Branch & Location","⭐ Ratings",
                "🔬 Advanced","🗃️ Data Explorer"])

# ═══ TAB 1: OVERVIEW ══════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        if "total_sales" in kpis: st.markdown(kpi_card("💵","Total Sales",f"${kpis['total_sales']:,.2f}"),unsafe_allow_html=True)
    with c2:
        if "total_gross_income" in kpis: st.markdown(kpi_card("💹","Total Gross Income",f"${kpis['total_gross_income']:,.2f}"),unsafe_allow_html=True)
    with c3:
        if "total_transactions" in kpis: st.markdown(kpi_card("🧾","Transactions",f"{kpis['total_transactions']:,}"),unsafe_allow_html=True)
    with c4:
        if "total_quantity" in kpis: st.markdown(kpi_card("📦","Total Quantity Sold",f"{kpis['total_quantity']:,}"),unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5:
        if "avg_order_value" in kpis: st.markdown(kpi_card("🛒","Avg Order Value",f"${kpis['avg_order_value']:,.2f}"),unsafe_allow_html=True)
    with c6:
        if "avg_unit_price" in kpis: st.markdown(kpi_card("🏷️","Avg Unit Price",f"${kpis['avg_unit_price']:,.2f}"),unsafe_allow_html=True)
    with c7:
        if "gross_margin_pct" in kpis: st.markdown(kpi_card("📊","Gross Margin %",f"{kpis['gross_margin_pct']:.2f}%"),unsafe_allow_html=True)
    with c8:
        if "avg_rating" in kpis: st.markdown(kpi_card("⭐","Avg Customer Rating",f"{kpis['avg_rating']:.2f}/10"),unsafe_allow_html=True)
    st.markdown("---")
    co1,co2 = st.columns(2)
    with co1:
        daily = an.sales_over_time(filtered_df)
        st.plotly_chart(sales_trend(daily), use_container_width=True, key="chart_1")
    with co2:
        st.plotly_chart(product_line_sunburst(filtered_df), use_container_width=True, key="chart_2")
    co3,co4 = st.columns(2)
    with co3:
        branch_sales = an.sales_by_col(filtered_df,"Branch")
        st.plotly_chart(sales_by_category(branch_sales,"Branch","Sales","Sales by Branch",horizontal=False), use_container_width=True, key="chart_3")
    with co4:
        city_sales = an.sales_by_col(filtered_df,"City")
        st.plotly_chart(sales_by_category(city_sales,"City","Sales","Sales by City",horizontal=False), use_container_width=True, key="chart_4")
    st.markdown('<div class="section-header">💡 Business Insights</div>', unsafe_allow_html=True)
    insights = generate_insights(filtered_df)
    ins_cols = st.columns(2)
    for i,insight in enumerate(insights):
        with ins_cols[i%2]:
            st.markdown(f'<div class="insight-card">💡 {insight}</div>', unsafe_allow_html=True)

# ═══ TAB 2: SALES ANALYTICS ═══════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-header">Sales Analytics</div>', unsafe_allow_html=True)
    daily = an.sales_over_time(filtered_df)
    st.plotly_chart(sales_trend(daily), use_container_width=True, key="chart_5")
    sa1,sa2 = st.columns(2)
    with sa1:
        pl_sales = an.sales_by_col(filtered_df,"Product line")
        st.plotly_chart(sales_by_category(pl_sales,"Product line","Sales","Sales by Product Line"), use_container_width=True, key="chart_6")
    with sa2:
        branch_sales = an.sales_by_col(filtered_df,"Branch")
        st.plotly_chart(sales_by_category(branch_sales,"Branch","Sales","Sales by Branch",horizontal=False), use_container_width=True, key="chart_7")
    sa3,sa4 = st.columns(2)
    with sa3:
        ct_sales = an.sales_by_col(filtered_df,"Customer type")
        st.plotly_chart(sales_by_category(ct_sales,"Customer type","Sales","Sales by Customer Type",horizontal=False), use_container_width=True, key="chart_8")
    with sa4:
        st.plotly_chart(gender_pie(filtered_df), use_container_width=True, key="chart_9")
    sa5,sa6 = st.columns(2)
    with sa5:
        pay_sales = an.sales_by_col(filtered_df,"Payment")
        st.plotly_chart(sales_by_category(pay_sales,"Payment","Sales","Sales by Payment Method",horizontal=False), use_container_width=True, key="chart_10")
    with sa6:
        qty_sales = an.quantity_by_col(filtered_df,"Product line")
        st.plotly_chart(sales_by_category(qty_sales,"Product line","Quantity","Quantity Sold by Product Line"), use_container_width=True, key="chart_11")
    st.markdown("---")
    sa7,sa8 = st.columns(2)
    with sa7:
        city_sales2 = an.sales_by_col(filtered_df,"City")
        st.plotly_chart(sales_by_category(city_sales2,"City","Sales","Sales by City",horizontal=False), use_container_width=True, key="chart_12")
    with sa8:
        avg_price_pl = an.avg_by_col(filtered_df,"Product line","Unit price")
        st.plotly_chart(sales_by_category(avg_price_pl,"Product line","Unit price","Avg Unit Price by Product Line"), use_container_width=True, key="chart_13")

# ═══ TAB 3: PRODUCT ANALYTICS ══════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-header">Product Analytics</div>', unsafe_allow_html=True)
    prod_df = an.product_line_analysis(filtered_df)
    pa1,pa2 = st.columns(2)
    with pa1:
        st.plotly_chart(product_line_sunburst(filtered_df), use_container_width=True, key="chart_14")
    with pa2:
        if not prod_df.empty and "Quantity" in prod_df.columns:
            st.plotly_chart(sales_by_category(prod_df[["Product line","Quantity"]],"Product line","Quantity","Units Sold by Product Line"), use_container_width=True, key="chart_15")
    pa3,pa4 = st.columns(2)
    with pa3:
        if not prod_df.empty and "Sales" in prod_df.columns:
            top5 = prod_df.nlargest(5,"Sales")
            st.plotly_chart(sales_by_category(top5,"Product line","Sales","Top Product Lines by Sales"), use_container_width=True, key="chart_16")
    with pa4:
        if not prod_df.empty and "Sales" in prod_df.columns:
            bot5 = prod_df.nsmallest(5,"Sales")
            st.plotly_chart(sales_by_category(bot5,"Product line","Sales","Lowest Product Lines by Sales"), use_container_width=True, key="chart_17")
    pa5,pa6 = st.columns(2)
    with pa5:
        avg_price_pl = an.avg_by_col(filtered_df,"Product line","Unit price")
        st.plotly_chart(sales_by_category(avg_price_pl,"Product line","Unit price","Avg Unit Price by Product Line"), use_container_width=True, key="chart_18")
    with pa6:
        if not prod_df.empty and "gross income" in prod_df.columns:
            st.plotly_chart(sales_by_category(prod_df,"Product line","gross income","Gross Income by Product Line"), use_container_width=True, key="chart_19")
    st.markdown('<div class="section-header">Pareto Analysis</div>', unsafe_allow_html=True)
    st.plotly_chart(pareto_chart(filtered_df,"Product line","Sales"), use_container_width=True, key="chart_20")

# ═══ TAB 4: CUSTOMER ANALYTICS ═════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-header">Customer Analytics</div>', unsafe_allow_html=True)
    ca1,ca2 = st.columns(2)
    with ca1:
        st.plotly_chart(gender_pie(filtered_df), use_container_width=True, key="chart_21")
    with ca2:
        if "Customer type" in filtered_df.columns and "Sales" in filtered_df.columns:
            ct_grp = filtered_df.groupby("Customer type")["Sales"].sum().reset_index()
            fig = px.pie(ct_grp, names="Customer type", values="Sales",
                         title="Sales by Customer Type",
                         color_discrete_sequence=["#7C3AED","#0D9488"], hole=0.45)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_22")
    ca3,ca4 = st.columns(2)
    with ca3:
        ct_a = an.customer_type_analysis(filtered_df)
        if not ct_a.empty and "Avg_Transaction" in ct_a.columns:
            fig = px.bar(ct_a, x="Customer type", y="Avg_Transaction",
                         title="Avg Transaction Value by Customer Type",
                         color="Customer type", color_discrete_sequence=["#7C3AED","#0D9488"],
                         text_auto=".2f", labels={"Avg_Transaction":"Avg Transaction ($)"})
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_23")
    with ca4:
        if "Customer type" in filtered_df.columns and "Quantity" in filtered_df.columns:
            ct_qty = filtered_df.groupby("Customer type")["Quantity"].sum().reset_index()
            fig = px.bar(ct_qty, x="Customer type", y="Quantity",
                         title="Total Quantity by Customer Type",
                         color="Customer type", color_discrete_sequence=["#7C3AED","#0D9488"], text_auto=True)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_24")
    ca5,ca6 = st.columns(2)
    with ca5:
        if all(c in filtered_df.columns for c in ["Gender","Product line","Sales"]):
            gpl = filtered_df.groupby(["Gender","Product line"])["Sales"].sum().reset_index()
            fig = px.bar(gpl, x="Product line", y="Sales", color="Gender", barmode="group",
                         title="Sales by Gender and Product Line",
                         color_discrete_sequence=["#7C3AED","#DB2777"])
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_25")
    with ca6:
        if "Customer type" in filtered_df.columns and "Rating" in filtered_df.columns:
            ct_r = filtered_df.groupby("Customer type")["Rating"].mean().reset_index()
            fig = px.bar(ct_r, x="Customer type", y="Rating",
                         title="Avg Rating by Customer Type",
                         color="Customer type", color_discrete_sequence=["#7C3AED","#0D9488"],
                         text_auto=".2f")
            fig.update_yaxes(range=[0,10])
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_26")

# ═══ TAB 5: PROFIT / GROSS INCOME ══════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-header">Gross Income Analysis</div>', unsafe_allow_html=True)
    if "gross income" not in filtered_df.columns:
        st.warning("Gross income column not found in the dataset.")
    else:
        gi1,gi2,gi3,gi4 = st.columns(4)
        with gi1: st.markdown(kpi_card("💹","Total Gross Income",f"${filtered_df['gross income'].sum():,.2f}"),unsafe_allow_html=True)
        with gi2: st.markdown(kpi_card("📊","Avg Gross Income",f"${filtered_df['gross income'].mean():,.2f}"),unsafe_allow_html=True)
        with gi3:
            if "Sales" in filtered_df.columns and filtered_df["Sales"].sum()>0:
                margin = filtered_df["gross income"].sum()/filtered_df["Sales"].sum()*100
                st.markdown(kpi_card("📈","Gross Margin %",f"{margin:.2f}%"),unsafe_allow_html=True)
        with gi4:
            if "gross margin percentage" in filtered_df.columns:
                st.markdown(kpi_card("🎯","Avg Margin %",f"{filtered_df['gross margin percentage'].mean():.2f}%"),unsafe_allow_html=True)
        pf1,pf2 = st.columns(2)
        with pf1:
            gi_pl = an.sales_by_col(filtered_df,"Product line","gross income")
            st.plotly_chart(sales_by_category(gi_pl,"Product line","gross income","Gross Income by Product Line"), use_container_width=True, key="chart_27")
        with pf2:
            gi_branch = an.sales_by_col(filtered_df,"Branch","gross income")
            st.plotly_chart(sales_by_category(gi_branch,"Branch","gross income","Gross Income by Branch",horizontal=False), use_container_width=True, key="chart_28")
        pf3,pf4 = st.columns(2)
        with pf3:
            st.plotly_chart(gross_income_trend(filtered_df), use_container_width=True, key="chart_29")
        with pf4:
            if "Sales" in filtered_df.columns:
                fig = px.scatter(filtered_df, x="Sales", y="gross income",
                                 title="Gross Income vs Total Sales",
                                 color="Product line" if "Product line" in filtered_df.columns else None,
                                 color_discrete_sequence=px.colors.qualitative.Vivid, opacity=0.6)
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_30")
        if "cogs" in filtered_df.columns and "Sales" in filtered_df.columns:
            pf5,pf6 = st.columns(2)
            with pf5:
                fig = px.scatter(filtered_df, x="cogs", y="gross income",
                                 title="COGS vs Gross Income",
                                 color="Product line" if "Product line" in filtered_df.columns else None,
                                 color_discrete_sequence=px.colors.qualitative.Vivid, opacity=0.6)
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_31")
            with pf6:
                cogs_pl = an.sales_by_col(filtered_df,"Product line","cogs")
                st.plotly_chart(sales_by_category(cogs_pl,"Product line","cogs","COGS by Product Line"), use_container_width=True, key="chart_32")

# ═══ TAB 6: TIME ANALYSIS ══════════════════════════════════════════════════════
with tabs[5]:
    st.markdown('<div class="section-header">Time Analysis</div>', unsafe_allow_html=True)
    tcols = st.columns(3)
    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "Sales" in filtered_df.columns:
        peak_hour = int(filtered_df.groupby("Hour")["Sales"].sum().idxmax())
        am_pm = "AM" if peak_hour < 12 else "PM"
        h12 = peak_hour if 1<=peak_hour<=12 else (peak_hour-12 if peak_hour>12 else 12)
        with tcols[0]: st.markdown(kpi_card("⏰","Peak Sales Hour",f"{h12}:00 {am_pm}"),unsafe_allow_html=True)
    if "Day_Name" in filtered_df.columns and "Sales" in filtered_df.columns:
        best_day = filtered_df.groupby("Day_Name")["Sales"].sum().idxmax()
        with tcols[1]: st.markdown(kpi_card("📅","Best Sales Day",best_day),unsafe_allow_html=True)
    if "Month_Name" in filtered_df.columns and "Sales" in filtered_df.columns and filtered_df["Month_Name"].nunique()>1:
        best_month = filtered_df.groupby("Month_Name")["Sales"].sum().idxmax()
        with tcols[2]: st.markdown(kpi_card("📆","Best Sales Month",best_month),unsafe_allow_html=True)
    ta1,ta2 = st.columns(2)
    with ta1:
        hourly = an.sales_by_hour(filtered_df)
        st.plotly_chart(sales_by_hour_chart(hourly), use_container_width=True, key="chart_33")
    with ta2:
        day_sales = an.sales_by_day_name(filtered_df)
        st.plotly_chart(sales_by_day_chart(day_sales), use_container_width=True, key="chart_34")
    ta3,ta4 = st.columns(2)
    with ta3:
        monthly = an.sales_by_month(filtered_df)
        st.plotly_chart(sales_by_month_chart(monthly), use_container_width=True, key="chart_35")
    with ta4:
        daily = an.sales_over_time(filtered_df)
        st.plotly_chart(sales_trend(daily), use_container_width=True, key="chart_36")
    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "Quantity" in filtered_df.columns:
        qty_h = filtered_df.groupby("Hour")["Quantity"].sum().reset_index()
        fig = px.bar(qty_h, x="Hour", y="Quantity", title="Quantity Sold by Hour",
                     color="Quantity", color_continuous_scale=px.colors.sequential.Greens, text_auto=True)
        fig.update_xaxes(tickmode="linear",tick0=0,dtick=1)
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_37")
    if "Hour" in filtered_df.columns and filtered_df["Hour"].notna().any() and "gross income" in filtered_df.columns:
        gi_h = filtered_df.groupby("Hour")["gross income"].sum().reset_index()
        fig = px.line(gi_h, x="Hour", y="gross income", title="Gross Income by Hour",
                      markers=True, color_discrete_sequence=["#D97706"])
        fig.update_traces(line_width=2, marker_size=7)
        fig.update_xaxes(tickmode="linear",tick0=0,dtick=1)
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_38")

# ═══ TAB 7: PAYMENT ANALYSIS ════════════════════════════════════════════════════
with tabs[6]:
    st.markdown('<div class="section-header">Payment Analysis</div>', unsafe_allow_html=True)
    pay_df = an.payment_analysis(filtered_df)
    if pay_df.empty:
        st.warning("Payment data not available.")
    else:
        pm1,pm2 = st.columns(2)
        with pm1: st.plotly_chart(payment_donut(pay_df), use_container_width=True, key="chart_39")
        with pm2: st.plotly_chart(payment_bar(pay_df), use_container_width=True, key="chart_40")
        pm3,pm4 = st.columns(2)
        with pm3:
            fig = px.bar(pay_df, x="Payment", y="Total_Sales", title="Total Sales by Payment Method",
                         color="Payment", color_discrete_sequence=px.colors.qualitative.Vivid, text_auto=".2s")
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_41")
        with pm4:
            fig = px.bar(pay_df, x="Payment", y="Avg_Transaction", title="Avg Transaction by Payment Method",
                         color="Payment", color_discrete_sequence=px.colors.qualitative.Vivid, text_auto=".2f",
                         labels={"Avg_Transaction":"Avg Transaction ($)"})
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_42")
        with st.expander("📊 Payment Summary Table"):
            st.dataframe(pay_df.style.format({"Total_Sales":"${:,.2f}","Avg_Transaction":"${:,.2f}","Transaction_Count":"{:,}"}), use_container_width=True)

# ═══ TAB 8: BRANCH & LOCATION ══════════════════════════════════════════════════
with tabs[7]:
    st.markdown('<div class="section-header">Branch & Location Analysis</div>', unsafe_allow_html=True)
    branch_df = an.branch_analysis(filtered_df)
    if branch_df.empty:
        st.warning("Branch data not available.")
    else:
        if "Sales" in branch_df.columns:
            best_br = branch_df.loc[branch_df["Sales"].idxmax(),"Branch"]
            best_br_val = branch_df["Sales"].max()
            st.markdown(f'<div class="insight-card">🏆 Best performing branch: <strong>{best_br}</strong> with ${best_br_val:,.2f} in total sales.</div>', unsafe_allow_html=True)
        bl1,bl2 = st.columns(2)
        with bl1:
            st.plotly_chart(sales_by_category(branch_df,"Branch","Sales","Sales by Branch",horizontal=False), use_container_width=True, key="chart_43")
        with bl2:
            if "gross income" in branch_df.columns:
                st.plotly_chart(sales_by_category(branch_df,"Branch","gross income","Gross Income by Branch",horizontal=False), use_container_width=True, key="chart_44")
        bl3,bl4 = st.columns(2)
        with bl3:
            if "Quantity" in branch_df.columns:
                st.plotly_chart(sales_by_category(branch_df,"Branch","Quantity","Quantity Sold by Branch",horizontal=False), use_container_width=True, key="chart_45")
        with bl4:
            if "Rating" in branch_df.columns:
                fig = px.bar(branch_df, x="Branch", y="Rating", title="Avg Rating by Branch",
                             color="Branch", color_discrete_sequence=px.colors.qualitative.Vivid, text_auto=".2f")
                fig.update_yaxes(range=[0,10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_46")
        if all(c in filtered_df.columns for c in ["Branch","Product line","Sales"]):
            bpl = filtered_df.groupby(["Branch","Product line"])["Sales"].sum().reset_index()
            fig = px.bar(bpl, x="Product line", y="Sales", color="Branch", barmode="group",
                         title="Product Line Sales by Branch",
                         color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_47")
        if "City" in filtered_df.columns and "Sales" in filtered_df.columns:
            city_grp = filtered_df.groupby("City")["Sales"].sum().reset_index().sort_values("Sales",ascending=False)
            fig = px.bar(city_grp, x="City", y="Sales", title="Sales by City",
                         color="City", color_discrete_sequence=px.colors.qualitative.Vivid, text_auto=".2s")
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_48")

# ═══ TAB 9: RATINGS ═══════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown('<div class="section-header">Customer Rating Analysis</div>', unsafe_allow_html=True)
    if "Rating" not in filtered_df.columns:
        st.warning("Rating column not found.")
    else:
        rk1,rk2,rk3 = st.columns(3)
        with rk1: st.markdown(kpi_card("⭐","Average Rating",f"{filtered_df['Rating'].mean():.2f}/10"),unsafe_allow_html=True)
        with rk2: st.markdown(kpi_card("🔺","Max Rating",f"{filtered_df['Rating'].max():.1f}"),unsafe_allow_html=True)
        with rk3: st.markdown(kpi_card("🔻","Min Rating",f"{filtered_df['Rating'].min():.1f}"),unsafe_allow_html=True)
        ra1,ra2 = st.columns(2)
        with ra1:
            st.plotly_chart(rating_histogram(an.rating_distribution(filtered_df)), use_container_width=True, key="chart_49")
        with ra2:
            if "Product line" in filtered_df.columns:
                pl_r = filtered_df.groupby("Product line")["Rating"].mean().reset_index().sort_values("Rating",ascending=False)
                fig = px.bar(pl_r, x="Product line", y="Rating", title="Avg Rating by Product Line",
                             color="Rating", color_continuous_scale=px.colors.sequential.Oranges, text_auto=".2f")
                fig.update_yaxes(range=[0,10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_50")
        ra3,ra4 = st.columns(2)
        with ra3:
            if "Branch" in filtered_df.columns:
                br_r = filtered_df.groupby("Branch")["Rating"].mean().reset_index().sort_values("Rating",ascending=False)
                fig = px.bar(br_r, x="Branch", y="Rating", title="Avg Rating by Branch",
                             color="Branch", color_discrete_sequence=px.colors.qualitative.Vivid, text_auto=".2f")
                fig.update_yaxes(range=[0,10])
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_51")
        with ra4:
            if "Sales" in filtered_df.columns:
                fig = px.scatter(filtered_df, x="Rating", y="Sales", title="Rating vs Sales",
                                 color="Product line" if "Product line" in filtered_df.columns else None,
                                 color_discrete_sequence=px.colors.qualitative.Vivid, opacity=0.55)
                st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_52")
        if "Gender" in filtered_df.columns:
            gender_r = filtered_df.groupby("Gender")["Rating"].mean().reset_index()
            fig = px.bar(gender_r, x="Gender", y="Rating", title="Avg Rating by Gender",
                         color="Gender", color_discrete_sequence=["#7C3AED","#DB2777"], text_auto=".2f")
            fig.update_yaxes(range=[0,10])
            st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_53")

# ═══ TAB 10: ADVANCED ANALYTICS ════════════════════════════════════════════════
with tabs[9]:
    st.markdown('<div class="section-header">Advanced Analytics</div>', unsafe_allow_html=True)
    adv1,adv2 = st.columns(2)
    with adv1:
        st.plotly_chart(price_histogram(an.price_distribution(filtered_df)), use_container_width=True, key="chart_54")
    with adv2:
        st.plotly_chart(price_vs_quantity(filtered_df), use_container_width=True, key="chart_55")
    adv3,adv4 = st.columns(2)
    with adv3:
        st.plotly_chart(price_vs_sales(filtered_df), use_container_width=True, key="chart_56")
    with adv4:
        corr = an.correlation_matrix(filtered_df)
        st.plotly_chart(correlation_heatmap(corr), use_container_width=True, key="chart_57")
    st.markdown('<div class="section-header">Pareto Analysis</div>', unsafe_allow_html=True)
    par1,par2 = st.columns(2)
    with par1:
        st.plotly_chart(pareto_chart(filtered_df,"Product line","Sales"), use_container_width=True, key="chart_58")
    with par2:
        if "gross income" in filtered_df.columns:
            st.plotly_chart(pareto_chart(filtered_df,"Product line","gross income"), use_container_width=True, key="chart_59")
    if "Product line" in filtered_df.columns and "Sales" in filtered_df.columns:
        st.markdown('<div class="section-header">Sales Contribution %</div>', unsafe_allow_html=True)
        contrib = filtered_df.groupby("Product line")["Sales"].sum().reset_index()
        contrib["Contribution %"] = contrib["Sales"]/contrib["Sales"].sum()*100
        contrib.sort_values("Contribution %",ascending=False,inplace=True)
        fig = px.bar(contrib, x="Product line", y="Contribution %",
                     title="Sales Contribution by Product Line (%)",
                     color="Contribution %", color_continuous_scale=px.colors.sequential.Purples,
                     text=contrib["Contribution %"].apply(lambda x: f"{x:.1f}%"))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_60")
    if "Quantity" in filtered_df.columns and "Sales" in filtered_df.columns:
        st.markdown('<div class="section-header">Sales vs Quantity Relationship</div>', unsafe_allow_html=True)
        fig = px.scatter(filtered_df, x="Quantity", y="Sales",
                         title="Sales vs Quantity Sold",
                         color="Product line" if "Product line" in filtered_df.columns else None,
                         color_discrete_sequence=px.colors.qualitative.Vivid,
                         size="Unit price" if "Unit price" in filtered_df.columns else None,
                         opacity=0.65)
        st.plotly_chart(fmtfig(fig), use_container_width=True, key="chart_61")

# ═══ TAB 11: DATA EXPLORER ══════════════════════════════════════════════════════
with tabs[10]:
    st.markdown('<div class="section-header">Data Explorer</div>', unsafe_allow_html=True)
    qr = quality_report
    de1,de2,de3,de4 = st.columns(4)
    with de1: st.markdown(kpi_card("📋","Total Rows (Raw)",f"{qr['rows']:,}"),unsafe_allow_html=True)
    with de2: st.markdown(kpi_card("📊","Columns",f"{qr['columns']}"),unsafe_allow_html=True)
    with de3: st.markdown(kpi_card("❓","Missing Cells",f"{qr['missing_cells']:,}"),unsafe_allow_html=True)
    with de4: st.markdown(kpi_card("📄","Duplicate Rows",f"{qr['duplicate_rows']:,}"),unsafe_allow_html=True)
    with st.expander("🧹 Data Cleaning Log", expanded=False):
        for action in cleaning_log:
            st.markdown(f"✅ {action}")
    with st.expander("🔍 Missing Values by Column", expanded=False):
        null_df = pd.DataFrame.from_dict(qr["null_by_col"], orient="index", columns=["Missing"])
        null_df = null_df[null_df["Missing"]>0]
        if null_df.empty:
            st.success("✅ No missing values found!")
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
            "Column": filtered_df.columns,
            "Unique Values": [filtered_df[c].nunique() for c in filtered_df.columns],
            "Sample Values": [str(filtered_df[c].dropna().unique()[:5].tolist()) for c in filtered_df.columns],
        })
        st.dataframe(uniq_df, use_container_width=True)
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(label="⬇️ Download Filtered CSV", data=csv_bytes,
                       file_name="filtered_supermarket_data.csv", mime="text/csv",
                       use_container_width=True)
