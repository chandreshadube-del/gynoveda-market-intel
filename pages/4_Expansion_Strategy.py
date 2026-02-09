"""
Expansion Intelligence Platform -- 100-Clinic Expansion Strategy
=================================================================
Pan-India expansion blueprint: Same-City micro-markets, New City entry,
IVF Competitor Map, Show%-based priority tiers, Implementation Roadmap.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import load_table

st.set_page_config(page_title="Expansion Strategy", page_icon="🚀", layout="wide")

st.markdown(
    '<span style="background:linear-gradient(135deg,#1565C0,#42A5F5);color:white;'
    'padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">'
    '🚀 Expansion Strategy</span>',
    unsafe_allow_html=True,
)
st.title("🚀 100-Clinic Expansion Strategy")
st.caption("Pan-India Blueprint: 100 Same-City + 75 New City Pincodes | Show%-Based Priority Tiers | Implementation Roadmap")

# ─── Load Data ────────────────────────────────────────────────────────
same_city = load_table("expansion_same_city")
new_city = load_table("expansion_new_city")
ivf_comp = load_table("ivf_competitor_map")
web_demand = load_table("web_order_demand")
roadmap = load_table("implementation_roadmap")
show_analysis = load_table("show_pct_analysis")
sim_clinics = load_table("scenario_simulator_clinics")
priority_tiers = load_table("expansion_priority_tiers")
rank_comparison = load_table("show_pct_rank_comparison")
impact_comp = load_table("show_pct_impact_comparison")
existing = load_table("existing_clinics_61")

has_data = not same_city.empty or not new_city.empty
if not has_data:
    st.info("No expansion strategy data loaded. Go to **Upload & Refresh** to import the Expansion Strategy workbook.")
    st.stop()


# ─── KPIs ─────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Current Clinics", "61")
with k2:
    st.metric("Same-City Pins", f"{len(same_city)}" if not same_city.empty else "0")
with k3:
    st.metric("New City Pins", f"{len(new_city)}" if not new_city.empty else "0")
with k4:
    st.metric("Target Total", "161+")
with k5:
    if not new_city.empty and 'City' in new_city.columns:
        st.metric("New Cities", f"{new_city['City'].nunique()}")
    else:
        st.metric("New Cities", "15")
with k6:
    if not priority_tiers.empty:
        p1_count = priority_tiers.iloc[0].get('Count', 18) if len(priority_tiers) > 0 else 18
        st.metric("P1 Expand Now", f"{p1_count}")
    else:
        st.metric("P1 Expand Now", "18")

st.divider()


# =====================================================================
# MAIN TABS
# =====================================================================
tabs = st.tabs([
    "Same-City Expansion", "New City Entry", "Show% Priority Tiers",
    "IVF Competitor Map", "Web Demand", "Implementation Roadmap"
])


# ── TAB 1: Same-City Expansion ───────────────────────────────────────
with tabs[0]:
    st.subheader("Same-City Micro-Market Expansion (100 Pincodes)")
    st.markdown("Near existing high-NTB clinics in 10 proven metro markets.")

    if not same_city.empty:
        # Coerce numeric
        for c in ['Highest Avg NTB']:
            if c in same_city.columns:
                same_city[c] = pd.to_numeric(same_city[c], errors='coerce')

        # City filter
        all_cities = ["All"] + sorted(same_city['City'].dropna().unique().tolist()) if 'City' in same_city.columns else ["All"]
        sel = st.selectbox("Filter by City", all_cities, key="sc_city")

        df_sc = same_city.copy()
        if sel != "All" and 'City' in df_sc.columns:
            df_sc = df_sc[df_sc['City'] == sel]

        # City summary
        if 'City' in same_city.columns and 'Micro-Market Pincode' in same_city.columns:
            city_counts = same_city.groupby('City').agg(
                pincodes=('Micro-Market Pincode', 'count'),
                max_ntb=('Highest Avg NTB', 'max')
            ).reset_index().sort_values('max_ntb', ascending=False)

            fig_sc = px.bar(
                city_counts, x='City', y='pincodes', color='max_ntb',
                color_continuous_scale='YlOrRd',
                text='pincodes',
                labels={'pincodes': 'Proposed Pincodes', 'max_ntb': 'Max Parent NTB'}
            )
            fig_sc.update_traces(textposition='outside')
            fig_sc.update_layout(height=350, xaxis_tickangle=-45, margin=dict(t=10))
            st.plotly_chart(fig_sc, use_container_width=True)

        # Detail table
        display_cols = [c for c in ['S.No', 'City', 'Micro-Market Pincode', 'Micro-Market Area',
                                     'Highest Avg NTB', 'Expansion Rationale',
                                     'Existing Clinics'] if c in df_sc.columns]
        st.dataframe(df_sc[display_cols], use_container_width=True, height=500, hide_index=True)

        # IVF presence
        if 'National IVFs Present' in df_sc.columns:
            with st.expander("IVF Competition in Selected Markets"):
                ivf_cols = [c for c in ['City', 'National IVFs Present', 'Regional IVFs Present']
                            if c in df_sc.columns]
                ivf_df = df_sc[ivf_cols].drop_duplicates()
                st.dataframe(ivf_df, use_container_width=True, hide_index=True)


# ── TAB 2: New City Entry ────────────────────────────────────────────
with tabs[1]:
    st.subheader("New City Expansion (75 Pincodes in 15 Cities)")
    st.markdown("High-demand new markets identified via web order analysis and demographic screening.")

    if not new_city.empty:
        for c in ['Web Order Qty', 'Projected Monthly NTB']:
            if c in new_city.columns:
                new_city[c] = pd.to_numeric(new_city[c], errors='coerce')

        # City summary
        if 'City' in new_city.columns:
            nc_summary = new_city.groupby(['City', 'State', 'Tier']).agg(
                pincodes=('City', 'count'),
                web_orders=('Web Order Qty', 'max'),
                monthly_ntb=('Projected Monthly NTB', 'max'),
            ).reset_index().sort_values('monthly_ntb', ascending=False)

            fig_nc = px.bar(
                nc_summary, x='City', y='monthly_ntb', color='Tier',
                text='pincodes',
                color_discrete_map={'Tier-2': '#FF7043', 'Tier-3': '#FFA726'},
                hover_data={'web_orders': ':,.0f', 'pincodes': True}
            )
            fig_nc.update_traces(texttemplate='%{text} pins', textposition='outside')
            fig_nc.update_layout(height=400, xaxis_tickangle=-45, xaxis_title="",
                                 yaxis_title="Projected Monthly NTB", margin=dict(t=10))
            st.plotly_chart(fig_nc, use_container_width=True)

        # Scatter: Web Orders vs Projected NTB
        if 'Web Order Qty' in new_city.columns and 'Projected Monthly NTB' in new_city.columns:
            nc_city = new_city.groupby('City').agg(
                web_orders=('Web Order Qty', 'max'),
                monthly_ntb=('Projected Monthly NTB', 'max'),
                pincodes=('City', 'count')
            ).reset_index()

            fig_scatter = px.scatter(
                nc_city, x='web_orders', y='monthly_ntb', size='pincodes',
                text='City', color='monthly_ntb', color_continuous_scale='YlOrRd',
                labels={'web_orders': 'Web Order Qty (Demand Signal)',
                        'monthly_ntb': 'Projected Monthly NTB'}
            )
            fig_scatter.update_traces(textposition='top center')
            fig_scatter.update_layout(height=400, margin=dict(t=10))
            st.plotly_chart(fig_scatter, use_container_width=True)

        # Detail table
        st.markdown("**All 75 Proposed Pincodes**")
        display_cols = [c for c in ['S.No', 'City', 'State', 'Tier', 'Pincode', 'Area Name',
                                     'Web Order Qty', 'Projected Monthly NTB',
                                     'Location Rationale', 'National IVFs', 'Regional IVFs']
                        if c in new_city.columns]
        st.dataframe(new_city[display_cols], use_container_width=True, height=500, hide_index=True)


# ── TAB 3: Show% Priority Tiers ─────────────────────────────────────
with tabs[2]:
    st.subheader("Show%-Based Expansion Priority Tiers")
    st.markdown(
        "Raw NTB measures booked appointments. **Show% measures actual walk-ins.** "
        "A clinic with 1,000 NTB but 11% Show% (110 actual patients) is operationally weaker "
        "than one with 300 NTB and 35% Show% (105 patients with better conversion). "
        "Show%-based planning prioritizes clinics that convert leads into actual visits."
    )

    # Priority tier cards
    if not priority_tiers.empty:
        tier_colors = {'P1 - IMMEDIATE': '#4CAF50', 'P2 - STRONG': '#2196F3',
                       'P3 - STANDARD': '#FF9800', 'P4 - WATCH': '#F44336'}

        for _, tier in priority_tiers.iterrows():
            tier_name = str(tier.get('Priority Tier', ''))
            color = tier_colors.get(tier_name, '#9E9E9E')

            with st.container():
                st.markdown(
                    f'<div style="border-left:4px solid {color};padding:12px 16px;'
                    f'margin:8px 0;background:#f8f9fa;border-radius:0 8px 8px 0">'
                    f'<strong style="color:{color};font-size:1.1rem">{tier_name}</strong><br>'
                    f'<span style="color:#666;font-size:0.85rem">'
                    f'{tier.get("Criteria", "")}</span><br>'
                    f'<strong>Count:</strong> {tier.get("Count", "")} clinics | '
                    f'<strong>Avg Show%:</strong> {tier.get("Avg Show%", "")} | '
                    f'<strong>Avg NTB Shows:</strong> {tier.get("Avg NTB Shows", "")}<br>'
                    f'<strong>Action:</strong> {tier.get("Expansion Action", "")}<br>'
                    f'<strong>Key Cities:</strong> {tier.get("Key Cities", "")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    # Rank comparison: NTB vs Show%
    if not rank_comparison.empty:
        st.markdown("**Top 20 Clinics — NTB Rank vs Show% Rank**")
        st.caption("See how clinic priorities shift when ranked by actual walk-ins instead of bookings.")

        for c in ['Avg NTB Appts', 'Avg NTB Shows']:
            if c in rank_comparison.columns:
                rank_comparison[c] = pd.to_numeric(rank_comparison[c], errors='coerce')

        clinic_col = 'Clinic' if 'Clinic' in rank_comparison.columns else rank_comparison.columns[1]

        fig_rank = go.Figure()
        fig_rank.add_trace(go.Bar(
            x=rank_comparison[clinic_col], y=rank_comparison.get('Avg NTB Appts', []),
            name='NTB Bookings', marker_color='#FFAB91', opacity=0.7
        ))
        fig_rank.add_trace(go.Bar(
            x=rank_comparison[clinic_col], y=rank_comparison.get('Avg NTB Shows', []),
            name='Actual Shows', marker_color='#4CAF50'
        ))
        fig_rank.update_layout(
            height=400, barmode='overlay', xaxis_tickangle=-45,
            yaxis_title='Monthly Patients', margin=dict(t=10),
            legend=dict(orientation='h', y=1.1)
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        st.dataframe(rank_comparison, use_container_width=True, height=400, hide_index=True)

    st.divider()

    # Impact comparison
    if not impact_comp.empty:
        st.markdown("**How Show%-Based Planning Changes the Roadmap**")
        disp_cols = [c for c in impact_comp.columns if c and not c.startswith('col_')]
        st.dataframe(impact_comp[disp_cols], use_container_width=True, hide_index=True)

    # Show% scatter for all 61 clinics
    if not sim_clinics.empty:
        st.divider()
        st.markdown("**All 61 Clinics — Show% vs NTB Volume**")

        for c in ['Avg NTB Appts', 'Current Show %', 'Current NTB Shows']:
            if c in sim_clinics.columns:
                sim_clinics[c] = pd.to_numeric(sim_clinics[c], errors='coerce')

        clinic_col_s = 'Clinic' if 'Clinic' in sim_clinics.columns else sim_clinics.columns[1]

        if 'Avg NTB Appts' in sim_clinics.columns and 'Current Show %' in sim_clinics.columns:
            fig_sim = px.scatter(
                sim_clinics, x='Avg NTB Appts', y='Current Show %',
                hover_name=clinic_col_s,
                color='Tier' if 'Tier' in sim_clinics.columns else None,
                color_discrete_map={'P1': '#4CAF50', 'P2': '#2196F3', 'P3': '#FF9800', 'P4': '#F44336'},
                size='Current NTB Shows' if 'Current NTB Shows' in sim_clinics.columns else None,
                labels={'Avg NTB Appts': 'Avg Monthly NTB (Bookings)', 'Current Show %': 'Show Rate'}
            )
            fig_sim.update_layout(
                height=500, margin=dict(t=10),
                yaxis_tickformat='.0%'
            )
            # Add quadrant lines
            avg_ntb = sim_clinics['Avg NTB Appts'].mean()
            avg_show = sim_clinics['Current Show %'].mean()
            fig_sim.add_hline(y=avg_show, line_dash="dash", line_color="gray",
                              annotation_text=f"Avg Show: {avg_show:.1%}")
            fig_sim.add_vline(x=avg_ntb, line_dash="dash", line_color="gray",
                              annotation_text=f"Avg NTB: {avg_ntb:,.0f}")
            st.plotly_chart(fig_sim, use_container_width=True)
            st.caption("Top-right = high bookings + high conversion (expand immediately). "
                       "Bottom-right = high bookings but low conversion (fix Show% first). "
                       "Bubble size = actual NTB Shows.")


# ── TAB 4: IVF Competitor Map ────────────────────────────────────────
with tabs[3]:
    st.subheader("IVF Competitor Landscape")

    if not ivf_comp.empty:
        for c in ['No. of Centers']:
            if c in ivf_comp.columns:
                ivf_comp[c] = ivf_comp[c].astype(str).str.replace('+', '', regex=False)
                ivf_comp[c] = pd.to_numeric(ivf_comp[c], errors='coerce')

        st.dataframe(ivf_comp, use_container_width=True, hide_index=True)

        if 'No. of Centers' in ivf_comp.columns and 'Chain Name' in ivf_comp.columns:
            fig_ivf = px.bar(
                ivf_comp.sort_values('No. of Centers', ascending=True),
                x='No. of Centers', y='Chain Name', orientation='h',
                color='Type' if 'Type' in ivf_comp.columns else None,
                text='No. of Centers',
                color_discrete_map={'National Chains': '#E53935', 'Hospital-Backed': '#1565C0',
                                    'Regional': '#4CAF50', 'Specialized': '#FF9800'}
            )
            fig_ivf.update_traces(textposition='outside')
            fig_ivf.update_layout(height=400, yaxis_title="", xaxis_title="Number of Centers",
                                  margin=dict(t=10))
            st.plotly_chart(fig_ivf, use_container_width=True)

        if 'Cities Present' in ivf_comp.columns:
            with st.expander("City-Level IVF Presence"):
                for _, row in ivf_comp.iterrows():
                    st.markdown(f"**{row.get('Chain Name', '')}** ({row.get('Type', '')}): "
                                f"{row.get('Cities Present', '')}")
    else:
        st.info("Upload the Expansion Strategy workbook to see IVF competitor data.")


# ── TAB 5: Web Demand ────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Web Order Demand — Top 100 Pincodes")
    st.markdown("Website first-time orders (2020-2025) as demand signals for expansion targeting.")

    if not web_demand.empty:
        for c in ['Total Qty', 'Total Revenue (₹)', 'Unique Customers']:
            if c in web_demand.columns:
                web_demand[c] = pd.to_numeric(web_demand[c], errors='coerce')

        wk1, wk2, wk3 = st.columns(3)
        with wk1:
            st.metric("Top 100 Pincodes", f"{len(web_demand)}")
        with wk2:
            if 'Total Qty' in web_demand.columns:
                st.metric("Total Orders", f"{web_demand['Total Qty'].sum():,.0f}")
        with wk3:
            if 'Total Revenue (₹)' in web_demand.columns:
                st.metric("Total Revenue", f"₹{web_demand['Total Revenue (₹)'].sum()/1e5:,.0f} L")

        if 'City' in web_demand.columns and 'Total Qty' in web_demand.columns:
            city_web = web_demand.groupby('City')['Total Qty'].sum().reset_index().sort_values(
                'Total Qty', ascending=False).head(20)
            fig_web = px.bar(
                city_web, x='City', y='Total Qty',
                text='Total Qty', color_discrete_sequence=['#1565C0']
            )
            fig_web.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_web.update_layout(height=400, xaxis_tickangle=-45, xaxis_title="",
                                  yaxis_title="Web Orders", margin=dict(t=10))
            st.plotly_chart(fig_web, use_container_width=True)

        st.dataframe(web_demand, use_container_width=True, height=500, hide_index=True)
    else:
        st.info("Upload Expansion Strategy workbook to see web order demand data.")


# ── TAB 6: Implementation Roadmap ────────────────────────────────────
with tabs[5]:
    st.subheader("4-Phase Implementation Roadmap")

    if not roadmap.empty:
        phase_colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']

        for i, (_, phase) in enumerate(roadmap.iterrows()):
            color = phase_colors[i % len(phase_colors)]
            phase_name = phase.get('Phase', f'Phase {i+1}')
            timeline = phase.get('Timeline', '')
            strategy = phase.get('Strategy', '')
            cities = phase.get('Cities/Regions', '')
            target = phase.get('Target Clinics', '')
            actions = phase.get('Key Actions', '')

            st.markdown(
                f'<div style="border-left:5px solid {color};padding:16px 20px;'
                f'margin:12px 0;background:linear-gradient(135deg,#f8f9fa,#fff);'
                f'border-radius:0 12px 12px 0;box-shadow:0 2px 4px rgba(0,0,0,0.05)">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<strong style="color:{color};font-size:1.2rem">{phase_name}</strong>'
                f'<span style="background:{color};color:white;padding:2px 10px;'
                f'border-radius:12px;font-size:0.8rem">{timeline}</span></div>'
                f'<p style="color:#444;margin:8px 0 4px"><strong>Strategy:</strong> {strategy}</p>'
                f'<p style="color:#444;margin:4px 0"><strong>Target:</strong> {target}</p>'
                f'<p style="color:#444;margin:4px 0"><strong>Cities:</strong> {cities}</p>'
                f'<p style="color:#666;margin:4px 0;font-size:0.9rem"><strong>Actions:</strong> {actions}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Timeline Gantt-style visual
        st.divider()
        st.markdown("**Timeline Overview**")
        gantt_data = []
        quarters = {'Q1-Q2 FY27': (0, 6), 'Q2-Q3 FY27': (3, 9),
                     'Q3-Q4 FY27': (6, 12), 'Q4 FY27-Q1 FY28': (9, 15)}
        for _, phase in roadmap.iterrows():
            tl = str(phase.get('Timeline', ''))
            start, end = quarters.get(tl, (0, 6))
            gantt_data.append({
                'Phase': str(phase.get('Phase', '')),
                'Start': start, 'Duration': end - start,
                'Target': str(phase.get('Target Clinics', ''))
            })

        if gantt_data:
            gantt_df = pd.DataFrame(gantt_data)
            fig_gantt = go.Figure()
            for i, row in gantt_df.iterrows():
                fig_gantt.add_trace(go.Bar(
                    x=[row['Duration']], y=[row['Phase']],
                    base=row['Start'], orientation='h',
                    marker_color=phase_colors[i % len(phase_colors)],
                    text=f"{row['Target']}",
                    textposition='inside',
                    name=row['Phase'],
                    showlegend=False
                ))
            fig_gantt.update_layout(
                height=200, xaxis_title="Months from Start",
                yaxis=dict(autorange='reversed'),
                margin=dict(t=10, b=30),
                xaxis=dict(tickvals=[0, 3, 6, 9, 12, 15],
                           ticktext=['Q1', 'Q2', 'Q3', 'Q4', 'Q1+1', 'Q2+1'])
            )
            st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.info("Upload Expansion Strategy workbook to see the implementation roadmap.")
