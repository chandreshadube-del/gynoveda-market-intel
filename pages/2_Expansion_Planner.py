"""
Expansion Intelligence Platform - Expansion Intelligence
==========================================================
Flagship expansion analysis page. Universal modules include:
  - Expansion Opportunity Finder (CEI-based)
  - Gap Market Analysis
  - Catchment Overlap Detection
Healthcare vertical additionally shows IVF Market Analysis tab.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import get_vertical, get_term, get_scoring, has_module
from db import load_table

st.set_page_config(page_title="Expansion Intelligence", page_icon="🚀", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]
acc = vc["color_accent"]
loc = get_term(V, "location")
locs = get_term(V, "locations")
txn = get_term(V, "transactions")
dims = get_scoring(V)

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{acc});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title(f"🚀 Expansion Intelligence")
st.markdown(f"Data-driven expansion planning for **{vc['name']}** - identify where to open next.")

# == Load Data ======================================================
master = load_table("master_state")
city_orders = load_table("city_orders_summary")
city_clinic = load_table("city_clinic_summary")
pincode_clinic = load_table("pincode_clinic")
nfhs = load_table("nfhs5_state")

# == Build Tabs (conditional on vertical) ===========================
tab_labels = ["🎯 Opportunity Finder", "📊 Gap Markets", "🗺️ Expansion Files"]
if V == "healthcare":
    tab_labels.insert(0, "🧬 IVF Market Analysis")

tabs = st.tabs(tab_labels)
tab_idx = 0

# ==================================================================
# IVF MARKET ANALYSIS TAB (Healthcare only)
# ==================================================================
if V == "healthcare":
    with tabs[tab_idx]:
        st.subheader("🧬 IVF & Fertility Market - National Overview")

        # Market KPIs
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Market Size (2024)", "$1.0–1.7B", delta="22% CAGR")
        with c2:
            st.metric("Infertile Couples", "27.5M", delta="Growing")
        with c3:
            st.metric("IVF Penetration", "<1%", delta="Massive gap")
        with c4:
            st.metric("IVF Clinics (est.)", "2,500+", delta="Fragmented")

        st.divider()

        # Cost Segments
        st.subheader("💰 IVF Cost Landscape - Segment Map")
        cost_data = pd.DataFrame({
            "Segment": ["Ultra-Affordable", "Budget", "Mid-Range", "Premium", "Ultra-Premium"],
            "Cost Range (₹ Lakhs)": ["0.8–1.5", "1.5–2.5", "2.5–4.0", "4.0–6.0", "6.0–10.0+"],
            "Target Audience": ["Tier-3/4 towns, low-income", "Tier-2/3 cities, middle class",
                                "Metro middle class", "Metro upper-middle", "HNI / Medical tourism"],
            "Key Players": ["Govt hospitals, NGO clinics", "Indira IVF, Crysta",
                            "Nova, Cloudnine", "Manipal, Max, Fortis", "Bloom, Milann premium"],
            "Market Share": ["5%", "30%", "35%", "20%", "10%"]
        })
        st.dataframe(cost_data, use_container_width=True, hide_index=True)

        # Major Chains
        st.subheader("🏢 Competitive Landscape - Major IVF Chains")
        chains = pd.DataFrame({
            "Chain": ["Indira IVF", "Nova IVF", "Birla Fertility", "Crysta IVF",
                      "Cloudnine", "Milann", "Bloom IVF"],
            "Centres": [130, 78, 45, 40, 35, 10, 8],
            "States": [18, 15, 12, 10, 8, 4, 3],
            "Segment": ["Budget", "Mid-Premium", "Premium", "Budget-Mid",
                         "Premium", "Premium", "Premium"],
            "Backed By": ["Self-funded", "PE-backed (Munjal)", "CK Birla Group",
                          "PE-backed", "PE-backed", "HCG Group", "Self-funded"],
            "Strength": ["Scale & reach", "Clinical outcomes", "Brand trust",
                         "Affordable pricing", "Maternity + IVF bundle",
                         "Bangalore legacy", "Niche premium"]
        })

        fig_chains = px.bar(chains.sort_values("Centres", ascending=True),
                            x="Centres", y="Chain", orientation='h',
                            color="Segment", text="Centres",
                            color_discrete_map={"Budget": "#00b894", "Mid-Premium": "#0984e3",
                                                "Premium": "#6c5ce7", "Budget-Mid": "#00cec9"})
        fig_chains.update_layout(height=350, yaxis_title="", xaxis_title="Number of Centres")
        st.plotly_chart(fig_chains, use_container_width=True)

        # NFHS-5 Health Indicators (if data available)
        if not nfhs.empty:
            st.divider()
            st.subheader("🏥 NFHS-5 Health Indicators by State")
            num_cols = nfhs.select_dtypes('number').columns.tolist()
            state_col = 'state' if 'state' in nfhs.columns else nfhs.columns[0]
            if num_cols:
                selected_metric = st.selectbox("Select indicator", num_cols)
                fig_nfhs = px.bar(nfhs.nlargest(20, selected_metric),
                                  x=state_col, y=selected_metric,
                                  color_discrete_sequence=[pri])
                fig_nfhs.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_nfhs, use_container_width=True)

        # Gap Markets
        st.divider()
        st.subheader("🎯 IVF Gap Markets - Top 25 Underserved Districts")
        gap_markets = pd.DataFrame({
            "Rank": range(1, 26),
            "State": ["Maharashtra"]*5 + ["Uttar Pradesh"]*4 + ["Karnataka"]*4 +
                     ["Tamil Nadu"]*4 + ["Andhra Pradesh"]*4 + ["Telangana"]*4,
            "District": ["Nagpur", "Nashik", "Aurangabad", "Kolhapur", "Solapur",
                         "Lucknow", "Kanpur", "Agra", "Varanasi",
                         "Mysuru", "Hubli-Dharwad", "Mangaluru", "Belgaum",
                         "Coimbatore", "Madurai", "Salem", "Tirunelveli",
                         "Visakhapatnam", "Vijayawada", "Guntur", "Tirupati",
                         "Warangal", "Karimnagar", "Nizamabad", "Khammam"],
            "Population (L)": [50, 62, 37, 39, 44, 35, 28, 18, 37,
                               10, 9, 6, 5, 16, 15, 8, 5,
                               18, 11, 8, 5, 8, 6, 5, 3],
            "IVF Centres": [3, 1, 2, 1, 0, 5, 2, 1, 2,
                            3, 1, 1, 0, 4, 2, 0, 0,
                            3, 2, 0, 1, 0, 0, 0, 0],
            "Gap Score": [0.92, 0.95, 0.88, 0.91, 0.97,
                          0.78, 0.89, 0.93, 0.85,
                          0.82, 0.94, 0.90, 0.96,
                          0.75, 0.84, 0.96, 0.97,
                          0.80, 0.86, 0.95, 0.90,
                          0.97, 0.98, 0.98, 0.99]
        })

        state_filter = st.multiselect("Filter by state", gap_markets['State'].unique().tolist(),
                                       default=gap_markets['State'].unique().tolist())
        filtered_gaps = gap_markets[gap_markets['State'].isin(state_filter)]
        st.dataframe(filtered_gaps, use_container_width=True, hide_index=True)

    tab_idx += 1


# ==================================================================
# OPPORTUNITY FINDER TAB (Universal)
# ==================================================================
with tabs[tab_idx]:
    st.subheader(f"🎯 {loc} Expansion Opportunity Finder")
    st.markdown(f"CEI-ranked list of states/cities with the highest expansion potential for **{vc['name']}**.")

    if master.empty or 'total_orders' not in master.columns:
        st.info("Upload demand data to enable the opportunity finder.")
    else:
        # Quick CEI computation
        opp = master[['state']].copy()
        opp['demand_score'] = master['total_orders'].rank(pct=True)
        opp['revenue_score'] = master['total_revenue'].rank(pct=True) if 'total_revenue' in master.columns else 0.5

        if 'clinic_firsttime_qty' in master.columns:
            ratio = master['clinic_firsttime_qty'] / master['total_orders'].replace(0, 1)
            opp['gap_score'] = 1 - ratio.rank(pct=True)
        else:
            opp['gap_score'] = 0.5

        opp['opportunity_score'] = opp['demand_score'] * 0.4 + opp['gap_score'] * 0.35 + opp['revenue_score'] * 0.25
        opp = opp.sort_values('opportunity_score', ascending=False)

        # Tier classification
        opp['Tier'] = pd.cut(opp['opportunity_score'], bins=[0, 0.4, 0.7, 1.0],
                             labels=['Tier 3: Watch', 'Tier 2: Emerging', 'Tier 1: Priority'])

        # Visualization
        fig = px.bar(opp.head(20), x='state', y='opportunity_score',
                     color='Tier', text=opp.head(20)['opportunity_score'].apply(lambda x: f"{x:.2f}"),
                     color_discrete_map={'Tier 1: Priority': '#27ae60', 'Tier 2: Emerging': '#f39c12', 'Tier 3: Watch': '#95a5a6'})
        fig.update_traces(textposition='outside')
        fig.update_layout(height=450, xaxis_tickangle=-45, xaxis_title="", yaxis_title="Opportunity Score")
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        display_opp = opp.copy()
        for c in ['demand_score', 'gap_score', 'revenue_score', 'opportunity_score']:
            display_opp[c] = display_opp[c].apply(lambda x: f"{x:.3f}")
        st.dataframe(display_opp, use_container_width=True, height=500, hide_index=True)

tab_idx += 1


# ==================================================================
# GAP MARKETS TAB (Universal)
# ==================================================================
with tabs[tab_idx]:
    st.subheader(f"📊 Gap Market Analysis")
    st.markdown(f"Cities/areas with high online demand but low {loc.lower()} presence - untapped expansion targets.")

    if not city_orders.empty and not city_clinic.empty:
        city_orders.columns = [c.lower() for c in city_orders.columns]
        city_clinic.columns = [c.lower() for c in city_clinic.columns]
        city_col_o = 'city' if 'city' in city_orders.columns else city_orders.columns[0]
        city_col_c = 'city' if 'city' in city_clinic.columns else city_clinic.columns[0]
        order_col = next((c for c in city_orders.columns if any(k in c.lower() for k in ['order', 'qty', 'quantity', 'demand', 'count'])), None)
        clinic_col = next((c for c in city_clinic.columns if any(k in c.lower() for k in ['qty', 'quantity', 'firsttime', 'first_time', 'total', 'count'])), None)

        # Fallback: use first numeric column
        if not order_col:
            num_cols = city_orders.select_dtypes('number').columns.tolist()
            order_col = num_cols[0] if num_cols else None
        if not clinic_col:
            num_cols = city_clinic.select_dtypes('number').columns.tolist()
            clinic_col = num_cols[0] if num_cols else None

        if order_col and clinic_col:
            orders_agg = city_orders.groupby(city_col_o)[order_col].sum().reset_index()
            clinic_agg = city_clinic.groupby(city_col_c)[clinic_col].sum().reset_index()

            merged = orders_agg.merge(clinic_agg, left_on=city_col_o, right_on=city_col_c, how='left')
            merged[clinic_col] = merged[clinic_col].fillna(0)
            merged['gap_ratio'] = merged[order_col] / (merged[clinic_col] + 1)
            merged = merged.sort_values('gap_ratio', ascending=False)

            st.markdown(f"**Top 20 Gap Markets** - High online {txn.lower()}, low {loc.lower()} coverage:")
            top_gaps = merged.head(20)
            fig = px.scatter(top_gaps, x=order_col, y=clinic_col, size='gap_ratio',
                             hover_name=city_col_o, color='gap_ratio',
                             color_continuous_scale='RdYlGn_r',
                             labels={order_col: f'Online {txn}', clinic_col: f'{loc} Volume',
                                     'gap_ratio': 'Gap Ratio'})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(merged.head(30), use_container_width=True, height=400, hide_index=True)
        else:
            st.info("Column mismatch. Ensure order and location datasets share a city column.")
    elif not master.empty:
        st.markdown("City-level data not available. Showing state-level gap analysis.")
        if 'total_orders' in master.columns and 'clinic_firsttime_qty' in master.columns:
            gap_df = master[['state', 'total_orders', 'clinic_firsttime_qty']].copy()
            gap_df['clinic_firsttime_qty'] = gap_df['clinic_firsttime_qty'].fillna(0)
            gap_df['gap_ratio'] = gap_df['total_orders'] / (gap_df['clinic_firsttime_qty'] + 1)
            gap_df = gap_df.sort_values('gap_ratio', ascending=False)
            st.dataframe(gap_df, use_container_width=True, height=400, hide_index=True)
    else:
        st.info("Upload both demand and location data to compute gap markets.")

tab_idx += 1


# ==================================================================
# EXPANSION FILES TAB (Universal - upload viewer)
# ==================================================================
with tabs[tab_idx]:
    st.subheader("🗺️ Uploaded Expansion Files")
    st.markdown("View previously uploaded expansion analysis files.")

    exp_scores = load_table("expansion_scores")
    comp_map = load_table("competition_map")

    if not exp_scores.empty:
        st.markdown("**Expansion Scores Data:**")
        st.dataframe(exp_scores, use_container_width=True, height=300, hide_index=True)

    if not comp_map.empty:
        st.markdown("**Competition Mapping Data:**")
        st.dataframe(comp_map, use_container_width=True, height=300, hide_index=True)

    if exp_scores.empty and comp_map.empty:
        st.info("No expansion files uploaded yet. Use the **Upload & Refresh** page to import expansion data.")
