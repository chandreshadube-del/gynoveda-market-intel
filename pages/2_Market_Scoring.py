"""
Expansion Intelligence Platform - Market Scoring (CEI)
=======================================================
Composite Expansion Index with dimensions that adapt per vertical.
Now supports district-level scoring from Census + NFHS-5 + HCES data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import get_vertical, get_term, get_scoring
from db import load_table

st.set_page_config(page_title="Market Scoring", page_icon="📊", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]
dims = get_scoring(V)

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title("📊 Composite Expansion Index (CEI)")
st.markdown(f"Multi-dimensional scoring to identify the best expansion markets for **{vc['name']}**.")

# == Load all data sources ==========================================
master = load_table("master_state")
city_orders = load_table("city_orders_summary")
city_clinic = load_table("city_clinic_summary")

# New: district-level data
cei_district = load_table("cei_district_scores")
census_demo = load_table("census_district_demographics")
census_hh = load_table("census_hh_assets")
state_health = load_table("state_health_spending")

has_district_data = not cei_district.empty and "Overall_CEI_Score" in cei_district.columns
has_census_data = not census_demo.empty
has_state_only = not master.empty and not has_district_data

# == Data Source Indicator ==========================================
if has_district_data:
    st.success(f"🎯 **District-level CEI active** - {len(cei_district):,} districts scored from Census 2011 + NFHS-5 + HCES data")
    analysis_level = st.radio("Analysis Level:", ["District (640)", "State (Aggregated)"], horizontal=True, key="level")
elif has_census_data:
    st.info(f"📋 Census demographics loaded ({len(census_demo):,} districts) but CEI scores not yet uploaded. Upload via Section 8 on Upload & Refresh page.")
    analysis_level = "State (Aggregated)"
elif has_state_only:
    st.warning("📊 State-level data only. Upload Census/CEI district data for granular scoring.")
    analysis_level = "State (Aggregated)"
else:
    st.info("No data loaded. Upload state/city data or Census/CEI data to enable scoring.")
    st.stop()


# ==================================================================
# DIMENSION CONFIGURATION
# ==================================================================
st.subheader("⚙️ Scoring Dimensions & Weights")

with st.expander("Customize Dimension Weights", expanded=False):
    st.caption("Adjust the relative importance of each expansion dimension. Weights will be normalized to sum to 100%.")
    custom_weights = {}
    cols_w = st.columns(min(len(dims), 4))
    for i, (dk, dv) in enumerate(dims.items()):
        with cols_w[i % len(cols_w)]:
            custom_weights[dk] = st.slider(
                f"{dk}: {dv['name']}",
                min_value=0.0, max_value=0.50, value=dv['weight'],
                step=0.05, key=f"w_{dk}"
            )
    total_w = sum(custom_weights.values())
    if total_w > 0:
        custom_weights = {k: v / total_w for k, v in custom_weights.items()}


# ==================================================================
# DIMENSION DATA STATUS
# ==================================================================
st.subheader("📋 Dimension Data Status")

dim_status = []
for dk, dv in dims.items():
    if has_district_data:
        col_map = {
            "D1": "Spending_Index", "D2": "Health_Need_Index", "D3": "Infrastructure_Index",
            "D4": "Infrastructure_Index", "D5": "Spending_Index", "D6": "Digital_Index", "D7": "Digital_Index"
        }
        has_data = col_map.get(dk, "") in cei_district.columns
    else:
        if dk == "D1":
            has_data = not master.empty and 'total_orders' in master.columns
        elif dk == "D2" and V == "healthcare":
            nfhs = load_table("nfhs5_state")
            has_data = not nfhs.empty or not state_health.empty
        elif dk == "D3":
            has_data = not city_clinic.empty or not master.empty
        elif dk == "D4":
            infra = load_table("infra_city")
            has_data = not infra.empty or not census_hh.empty
        elif dk == "D5":
            has_data = not master.empty
        elif dk == "D6":
            has_data = not census_hh.empty
        else:
            has_data = False

    source = "Census/NFHS/HCES" if has_district_data and has_data else ("Uploaded Data" if has_data else "-")
    dim_status.append({
        "Dimension": dk,
        "Name": dv["name"],
        "Weight": f"{custom_weights.get(dk, dv['weight'])*100:.0f}%",
        "Data Status": "✅ Active" if has_data else "⏳ Placeholder",
        "Source": source,
        "Level": "District" if has_district_data and has_data else ("State" if has_data else "-")
    })

st.dataframe(pd.DataFrame(dim_status), use_container_width=True, hide_index=True)


# ==================================================================
# DISTRICT-LEVEL CEI SCORING (when uploaded)
# ==================================================================
if has_district_data and analysis_level == "District (640)":
    st.divider()
    st.subheader("🏆 CEI Rankings - District Level")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        states = sorted(cei_district['State'].dropna().unique().tolist())
        sel_states = st.multiselect("Filter by State:", states, default=[], key="state_filter")
    with col_f2:
        if 'District_Tier' in cei_district.columns:
            tiers = sorted(cei_district['District_Tier'].dropna().unique().tolist())
            sel_tiers = st.multiselect("Filter by Tier:", tiers, default=[], key="tier_filter")
        else:
            sel_tiers = []
    with col_f3:
        top_n = st.slider("Show top N districts:", 10, 100, 30, key="top_n")

    # Apply filters
    filtered = cei_district.copy()
    if sel_states:
        filtered = filtered[filtered['State'].isin(sel_states)]
    if sel_tiers and 'District_Tier' in filtered.columns:
        filtered = filtered[filtered['District_Tier'].isin(sel_tiers)]

    filtered = filtered.sort_values('Overall_CEI_Score', ascending=False)

    # KPI row
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Districts Scored", f"{len(filtered):,}")
    with col_k2:
        st.metric("States Covered", f"{filtered['State'].nunique()}")
    with col_k3:
        st.metric("Avg CEI Score", f"{filtered['Overall_CEI_Score'].mean():.2f}")
    with col_k4:
        if 'Population' in filtered.columns:
            st.metric("Total Population", f"{filtered['Population'].sum()/1e7:.1f} Cr")

    # Top N bar chart
    top = filtered.head(top_n)
    fig = px.bar(
        top, x='District', y='Overall_CEI_Score',
        color='Overall_CEI_Score',
        color_continuous_scale='RdYlGn',
        hover_data=['State', 'Population'] if 'Population' in top.columns else ['State'],
        text=top['Overall_CEI_Score'].apply(lambda x: f"{x:.1f}")
    )
    fig.update_traces(textposition='outside', textfont_size=9)
    fig.update_layout(
        height=500, xaxis_tickangle=-60, xaxis_title="",
        yaxis_title="CEI Score", coloraxis_showscale=False,
        margin=dict(b=120)
    )
    st.plotly_chart(fig, use_container_width=True)

    # == Radar chart for top 5 ==
    st.subheader("🕸️ Dimension Breakdown - Top 5 Districts")

    dim_col_map = {}
    for dk, dv in dims.items():
        name_lower = dv["name"].lower()
        if "demand" in name_lower or "spend" in name_lower:
            dim_col_map[dk] = "Spending_Index"
        elif "health" in name_lower:
            dim_col_map[dk] = "Health_Need_Index"
        elif "compet" in name_lower or "infra" in name_lower:
            dim_col_map[dk] = "Infrastructure_Index"
        elif "digital" in name_lower:
            dim_col_map[dk] = "Digital_Index"
        elif "demographic" in name_lower:
            dim_col_map[dk] = "Spending_Index"
        elif "retail" in name_lower or "footfall" in name_lower:
            dim_col_map[dk] = "Digital_Index"
        else:
            dim_col_map[dk] = "Overall_CEI_Score"

    available_dims = {dk: col for dk, col in dim_col_map.items() if col in filtered.columns}
    top5 = filtered.head(5)

    if available_dims:
        fig_radar = go.Figure()
        for _, row in top5.iterrows():
            r_values = []
            for dk, col in available_dims.items():
                val = row.get(col, 0)
                col_max = filtered[col].max()
                col_min = filtered[col].min()
                if col_max > col_min:
                    r_values.append((val - col_min) / (col_max - col_min))
                else:
                    r_values.append(0.5)

            fig_radar.add_trace(go.Scatterpolar(
                r=r_values,
                theta=[dims[dk]["name"] for dk in available_dims.keys()],
                fill='toself',
                name=f"{row['District']} ({row['State'][:3]})"
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=500, showlegend=True
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # == State-aggregated heatmap ==
    st.subheader("🗺️ State-Level CEI Heatmap")

    agg_dict = {
        'Overall_CEI_Score': ['mean', 'max'],
        'District': 'count',
    }
    if 'Population' in filtered.columns:
        agg_dict['Population'] = 'sum'

    state_agg = filtered.groupby('State').agg(**{
        'Avg_CEI': ('Overall_CEI_Score', 'mean'),
        'Max_CEI': ('Overall_CEI_Score', 'max'),
        'Districts': ('District', 'count'),
        **({'Total_Pop': ('Population', 'sum')} if 'Population' in filtered.columns else {})
    }).reset_index().sort_values('Avg_CEI', ascending=False)

    fig_hm = px.bar(
        state_agg.head(20), x='State', y='Avg_CEI',
        color='Avg_CEI', color_continuous_scale='Viridis',
        hover_data=['Districts'],
        text=state_agg.head(20)['Avg_CEI'].apply(lambda x: f"{x:.1f}")
    )
    fig_hm.update_traces(textposition='outside')
    fig_hm.update_layout(height=400, xaxis_tickangle=-45, coloraxis_showscale=False)
    st.plotly_chart(fig_hm, use_container_width=True)

    # == Full table ==
    st.subheader("📊 Full District Rankings")
    display_cols = ['State', 'District']
    for c in ['Population', 'District_Tier', 'Spending_Index', 'Infrastructure_Index',
              'Health_Need_Index', 'Digital_Index', 'Overall_CEI_Score',
              'Literacy_Rate', 'Urbanization_Proxy_Pct', 'Non_Agri_Worker_Pct',
              'HH_Mobile_Pct', 'HH_Banking_Pct']:
        if c in filtered.columns:
            display_cols.append(c)

    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True, height=500, hide_index=True,
        column_config={
            "Population": st.column_config.NumberColumn(format="%d"),
            "Overall_CEI_Score": st.column_config.NumberColumn(format="%.2f"),
            "Spending_Index": st.column_config.NumberColumn(format="%.2f"),
            "Infrastructure_Index": st.column_config.NumberColumn(format="%.2f"),
            "Health_Need_Index": st.column_config.NumberColumn(format="%.2f"),
            "Digital_Index": st.column_config.NumberColumn(format="%.2f"),
        }
    )

    csv_data = filtered[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CEI Rankings (CSV)", csv_data, "cei_district_rankings.csv", "text/csv")


# ==================================================================
# STATE-LEVEL SCORING (original behavior + census enrichment)
# ==================================================================
if (has_state_only and analysis_level == "State (Aggregated)") or \
   (has_district_data and analysis_level == "State (Aggregated)"):

    st.divider()
    st.subheader("🏆 CEI Rankings - State Level")

    if has_district_data:
        score_df = cei_district.groupby('State').agg(**{
            'CEI': ('Overall_CEI_Score', 'mean'),
            'Max_CEI': ('Overall_CEI_Score', 'max'),
            'Districts': ('District', 'count'),
            **({
                'Avg_Spending': ('Spending_Index', 'mean'),
                'Avg_Infra': ('Infrastructure_Index', 'mean'),
                'Avg_Health': ('Health_Need_Index', 'mean'),
                'Avg_Digital': ('Digital_Index', 'mean'),
            } if 'Spending_Index' in cei_district.columns else {})
        }).reset_index().sort_values('CEI', ascending=False)

        score_df.rename(columns={'State': 'state'}, inplace=True)

        if 'Avg_Spending' in score_df.columns:
            score_df['D1'] = score_df['Avg_Spending'].rank(pct=True)
            score_df['D2'] = score_df['Avg_Health'].rank(pct=True)
            score_df['D3'] = 1 - score_df['Avg_Infra'].rank(pct=True)
            score_df['D4'] = score_df['Avg_Infra'].rank(pct=True)
            score_df['D5'] = score_df['Avg_Spending'].rank(pct=True)
            score_df['D6'] = score_df['Avg_Digital'].rank(pct=True)
            score_df['D7'] = score_df['Avg_Digital'].rank(pct=True)

    elif has_state_only and 'total_orders' in master.columns:
        score_df = master[['state']].copy()
        score_df['D1'] = master['total_orders'].rank(pct=True) if 'total_orders' in master.columns else 0.5

        if 'clinic_firsttime_qty' in master.columns and 'total_orders' in master.columns:
            ratio = master['clinic_firsttime_qty'] / master['total_orders'].replace(0, 1)
            score_df['D3'] = 1 - ratio.rank(pct=True)
        else:
            score_df['D3'] = 0.5

        score_df['D5'] = master['total_revenue'].rank(pct=True) if 'total_revenue' in master.columns else 0.5

        for d in ['D2', 'D4', 'D6', 'D7']:
            if d not in score_df.columns:
                score_df[d] = 0.5

        score_df['CEI'] = sum(
            score_df.get(dk, pd.Series(0.5, index=score_df.index)) * custom_weights.get(dk, dv['weight'])
            for dk, dv in dims.items()
        )
        score_df = score_df.sort_values('CEI', ascending=False)
    else:
        st.info("Upload demand data to compute CEI scores.")
        st.stop()

    # Top states bar chart
    top15 = score_df.head(15)
    fig = px.bar(top15, x='state', y='CEI', color='CEI',
                 color_continuous_scale='RdYlGn',
                 text=top15['CEI'].apply(lambda x: f"{x:.2f}"))
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400, xaxis_tickangle=-45, xaxis_title="", yaxis_title="CEI Score",
                      coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Radar chart for top 5
    st.subheader("🕸️ Dimension Breakdown - Top 5 States")
    top5 = score_df.head(5)
    dim_cols = [dk for dk in dims.keys() if dk in score_df.columns]

    fig_radar = go.Figure()
    for _, row in top5.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row.get(d, 0.5) for d in dim_cols],
            theta=[dims[d]["name"] for d in dim_cols],
            fill='toself',
            name=row['state']
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=500, showlegend=True
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Full table
    st.subheader("📊 Full State Rankings")
    display = score_df.copy()
    for d in dim_cols:
        if d in display.columns:
            display[d] = display[d].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)
    display['CEI'] = display['CEI'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x)
    st.dataframe(display, use_container_width=True, height=500, hide_index=True)


# ==================================================================
# CENSUS DATA EXPLORER (bonus section when census data is uploaded)
# ==================================================================
if has_census_data:
    st.divider()
    st.subheader("🔬 Census Data Explorer")
    st.caption("Explore the underlying Census 2011 demographic data powering the CEI engine.")

    tab_demo, tab_infra = st.tabs(["Demographics", "Household Infrastructure"])

    with tab_demo:
        sel_state_demo = st.selectbox(
            "Filter by state:",
            ["All States"] + sorted(census_demo['State'].dropna().unique().tolist()),
            key="census_state"
        )
        demo_data = census_demo if sel_state_demo == "All States" else census_demo[census_demo['State'] == sel_state_demo]

        if 'Total_Population' in demo_data.columns and 'Literacy_Rate_Pct' in demo_data.columns:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                fig_pop = px.histogram(
                    demo_data, x='Total_Population', nbins=30,
                    title="District Population Distribution",
                    labels={'Total_Population': 'Population'}
                )
                fig_pop.update_layout(height=300, margin=dict(t=40))
                st.plotly_chart(fig_pop, use_container_width=True)
            with col_d2:
                y_col = 'Work_Participation_Pct' if 'Work_Participation_Pct' in demo_data.columns else 'Total_Population'
                fig_lit = px.scatter(
                    demo_data, x='Literacy_Rate_Pct', y=y_col,
                    color='State' if sel_state_demo == "All States" and demo_data['State'].nunique() <= 10 else None,
                    hover_data=['District', 'State'],
                    title="Literacy vs Work Participation"
                )
                fig_lit.update_layout(height=300, margin=dict(t=40))
                st.plotly_chart(fig_lit, use_container_width=True)

        st.dataframe(demo_data.head(50), use_container_width=True, height=300, hide_index=True)

    with tab_infra:
        if not census_hh.empty:
            sel_state_hh = st.selectbox(
                "Filter by state:",
                ["All States"] + sorted(census_hh['State'].dropna().unique().tolist()),
                key="hh_state"
            )
            hh_data = census_hh if sel_state_hh == "All States" else census_hh[census_hh['State'] == sel_state_hh]

            infra_cols = [c for c in hh_data.columns if c.startswith('HH_') and c.endswith('_Pct')]
            if infra_cols:
                avg_vals = hh_data[infra_cols].mean().sort_values(ascending=True)
                fig_infra = px.bar(
                    x=avg_vals.values,
                    y=[c.replace('HH_', '').replace('_Pct', '').replace('_', ' ') for c in avg_vals.index],
                    orientation='h',
                    title=f"Avg Household Infrastructure - {sel_state_hh}",
                    labels={'x': '%', 'y': ''}
                )
                fig_infra.update_layout(height=350, margin=dict(t=40, l=150))
                st.plotly_chart(fig_infra, use_container_width=True)

            st.dataframe(hh_data.head(50), use_container_width=True, height=300, hide_index=True)
        else:
            st.info("Upload household infrastructure data (Census District Demographics, Sheet 2) to see infrastructure indicators.")
