from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="ShopSphere | E-commerce Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "cleaned_ecommerce_orders.csv"
BLUE, TEAL, AMBER, RED, PURPLE = "#2463a6", "#18a999", "#e9a23b", "#d9534f", "#8a7ad6"
CATEGORY_COLORS = {"Electronics": BLUE, "Office": AMBER, "Wearables": TEAL, "Accessories": PURPLE}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1400px;}
    [data-testid="stMetric"] {
        border: 1px solid rgba(128,140,160,.28); padding: 14px 18px;
        border-radius: 14px; background: rgba(128,140,160,.06);
    }
    .hero {
        background: linear-gradient(115deg, #142b4a 0%, #205b83 60%, #2b8c9c 100%);
        padding: 26px 30px; border-radius: 18px; color: #fff; margin-bottom: 16px;
    }
    .hero h1 {color: #fff; margin: 0; font-size: 1.9rem;}
    .hero p {color: #d9eaf6; margin: 6px 0 0 0;}
    .note {font-size: .85rem; opacity: .75;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["OrderDate"])
    required = {
        "OrderID", "OrderDate", "CustomerID", "CustomerName", "Product", "Category",
        "City", "Quantity", "Revenue", "Cost", "Profit", "PaymentMethod",
        "OrderStatus", "Discount",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    return data


if not DATA_PATH.exists():
    st.error("Cleaned dataset not found. Run ECommerce_Analysis.ipynb first.")
    st.stop()

df = load_data(str(DATA_PATH))

# ---------------------------------------------------------------- sidebar
st.sidebar.markdown("## Filters")
d_min, d_max = df["OrderDate"].min().date(), df["OrderDate"].max().date()
picked = st.sidebar.date_input("Order date range", (d_min, d_max), min_value=d_min, max_value=d_max)
start, end = (picked if isinstance(picked, (tuple, list)) and len(picked) == 2 else (d_min, d_max))

categories = sorted(df["Category"].dropna().unique())
cities = sorted(df["City"].dropna().unique())
statuses = sorted(df["OrderStatus"].dropna().unique())
payments = sorted(df["PaymentMethod"].dropna().unique())

sel_cat = st.sidebar.multiselect("Category", categories, default=categories)
sel_city = st.sidebar.multiselect("City", cities, default=cities)
sel_status = st.sidebar.multiselect("Order status", statuses, default=statuses)
sel_pay = st.sidebar.multiselect("Payment method", payments, default=payments)

mask = (
    df["OrderDate"].dt.date.between(start, end)
    & df["Category"].isin(sel_cat)
    & df["City"].isin(sel_city)
    & df["OrderStatus"].isin(sel_status)
    & df["PaymentMethod"].isin(sel_pay)
)
f = df.loc[mask].copy()

# ---------------------------------------------------------------- header
st.markdown(
    """
    <div class="hero">
      <h1>ShopSphere | E-commerce Intelligence</h1>
      <p>Sales performance · Product profitability · Customer value · Geographic trends</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if f.empty:
    st.warning("No records match the current filters. Adjust the filters in the sidebar.")
    st.stop()

metric = st.radio("Metric", ["Revenue", "Profit", "Orders"], horizontal=True)


def agg(frame: pd.DataFrame, by) -> pd.DataFrame:
    return frame.groupby(by, as_index=False).agg(
        Revenue=("Revenue", "sum"), Profit=("Profit", "sum"),
        Orders=("OrderID", "nunique"), Units=("Quantity", "sum"),
    )


def axis_fmt(fig, axis="x"):
    if metric != "Orders":
        getattr(fig, f"update_{axis}axes")(tickprefix="₹", tickformat="~s")
    return fig


# ---------------------------------------------------------------- KPIs
revenue, profit = f["Revenue"].sum(), f["Profit"].sum()
orders, units = f["OrderID"].nunique(), f["Quantity"].sum()
cols = st.columns(6)
cols[0].metric("Revenue", f"₹{revenue / 1e6:,.1f}M")
cols[1].metric("Profit", f"₹{profit / 1e6:,.1f}M")
cols[2].metric("Margin", f"{profit / revenue * 100:.2f}%" if revenue else "n/a")
cols[3].metric("Orders", f"{orders:,}")
cols[4].metric("Avg order value", f"₹{revenue / orders:,.0f}" if orders else "n/a")
cols[5].metric("Units sold", f"{units:,}")

# ---------------------------------------------------------------- trend + status
monthly = agg(f.assign(Month=f["OrderDate"].dt.to_period("M").astype(str)), "Month")
left, right = st.columns([1.5, 1])
with left:
    fig = px.area(monthly, x="Month", y=metric, markers=True, title=f"Monthly {metric}",
                  template="plotly_white", color_discrete_sequence=[BLUE])
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(axis_fmt(fig, "y"), use_container_width=True)
with right:
    status = f.groupby("OrderStatus", as_index=False).agg(Orders=("OrderID", "nunique"))
    fig = px.pie(status, names="OrderStatus", values="Orders", hole=0.62,
                 title="Order status mix", template="plotly_white",
                 color_discrete_sequence=[BLUE, RED, AMBER])
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=340, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- product + city
product = agg(f, ["Product", "Category"])
product["Profit Margin"] = np.where(product["Revenue"] != 0, product["Profit"] / product["Revenue"] * 100, 0)
city = agg(f, "City")
city["Profit Margin"] = np.where(city["Revenue"] != 0, city["Profit"] / city["Revenue"] * 100, 0)

left, right = st.columns(2)
with left:
    fig = px.bar(product.sort_values(metric), x=metric, y="Product", color="Category",
                 orientation="h", title=f"Products by {metric.lower()}",
                 template="plotly_white", color_discrete_map=CATEGORY_COLORS)
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(axis_fmt(fig), use_container_width=True)
with right:
    fig = px.bar(city.sort_values(metric), x=metric, y="City", orientation="h",
                 color="Profit Margin", color_continuous_scale=["#b7d9e8", "#205b83"],
                 title=f"Cities by {metric.lower()}", template="plotly_white")
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(axis_fmt(fig), use_container_width=True)

# ---------------------------------------------------------------- profit concentration
pareto = product.sort_values("Profit", ascending=False).reset_index(drop=True)
total_profit = pareto["Profit"].sum()
pareto["Cumulative Profit %"] = pareto["Profit"].cumsum() / total_profit * 100 if total_profit else 0
fig = px.line(pareto, x="Product", y="Cumulative Profit %", markers=True,
              title="Profit concentration (cumulative share of profit)", template="plotly_white",
              color_discrete_sequence=[TEAL])
fig.update_yaxes(ticksuffix="%", range=[0, 105])
fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- segments + discounts
customer = f.groupby(["CustomerID", "CustomerName"], as_index=False).agg(
    Orders=("OrderID", "nunique"), Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
customer["Segment"] = np.select(
    [customer["Orders"].eq(1), customer["Orders"].between(2, 4), customer["Orders"].ge(5)],
    ["One-time", "Occasional", "Frequent"], default="Unclassified")
segment = customer.groupby("Segment", as_index=False).agg(
    Customers=("CustomerID", "nunique"), Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
segment["Revenue / Customer"] = (segment["Revenue"] / segment["Customers"]).round(0)
segment["Profit / Customer"] = (segment["Profit"] / segment["Customers"]).round(0)

discount = agg(f, "Discount")
discount["Margin %"] = np.where(discount["Revenue"] != 0, discount["Profit"] / discount["Revenue"] * 100, 0).round(2)
discount["Discount"] = (discount["Discount"] * 100).round(0).astype(int).astype(str) + "%"

st.markdown("### Customers & Discounts")
left, right = st.columns(2)
with left:
    st.markdown("**Customer segments** (1 order, 2-4 orders, 5+ orders)")
    st.dataframe(segment, use_container_width=True, hide_index=True)
with right:
    st.markdown("**Discount level vs. margin** (descriptive only, not causal)")
    st.dataframe(discount[["Discount", "Orders", "Revenue", "Margin %"]],
                 use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- detail tables
st.markdown("### Detail Tables")
t1, t2, t3 = st.tabs(["Products", "Cities", "Top customers"])
with t1:
    show = product.sort_values("Revenue", ascending=False).copy()
    show["Profit Margin"] = show["Profit Margin"].map(lambda x: f"{x:.2f}%")
    st.dataframe(show, use_container_width=True, hide_index=True)
with t2:
    show = city.sort_values("Revenue", ascending=False).copy()
    show["Profit Margin"] = show["Profit Margin"].map(lambda x: f"{x:.2f}%")
    st.dataframe(show, use_container_width=True, hide_index=True)
with t3:
    st.dataframe(customer.sort_values("Revenue", ascending=False).head(20),
                 use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    '<p class="note">Data note: the source is synthetic. Revenue and profit are populated for all '
    "order statuses, including Cancelled and Returned, so totals are not verified net sales. "
    "All charts and tables respond to the sidebar filters and the metric selector.</p>",
    unsafe_allow_html=True,
)
