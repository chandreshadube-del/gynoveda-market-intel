"""
Expansion Intelligence Platform — Main Dashboard
==================================================
Universal multi-industry expansion analytics platform.
Sidebar vertical selector switches between Healthcare, Fashion,
Real Estate, Mall Development, and F&B/QSR verticals.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

from config import (
    VERTICALS, get_vertical, get_term, get_modules,
    has_module, MODULE_REGISTRY, all_vertical_keys, vertical_selector_options
)
from db import load_table, load_geojson, get_db_status

# ── Page Config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Expansion Intelligence Platform",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session State Init ─────────────────────────────────────────────
if "vertical" not in st.session_state:
    st.session_state.vertical = "healthcare"
if "sub_vertical" not in st.session_state:
    st.session_state.sub_vertical = None

V = st.session_state.vertical
vc = get_vertical(V)

# ── Dynamic CSS (themed to selected vertical) ─────────────────────
pri = vc["color_primary"]
acc = vc["color_accent"]
st.markdown(f"""
<style>
    .main > div {{ padding-top: 1rem; }}
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {pri}11, {acc}11);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px 20px;
    }}
    [data-testid="stMetric"] label {{ font-size: 0.85rem; color: #555; }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{ font-size: 1.6rem; font-weight: 700; }}
    .block-container {{ max-width: 1200px; }}
    h1 {{ color: #2d3436; }}
    h2, h3 {{ color: #636e72; }}
    .vertical-badge {{
        display: inline-block;
        background: linear-gradient(135deg, {pri}, {acc});
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
    }}
</style>
""", unsafe_allow_html=True)


# ── Sidebar — Vertical Selector + Navigation ──────────────────────
with st.sidebar:
    # Platform branding
    st.markdown("### 🌐 Expansion Intelligence")
    st.caption("Multi-Industry Analytics Platform")
    st.divider()

    # ── Vertical Switcher ──
    st.markdown("**Industry Vertical**")
    options = vertical_selector_options()
    labels = [o["label"] for o in options]
    keys = [o["key"] for o in options]

    current_idx = keys.index(V) if V in keys else 0
    selected_label = st.selectbox(
        "Select vertical",
        labels,
        index=current_idx,
        label_visibility="collapsed"
    )
    selected_key = keys[labels.index(selected_label)]

    if selected_key != V:
        st.session_state.vertical = selected_key
        st.rerun()

    # Sub-vertical (company selector within vertical)
    subs = vc.get("sub_verticals", [])
    if subs:
        sub = st.selectbox("Company / Brand", subs, label_visibility="collapsed")
        st.session_state.sub_vertical = sub

    st.caption(f"*{vc['tagline']}*")
    st.divider()

    # ── Navigation — only show modules enabled for this vertical ──
    st.markdown("**Navigation**")
    modules = get_modules(V)
    for mod_key in modules:
        mod = MODULE_REGISTRY.get(mod_key)
        if mod:
            try:
                st.page_link(mod["page"], label=f"{mod['icon']}  {mod['label']}")
            except Exception:
                st.caption(f"  {mod['icon']}  {mod['label']} *(not found)*")

    st.divider()
    # DB Status
    db_status = get_db_status()
    st.caption(f"{db_status['icon']} {db_status['mode']}")


# ── Load Data ──────────────────────────────────────────────────────
TABLES = [
    "master_state", "state_orders_summary", "state_clinic_summary",
    "city_orders_summary", "city_clinic_summary",
    "year_trend", "year_state_orders", "product_state",
    "clinic_performance", "clinic_zip_summary", "clinic_monthly_trend",
    "pincode_clinic"
]
data = {name: load_table(name) for name in TABLES}
geojson = load_geojson()
master = data.get("master_state", pd.DataFrame())


# ── Dashboard Header ──────────────────────────────────────────────
st.markdown(f'<span class="vertical-badge">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)

sub_label = f" — {st.session_state.sub_vertical}" if st.session_state.sub_vertical else ""
st.title(f"Expansion Intelligence Dashboard{sub_label}")
st.markdown(f"Unified view of **demand signals**, **{get_term(V, 'location').lower()} performance**, and **expansion opportunities**.")


# ── KPI Row ────────────────────────────────────────────────────────
if master.empty:
    st.info(f"No data loaded for {vc['name']}. Go to **Upload & Refresh** to import your data.")
    st.stop()

kpi_defs = vc["kpi_cards"]
cols = st.columns(len(kpi_defs))

for col, kpi in zip(cols, kpi_defs):
    with col:
        key = kpi["key"]
        if key == "states_covered":
            val = master[master['total_orders'] > 0]['state'].nunique() if 'total_orders' in master.columns else 0
        elif key == "cities_covered":
            city_df = data.get("city_orders_summary", pd.DataFrame())
            val = city_df['city'].nunique() if 'city' in city_df.columns and not city_df.empty else 0
        elif key in master.columns:
            val = master[key].sum()
        else:
            val = 0

        divisor = kpi.get("divisor", 1)
        fmt = kpi["fmt"]
        try:
            display_val = fmt.format(val / divisor)
        except Exception:
            display_val = f"{val:,.0f}"
        st.metric(kpi["label"], display_val)

st.divider()


# ── National Trends ────────────────────────────────────────────────
col_chart, col_table = st.columns([1.5, 1])

with col_chart:
    st.subheader(f"📈 {get_term(V, 'transactions')} — Year-over-Year Trend")
    year_trend = data.get("year_trend", pd.DataFrame())
    if not year_trend.empty and "total_orders" in year_trend.columns:
        fig = px.bar(
            year_trend, x='Year', y='total_orders',
            text='total_orders',
            color_discrete_sequence=[pri]
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(
            xaxis_title="", yaxis_title=get_term(V, "transactions"),
            height=350, margin=dict(t=10, b=30), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload transaction data to see year-over-year trends.")

with col_table:
    top_label = get_term(V, "transactions")
    st.subheader(f"🏆 Top 10 States by {top_label}")
    if 'total_orders' in master.columns:
        top10 = master.nlargest(10, 'total_orders')[['state', 'total_orders', 'total_revenue']].copy()
        top10['total_revenue'] = top10['total_revenue'].apply(lambda x: f"₹{x/1e7:.1f} Cr" if pd.notna(x) else "—")
        top10['total_orders'] = top10['total_orders'].apply(lambda x: f"{x:,.0f}")
        top10.columns = ['State', top_label, 'Revenue']
        top10.index = range(1, len(top10)+1)
        st.dataframe(top10, use_container_width=True, height=350)
    else:
        st.info("No state-level data available.")


# ── State Heatmap ──────────────────────────────────────────────────
st.divider()
st.subheader(f"🗺️ Demand Heatmap — {get_term(V, 'transactions')} by State")

if geojson and not master.empty and 'total_orders' in master.columns:
    geo_name_map = {
        'Andaman & Nicobar Islands': 'Andaman and Nicobar',
        'Andaman and Nicobar Islands': 'Andaman and Nicobar',
        'JAMMU AND KASHMIR': 'Jammu and Kashmir',
        'Jammu & Kashmir': 'Jammu and Kashmir',
        'Dadra and Nagar Haveli and Daman and Diu': 'Dadra and Nagar Haveli',
    }
    plot_df = master.copy()
    plot_df['state_geo'] = plot_df['state'].map(lambda x: geo_name_map.get(x, x))

    fig_map = px.choropleth(
        plot_df,
        geojson=geojson,
        locations='state_geo',
        featureidkey='properties.state',
        color='total_orders',
        color_continuous_scale='YlOrRd',
        hover_name='state',
        hover_data={'total_orders': ':,.0f', 'total_revenue': ':,.0f', 'state_geo': False},
        labels={'total_orders': get_term(V, 'transactions'), 'total_revenue': 'Revenue (₹)'}
    )
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor='rgba(0,0,0,0)')
    fig_map.update_layout(height=550, margin=dict(t=0, b=0, l=0, r=0), coloraxis_colorbar_title=get_term(V, 'transactions'))
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Map data not available. Upload GeoJSON or transaction data to enable heatmaps.")


# ── Demand vs Location Correlation ─────────────────────────────────
st.divider()
loc_term = get_term(V, "location")
cust_term = get_term(V, "customers")
st.subheader(f"🔗 Online Demand vs {loc_term} Revenue — State Correlation")

if 'total_orders' in master.columns and 'clinic_firsttime_qty' in master.columns:
    corr_df = master.dropna(subset=['total_orders', 'clinic_firsttime_qty'])
    corr_df = corr_df[corr_df['total_orders'] > 100]
    if not corr_df.empty:
        fig_scatter = px.scatter(
            corr_df, x='total_orders', y='clinic_firsttime_qty',
            size='total_revenue', hover_name='state',
            color='total_revenue', color_continuous_scale='Viridis',
            labels={
                'total_orders': f'Online {get_term(V, "transactions")}',
                'clinic_firsttime_qty': f'{loc_term} First-Time {cust_term}',
                'total_revenue': 'Online Revenue (₹)'
            }
        )
        fig_scatter.update_layout(height=450, margin=dict(t=10))
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption(f"Bubble size = online revenue. States in the top-right quadrant show strong alignment between digital demand and {loc_term.lower()} traction.")
    else:
        st.info(f"Not enough data for correlation analysis. Upload both online and {loc_term.lower()} data.")
else:
    st.info(f"Upload {loc_term.lower()} performance data alongside online demand data to see correlation insights.")
