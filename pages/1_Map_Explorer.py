"""
Expansion Intelligence Platform — Map Explorer
================================================
Interactive geographic analysis with state/city drill-down.
Adapts terminology to the active industry vertical.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import get_vertical, get_term
from db import load_table, load_geojson

st.set_page_config(page_title="Map Explorer", page_icon="🗺️", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]
loc = get_term(V, "location")
txn = get_term(V, "transactions")

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title("🗺️ Map Explorer")

# Load data
master = load_table("master_state")
city_orders = load_table("city_orders_summary")
city_clinic = load_table("city_clinic_summary")
geojson = load_geojson()

if master.empty:
    st.info("No data loaded. Go to **Upload & Refresh** to import data.")
    st.stop()

tab1, tab2 = st.tabs(["State View", "City Drill-Down"])

with tab1:
    st.subheader(f"State-Level {txn} Heatmap")
    metric = st.selectbox("Color by", ["total_orders", "total_revenue", "clinic_firsttime_qty"], format_func=lambda x: {"total_orders": f"Online {txn}", "total_revenue": "Revenue (₹)", "clinic_firsttime_qty": f"{loc} First-Time"}.get(x, x))

    if geojson:
        geo_map = {
            'Andaman & Nicobar Islands': 'Andaman and Nicobar',
            'Andaman and Nicobar Islands': 'Andaman and Nicobar',
            'JAMMU AND KASHMIR': 'Jammu and Kashmir',
            'Jammu & Kashmir': 'Jammu and Kashmir',
            'Dadra and Nagar Haveli and Daman and Diu': 'Dadra and Nagar Haveli',
        }
        plot_df = master.copy()
        plot_df['state_geo'] = plot_df['state'].map(lambda x: geo_map.get(x, x))

        fig = px.choropleth(plot_df, geojson=geojson, locations='state_geo',
                            featureidkey='properties.state', color=metric,
                            color_continuous_scale='YlOrRd', hover_name='state')
        fig.update_geos(fitbounds="locations", visible=False, bgcolor='rgba(0,0,0,0)')
        fig.update_layout(height=600, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback bar chart
        fig = px.bar(master.nlargest(20, metric), x='state', y=metric, color_discrete_sequence=[pri])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # State-level table
    st.subheader("State Data Table")
    display_cols = [c for c in ['state', 'total_orders', 'total_revenue', 'clinic_firsttime_qty', 'total_qty'] if c in master.columns]
    st.dataframe(master[display_cols].sort_values('total_orders', ascending=False) if 'total_orders' in master.columns else master, use_container_width=True, height=400)

with tab2:
    st.subheader(f"City-Level Analysis")

    # State filter
    if 'state' in master.columns:
        states = sorted(master['state'].dropna().unique())
        selected = st.multiselect("Filter by state", states, default=states[:3] if len(states) >= 3 else states)
    else:
        selected = []

    # City orders
    if not city_orders.empty:
        city_orders.columns = [c.lower() for c in city_orders.columns]
        if 'state' in city_orders.columns:
            filtered = city_orders[city_orders['state'].isin(selected)] if selected else city_orders
        else:
            filtered = city_orders
        if not filtered.empty:
            order_col = 'total_orders' if 'total_orders' in filtered.columns else filtered.select_dtypes('number').columns[0] if len(filtered.select_dtypes('number').columns) > 0 else None
            if order_col:
                top = filtered.nlargest(30, order_col)
                fig = px.bar(top, x='city' if 'city' in top.columns else top.columns[0], y=order_col,
                             color_discrete_sequence=[pri], text=order_col)
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig.update_layout(height=450, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(filtered, use_container_width=True, height=400)
        else:
            st.info("No city data for selected states.")
    else:
        st.info("Upload city-level data to enable drill-down.")
