import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/"src"))

import duckdb 
import streamlit as st

from hm_forecasting.dashboard import sales_velocity, dead_stock, geospatial_demand

st.set_page_config(page_title = "H&M Demand Forecasting Dashboad", layout = "wide")
st.title("H&M Retail Demand Forecasting Dashboard")

con = duckdb.connect("hm_retail.duckdb", read_only = True)

# Streamlit Dashboard for Sales Velocity
st.header("Sales Velocity")
st.caption("Weekly units sold, top 5 product groups by total volume")

velocity_df = sales_velocity(con)

top_groups = velocity_df.groupby("product_group_name")["units_sold"].sum().nlargest(5).index
chart_df = velocity_df[velocity_df["product_group_name"].isin(top_groups)]
chart_data = chart_df.pivot(index = "week_start", columns = "product_group_name", values = "units_sold")

st.line_chart(chart_data)


# Streamlit Dashboard for Inventory Turn Risk
st.header("Inventory Turn Risk")
st.caption("Products with no sales in the selected window")

threshold = st.slider("Days since last sale", min_value=0, max_value=180, value=30, step=10)

dead_stock_df = dead_stock(con)
at_risk = dead_stock_df[dead_stock_df["days_since_last_sale"] >= threshold]

st.write(f"{len(at_risk)} products with {threshold}+ days since last sale")
st.dataframe(at_risk)

# Streamlit Dashboard for Geospatial Demand
st.header("Geospatial Demand")
st.caption("Top 15 postal codes by units sold")

geo_df = geospatial_demand(con)
top_postal = geo_df.head(15).set_index("postal_code")

st.bar_chart(top_postal["units_sold"])
st.dataframe(geo_df)