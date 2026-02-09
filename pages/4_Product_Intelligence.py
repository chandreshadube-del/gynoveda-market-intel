"""
Expansion Intelligence Platform — Product / Category Intelligence
===================================================================
Product mix, category performance, and demand-pattern analytics.
Adapts terminology: Products (healthcare) → Categories (fashion) → Menu (F&B).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import get_vertical, get_term
from db import load_table

st.set_page_config(page_title="Product Intelligence", page_icon="📦", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]
prod = get_term(V, "product")
prods = get_term(V, "products")

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title(f"📦 {prod} Intelligence")
st.markdown(f"Analyze {prods.lower()} mix, demand patterns, and geographic distribution.")

product_state = load_table("product_state")

if product_state.empty:
    st.info(f"No {prod.lower()} data loaded. Go to **Upload & Refresh** to import {prod.lower()} data.")
    st.stop()

# Detect columns
cat_col = next((c for c in ['product_category', 'category', 'product', 'item'] if c in product_state.columns), product_state.columns[0])
state_col = 'state' if 'state' in product_state.columns else None
qty_col = next((c for c in ['total_orders', 'quantity', 'order_qty', 'total_qty'] if c in product_state.columns), None)
rev_col = next((c for c in ['total_revenue', 'revenue', 'amount'] if c in product_state.columns), None)

# KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(f"Unique {prods}", f"{product_state[cat_col].nunique():,}")
with col2:
    if qty_col:
        st.metric(f"Total {get_term(V, 'transactions')}", f"{product_state[qty_col].sum():,.0f}")
with col3:
    if rev_col:
        st.metric("Total Revenue", f"₹{product_state[rev_col].sum()/1e7:.1f} Cr")

st.divider()

tab1, tab2 = st.tabs([f"{prod} Rankings", f"State × {prod} Heatmap"])

with tab1:
    if qty_col:
        prod_totals = product_state.groupby(cat_col)[qty_col].sum().reset_index().sort_values(qty_col, ascending=False)
        fig = px.bar(prod_totals.head(20), x=cat_col, y=qty_col, color_discrete_sequence=[pri],
                     text=qty_col)
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(height=450, xaxis_tickangle=-45, xaxis_title="", yaxis_title=f"Total {get_term(V, 'transactions')}")
        st.plotly_chart(fig, use_container_width=True)

    # Pie chart
    if qty_col:
        top10 = prod_totals.head(10).copy()
        fig_pie = px.pie(top10, values=qty_col, names=cat_col, color_discrete_sequence=px.colors.qualitative.Set3)
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    if state_col and qty_col:
        pivot = product_state.pivot_table(index=state_col, columns=cat_col, values=qty_col, aggfunc='sum').fillna(0)
        top_cats = product_state.groupby(cat_col)[qty_col].sum().nlargest(10).index.tolist()
        pivot_top = pivot[top_cats] if all(c in pivot.columns for c in top_cats) else pivot.iloc[:, :10]

        fig_heat = px.imshow(pivot_top, text_auto=True, aspect='auto',
                             color_continuous_scale='YlOrRd',
                             labels=dict(x=prod, y="State", color=get_term(V, 'transactions')))
        fig_heat.update_layout(height=600)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info(f"Upload state-level {prod.lower()} data to see the heatmap.")

# Full data table
st.divider()
st.subheader("📊 Full Data Table")
st.dataframe(product_state, use_container_width=True, height=400, hide_index=True)
