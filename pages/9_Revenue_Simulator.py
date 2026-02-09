"""
Expansion Intelligence Platform -- Revenue Projection & Scenario Simulator
============================================================================
Interactive 175-pincode revenue waterfall with editable assumptions.
NTB -> Show% -> Conversion -> Revenue model with 6-month ramp-up.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json, os
from db import load_table, DATA_DIR

st.set_page_config(page_title="Revenue Simulator", page_icon="💰", layout="wide")

st.markdown(
    '<span style="background:linear-gradient(135deg,#E53935,#FF7043);color:white;'
    'padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">'
    '💰 Revenue Projection</span>',
    unsafe_allow_html=True,
)
st.title("💰 Revenue Projection & Scenario Simulator")
st.caption("175 Proposed Pincodes | 12-Month Financial Model | NTB → Show% → Conversion → Revenue Waterfall")

# ─── Load Data ────────────────────────────────────────────────────────
rev = load_table("revenue_projection_175")
city_rollup = load_table("revenue_city_rollup")
existing = load_table("existing_clinics_61")
sim_clinics = load_table("scenario_simulator_clinics")

if rev.empty:
    st.info("No revenue projection data loaded. Go to **Upload & Refresh** to import the Expansion Strategy workbook.")
    st.stop()

# Load base assumptions
ASSUMPTIONS_PATH = os.path.join(DATA_DIR, "revenue_assumptions.json")
if os.path.exists(ASSUMPTIONS_PATH):
    with open(ASSUMPTIONS_PATH) as f:
        BASE = json.load(f)
else:
    BASE = {
        'conversion_pct': 0.40, 'sale_value': 18000,
        'show_pct_adjustment': 0, 'new_city_default_show_pct': 0.20,
        'same_city_ntb_scaling': 0.50, 'new_city_ntb_scaling': 1.0,
        'ramp_m1': 0.30, 'ramp_m2': 0.50, 'ramp_m3': 0.65,
        'ramp_m4': 0.80, 'ramp_m5': 0.90, 'ramp_m6': 1.0,
    }

# ─── Numeric Coerce ──────────────────────────────────────────────────
num_cols = ['projected_ss_ntb', 'projected_show_pct', 'monthly_show_ntb',
            'conv_pct', 'monthly_converted', 'sale_per_patient', 'ss_monthly_revenue',
            'rev_12m_total', 'ntb_shows_12m', 'converted_12m', 'ntb_appts_12m', 'parent_avg_ntb']
for c in num_cols:
    if c in rev.columns:
        rev[c] = pd.to_numeric(rev[c], errors='coerce')

for mc in [f'm{i}_rev' for i in range(1, 13)]:
    if mc in rev.columns:
        rev[mc] = pd.to_numeric(rev[mc], errors='coerce')

if not city_rollup.empty:
    for c in ['total_ss_ntb', 'avg_show_pct', 'total_ss_show_ntb',
              'total_ss_monthly_rev', 'rev_12m_total', 'ntb_shows_12m', 'converted_12m']:
        if c in city_rollup.columns:
            city_rollup[c] = pd.to_numeric(city_rollup[c], errors='coerce')


# =====================================================================
# SIDEBAR: SCENARIO SIMULATOR
# =====================================================================
with st.sidebar:
    st.markdown("### 🎛️ Scenario Simulator")
    st.caption("Adjust assumptions — all projections recalculate instantly.")

    st.markdown("**Preset Scenarios**")
    preset = st.radio("", ["Custom", "Worst Case", "Conservative", "Base Case", "Optimistic", "Aggressive"],
                       index=3, horizontal=True, key="preset")

    preset_map = {
        "Worst Case":    {'conv': 0.30, 'sale': 15000, 'show_adj': -0.05},
        "Conservative":  {'conv': 0.35, 'sale': 16000, 'show_adj': -0.03},
        "Base Case":     {'conv': 0.40, 'sale': 18000, 'show_adj': 0.00},
        "Optimistic":    {'conv': 0.45, 'sale': 18000, 'show_adj': 0.05},
        "Aggressive":    {'conv': 0.50, 'sale': 20000, 'show_adj': 0.05},
    }

    if preset != "Custom" and preset in preset_map:
        p = preset_map[preset]
        conv_pct = p['conv']
        sale_val = p['sale']
        show_adj = p['show_adj']
    else:
        conv_pct = None
        sale_val = None
        show_adj = None

    st.divider()
    st.markdown("**Editable Assumptions**")

    conv_pct = st.slider("Conversion % (Show NTB → Sale)",
                          min_value=0.20, max_value=0.70, step=0.05,
                          value=conv_pct if conv_pct else BASE['conversion_pct'],
                          format="%.0f%%", key="conv")

    sale_val = st.number_input("Sale Value per Patient (₹)",
                                min_value=10000, max_value=30000, step=1000,
                                value=int(sale_val if sale_val else BASE['sale_value']),
                                key="sale")

    show_adj = st.slider("Global Show% Adjustment (ppts)",
                          min_value=-0.10, max_value=0.15, step=0.01,
                          value=show_adj if show_adj is not None else 0.0,
                          format="%+.0f%%", key="show_adj")

    new_city_show = st.slider("New City Default Show%",
                               min_value=0.10, max_value=0.35, step=0.01,
                               value=BASE.get('new_city_default_show_pct', 0.20),
                               format="%.0f%%", key="nc_show")

    st.divider()
    st.markdown("**Ramp-Up Curve**")
    ramp_speed = st.select_slider("Ramp Speed", options=["Slow", "Standard", "Fast"],
                                   value="Standard", key="ramp")
    ramp_curves = {
        "Slow":     [0.20, 0.35, 0.50, 0.65, 0.80, 0.90],
        "Standard": [0.30, 0.50, 0.65, 0.80, 0.90, 1.00],
        "Fast":     [0.50, 0.70, 0.85, 0.95, 1.00, 1.00],
    }
    ramp = ramp_curves[ramp_speed] + [1.0] * 6  # M7-M12 always 100%


# =====================================================================
# RECALCULATE PROJECTIONS
# =====================================================================
sim = rev.copy()

# Apply show% adjustment
sim['adj_show_pct'] = sim['projected_show_pct'] + show_adj
# For new-city rows, apply the new city default
is_new_city = sim['type'].str.contains('New', na=False)
sim.loc[is_new_city, 'adj_show_pct'] = new_city_show + show_adj
sim['adj_show_pct'] = sim['adj_show_pct'].clip(0.05, 0.95)

# Recalculate waterfall
sim['sim_show_ntb'] = sim['projected_ss_ntb'] * sim['adj_show_pct']
sim['sim_converted'] = sim['sim_show_ntb'] * conv_pct
sim['sim_ss_monthly_rev'] = sim['sim_converted'] * sale_val

# Apply ramp-up for 12 months
for i in range(12):
    sim[f'sim_m{i+1}_rev'] = sim['sim_ss_monthly_rev'] * ramp[i]

sim['sim_12m_total'] = sum(sim[f'sim_m{i+1}_rev'] for i in range(12))
sim['sim_12m_shows'] = sum(sim['sim_show_ntb'] * ramp[i] for i in range(12))
sim['sim_12m_converted'] = sum(sim['sim_converted'] * ramp[i] for i in range(12))


# =====================================================================
# KPI ROW
# =====================================================================
total_12m = sim['sim_12m_total'].sum()
base_12m = rev['rev_12m_total'].sum()
delta_12m = total_12m - base_12m
total_shows = sim['sim_12m_shows'].sum()
total_conv = sim['sim_12m_converted'].sum()
ss_monthly = sim['sim_ss_monthly_rev'].sum()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("12M Revenue", f"₹{total_12m/1e7:.1f} Cr",
              delta=f"₹{delta_12m/1e7:+.1f} Cr vs Base" if abs(delta_12m) > 100000 else None)
with k2:
    st.metric("SS Monthly Revenue", f"₹{ss_monthly/1e5:.0f} L")
with k3:
    st.metric("12M NTB Shows", f"{total_shows:,.0f}")
with k4:
    st.metric("12M Converted Patients", f"{total_conv:,.0f}")
with k5:
    avg_show = sim['adj_show_pct'].mean()
    st.metric("Wtd Avg Show%", f"{avg_show:.1%}")

st.divider()


# =====================================================================
# MAIN TABS
# =====================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Monthly Waterfall", "City-Wise", "Pincode Detail",
    "Existing Clinics", "Scenario Matrix"
])


# ── TAB 1: Monthly Revenue Waterfall ─────────────────────────────────
with tab1:
    st.subheader("12-Month Revenue Progression")

    monthly_data = []
    for i in range(12):
        m_rev = sim[f'sim_m{i+1}_rev'].sum()
        m_shows = (sim['sim_show_ntb'] * ramp[i]).sum()
        monthly_data.append({
            'Month': f'M{i+1}',
            'Revenue': m_rev,
            'Cumulative': None,
            'Ramp': ramp[i],
            'NTB Shows': m_shows,
            'Status': 'Ramp-Up' if ramp[i] < 1.0 else 'Steady State'
        })

    monthly_df = pd.DataFrame(monthly_data)
    monthly_df['Cumulative'] = monthly_df['Revenue'].cumsum()

    # Dual-axis: bar (monthly) + line (cumulative)
    fig_w = go.Figure()
    fig_w.add_trace(go.Bar(
        x=monthly_df['Month'], y=monthly_df['Revenue'],
        name='Monthly Revenue',
        marker_color=['#FF7043' if r < 1.0 else '#4CAF50' for r in monthly_df['Ramp']],
        text=[f"₹{v/1e5:.0f}L" for v in monthly_df['Revenue']],
        textposition='outside'
    ))
    fig_w.add_trace(go.Scatter(
        x=monthly_df['Month'], y=monthly_df['Cumulative'],
        name='Cumulative',
        line=dict(color='#E53935', width=3),
        yaxis='y2',
        text=[f"₹{v/1e7:.1f}Cr" for v in monthly_df['Cumulative']],
        textposition='top center',
        mode='lines+markers+text'
    ))
    fig_w.update_layout(
        height=450,
        yaxis=dict(title='Monthly Revenue (₹)', showgrid=False),
        yaxis2=dict(title='Cumulative Revenue (₹)', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation='h', y=1.12),
        margin=dict(t=40)
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # Ramp-up curve visual
    st.markdown("**6-Month Ramp-Up Curve Applied**")
    ramp_fig = go.Figure()
    ramp_fig.add_trace(go.Bar(
        x=[f'M{i+1}' for i in range(12)],
        y=[r * 100 for r in ramp],
        marker_color=['#FF7043' if r < 1.0 else '#4CAF50' for r in ramp],
        text=[f'{r:.0%}' for r in ramp],
        textposition='outside'
    ))
    ramp_fig.update_layout(height=250, yaxis_title='% of Steady State', yaxis_range=[0, 115],
                           margin=dict(t=10, b=10))
    st.plotly_chart(ramp_fig, use_container_width=True)

    st.caption(f"Ramp-up reduces Year 1 from ₹{ss_monthly*12/1e7:.1f} Cr (theoretical max) to "
               f"₹{total_12m/1e7:.1f} Cr — a {(1 - total_12m/(ss_monthly*12))*100:.0f}% reduction. "
               "This gap closes in Year 2.")


# ── TAB 2: City-Wise Projections ─────────────────────────────────────
with tab2:
    st.subheader("City-Wise Revenue Projections (Simulated)")

    city_sim = sim.groupby('city').agg(
        pincodes=('city', 'count'),
        total_ss_ntb=('projected_ss_ntb', 'sum'),
        avg_show_pct=('adj_show_pct', 'mean'),
        total_show_ntb=('sim_show_ntb', 'sum'),
        ss_monthly_rev=('sim_ss_monthly_rev', 'sum'),
        rev_12m=('sim_12m_total', 'sum'),
        shows_12m=('sim_12m_shows', 'sum'),
        converted_12m=('sim_12m_converted', 'sum'),
    ).reset_index().sort_values('rev_12m', ascending=False)

    # Determine type
    city_type = sim.groupby('city')['type'].first().reset_index()
    city_sim = city_sim.merge(city_type, on='city', how='left')

    fig_city = px.bar(
        city_sim.head(25), x='city', y='rev_12m',
        color='type',
        color_discrete_map={'Same-City': '#4CAF50', 'New City': '#FF7043',
                            'New City (Tier-2)': '#FF7043', 'New City (Tier-3)': '#FFA726'},
        text=city_sim.head(25)['rev_12m'].apply(lambda v: f"₹{v/1e5:.0f}L"),
        hover_data={'pincodes': True, 'avg_show_pct': ':.1%', 'total_ss_ntb': ':,.0f'}
    )
    fig_city.update_traces(textposition='outside')
    fig_city.update_layout(height=450, xaxis_tickangle=-45, xaxis_title="", yaxis_title="12M Revenue (₹)",
                           margin=dict(t=10))
    st.plotly_chart(fig_city, use_container_width=True)

    # Same-City vs New City split
    sc1, sc2 = st.columns(2)
    with sc1:
        same_city_rev = sim[~is_new_city]['sim_12m_total'].sum()
        new_city_rev = sim[is_new_city]['sim_12m_total'].sum()
        fig_pie = px.pie(
            values=[same_city_rev, new_city_rev],
            names=['Same-City (100 pins)', 'New City (75 pins)'],
            color_discrete_sequence=['#4CAF50', '#FF7043'],
            hole=0.4
        )
        fig_pie.update_traces(texttemplate='₹%{value:,.0f}<br>%{percent}')
        fig_pie.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with sc2:
        st.markdown("**Same-City vs New City Economics**")
        econ = pd.DataFrame([
            {'Metric': '12M Revenue', 'Same-City': f"₹{same_city_rev/1e7:.1f} Cr",
             'New City': f"₹{new_city_rev/1e7:.1f} Cr"},
            {'Metric': 'Revenue per Pin', 'Same-City': f"₹{same_city_rev/100/1e5:.1f} L",
             'New City': f"₹{new_city_rev/75/1e5:.1f} L"},
            {'Metric': 'Avg Show%', 'Same-City': f"{sim[~is_new_city]['adj_show_pct'].mean():.1%}",
             'New City': f"{sim[is_new_city]['adj_show_pct'].mean():.1%}"},
            {'Metric': 'Risk Profile', 'Same-City': 'Lower (proven market)',
             'New City': 'Higher (unproven market)'},
        ])
        st.dataframe(econ, use_container_width=True, hide_index=True)

    # Full city table
    st.markdown("**All Cities Ranked**")
    city_display = city_sim.copy()
    city_display['rev_12m_fmt'] = city_display['rev_12m'].apply(lambda v: f"₹{v/1e5:.0f} L")
    city_display['ss_monthly_fmt'] = city_display['ss_monthly_rev'].apply(lambda v: f"₹{v/1e5:.0f} L")
    city_display['avg_show_pct'] = city_display['avg_show_pct'].apply(lambda v: f"{v:.1%}")
    st.dataframe(
        city_display[['city', 'pincodes', 'type', 'total_ss_ntb', 'avg_show_pct',
                       'ss_monthly_fmt', 'rev_12m_fmt', 'shows_12m', 'converted_12m']],
        use_container_width=True, height=500, hide_index=True
    )


# ── TAB 3: Pincode Detail ────────────────────────────────────────────
with tab3:
    st.subheader("175 Pincode Revenue Detail")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        all_cities = ["All"] + sorted(sim['city'].dropna().unique().tolist())
        sel_city = st.selectbox("City", all_cities, key="pin_city")
    with fc2:
        all_types = ["All"] + sorted(sim['type'].dropna().unique().tolist())
        sel_type = st.selectbox("Expansion Type", all_types, key="pin_type")
    with fc3:
        sort_opt = st.selectbox("Sort by", ["12M Revenue", "Show%", "SS NTB", "Pincode"],
                                key="pin_sort")

    pin_df = sim.copy()
    if sel_city != "All":
        pin_df = pin_df[pin_df['city'] == sel_city]
    if sel_type != "All":
        pin_df = pin_df[pin_df['type'] == sel_type]

    sort_map = {'12M Revenue': 'sim_12m_total', 'Show%': 'adj_show_pct',
                'SS NTB': 'projected_ss_ntb', 'Pincode': 'pincode'}
    pin_df = pin_df.sort_values(sort_map[sort_opt], ascending=(sort_opt == 'Pincode'))

    # Display columns
    pin_show = pin_df[['pincode', 'area', 'city', 'type', 'parent_clinic',
                        'projected_ss_ntb', 'adj_show_pct', 'sim_show_ntb',
                        'sim_converted', 'sim_ss_monthly_rev', 'sim_12m_total']].copy()
    pin_show.columns = ['Pincode', 'Area', 'City', 'Type', 'Parent',
                         'SS NTB', 'Show%', 'Show NTB', 'Converted',
                         'SS Monthly Rev', '12M Revenue']
    pin_show['Show%'] = pin_show['Show%'].apply(lambda v: f"{v:.1%}" if pd.notna(v) else "--")
    pin_show['SS Monthly Rev'] = pin_show['SS Monthly Rev'].apply(lambda v: f"₹{v/1e5:.1f}L" if pd.notna(v) else "--")
    pin_show['12M Revenue'] = pin_show['12M Revenue'].apply(lambda v: f"₹{v/1e5:.1f}L" if pd.notna(v) else "--")

    st.dataframe(pin_show, use_container_width=True, height=600, hide_index=True)
    st.caption(f"Showing {len(pin_df)} of {len(sim)} pincodes | "
               f"Filtered 12M Revenue: ₹{pin_df['sim_12m_total'].sum()/1e7:.1f} Cr")

    # Top 20 bar
    if len(pin_df) > 0:
        top20 = pin_df.nlargest(20, 'sim_12m_total')
        top20['label'] = top20['area'] + ' (' + top20['city'] + ')'
        fig_top = px.bar(
            top20.sort_values('sim_12m_total'),
            x='sim_12m_total', y='label', orientation='h',
            color='type', text=top20.sort_values('sim_12m_total')['sim_12m_total'].apply(
                lambda v: f"₹{v/1e5:.0f}L"),
            color_discrete_map={'Same-City': '#4CAF50', 'New City': '#FF7043',
                                'New City (Tier-2)': '#FF7043', 'New City (Tier-3)': '#FFA726'}
        )
        fig_top.update_traces(textposition='outside')
        fig_top.update_layout(height=500, yaxis_title="", xaxis_title="12M Revenue (₹)",
                              margin=dict(t=10))
        st.plotly_chart(fig_top, use_container_width=True)


# ── TAB 4: Existing Clinic Benchmarks ────────────────────────────────
with tab4:
    st.subheader("Existing 61 Clinics — Parent Benchmarks")

    if not existing.empty:
        # Detect monthly columns
        month_cols = [c for c in existing.columns if c.startswith(('Jan-', 'Feb-', 'Mar-', 'Apr-',
                      'May-', 'Jun-', 'Jul-', 'Aug-', 'Sep-', 'Oct-', 'Nov-', 'Dec-'))]

        for c in ['Total Appts', 'Avg NTB (L12M)', 'Active Months', 'Cabins'] + month_cols:
            if c in existing.columns:
                existing[c] = pd.to_numeric(existing[c], errors='coerce')

        if 'Avg NTB (L12M)' in existing.columns:
            existing = existing.sort_values('Avg NTB (L12M)', ascending=False)

            # implied revenue using scenario assumptions
            existing['Impl_ShowNTB'] = existing['Avg NTB (L12M)'] * 0.22  # pan-india avg
            existing['Impl_Revenue'] = existing['Impl_ShowNTB'] * conv_pct * sale_val

            e1, e2, e3 = st.columns(3)
            with e1:
                st.metric("Total Clinics", f"{len(existing)}")
            with e2:
                st.metric("Avg NTB (L12M)", f"{existing['Avg NTB (L12M)'].mean():,.0f}")
            with e3:
                if 'Total Appts' in existing.columns:
                    st.metric("Total Appointments", f"{existing['Total Appts'].sum():,.0f}")

            fig_ex = px.bar(
                existing.head(30),
                x='Clinic Name' if 'Clinic Name' in existing.columns else existing.columns[1],
                y='Avg NTB (L12M)',
                color='Region' if 'Region' in existing.columns else None,
                text='Avg NTB (L12M)',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_ex.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_ex.update_layout(height=450, xaxis_tickangle=-45, xaxis_title="",
                                 yaxis_title="Avg Monthly NTB", margin=dict(t=10))
            st.plotly_chart(fig_ex, use_container_width=True)

            # Monthly NTB heatmap
            if month_cols:
                st.markdown("**Monthly NTB Heatmap (Top 20 Clinics)**")
                clinic_col = 'Clinic Name' if 'Clinic Name' in existing.columns else existing.columns[1]
                heat_df = existing.head(20).set_index(clinic_col)[month_cols]
                fig_heat = px.imshow(
                    heat_df.values, x=month_cols, y=heat_df.index.tolist(),
                    color_continuous_scale='YlOrRd', aspect='auto',
                    labels=dict(color="NTB Appts")
                )
                fig_heat.update_layout(height=500, margin=dict(t=10))
                st.plotly_chart(fig_heat, use_container_width=True)

            # Detail table
            disp_cols = [c for c in ['S.No', 'Clinic Name', 'City', 'Region',
                                      'Cabins', 'Avg NTB (L12M)', 'Active Months',
                                      'Total Appts'] if c in existing.columns]
            st.dataframe(existing[disp_cols], use_container_width=True, height=400, hide_index=True)
    else:
        st.info("Upload Expansion Strategy workbook to see existing clinic benchmarks.")


# ── TAB 5: Scenario Matrix ──────────────────────────────────────────
with tab5:
    st.subheader("Sensitivity Analysis — Combined Scenario Matrix")
    st.markdown("How 12M revenue changes under different Show%, Conversion%, and Sale Value combinations.")

    show_range = [0.15, 0.18, 0.20, 0.22, 0.25, 0.30]
    conv_range = [0.30, 0.35, 0.40, 0.45, 0.50]

    # Quick recalc for matrix
    base_ntb = sim['projected_ss_ntb'].sum()  # total SS NTB
    ramp_factor = sum(ramp) / 12  # weighted ramp

    matrix_data = []
    for s in show_range:
        row_data = {}
        for c in conv_range:
            rev_val = base_ntb * s * c * sale_val * 12 * ramp_factor
            row_data[f"Conv {c:.0%}"] = f"₹{rev_val/1e7:.0f} Cr"
        matrix_data.append({'Show%': f'{s:.0%}', **row_data})

    matrix_df = pd.DataFrame(matrix_data).set_index('Show%')
    st.dataframe(matrix_df, use_container_width=True)

    # Highlight current scenario
    st.caption(f"Current scenario: Show% ≈ {avg_show:.0%}, Conv = {conv_pct:.0%}, "
               f"Sale = ₹{sale_val:,} → **₹{total_12m/1e7:.1f} Cr**")

    st.divider()

    # Tornado chart: sensitivity
    st.markdown("**Sensitivity Tornado — Which Lever Moves Revenue Most?**")
    base_rev = total_12m
    sensitivities = []

    # Show% sensitivity
    for adj_name, adj_val in [("Show% -5ppt", -0.05), ("Show% +5ppt", 0.05)]:
        s_df = sim.copy()
        s_df['adj_show_pct'] = (s_df['adj_show_pct'] + adj_val).clip(0.05, 0.95)
        s_rev = float(sum(
            (s_df['projected_ss_ntb'] * s_df['adj_show_pct'] * conv_pct * sale_val * ramp[i]).sum()
            for i in range(12)
        ))
        sensitivities.append({'Lever': adj_name, 'Revenue': s_rev, 'Delta': s_rev - base_rev})

    # Conv% sensitivity
    for c_name, c_val in [("Conv 30%", 0.30), ("Conv 50%", 0.50)]:
        s_rev = float(sum(
            (sim['projected_ss_ntb'] * sim['adj_show_pct'] * c_val * sale_val * ramp[i]).sum()
            for i in range(12)
        ))
        sensitivities.append({'Lever': c_name, 'Revenue': s_rev, 'Delta': s_rev - base_rev})

    # Sale value sensitivity
    for sv_name, sv_val in [("Sale ₹15K", 15000), ("Sale ₹20K", 20000)]:
        s_rev = float(sum(
            (sim['projected_ss_ntb'] * sim['adj_show_pct'] * conv_pct * sv_val * ramp[i]).sum()
            for i in range(12)
        ))
        sensitivities.append({'Lever': sv_name, 'Revenue': s_rev, 'Delta': s_rev - base_rev})

    sens_df = pd.DataFrame(sensitivities).sort_values('Delta')
    fig_tornado = px.bar(
        sens_df, x='Delta', y='Lever', orientation='h',
        color=sens_df['Delta'].apply(lambda v: 'Upside' if v > 0 else 'Downside'),
        color_discrete_map={'Upside': '#4CAF50', 'Downside': '#E53935'},
        text=sens_df['Delta'].apply(lambda v: f"₹{v/1e7:+.1f} Cr")
    )
    fig_tornado.update_traces(textposition='outside')
    fig_tornado.update_layout(height=300, xaxis_title="Revenue Impact vs Base (₹)", yaxis_title="",
                              showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig_tornado, use_container_width=True)

    st.caption(f"Base case revenue: ₹{base_rev/1e7:.1f} Cr. "
               "Each bar shows the incremental impact of changing one assumption.")
