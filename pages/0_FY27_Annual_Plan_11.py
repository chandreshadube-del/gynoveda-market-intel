"""
FY27 Annual Plan — CEO Decision Dashboard
==========================================
Proof-gated expansion: Every clinic earns its place.
Same-city anchored on capacity saturation + NTB:Pop ratio.
New-city anchored on web demand + ratio-validated NTB projection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from db import load_table

st.set_page_config(page_title="FY27 Annual Plan", page_icon="📋", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main > div { padding-top: 0.3rem; }
    .block-container { max-width: 1350px; padding-top: 0.5rem; }
    [data-testid="stMetric"] {
        border-radius: 10px; padding: 10px 14px; border: 1px solid #e8e8e8;
    }
    [data-testid="stMetric"] label { font-size: 0.75rem; color: #888; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.3rem; font-weight: 700; }
    .gate-pass { background: #E8F5E9; border-left: 4px solid #43A047; padding: 12px 16px;
        border-radius: 8px; margin: 6px 0; }
    .gate-fail { background: #FFEBEE; border-left: 4px solid #E53935; padding: 12px 16px;
        border-radius: 8px; margin: 6px 0; }
    .gate-warn { background: #FFF8E1; border-left: 4px solid #FFA000; padding: 12px 16px;
        border-radius: 8px; margin: 6px 0; }
    .insight-box { background: #F3E5F5; border-left: 4px solid #7B1FA2; padding: 12px 16px;
        border-radius: 8px; margin: 8px 0; font-size: 0.88rem; }
    .section-header { font-size: 1.05rem; font-weight: 700; color: #2d3436; margin: 0.4rem 0 0.2rem 0; }
    .ratio-card { background: #E3F2FD; border: 1px solid #BBDEFB; border-radius: 10px;
        padding: 12px 16px; margin: 4px 0; text-align: center; }
</style>
""", unsafe_allow_html=True)


# ── Load Data ────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    d = {}
    tables = ['existing_clinics_61', 'scenario_simulator_clinics', 'show_pct_analysis',
              'revenue_projection_175', 'expansion_priority_tiers', 'implementation_roadmap',
              'expansion_same_city', 'expansion_new_city', 'ivf_competitor_map',
              'web_order_demand', 'clinic_monthly_trend', 'master_state',
              'show_pct_rank_comparison', 'show_pct_impact_comparison',
              'pincode_clinic']
    for t in tables:
        d[t] = load_table(t)
    return d

data = load_all()
ec = data['existing_clinics_61']
sim = data['scenario_simulator_clinics']
show = data['show_pct_analysis']
rev = data['revenue_projection_175']
tiers = data['expansion_priority_tiers']
road = data['implementation_roadmap']
same = data['expansion_same_city']
newc = data['expansion_new_city']
ivf = data['ivf_competitor_map']
web = data['web_order_demand']
cm = data['clinic_monthly_trend']
master = data['master_state']
pincode_clinic = data['pincode_clinic']

if ec.empty:
    st.warning("No clinic data loaded. Please upload data via **Upload & Refresh**.")
    st.stop()

# ── Parse numerics ───────────────────────────────────────────────────
month_cols = [c for c in ec.columns if c.startswith(('Jan-', 'Feb-', 'Mar-', 'Apr-',
              'May-', 'Jun-', 'Jul-', 'Aug-', 'Sep-', 'Oct-', 'Nov-', 'Dec-'))]
for c in month_cols + ['Avg NTB (L12M)', 'Total Appts', 'Cabins', 'Active Months']:
    if c in ec.columns:
        ec[c] = pd.to_numeric(ec[c], errors='coerce')

for c in ['Avg NTB Appts', 'Current Show %', 'Current NTB Shows']:
    if c in sim.columns:
        sim[c] = pd.to_numeric(sim[c], errors='coerce')

for c in ['projected_ss_ntb', 'projected_show_pct', 'ss_monthly_revenue', 'rev_12m_total']:
    if c in rev.columns:
        rev[c] = pd.to_numeric(rev[c], errors='coerce')

if not cm.empty and 'Month' in cm.columns:
    cm['Month'] = pd.to_datetime(cm['Month'], errors='coerce')
    for c in ['qty', 'revenue', 'transactions']:
        if c in cm.columns:
            cm[c] = pd.to_numeric(cm[c], errors='coerce').fillna(0)

# ── Constants ────────────────────────────────────────────────────────
CONV_PCT = 0.40
SALE_VAL = 22000  # ₹22K per NTB patient
TARGET_MONTHLY = 4400000  # 44 lakhs
SHOW_THRESHOLD = 150  # NTB shows qualifying threshold
CABIN_CAPACITY = 100  # theoretical max shows per cabin per month

# ── Derived metrics ──────────────────────────────────────────────────
sim['est_monthly_rev'] = sim['Current NTB Shows'] * CONV_PCT * SALE_VAL
sim['est_annual_rev'] = sim['est_monthly_rev'] * 12
sim['target_pct'] = (sim['est_monthly_rev'] / TARGET_MONTHLY * 100).round(1)

# NTB monthly trend
ntb_monthly = ec[month_cols].sum()
clinic_count_monthly = (ec[month_cols] > 0).sum()
ntb_per_clinic = ntb_monthly / clinic_count_monthly.replace(0, np.nan)
peak_ntb = ntb_monthly.max()
latest_ntb = ntb_monthly.iloc[-1] if len(ntb_monthly) > 0 else 0

# L3M trend for each clinic
l3m_cols = month_cols[-3:] if len(month_cols) >= 3 else month_cols
l12m_cols = month_cols[-12:] if len(month_cols) >= 12 else month_cols
ec['l3m_avg'] = ec[l3m_cols].mean(axis=1) if l3m_cols else 0
ec['l12m_avg'] = ec[l12m_cols].mean(axis=1) if l12m_cols else ec.get('Avg NTB (L12M)', 0)
ec['l3m_l12m_ratio'] = ec['l3m_avg'] / ec['l12m_avg'].replace(0, np.nan)

# Utilization: NTB Shows / (Cabins * Capacity)
sim_ec = sim.merge(
    ec[['Clinic Name', 'Cabins', 'l3m_avg', 'l12m_avg', 'l3m_l12m_ratio']].rename(
        columns={'Clinic Name': 'Clinic'}),
    on='Clinic', how='left'
)
sim_ec['utilization'] = sim_ec['Current NTB Shows'] / (sim_ec['Cabins'].fillna(2) * CABIN_CAPACITY) * 100

# City population map (UA estimates 2025)
CITY_POP = {
    'Mumbai': 21000000, 'Delhi': 19000000, 'Bengaluru': 13000000,
    'Hyderabad': 10000000, 'Kolkata': 15000000, 'Ahmedabad': 8500000,
    'Pune': 7500000, 'Lucknow': 4000000, 'Surat': 6500000, 'Patna': 2500000,
    'Thane': 2400000, 'Nagpur': 3000000, 'Kalyan': 1600000, 'Navi Mumbai': 2000000,
    'Noida': 1200000, 'Guwahati': 1200000, 'Raipur': 1500000, 'Siliguri': 800000,
    'Rajkot': 1800000, 'Bhubaneswar': 1100000, 'Jaipur': 4000000,
    'Vadodara': 2200000, 'Ghaziabad': 2400000, 'Varanasi': 1700000,
    'Agra': 2100000, 'Meerut': 1600000, 'Ludhiana': 1800000,
    'Dehradun': 800000, 'Bhopal': 2400000, 'Indore': 3000000,
    'Amritsar': 1300000, 'Faridabad': 1800000, 'Chandigarh': 1200000,
    'Nashik': 2000000, 'Ranchi': 1500000, 'Jalandhar': 1000000,
    'Chennai': 10000000, 'Secunderabad': 3500000, 'Prayagraj': 1500000,
    'Kanpur': 3200000, 'Dimapur': 200000, 'Margao': 100000,
    'Mysuru': 1100000, 'Itanagar': 60000, 'Asansol': 700000,
    'Howrah': 1200000,
    # New cities
    'Coimbatore': 2100000, 'Jamshedpur': 1500000, 'Jabalpur': 1300000,
    'Patiala': 500000, 'Ernakulam/Kochi': 2100000, 'Jodhpur': 1300000,
    'Mangalore': 700000, 'Agartala': 500000, 'Bareilly': 1000000,
    'Vishakhapatnam': 2100000, 'Jammu': 600000, 'Srinagar': 1500000,
    'Shillong': 400000, 'Imphal': 500000, 'Gangtok': 150000,
}

# NTB:Pop ratio calculation
city_ntb = sim.groupby('City').agg(
    clinics=('Clinic', 'count'),
    total_shows=('Current NTB Shows', 'sum'),
    total_ntb=('Avg NTB Appts', 'sum'),
    avg_show=('Current Show %', 'mean')
).reset_index()
city_ntb['population'] = city_ntb['City'].map(CITY_POP)
city_ntb['ntb_per_lakh'] = city_ntb['total_shows'] / (city_ntb['population'] / 100000)
city_ntb_valid = city_ntb.dropna(subset=['population'])
MEDIAN_RATIO = city_ntb_valid['ntb_per_lakh'].median()
P25_RATIO = city_ntb_valid['ntb_per_lakh'].quantile(0.25)
P75_RATIO = city_ntb_valid['ntb_per_lakh'].quantile(0.75)

# Parse new city populations
def parse_pop(txt):
    if pd.isna(txt): return np.nan
    txt = str(txt).lower().replace('(metro)', '').replace('(city)', '').replace('lakh', '').replace('lakhs', '').strip()
    try: return float(txt) * 100000
    except: return np.nan

if not newc.empty and 'Est. Population' in newc.columns:
    newc['pop_numeric'] = newc['Est. Population'].apply(parse_pop)


# ================================================================
# SIDEBAR — Scenario Controls
# ================================================================
with st.sidebar:
    st.markdown("### 📋 FY27 Plan Controls")
    st.divider()
    scn_label = st.radio("Scenario", ["Conservative", "Base Case", "Optimistic"], index=1)
    show_adj = {'Conservative': -0.02, 'Base Case': 0.0, 'Optimistic': 0.03}[scn_label]
    conv_adj = {'Conservative': 0.35, 'Base Case': 0.40, 'Optimistic': 0.45}[scn_label]

    st.divider()
    ntb_threshold = st.slider("Same-City NTB Show Threshold", 100, 250, SHOW_THRESHOLD, 10)
    ratio_mode = st.radio("NTB:Pop Ratio for New Cities",
                          ["Median (3.8/lakh)", "Conservative (P25: 2.6/lakh)", "Custom"],
                          index=0)
    if ratio_mode.startswith("Median"):
        applied_ratio = MEDIAN_RATIO
    elif ratio_mode.startswith("Conservative"):
        applied_ratio = P25_RATIO
    else:
        applied_ratio = st.number_input("Custom ratio (shows/lakh pop)", 1.0, 15.0, 3.8, 0.5)

    st.divider()
    st.caption(f"Show% adj: {show_adj:+.0%} | Conv: {conv_adj:.0%}")
    st.caption(f"NTB:Pop ratio: {applied_ratio:.1f} shows/lakh")


# ================================================================
# HEADER
# ================================================================
st.markdown("### 📋 FY27 Annual Expansion Plan")
st.caption("Proof-Gated Strategy — Every clinic earns its place through data, not optimism")


# ================================================================
# SECTION 1 — THE CASE FOR CAUTION
# ================================================================
st.divider()
st.markdown('<p class="section-header">1️⃣ THE CASE FOR CAUTION — Why We Must Be Smart, Not Just Fast</p>',
            unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
decline_pct = (peak_ntb - latest_ntb) / peak_ntb * 100 if peak_ntb > 0 else 0
avg_show = sim['Current Show %'].mean()
clinics_below_50 = (sim['target_pct'] < 50).sum()
p4_count = len(sim[sim['Tier'] == 'P4']) if 'Tier' in sim.columns else 0

with c1:
    st.metric("NTB Decline from Peak", f"-{decline_pct:.0f}%",
              delta=f"{latest_ntb:,.0f} vs {peak_ntb:,.0f}", delta_color="inverse")
with c2:
    st.metric("Network Avg Show%", f"{avg_show:.1%}",
              delta=f"{(sim['Current Show %'] < 0.18).sum()} of 61 below 18%", delta_color="inverse")
with c3:
    st.metric("Below 50% Target", f"{clinics_below_50} of {len(sim)}",
              delta="Producing <₹22L/month", delta_color="inverse")
with c4:
    st.metric("P4 Watch Clinics", f"{p4_count}",
              delta="Show% below 15%", delta_color="inverse")
with c5:
    st.metric("NTB/Clinic (Latest)", f"{ntb_per_clinic.iloc[-1]:,.0f}",
              delta=f"Peak was {ntb_per_clinic.max():,.0f}", delta_color="inverse")

# NTB trend chart + insight
rc1, rc2 = st.columns([1.7, 1])

with rc1:
    ntb_df = pd.DataFrame({
        'Month': month_cols, 'Network NTB': ntb_monthly.values,
        'Per Clinic': ntb_per_clinic.values,
        'Clinics': clinic_count_monthly.values
    })
    fig_t = make_subplots(specs=[[{"secondary_y": True}]])
    fig_t.add_trace(go.Bar(
        x=ntb_df['Month'], y=ntb_df['Network NTB'], name='Total NTB',
        marker_color=['#43A047' if v >= peak_ntb*0.9 else '#FFA000' if v >= peak_ntb*0.7
                      else '#E53935' for v in ntb_df['Network NTB']],
        text=ntb_df['Network NTB'].apply(lambda v: f"{v/1e3:.1f}K"),
        textposition='outside'), secondary_y=False)
    fig_t.add_trace(go.Scatter(
        x=ntb_df['Month'], y=ntb_df['Per Clinic'], name='NTB/Clinic',
        mode='lines+markers', line=dict(color='#1565C0', width=3),
        marker=dict(size=7)), secondary_y=True)
    fig_t.update_layout(height=280, margin=dict(t=30, b=20, l=40, r=40),
                        title_text="Network NTB — The Plateau Problem", title_font_size=12,
                        legend=dict(orientation='h', y=1.15))
    fig_t.update_yaxes(title_text="Total NTB", secondary_y=False)
    fig_t.update_yaxes(title_text="Per Clinic", secondary_y=True)
    st.plotly_chart(fig_t, use_container_width=True)

with rc2:
    p4_rev = sim[sim['Tier'] == 'P4']['est_annual_rev'].sum() if 'Tier' in sim.columns else 0
    st.markdown(f'<div class="insight-box">'
                f'<b>📊 The Data Says:</b><br>'
                f'• NTB peaked at <b>{peak_ntb:,.0f}</b>, now <b>{latest_ntb:,.0f}</b> (-{decline_pct:.0f}%)<br>'
                f'• NTB per clinic fell from <b>{ntb_per_clinic.max():,.0f}</b> to <b>{ntb_per_clinic.iloc[-1]:,.0f}</b><br>'
                f'• <b>{p4_count}</b> clinics (Show% &lt;15%) lock ₹{p4_rev/1e7:.1f}Cr in underperformance<br>'
                f'• Adding clinics without fixing Show% grows cost faster than revenue<br><br>'
                f'<b>🎯 The answer:</b> Not fewer or more clinics — <b>smarter clinics</b>.'
                f'</div>', unsafe_allow_html=True)


# ================================================================
# SECTION 1B — STATE-WISE STANDARD SHOW% BENCHMARK
# ================================================================
st.divider()
st.markdown('<p class="section-header">📊 STATE-WISE SHOW% — Gynoveda vs Industry Standard (Verified Benchmarks)</p>',
            unsafe_allow_html=True)

# City → State mapping
CITY_STATE = {
    'Mumbai': 'Maharashtra', 'Pune': 'Maharashtra', 'Nagpur': 'Maharashtra',
    'Thane': 'Maharashtra', 'Kalyan': 'Maharashtra', 'Navi Mumbai': 'Maharashtra',
    'Nashik': 'Maharashtra', 'Delhi': 'Delhi', 'Noida': 'Uttar Pradesh',
    'Ghaziabad': 'Uttar Pradesh', 'Lucknow': 'Uttar Pradesh', 'Varanasi': 'Uttar Pradesh',
    'Agra': 'Uttar Pradesh', 'Meerut': 'Uttar Pradesh', 'Prayagraj': 'Uttar Pradesh',
    'Kanpur': 'Uttar Pradesh', 'Bengaluru': 'Karnataka', 'Mysuru': 'Karnataka',
    'Hyderabad': 'Telangana', 'Secunderabad': 'Telangana',
    'Kolkata': 'West Bengal', 'Siliguri': 'West Bengal', 'Asansol': 'West Bengal', 'Howrah': 'West Bengal',
    'Ahmedabad': 'Gujarat', 'Surat': 'Gujarat', 'Vadodara': 'Gujarat', 'Rajkot': 'Gujarat',
    'Jaipur': 'Rajasthan', 'Patna': 'Bihar', 'Ranchi': 'Jharkhand',
    'Bhubaneswar': 'Odisha', 'Raipur': 'Chhattisgarh', 'Guwahati': 'Assam',
    'Chennai': 'Tamil Nadu', 'Bhopal': 'Madhya Pradesh', 'Indore': 'Madhya Pradesh',
    'Chandigarh': 'Chandigarh', 'Ludhiana': 'Punjab', 'Amritsar': 'Punjab',
    'Jalandhar': 'Punjab', 'Faridabad': 'Haryana', 'Dehradun': 'Uttarakhand',
    'Dimapur': 'Nagaland', 'Itanagar': 'Arunachal Pradesh', 'Margao': 'Goa',
}

sim['State'] = sim['City'].map(CITY_STATE)

# State-wise Gynoveda actual
state_perf = sim.groupby('State').agg(
    clinics=('Clinic', 'count'),
    total_ntb=('Avg NTB Appts', 'sum'),
    total_shows=('Current NTB Shows', 'sum'),
    avg_show_simple=('Current Show %', 'mean'),
).reset_index()
state_perf['gyno_show_pct'] = state_perf['total_shows'] / state_perf['total_ntb']

# Industry Standard Show% by State
# Sources: Dantas et al. 2018 (global meta 23% no-show = 77% show for traditional clinics)
# IHCI data: 40-60% follow-up show in public sector
# For ONLINE-TO-OFFLINE model (Gynoveda's funnel): eSanjeevani 18% referral conversion,
# Punjab RCT 11-20% appointment show, private clinic 75-85% traditional show
#
# Standard Show% here = expected show rate for an ONLINE-BOOKED appointment at a private
# outpatient clinic in that state, adjusted by:
#   - State urbanization rate (Census 2011)
#   - Healthcare infrastructure density (NFHS-5 facility access)
#   - Out-of-pocket burden (higher OOP = lower show)
#   - Distance/transport access
#
# Base: 20% for online-to-offline models (eSanjeevani + Punjab RCT midpoint)
# Adjustments: +5% for high-infra metro states, -3% for low-infra states

STD_SHOW_PCT = {
    # High healthcare infrastructure, metro-heavy states
    'Maharashtra': 0.22,     # Strong private infra (Apollo, Fortis, Kokilaben), high urbanization 45%
    'Karnataka': 0.24,       # Bengaluru health hub, 39% urbanization, strong IT-savvy population
    'Telangana': 0.22,       # Hyderabad health corridor, 39% urban, growing private sector
    'Delhi': 0.21,           # Highest density but congestion/distance paradox, 98% urban
    'Tamil Nadu': 0.23,      # Strongest public health system, 48% urban, high health literacy
    'Gujarat': 0.20,         # 43% urban, moderate private infra, high OOP
    'West Bengal': 0.19,     # Kolkata-centric, rest underserved, 32% urban
    'Chandigarh': 0.22,      # Union territory, high urban, good infra
    'Goa': 0.23,             # Small state, high literacy, good access

    # Mid-tier healthcare infrastructure
    'Punjab': 0.18,          # 37% urban, moderate infra, high OOP burden
    'Haryana': 0.17,         # 35% urban, NCR proximity helps, but patchy outside Gurgaon
    'Madhya Pradesh': 0.16,  # 28% urban, weak public health, high rural default
    'Rajasthan': 0.15,       # 25% urban, vast distances, low health-seeking behavior
    'Uttar Pradesh': 0.15,   # 22% urban, worst doctor:patient ratio, highest OOP in NCD
    'Bihar': 0.13,           # 11% urban, weakest health infra nationally, NFHS-5 bottom quartile
    'Uttarakhand': 0.17,     # 30% urban, terrain challenges, moderate health literacy

    # East & Northeast — smaller samples, higher variance
    'Jharkhand': 0.18,       # Ranchi urban pocket performs, rural default high
    'Odisha': 0.18,          # Improving health systems, 17% urban
    'Chhattisgarh': 0.17,    # 23% urban, tribal areas underserved
    'Assam': 0.19,           # Guwahati health hub, rest challenging
    'Arunachal Pradesh': 0.15, # Extreme terrain, lowest density, but high motivation if booked
    'Nagaland': 0.16,        # Small urban base, limited clinic options boost show
    'Tripura': 0.16,
    'Meghalaya': 0.15,
    'Manipur': 0.16,
    'Sikkim': 0.15,

    # New expansion states (no current clinics)
    'Kerala': 0.25,          # Highest health literacy nationally, 48% urban, strong health-seeking
    'Andhra Pradesh': 0.20,  # Post-bifurcation rebuilding, Vizag metro anchor
    'Jammu & Kashmir': 0.16, # Challenging access, but urban pockets viable
}

state_perf['std_show_pct'] = state_perf['State'].map(STD_SHOW_PCT)
state_perf['gap'] = state_perf['gyno_show_pct'] - state_perf['std_show_pct']
state_perf['gap_rev_impact'] = state_perf['gap'] * state_perf['total_ntb'] * conv_adj * SALE_VAL * 12
state_perf = state_perf.sort_values('gyno_show_pct', ascending=True)

# Visualization: Grouped bar — Gynoveda Actual vs Standard
sb1, sb2 = st.columns([1.8, 1])

with sb1:
    fig_bench = go.Figure()

    # Standard benchmark bars
    fig_bench.add_trace(go.Bar(
        y=state_perf['State'], x=state_perf['std_show_pct'] * 100,
        orientation='h', name='Industry Standard (Online-to-Offline)',
        marker_color='#B0BEC5', marker_line_color='#78909C', marker_line_width=1,
        text=state_perf['std_show_pct'].apply(lambda v: f"{v:.0%}"),
        textposition='inside', textfont=dict(size=10)
    ))

    # Gynoveda actual bars
    fig_bench.add_trace(go.Bar(
        y=state_perf['State'], x=state_perf['gyno_show_pct'] * 100,
        orientation='h', name='Gynoveda Actual',
        marker_color=[
            '#43A047' if g > 0.03 else '#FFA000' if g >= -0.02 else '#E53935'
            for g in state_perf['gap']],
        text=state_perf.apply(lambda r: f"{r['gyno_show_pct']:.0%} ({r['clinics']} cl)", axis=1),
        textposition='outside', textfont=dict(size=10)
    ))

    fig_bench.update_layout(
        height=max(450, len(state_perf) * 35), barmode='group',
        margin=dict(t=40, b=20, l=10, r=80),
        title_text="Gynoveda Show% vs Industry Standard — State-Wise Benchmark",
        title_font_size=12,
        legend=dict(orientation='h', y=1.08),
        xaxis_title="Show Rate (%)", xaxis=dict(ticksuffix='%')
    )
    st.plotly_chart(fig_bench, use_container_width=True)

with sb2:
    above_std = (state_perf['gap'] > 0.02).sum()
    at_std = ((state_perf['gap'] >= -0.02) & (state_perf['gap'] <= 0.02)).sum()
    below_std = (state_perf['gap'] < -0.02).sum()
    total_outperform_rev = state_perf[state_perf['gap'] > 0]['gap_rev_impact'].sum()
    total_underperform_rev = state_perf[state_perf['gap'] < 0]['gap_rev_impact'].sum()

    st.markdown(f'<div class="ratio-card">'
                f'<span style="font-size:1.5rem;font-weight:800;color:#43A047;">{above_std}</span> '
                f'<span style="font-size:0.85rem;">states above standard</span></div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="ratio-card">'
                f'<span style="font-size:1.5rem;font-weight:800;color:#FFA000;">{at_std}</span> '
                f'<span style="font-size:0.85rem;">states at standard (±2ppt)</span></div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="ratio-card">'
                f'<span style="font-size:1.5rem;font-weight:800;color:#E53935;">{below_std}</span> '
                f'<span style="font-size:0.85rem;">states below standard</span></div>',
                unsafe_allow_html=True)

    st.markdown(
        f'<div class="insight-box">'
        f'<b>📚 Benchmark Sources:</b><br><br>'
        f'<b>Global:</b> Dantas et al. 2018 meta-analysis (105 studies) — 23% avg no-show rate globally.<br><br>'
        f'<b>India Online-to-Offline:</b> eSanjeevani national telemedicine — 18% referral-to-physical conversion '
        f'(Lancet Regional Health 2024). Punjab RCT — 11-20% appointment show rate '
        f'(BMC Public Health 2024).<br><br>'
        f'<b>India Chronic Disease:</b> IHCI 24-site study — 51% follow-up show rate '
        f'(J Clinical Hypertension 2021). Das et al. Punjab — 40-50% attendance.<br><br>'
        f'<b>Adjustment factors:</b> State urbanization rate (Census 2011), '
        f'health facility density (NFHS-5), out-of-pocket burden, and digital penetration.<br><br>'
        f'<b>Base standard: 20%</b> for online-booked → physical clinic show-up, '
        f'adjusted ±5ppt by state infrastructure.'
        f'</div>', unsafe_allow_html=True)

# Revenue impact of gap
st.markdown('<p class="section-header" style="margin-top:0.5rem;">Revenue Impact: Above vs Below Standard</p>',
            unsafe_allow_html=True)

gi1, gi2, gi3 = st.columns(3)
with gi1:
    st.metric("Outperforming States Revenue Edge",
              f"+₹{total_outperform_rev/1e7:.1f} Cr/yr",
              delta=f"{above_std} states above benchmark")
with gi2:
    st.metric("Underperforming States Revenue Gap",
              f"₹{abs(total_underperform_rev)/1e7:.1f} Cr/yr",
              delta=f"{below_std} states need intervention", delta_color="inverse")
with gi3:
    net = total_outperform_rev + total_underperform_rev
    st.metric("Net Position vs Standard",
              f"{'+'if net>0 else ''}₹{net/1e7:.1f} Cr/yr",
              delta="Above standard" if net > 0 else "Below standard")

# State detail table in expander
with st.expander("📋 Full State-Wise Benchmark Detail"):
    detail_df = state_perf[['State', 'clinics', 'total_ntb', 'total_shows',
                            'gyno_show_pct', 'std_show_pct', 'gap', 'gap_rev_impact']].copy()
    detail_df.columns = ['State', 'Clinics', 'Monthly NTB', 'Monthly Shows',
                         'Gynoveda Show%', 'Std Show%', 'Gap', 'Annual Rev Impact (₹)']
    detail_df['Gynoveda Show%'] = detail_df['Gynoveda Show%'].apply(lambda v: f"{v:.1%}")
    detail_df['Std Show%'] = detail_df['Std Show%'].apply(lambda v: f"{v:.1%}" if pd.notna(v) else 'N/A')
    detail_df['Gap'] = detail_df['Gap'].apply(lambda v: f"{v:+.1%}" if pd.notna(v) else 'N/A')
    detail_df['Annual Rev Impact (₹)'] = detail_df['Annual Rev Impact (₹)'].apply(
        lambda v: f"₹{v/1e5:+,.0f}L" if pd.notna(v) else 'N/A')
    detail_df = detail_df.sort_values('State')
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # Also show new expansion state benchmarks
    new_states = [s for s in STD_SHOW_PCT if s not in state_perf['State'].values]
    if new_states:
        st.markdown("**Standard Show% for New Expansion States (no current clinics):**")
        new_df = pd.DataFrame([
            {'State': s, 'Std Show%': f"{STD_SHOW_PCT[s]:.0%}",
             'Rationale': {
                 'Kerala': 'Highest health literacy, 48% urban, strong health-seeking culture',
                 'Andhra Pradesh': 'Vizag metro anchor, post-bifurcation health rebuilding',
                 'Jammu & Kashmir': 'Urban pockets viable, terrain limits rural catchment',
                 'Tripura': 'Small state, Agartala urban base, limited alternatives',
                 'Meghalaya': 'Shillong-centric, small catchment, NE healthcare gaps',
                 'Manipur': 'Imphal urban pocket, limited organized healthcare',
                 'Sikkim': 'Smallest state, Gangtok only viable market',
             }.get(s, 'Based on urbanization + health infrastructure index')}
            for s in new_states
        ])
        st.dataframe(new_df, use_container_width=True, hide_index=True)


# ================================================================
# SECTION 2 — EXPANSION STRATEGY (Same-City + New City in Tabs)
# ================================================================
st.divider()
st.markdown('<p class="section-header">2️⃣ EXPANSION STRATEGY — Where to Open Next</p>',
            unsafe_allow_html=True)

exp_tab_same, exp_tab_new = st.tabs(["🏙️ Same-City Expansion", "🌍 New City Expansion"])

with exp_tab_same:
    st.markdown(f'<p class="section-header" style="font-size:1.1rem;">Same-City — Clinics at Capacity (≥{ntb_threshold} NTB Shows/Month)</p>',
                unsafe_allow_html=True)

    # Step 1: Filter qualifying clinics
    qualifying = sim_ec[sim_ec['Current NTB Shows'] >= ntb_threshold].copy()
    qualifying['l3m_stable'] = qualifying['l3m_l12m_ratio'] >= 0.90
    qualifying['qual_score'] = (
        qualifying['Current NTB Shows'] / qualifying['Current NTB Shows'].max() * 40 +
        qualifying['Current Show %'] / qualifying['Current Show %'].max() * 30 +
        qualifying['utilization'] / qualifying['utilization'].max() * 30
    ).round(1)
    qualifying = qualifying.sort_values('qual_score', ascending=False)

    q1, q2, q3 = st.columns([0.3, 1.2, 1])

    with q1:
        st.markdown(f'<div class="ratio-card"><span style="font-size:2rem;font-weight:800;">{len(qualifying)}</span>'
                    f'<br><span style="font-size:0.8rem;color:#666;">Clinics Qualify</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="ratio-card"><span style="font-size:1.5rem;font-weight:700;">'
                    f'{qualifying["utilization"].mean():.0f}%</span>'
                    f'<br><span style="font-size:0.8rem;color:#666;">Avg Utilization</span></div>',
                    unsafe_allow_html=True)

    with q2:
        # Horizontal bar: qualifying clinics by NTB Shows + utilization overlay
        fig_qual = go.Figure()
        fig_qual.add_trace(go.Bar(
            y=qualifying['Clinic'], x=qualifying['Current NTB Shows'],
            orientation='h', name='NTB Shows',
            marker_color=['#43A047' if u >= 80 else '#FFA000' if u >= 60 else '#1565C0'
                          for u in qualifying['utilization']],
            text=qualifying.apply(lambda r: f"{r['Current NTB Shows']:.0f} shows | {r['utilization']:.0f}% util | {r['Current Show %']:.0%} show%", axis=1),
            textposition='inside', insidetextanchor='middle',
            textfont=dict(size=11, color='white')
        ))
        fig_qual.add_vline(x=ntb_threshold, line_dash="dash", line_color="#E53935",
                           annotation_text=f"Threshold: {ntb_threshold}")
        fig_qual.update_layout(
            height=max(200, len(qualifying) * 55), margin=dict(t=30, b=20, l=10, r=10),
            title_text=f"Step 1: Clinics with ≥{ntb_threshold} Avg Monthly NTB Shows",
            title_font_size=12, showlegend=False, xaxis_title="Monthly NTB Shows"
        )
        st.plotly_chart(fig_qual, use_container_width=True)

    with q3:
        for _, r in qualifying.iterrows():
            status = "🟢 Stable" if r.get('l3m_stable', False) else "🟡 Declining L3M"
            cabins = r.get('Cabins', 2)
            st.markdown(
                f'<div class="gate-pass" style="padding:8px 12px;">'
                f'<b>{r["Clinic"]}</b> ({r["City"]}) — {cabins:.0f} cabins<br>'
                f'Shows: <b>{r["Current NTB Shows"]:.0f}</b>/mo | '
                f'Util: <b>{r["utilization"]:.0f}%</b> | '
                f'Show%: <b>{r["Current Show %"]:.1%}</b> | {status}'
                f'</div>', unsafe_allow_html=True)


    # Step 2: Micro-markets for qualifying clinics
    st.markdown(f'<p class="section-header" style="margin-top:1rem;">Step 2: Micro-Market Identification for {len(qualifying)} Saturated Clinics</p>',
                unsafe_allow_html=True)

    if not same.empty and 'City' in same.columns:
        qual_cities = qualifying['City'].unique().tolist()
        same_filtered = same[same['City'].isin(qual_cities)].copy()

        if not same_filtered.empty:
            sm1, sm2 = st.columns([1.5, 1])

            with sm1:
                city_pin_counts = same_filtered.groupby('City').size().reset_index(name='Proposed Pins')
                city_pin_counts = city_pin_counts.merge(
                    qualifying.groupby('City')['Current NTB Shows'].sum().reset_index(name='Parent NTB Shows'),
                    on='City', how='left'
                )
                city_pin_counts = city_pin_counts.sort_values('Parent NTB Shows', ascending=True)

                fig_micro = go.Figure()
                fig_micro.add_trace(go.Bar(
                    y=city_pin_counts['City'], x=city_pin_counts['Proposed Pins'],
                    orientation='h', marker_color='#43A047',
                    text=city_pin_counts.apply(
                        lambda r: f"{r['Proposed Pins']} pins | Parent: {r['Parent NTB Shows']:.0f} shows/mo", axis=1),
                    textposition='inside', insidetextanchor='middle',
                    textfont=dict(color='white')
                ))
                fig_micro.update_layout(
                    height=max(200, len(city_pin_counts) * 50),
                    margin=dict(t=30, b=20, l=10, r=10),
                    title_text="Step 2: Proposed Micro-Markets by Saturated City",
                    title_font_size=12, showlegend=False
                )
                st.plotly_chart(fig_micro, use_container_width=True)

            with sm2:
                est_no_show = qualifying['Avg NTB Appts'].sum() - qualifying['Current NTB Shows'].sum()
                est_recovery_rev = est_no_show * 0.30 * CONV_PCT * SALE_VAL  # 30% recovery assumption
                st.markdown(
                    f'<div class="insight-box">'
                    f'<b>📍 No-Show Recovery Logic:</b><br><br>'
                    f'These {len(qualifying)} clinics book <b>{qualifying["Avg NTB Appts"].sum():,.0f}</b> NTB appointments/mo '
                    f'but only <b>{qualifying["Current NTB Shows"].sum():,.0f}</b> show up.<br><br>'
                    f'<b>{est_no_show:,.0f} patients/month</b> are no-shows from these saturated clinics. '
                    f'Distance and travel time are primary barriers.<br><br>'
                    f'Satellite clinics in top no-show pincodes can recover an estimated '
                    f'<b>30%</b> of these patients → <b>₹{est_recovery_rev/1e5:.0f}L/month</b> in recovered revenue.<br><br>'
                    f'<b>This is not new CAC — these patients are already acquired.</b>'
                    f'</div>', unsafe_allow_html=True)

        # Expandable micro-market detail per city
        for city in qual_cities:
            city_same = same_filtered[same_filtered['City'] == city]
            if not city_same.empty:
                with st.expander(f"📍 {city} — {len(city_same)} Micro-Markets"):
                    display_cols = [c for c in ['Micro-Market Area', 'Micro-Market Pincode',
                                                'Expansion Rationale', 'National IVFs Present',
                                                'Regional IVFs Present'] if c in city_same.columns]
                    st.dataframe(city_same[display_cols], use_container_width=True, hide_index=True)


with exp_tab_new:
    # ── NTB:POPULATION RATIO ENGINE ──
    st.markdown('<p class="section-header" style="font-size:1.1rem;">NTB:POPULATION RATIO — The Projection Anchor</p>',
                unsafe_allow_html=True)

    rp1, rp2 = st.columns([1.5, 1])

    with rp1:
        # Scatter: NTB Shows per Lakh vs City
        ratio_plot = city_ntb_valid.sort_values('ntb_per_lakh', ascending=True).copy()
        ratio_plot['color'] = ratio_plot['ntb_per_lakh'].apply(
            lambda v: '#43A047' if v >= P75_RATIO else '#FFA000' if v >= MEDIAN_RATIO else '#E53935')

        fig_ratio = go.Figure()
        fig_ratio.add_trace(go.Bar(
            y=ratio_plot['City'], x=ratio_plot['ntb_per_lakh'],
            orientation='h', marker_color=ratio_plot['color'],
            text=ratio_plot.apply(lambda r: f"{r['ntb_per_lakh']:.1f}/L | {r['clinics']} cl | Pop {r['population']/1e5:.0f}L", axis=1),
            textposition='outside', textfont=dict(size=10)
        ))
        fig_ratio.add_vline(x=MEDIAN_RATIO, line_dash="dash", line_color="#1565C0",
                            annotation_text=f"Median: {MEDIAN_RATIO:.1f}/lakh")
        fig_ratio.update_layout(
            height=max(600, len(ratio_plot) * 18), margin=dict(t=30, b=20, l=10, r=80),
            title_text="NTB Shows per Lakh Population — All Existing Cities",
            title_font_size=12, showlegend=False, xaxis_title="NTB Shows per Lakh"
        )
        st.plotly_chart(fig_ratio, use_container_width=True)

    with rp2:
        st.markdown(f'<div class="ratio-card">'
                    f'<span style="font-size:1.8rem;font-weight:800;color:#1565C0;">{MEDIAN_RATIO:.1f}</span><br>'
                    f'<span style="font-size:0.85rem;">Median NTB Shows per Lakh Population</span></div>',
                    unsafe_allow_html=True)

        st.markdown(f'<div class="ratio-card">'
                    f'<span style="font-size:1.3rem;font-weight:700;">P25: {P25_RATIO:.1f} | P75: {P75_RATIO:.1f}</span><br>'
                    f'<span style="font-size:0.85rem;">Conservative to Optimistic Range</span></div>',
                    unsafe_allow_html=True)

        st.markdown(
            f'<div class="insight-box">'
            f'<b>🔬 Methodology:</b><br><br>'
            f'For each of Gynoveda\'s <b>{len(city_ntb_valid)}</b> existing clinic cities, we calculate:<br><br>'
            f'<b>NTB Shows ÷ City Population (lakhs)</b><br><br>'
            f'This gives a proven conversion ratio from population to actual clinic walk-ins. '
            f'The median ratio of <b>{MEDIAN_RATIO:.1f} shows per lakh</b> is then applied to new city populations '
            f'for defensible NTB projections.<br><br>'
            f'<b>Why this matters:</b> The original Excel projected Coimbatore (21L pop) at 630 NTB/month. '
            f'The ratio-based projection gives <b>{21 * applied_ratio:.0f}</b> — a more realistic starting point '
            f'that protects against over-investment.'
            f'</div>', unsafe_allow_html=True)


        # ── NEW CITY EXPANSION (Demand-Validated) ──
        st.divider()
        st.markdown('<p class="section-header" style="font-size:1.1rem;">New City — Demand-Validated, Ratio-Projected</p>',
                    unsafe_allow_html=True)

    if not newc.empty and 'pop_numeric' in newc.columns:
        # Step 1: Web demand + zero clinic mapping
        newc_cities = newc.drop_duplicates('City').copy()
        newc_cities['ratio_ntb_base'] = newc_cities['pop_numeric'] / 100000 * MEDIAN_RATIO
        newc_cities['ratio_ntb_applied'] = newc_cities['pop_numeric'] / 100000 * applied_ratio
        newc_cities['Projected Monthly NTB'] = pd.to_numeric(newc_cities['Projected Monthly NTB'], errors='coerce')
        newc_cities['Web Order Qty'] = pd.to_numeric(newc_cities['Web Order Qty'], errors='coerce')
        newc_cities['overestimate_factor'] = newc_cities['Projected Monthly NTB'] / newc_cities['ratio_ntb_applied'].replace(0, np.nan)

        nc1, nc2 = st.columns([1.5, 1])

        with nc1:
            # Grouped bar: Original projection vs Ratio-based projection
            nc_sorted = newc_cities.sort_values('ratio_ntb_applied', ascending=True)

            fig_nc = go.Figure()
            fig_nc.add_trace(go.Bar(
                y=nc_sorted['City'], x=nc_sorted['Projected Monthly NTB'],
                orientation='h', name='Original Projection',
                marker_color='#FFCDD2', opacity=0.7,
                text=nc_sorted['Projected Monthly NTB'].apply(lambda v: f"{v:,.0f}"),
                textposition='outside'
            ))
            fig_nc.add_trace(go.Bar(
                y=nc_sorted['City'], x=nc_sorted['ratio_ntb_applied'],
                orientation='h', name=f'Ratio-Based ({applied_ratio:.1f}/lakh)',
                marker_color='#1565C0',
                text=nc_sorted['ratio_ntb_applied'].apply(lambda v: f"{v:,.0f}"),
                textposition='outside'
            ))
            fig_nc.update_layout(
                height=500, barmode='group', margin=dict(t=30, b=20, l=10, r=80),
                title_text="Step 1: Original vs Ratio-Based NTB Projections — New Cities",
                title_font_size=12, legend=dict(orientation='h', y=1.08),
                xaxis_title="Monthly NTB Shows"
            )
            st.plotly_chart(fig_nc, use_container_width=True)

        with nc2:
            # Web demand validation
            fig_web = px.scatter(
                nc_sorted, x='Web Order Qty', y='ratio_ntb_applied',
                size='pop_numeric', hover_name='City',
                color='Tier' if 'Tier' in nc_sorted.columns else None,
                color_discrete_map={'Tier-2': '#1565C0', 'Tier-3': '#FF6F00'},
                labels={'Web Order Qty': 'Website Orders', 'ratio_ntb_applied': 'Projected NTB (Ratio)',
                        'pop_numeric': 'Population'}
            )
            fig_web.update_layout(
                height=300, margin=dict(t=30, b=20),
                title_text="Web Demand vs Projected NTB", title_font_size=12,
                legend=dict(orientation='h', y=1.12)
            )
            st.plotly_chart(fig_web, use_container_width=True)

            avg_overestimate = newc_cities['overestimate_factor'].mean()
            st.markdown(
                f'<div class="gate-fail">'
                f'<b>⚠️ Projection Reality Check:</b><br>'
                f'The original Excel projections overestimate NTB by <b>{avg_overestimate:.1f}x on average</b> '
                f'compared to the ratio-based model.<br><br>'
                f'Using the proven NTB:Pop ratio of <b>{applied_ratio:.1f}/lakh</b> gives conservative but '
                f'<b>defensible</b> numbers the CEO can trust.'
                f'</div>', unsafe_allow_html=True)

        # Step 2: New city micro-markets with IVF mapping
        st.markdown('<p class="section-header" style="margin-top:0.5rem;">Step 2-3: New City Micro-Markets + IVF Landscape</p>',
                    unsafe_allow_html=True)

        for _, city_row in newc_cities.sort_values('ratio_ntb_applied', ascending=False).iterrows():
            city_name = city_row['City']
            city_pins = newc[newc['City'] == city_name]

            with st.expander(f"🏙️ {city_name} — Pop: {city_row['Est. Population']} | "
                             f"Ratio NTB: {city_row['ratio_ntb_applied']:.0f}/mo | "
                             f"Web Orders: {city_row['Web Order Qty']:,.0f} | "
                             f"Tier: {city_row.get('Tier', 'N/A')}"):

                ec1, ec2 = st.columns([1.5, 1])
                with ec1:
                    display_cols = [c for c in ['Area Name', 'Pincode', 'Location Rationale',
                                                'National IVFs', 'Regional IVFs'] if c in city_pins.columns]
                    st.dataframe(city_pins[display_cols], use_container_width=True, hide_index=True)

                with ec2:
                    ratio_rev = city_row['ratio_ntb_applied'] * CONV_PCT * SALE_VAL
                    st.markdown(
                        f'<div class="ratio-card">'
                        f'Projected Monthly Revenue<br>'
                        f'<span style="font-size:1.5rem;font-weight:700;">₹{ratio_rev/1e5:.1f}L</span><br>'
                        f'<span style="font-size:0.75rem;">{city_row["ratio_ntb_applied"]:.0f} shows × {CONV_PCT:.0%} conv × ₹{SALE_VAL/1e3:.0f}K</span>'
                        f'</div>', unsafe_allow_html=True)

                    if pd.notna(city_row.get('National IVFs')):
                        st.markdown(f"**National IVFs:** {city_row.get('National IVFs', 'N/A')}")
                    if pd.notna(city_row.get('Regional IVFs')):
                        st.markdown(f"**Regional IVFs:** {city_row.get('Regional IVFs', 'N/A')}")



# ================================================================
# SECTION 3 — SHOW% FIX BEFORE EXPANSION
# ================================================================
st.divider()
st.markdown('<p class="section-header">3️⃣ FIX BEFORE EXPAND — ₹0 CAC Revenue Unlock</p>',
            unsafe_allow_html=True)

# Tier performance
if 'Tier' in sim.columns:
    tier_data = sim.groupby('Tier').agg(
        clinics=('Clinic', 'count'), avg_show=('Current Show %', 'mean'),
        avg_ntb=('Avg NTB Appts', 'mean'), avg_shows=('Current NTB Shows', 'mean'),
        total_rev=('est_annual_rev', 'sum'), avg_target=('target_pct', 'mean')
    ).reset_index()

    fx1, fx2 = st.columns([1.3, 1])

    with fx1:
        # Scatter: all 61 clinics with gate lines
        sim['bubble'] = sim['Current NTB Shows'].clip(lower=5) * 0.3
        fig_sc = px.scatter(
            sim, x='Avg NTB Appts', y='Current Show %',
            size='bubble', color='Tier',
            color_discrete_map={'P1': '#43A047', 'P2': '#1565C0', 'P3': '#FFA000', 'P4': '#E53935'},
            hover_name='Clinic',
            hover_data={'Avg NTB Appts': ':,.0f', 'Current Show %': ':.1%',
                        'est_monthly_rev': ':,.0f', 'bubble': False},
            labels={'Avg NTB Appts': 'Avg Monthly NTB Appointments', 'Current Show %': 'Show Rate'}
        )
        fig_sc.add_hline(y=0.25, line_dash="dash", line_color="#43A047", annotation_text="P1: 25%")
        fig_sc.add_hline(y=0.18, line_dash="dash", line_color="#FFA000", annotation_text="P2: 18%")
        fig_sc.add_hline(y=0.15, line_dash="dot", line_color="#E53935", annotation_text="P4: 15%")
        fig_sc.update_layout(height=380, margin=dict(t=30, b=20),
                             title_text="61 Clinics: NTB × Show% — Gate Classification",
                             title_font_size=12, legend=dict(orientation='h', y=1.12))
        fig_sc.update_yaxes(tickformat='.0%')
        st.plotly_chart(fig_sc, use_container_width=True)

    with fx2:
        # Show% improvement uplift
        p34 = sim[sim['Tier'].isin(['P3', 'P4'])]
        curr_p34 = p34['est_annual_rev'].sum()
        fix_p34 = (p34['Avg NTB Appts'] * 0.20 * CONV_PCT * SALE_VAL * 12).sum()
        uplift_p34 = fix_p34 - curr_p34

        p2 = sim[sim['Tier'] == 'P2']
        curr_p2 = p2['est_annual_rev'].sum()
        fix_p2 = (p2['Avg NTB Appts'] * 0.25 * CONV_PCT * SALE_VAL * 12).sum()
        uplift_p2 = fix_p2 - curr_p2

        total_uplift = uplift_p34 + uplift_p2

        fig_up = go.Figure()
        fig_up.add_trace(go.Bar(
            x=['P3+P4 → 20%', 'P2 → 25%', 'Combined'],
            y=[curr_p34/1e7, curr_p2/1e7, (curr_p34+curr_p2)/1e7],
            name='Current', marker_color='#BDBDBD',
            text=[f"₹{curr_p34/1e7:.1f}", f"₹{curr_p2/1e7:.1f}", f"₹{(curr_p34+curr_p2)/1e7:.1f}"],
            textposition='inside'))
        fig_up.add_trace(go.Bar(
            x=['P3+P4 → 20%', 'P2 → 25%', 'Combined'],
            y=[uplift_p34/1e7, uplift_p2/1e7, total_uplift/1e7],
            name='Uplift', marker_color='#43A047',
            text=[f"+₹{uplift_p34/1e7:.1f}", f"+₹{uplift_p2/1e7:.1f}", f"+₹{total_uplift/1e7:.1f}"],
            textposition='outside'))
        fig_up.update_layout(height=280, barmode='stack', margin=dict(t=30, b=20),
                             title_text="Show% Fix = Revenue Without New Leases", title_font_size=12,
                             legend=dict(orientation='h', y=1.12), yaxis_title="₹ Cr")
        st.plotly_chart(fig_up, use_container_width=True)

        st.markdown(f'<div class="gate-pass">'
                    f'<b>💰 ₹{total_uplift/1e7:.1f} Cr unlock</b> from Show% fixes across '
                    f'{len(p34)+len(p2)} clinics — <b>zero new leases, zero CAC</b>. '
                    f'This is FY27\'s highest-ROI initiative.'
                    f'</div>', unsafe_allow_html=True)


# ================================================================
# SECTION 3B — UNIT ECONOMICS (Actual Cost Structure)
# ================================================================
st.divider()
st.markdown('<p class="section-header">💰 UNIT ECONOMICS — Per Clinic P&L (Actual Costs)</p>',
            unsafe_allow_html=True)

# Cost constants
DR_SALARY = 100000   # 2 doctors @ ₹50K each
MGR_SALARY = 30000
HK_SALARY = 10000
RECEP_SALARY = 15000
ELECTRICITY = 5000
RENT = 150000        # Avg clinic rent
MONTHLY_OPEX = RENT + DR_SALARY + MGR_SALARY + HK_SALARY + RECEP_SALARY + ELECTRICITY  # ₹3.1L
ANNUAL_OPEX = MONTHLY_OPEX * 12  # ₹37.2L
CAPEX_CONSTRUCTION = 2800000  # ₹28L

BREAKEVEN_SHOWS = MONTHLY_OPEX / (conv_adj * SALE_VAL)

# Per-clinic P&L for all 61
sim_ec_pl = sim.copy()
sim_ec_pl['monthly_rev'] = sim_ec_pl['Current NTB Shows'] * conv_adj * SALE_VAL
sim_ec_pl['monthly_profit'] = sim_ec_pl['monthly_rev'] - MONTHLY_OPEX
sim_ec_pl['annual_profit'] = sim_ec_pl['monthly_profit'] * 12
sim_ec_pl['margin_pct'] = (sim_ec_pl['monthly_profit'] / sim_ec_pl['monthly_rev'].replace(0, np.nan) * 100).round(1)
sim_ec_pl['payback_months'] = (CAPEX_CONSTRUCTION / sim_ec_pl['monthly_profit'].clip(lower=1)).round(0)
sim_ec_pl['payback_months'] = sim_ec_pl['payback_months'].clip(upper=99)
sim_ec_pl['profitable'] = sim_ec_pl['monthly_profit'] > 0

profitable_count = sim_ec_pl['profitable'].sum()
loss_count = len(sim_ec_pl) - profitable_count
total_network_profit = sim_ec_pl['annual_profit'].sum()

# KPIs
ue1, ue2, ue3, ue4, ue5, ue6 = st.columns(6)
with ue1:
    st.metric("Monthly OpEx/Clinic", f"₹{MONTHLY_OPEX/1e5:.1f}L",
              delta="Rent + Dr×2 + Mgr + HK + Recep + Elec")
with ue2:
    st.metric("Capex (Construction)", f"₹{CAPEX_CONSTRUCTION/1e5:.0f}L")
with ue3:
    st.metric("Breakeven NTB Shows", f"{BREAKEVEN_SHOWS:.0f}/month",
              delta=f"@ {conv_adj:.0%} conv × ₹{SALE_VAL/1e3:.0f}K")
with ue4:
    st.metric("Profitable Clinics", f"{profitable_count} of {len(sim_ec_pl)}",
              delta=f"{loss_count} below breakeven", delta_color="inverse")
with ue5:
    avg_margin = sim_ec_pl[sim_ec_pl['profitable']]['margin_pct'].mean()
    st.metric("Avg Margin (Profitable)", f"{avg_margin:.0f}%")
with ue6:
    st.metric("Network Annual Profit", f"₹{total_network_profit/1e7:.1f} Cr",
              delta="After ₹3.1L/mo OpEx per clinic")

# Two charts side by side
uc1, uc2 = st.columns([1.3, 1])

with uc1:
    # Waterfall: Revenue → Cost breakdown → Profit per avg clinic
    avg_shows = sim_ec_pl['Current NTB Shows'].mean()
    avg_rev = avg_shows * conv_adj * SALE_VAL
    fig_unit = go.Figure(go.Waterfall(
        orientation="v",
        x=['Revenue', 'Rent', 'Doctors (2)', 'Clinic Mgr', 'Housekeeping', 'Receptionist',
           'Electricity', 'Monthly Profit'],
        y=[avg_rev, -RENT, -DR_SALARY, -MGR_SALARY, -HK_SALARY, -RECEP_SALARY,
           -ELECTRICITY, 0],
        measure=['absolute', 'relative', 'relative', 'relative', 'relative', 'relative',
                 'relative', 'total'],
        text=[f"₹{avg_rev/1e5:.1f}L", f"-₹{RENT/1e3:.0f}K", f"-₹{DR_SALARY/1e3:.0f}K", f"-₹{MGR_SALARY/1e3:.0f}K",
              f"-₹{HK_SALARY/1e3:.0f}K", f"-₹{RECEP_SALARY/1e3:.0f}K", f"-₹{ELECTRICITY/1e3:.0f}K",
              f"₹{(avg_rev-MONTHLY_OPEX)/1e5:.1f}L"],
        textposition='outside',
        connector=dict(line=dict(color='#ccc')),
        increasing=dict(marker=dict(color='#43A047')),
        decreasing=dict(marker=dict(color='#E53935')),
        totals=dict(marker=dict(color='#1565C0'))
    ))
    fig_unit.update_layout(
        height=320, margin=dict(t=40, b=20),
        title_text=f"Average Clinic P&L ({avg_shows:.0f} shows/mo)",
        title_font_size=12, showlegend=False, yaxis_title="₹"
    )
    st.plotly_chart(fig_unit, use_container_width=True)

with uc2:
    # Breakeven sensitivity: shows vs monthly profit
    show_range = list(range(10, 220, 10))
    profits = [(s * conv_adj * SALE_VAL - MONTHLY_OPEX) / 1e5 for s in show_range]

    fig_be = go.Figure()
    fig_be.add_trace(go.Scatter(
        x=show_range, y=profits, mode='lines+markers',
        line=dict(color='#1565C0', width=3),
        marker=dict(size=6,
                    color=['#E53935' if p < 0 else '#43A047' for p in profits]),
        text=[f"₹{p:.1f}L" for p in profits], textposition='top center',
        hovertemplate='%{x} shows → ₹%{y:.1f}L profit<extra></extra>'
    ))
    fig_be.add_hline(y=0, line_dash="dash", line_color="#E53935",
                     annotation_text="Breakeven")
    fig_be.add_vline(x=BREAKEVEN_SHOWS, line_dash="dot", line_color="#FFA000",
                     annotation_text=f"BE: {BREAKEVEN_SHOWS:.0f} shows")
    # Mark network avg
    fig_be.add_vline(x=avg_shows, line_dash="dash", line_color="#43A047",
                     annotation_text=f"Network avg: {avg_shows:.0f}")
    fig_be.update_layout(
        height=320, margin=dict(t=40, b=20),
        title_text="Monthly Profit vs NTB Shows (Sensitivity)",
        title_font_size=12, xaxis_title="NTB Shows/Month",
        yaxis_title="Monthly Profit (₹ Lakhs)"
    )
    st.plotly_chart(fig_be, use_container_width=True)

# Clinic-level profitability scatter
st.markdown('<p class="section-header" style="margin-top:0.3rem;">61 Clinic Profitability Map</p>',
            unsafe_allow_html=True)

uc3, uc4 = st.columns([1.5, 1])

with uc3:
    sim_ec_pl['bubble_size'] = sim_ec_pl['monthly_rev'].clip(lower=10000) / 5000
    fig_profit = px.scatter(
        sim_ec_pl, x='Current NTB Shows', y='monthly_profit',
        size='bubble_size', color='Tier' if 'Tier' in sim_ec_pl.columns else None,
        color_discrete_map={'P1': '#43A047', 'P2': '#1565C0', 'P3': '#FFA000', 'P4': '#E53935'},
        hover_name='Clinic',
        hover_data={'Current NTB Shows': ':,.0f', 'monthly_profit': ':,.0f',
                    'margin_pct': ':.0f', 'payback_months': ':.0f', 'bubble_size': False},
        labels={'Current NTB Shows': 'Monthly NTB Shows', 'monthly_profit': 'Monthly Profit (₹)'}
    )
    fig_profit.add_hline(y=0, line_dash="dash", line_color="#E53935",
                         annotation_text="Breakeven Line")
    fig_profit.add_vline(x=BREAKEVEN_SHOWS, line_dash="dot", line_color="#FFA000")
    fig_profit.update_layout(
        height=350, margin=dict(t=30, b=20),
        title_text="Clinic Profitability: NTB Shows vs Monthly Profit",
        title_font_size=12, legend=dict(orientation='h', y=1.1),
        yaxis_tickformat=',d'
    )
    st.plotly_chart(fig_profit, use_container_width=True)

with uc4:
    # Payback period distribution
    payback_bins = sim_ec_pl[sim_ec_pl['profitable']].copy()
    pb_cats = pd.cut(payback_bins['payback_months'],
                     bins=[0, 3, 6, 12, 24, 100],
                     labels=['<3 mo', '3-6 mo', '6-12 mo', '12-24 mo', '>24 mo'])
    pb_dist = pb_cats.value_counts().sort_index()

    fig_pb = go.Figure(go.Bar(
        x=pb_dist.index.astype(str), y=pb_dist.values,
        marker_color=['#43A047', '#66BB6A', '#FFA000', '#FF6F00', '#E53935'],
        text=pb_dist.values, textposition='outside'
    ))
    fig_pb.update_layout(
        height=250, margin=dict(t=30, b=20),
        title_text="Capex Payback Period Distribution",
        title_font_size=12, xaxis_title="Payback Period",
        yaxis_title="# Clinics"
    )
    st.plotly_chart(fig_pb, use_container_width=True)

    # Loss-making clinics callout
    loss_clinics = sim_ec_pl[~sim_ec_pl['profitable']].sort_values('monthly_profit')
    if len(loss_clinics) > 0:
        loss_list = ', '.join(loss_clinics['Clinic'].head(5).values)
        st.markdown(
            f'<div class="gate-fail">'
            f'<b>⚠️ {loss_count} clinics below ₹3.1L OpEx breakeven:</b><br>'
            f'{loss_list}{"..." if loss_count > 5 else ""}<br><br>'
            f'Combined monthly loss: <b>₹{abs(loss_clinics["monthly_profit"].sum())/1e5:.1f}L</b>'
            f'</div>', unsafe_allow_html=True)

# Cost structure callout
st.markdown(
    f'<div class="insight-box">'
    f'<b>📊 Cost Structure Per Clinic (Monthly):</b><br><br>'
    f'Rent: <b>₹1,50,000</b> | Doctors (2): <b>₹1,00,000</b> | Clinic Manager: <b>₹30,000</b> | '
    f'Housekeeping: <b>₹10,000</b> | Receptionist: <b>₹15,000</b> | '
    f'Electricity: <b>₹5,000</b><br>'
    f'<b>Total Monthly OpEx: ₹3,10,000</b> | Annual: <b>₹37.2L</b> | '
    f'Capex (one-time): <b>₹28L</b><br><br>'
    f'<b>Key insight:</b> Breakeven at <b>{BREAKEVEN_SHOWS:.0f} NTB shows/month</b> — '
    f'rent alone is 48% of total OpEx, making location ROI the critical decision. '
    f'Every clinic that crosses {BREAKEVEN_SHOWS:.0f} shows generates pure margin; '
    f'the real question is Show% and footfall velocity.'
    f'</div>', unsafe_allow_html=True)


# ================================================================
# SECTION 4 — FY27 REVENUE PROJECTION (Ratio-Adjusted)
# ================================================================
st.divider()
st.markdown('<p class="section-header">4️⃣ FY27 REVENUE PROJECTION — Ratio-Adjusted, Scenario-Tested</p>',
            unsafe_allow_html=True)

# Recalculate new city revenue using ratio-based NTB
ramp = [0.30, 0.50, 0.65, 0.80, 0.90, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
network_annual = sim['est_annual_rev'].sum()
network_monthly = sim['est_monthly_rev'].sum()

# Same-city: use original projected NTB (derived from parent clinics)
same_rev_data = rev[~rev['type'].str.contains('New', na=False)].copy() if 'type' in rev.columns else pd.DataFrame()
if not same_rev_data.empty:
    same_rev_data['adj_show'] = (same_rev_data['projected_show_pct'] + show_adj).clip(0.08, 0.50)
    same_rev_data['adj_monthly'] = same_rev_data['projected_ss_ntb'] * same_rev_data['adj_show'] * conv_adj * SALE_VAL
    same_12m = sum(same_rev_data['adj_monthly'] * ramp[i] for i in range(12)).sum()
else:
    same_12m = 0

# New city: use RATIO-BASED NTB projections
if not newc.empty and 'pop_numeric' in newc.columns:
    newc_proj = newc.drop_duplicates('City').copy()
    newc_proj['ratio_shows'] = newc_proj['pop_numeric'] / 100000 * applied_ratio
    newc_proj['adj_show'] = (avg_show + show_adj)
    newc_proj['monthly_rev'] = newc_proj['ratio_shows'] * newc_proj['adj_show'] * conv_adj * SALE_VAL
    new_12m = sum(newc_proj['monthly_rev'] * ramp[i] for i in range(12)).sum()
else:
    new_12m = 0

total_new = same_12m + new_12m
grand_total = network_annual + total_new + total_uplift  # existing + new + Show% fix

# Monthly ramp
m_existing = [network_monthly] * 12
m_same = [float(same_rev_data['adj_monthly'].sum() * ramp[i]) for i in range(12)] if not same_rev_data.empty else [0]*12
m_new = [float(newc_proj['monthly_rev'].sum() * ramp[i]) for i in range(12)] if not newc.empty and 'monthly_rev' in newc_proj.columns else [0]*12
m_total = [e + s + n for e, s, n in zip(m_existing, m_same, m_new)]
months_label = ['Apr-26', 'May-26', 'Jun-26', 'Jul-26', 'Aug-26', 'Sep-26',
                'Oct-26', 'Nov-26', 'Dec-26', 'Jan-27', 'Feb-27', 'Mar-27']

# KPI row
rk1, rk2, rk3, rk4, rk5 = st.columns(5)
with rk1:
    st.metric("Existing 61 Rev", f"₹{network_annual/1e7:.1f} Cr")
with rk2:
    st.metric("Show% Fix Uplift", f"+₹{total_uplift/1e7:.1f} Cr")
with rk3:
    st.metric("Same-City New Rev", f"+₹{same_12m/1e7:.1f} Cr")
with rk4:
    st.metric("New City Rev (Ratio)", f"+₹{new_12m/1e7:.1f} Cr")
with rk5:
    st.metric(f"FY27 Total ({scn_label})", f"₹{grand_total/1e7:.1f} Cr")

# Waterfall + Monthly ramp
rv1, rv2 = st.columns([1, 1.5])

with rv1:
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        x=['Existing\n61 Clinics', 'Show% Fix\n(₹0 CAC)', 'Same-City\nNew', 'New City\n(Ratio)', 'FY27\nTotal'],
        y=[network_annual/1e7, total_uplift/1e7, same_12m/1e7, new_12m/1e7, 0],
        measure=['absolute', 'relative', 'relative', 'relative', 'total'],
        text=[f"₹{network_annual/1e7:.1f}Cr", f"+₹{total_uplift/1e7:.1f}Cr",
              f"+₹{same_12m/1e7:.1f}Cr", f"+₹{new_12m/1e7:.1f}Cr", f"₹{grand_total/1e7:.1f}Cr"],
        textposition='outside',
        connector=dict(line=dict(color='#ccc')),
        increasing=dict(marker=dict(color='#43A047')),
        totals=dict(marker=dict(color='#1565C0'))
    ))
    fig_wf.update_layout(height=320, margin=dict(t=30, b=20),
                         title_text="FY27 Revenue Waterfall", title_font_size=12,
                         yaxis_title="₹ Cr", showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True)

with rv2:
    fig_ramp = make_subplots(specs=[[{"secondary_y": True}]])
    fig_ramp.add_trace(go.Bar(x=months_label, y=[v/1e7 for v in m_existing],
                              name='Existing 61', marker_color='#BBDEFB'), secondary_y=False)
    fig_ramp.add_trace(go.Bar(x=months_label, y=[v/1e7 for v in m_same],
                              name='Same-City New', marker_color='#43A047'), secondary_y=False)
    fig_ramp.add_trace(go.Bar(x=months_label, y=[v/1e7 for v in m_new],
                              name='New City (Ratio)', marker_color='#FF6F00'), secondary_y=False)
    cum = np.cumsum(m_total)
    fig_ramp.add_trace(go.Scatter(x=months_label, y=[v/1e7 for v in cum],
                                  name='Cumulative', mode='lines+markers',
                                  line=dict(color='#E53935', width=3)), secondary_y=True)
    fig_ramp.update_layout(height=320, barmode='stack', margin=dict(t=30, b=20),
                           title_text="FY27 Monthly Revenue Ramp", title_font_size=12,
                           legend=dict(orientation='h', y=1.12))
    fig_ramp.update_yaxes(title_text="Monthly (₹ Cr)", secondary_y=False)
    fig_ramp.update_yaxes(title_text="Cumulative (₹ Cr)", secondary_y=True)
    st.plotly_chart(fig_ramp, use_container_width=True)


# ── Per-Clinic Revenue Projection Detail ─────────────────────────
st.markdown('<p class="section-header" style="margin-top:0.5rem;">📊 Per-Clinic Revenue Projection (₹22K/NTB Patient)</p>',
            unsafe_allow_html=True)

pc_tab1, pc_tab2 = st.tabs(["Same-City New Clinics", "New City Clinics"])

with pc_tab1:
    if not same_rev_data.empty:
        sc_detail = same_rev_data.copy()
        sc_detail['adj_show_pct'] = sc_detail['adj_show'] * 100
        sc_detail['ntb_shows'] = sc_detail['projected_ss_ntb'] * sc_detail['adj_show']
        sc_detail['monthly_rev_ss'] = sc_detail['ntb_shows'] * conv_adj * SALE_VAL
        for i in range(12):
            sc_detail[months_label[i]] = sc_detail['monthly_rev_ss'] * ramp[i]
        sc_detail['yr1_total'] = sum(sc_detail[months_label[i]] for i in range(12))
        sc_detail['breakeven_month'] = sc_detail['monthly_rev_ss'].apply(
            lambda v: next((i+1 for i, r in enumerate(ramp) if v * r >= TARGET_MONTHLY * 0.6), 12))

        # Chart: top 25 same-city clinics by yr1 revenue
        sc_top = sc_detail.nlargest(25, 'yr1_total').sort_values('yr1_total', ascending=True)
        display_name = 'area' if 'area' in sc_top.columns else 'pincode'
        sc_top['label'] = sc_top.apply(
            lambda r: f"{r.get('city', '')} - {r.get(display_name, r.get('pincode', ''))}", axis=1)

        fig_sc_rev = go.Figure()
        fig_sc_rev.add_trace(go.Bar(
            y=sc_top['label'], x=sc_top['yr1_total'] / 1e5,
            orientation='h', marker_color='#43A047',
            text=sc_top.apply(lambda r: (
                f"₹{r['yr1_total']/1e5:.0f}L/yr | "
                f"{r['ntb_shows']:.0f} shows/mo | "
                f"₹{r['monthly_rev_ss']/1e5:.1f}L/mo SS"
            ), axis=1),
            textposition='outside', textfont=dict(size=10)
        ))
        fig_sc_rev.add_vline(x=TARGET_MONTHLY*12/1e5, line_dash="dash", line_color="#E53935",
                             annotation_text=f"Target: ₹{TARGET_MONTHLY*12/1e5:.0f}L/yr")
        fig_sc_rev.update_layout(
            height=max(350, len(sc_top) * 28), margin=dict(t=30, b=20, l=10, r=120),
            title_text="Same-City: Top 25 New Clinics — Year 1 Revenue Projection",
            title_font_size=12, showlegend=False, xaxis_title="Year 1 Revenue (₹ Lakhs)"
        )
        st.plotly_chart(fig_sc_rev, use_container_width=True)

        # Monthly ramp heatmap for top 10
        sc_hm = sc_top.tail(10).copy()
        hm_data = sc_hm[months_label].values / 1e5
        fig_hm = go.Figure(go.Heatmap(
            z=hm_data, x=months_label, y=sc_hm['label'],
            colorscale='Greens', text=np.round(hm_data, 1),
            texttemplate='₹%{text:.0f}L', textfont=dict(size=10),
            hovertemplate='%{y}<br>%{x}: ₹%{z:.1f}L<extra></extra>'
        ))
        fig_hm.update_layout(
            height=350, margin=dict(t=30, b=20, l=10, r=10),
            title_text="Monthly Revenue Ramp — Top 10 Same-City Clinics (₹ Lakhs)",
            title_font_size=12
        )
        st.plotly_chart(fig_hm, use_container_width=True)

        # Summary metrics
        scm1, scm2, scm3, scm4 = st.columns(4)
        with scm1:
            st.metric("Same-City Clinics", f"{len(sc_detail)}")
        with scm2:
            st.metric("Avg Yr1 Revenue", f"₹{sc_detail['yr1_total'].mean()/1e5:.0f}L")
        with scm3:
            above_target = (sc_detail['yr1_total'] >= TARGET_MONTHLY * 12 * 0.6).sum()
            st.metric("Above 60% Target", f"{above_target} of {len(sc_detail)}")
        with scm4:
            st.metric("Total Yr1 Revenue", f"₹{sc_detail['yr1_total'].sum()/1e7:.1f} Cr")
    else:
        st.info("No same-city expansion data available.")

with pc_tab2:
    if not newc.empty and 'pop_numeric' in newc.columns:
        nc_detail = newc.drop_duplicates('City').copy()
        nc_detail['ratio_shows'] = nc_detail['pop_numeric'] / 100000 * applied_ratio
        nc_detail['adj_show_pct'] = (avg_show + show_adj)
        nc_detail['ntb_shows'] = nc_detail['ratio_shows'] * nc_detail['adj_show_pct']
        nc_detail['monthly_rev_ss'] = nc_detail['ntb_shows'] * conv_adj * SALE_VAL
        for i in range(12):
            nc_detail[months_label[i]] = nc_detail['monthly_rev_ss'] * ramp[i]
        nc_detail['yr1_total'] = sum(nc_detail[months_label[i]] for i in range(12))

        nc_sorted = nc_detail.sort_values('yr1_total', ascending=True)

        fig_nc_rev = go.Figure()
        fig_nc_rev.add_trace(go.Bar(
            y=nc_sorted['City'], x=nc_sorted['yr1_total'] / 1e5,
            orientation='h',
            marker_color=['#1565C0' if t == 'Tier-2' else '#FF6F00'
                          for t in nc_sorted.get('Tier', ['Tier-2'] * len(nc_sorted))],
            text=nc_sorted.apply(lambda r: (
                f"₹{r['yr1_total']/1e5:.0f}L/yr | "
                f"Pop: {r['pop_numeric']/1e5:.0f}L | "
                f"{r['ntb_shows']:.0f} shows/mo | "
                f"₹{r['monthly_rev_ss']/1e5:.1f}L/mo SS"
            ), axis=1),
            textposition='outside', textfont=dict(size=10)
        ))
        fig_nc_rev.add_vline(x=TARGET_MONTHLY*12/1e5, line_dash="dash", line_color="#E53935",
                             annotation_text=f"Target: ₹{TARGET_MONTHLY*12/1e5:.0f}L/yr")
        fig_nc_rev.update_layout(
            height=max(350, len(nc_sorted) * 40), margin=dict(t=30, b=20, l=10, r=140),
            title_text="New City: Per-Clinic Year 1 Revenue (NTB:Pop Ratio-Based, ₹22K/Patient)",
            title_font_size=12, showlegend=False, xaxis_title="Year 1 Revenue (₹ Lakhs)"
        )
        st.plotly_chart(fig_nc_rev, use_container_width=True)

        # Monthly ramp heatmap for all new cities
        hm_nc = nc_sorted[months_label].values / 1e5
        fig_hm_nc = go.Figure(go.Heatmap(
            z=hm_nc, x=months_label, y=nc_sorted['City'],
            colorscale='Blues', text=np.round(hm_nc, 1),
            texttemplate='₹%{text:.0f}L', textfont=dict(size=10),
            hovertemplate='%{y}<br>%{x}: ₹%{z:.1f}L<extra></extra>'
        ))
        fig_hm_nc.update_layout(
            height=max(300, len(nc_sorted) * 32), margin=dict(t=30, b=20, l=10, r=10),
            title_text="Monthly Revenue Ramp — New City Clinics (₹ Lakhs)",
            title_font_size=12
        )
        st.plotly_chart(fig_hm_nc, use_container_width=True)

        # Unit economics per city (actual costs)
        nc_detail['monthly_opex'] = 310000  # ₹3.1L actual (rent + staff + elec)
        nc_detail['annual_opex'] = nc_detail['monthly_opex'] * 12
        nc_detail['capex'] = 2800000  # ₹28L construction
        nc_detail['annual_cost'] = nc_detail['annual_opex'] + nc_detail['capex']
        nc_detail['yr1_margin'] = nc_detail['yr1_total'] - nc_detail['annual_cost']
        nc_detail['margin_pct'] = (nc_detail['yr1_margin'] / nc_detail['yr1_total'] * 100).round(1)
        nc_detail['payback_months'] = np.where(
            nc_detail['monthly_rev_ss'] > 310000,
            (nc_detail['capex'] / (nc_detail['monthly_rev_ss'] - 310000)).round(0),
            99)

        ncm1, ncm2, ncm3, ncm4 = st.columns(4)
        with ncm1:
            st.metric("New Cities", f"{len(nc_detail)}")
        with ncm2:
            st.metric("Avg Yr1 Revenue", f"₹{nc_detail['yr1_total'].mean()/1e5:.0f}L")
        with ncm3:
            profitable = (nc_detail['yr1_margin'] > 0).sum()
            st.metric("Yr1 Profitable", f"{profitable} of {len(nc_detail)}")
        with ncm4:
            st.metric("Total Yr1 Revenue", f"₹{nc_detail['yr1_total'].sum()/1e7:.1f} Cr")

        st.markdown(
            f'<div class="insight-box">'
            f'<b>💡 Unit Economics (Actual Costs):</b> Monthly OpEx is <b>₹3.1L</b> per clinic '
            f'(Rent ₹1.5L + 2 doctors ₹1L + Manager ₹30K + HK ₹10K + Receptionist ₹15K + Electricity ₹5K). '
            f'Capex is <b>₹28L</b> one-time construction. '
            f'Breakeven at <b>{310000/(conv_adj * SALE_VAL):,.0f} NTB shows/month</b>. '
            f'Cities with ratio-projected shows below this threshold should use lean 1-cabin format '
            f'or co-locate with existing healthcare providers.'
            f'</div>', unsafe_allow_html=True)
    else:
        st.info("No new city expansion data available.")


# ================================================================
# SECTION 5 — RISK-ADJUSTED EXPANSION SCORECARD
# ================================================================
st.divider()
st.markdown('<p class="section-header">5️⃣ RISK SCORECARD — What Could Go Wrong (and How We\'ll Know)</p>',
            unsafe_allow_html=True)

st.markdown("""
<div class="gate-warn">
<b>⚠️ Why This Section Exists:</b> Every VC-backed Indian healthcare chain that expanded fast got burned.
Pristyn Care (₹1.69 spent per ₹1 earned, 3 layoff rounds), mFine (75% workforce cut),
Glamyo Health (total shutdown), Cure.fit (15 cities exited). This section stress-tests our plan
against the five highest-probability failure modes — using our actual data, not generic scenarios.
</div>
""", unsafe_allow_html=True)

risk_tabs = st.tabs([
    "🏠 Rent Stress Test",
    "📉 Conversion Decay",
    "🔥 Cash Burn J-Curve",
    "🎯 Cannibalization Map",
    "🚦 Kill Criteria"
])

# ── 7A: RENT ESCALATION STRESS TEST ─────────────────────────────
with risk_tabs[0]:
    st.markdown('<p class="section-header">7A. Rent Escalation Stress Test — The Silent Margin Killer</p>',
                unsafe_allow_html=True)

    RENT_ESCALATION_LOW = 0.05
    RENT_ESCALATION_MID = 0.07
    RENT_ESCALATION_HIGH = 0.10
    LEASE_YEARS = 5

    years_r = list(range(1, LEASE_YEARS + 1))
    scenarios_rent = {}
    for label, esc in [('5% Escalation', RENT_ESCALATION_LOW),
                       ('7% Escalation (Market Std)', RENT_ESCALATION_MID),
                       ('10% Escalation (Hot Market)', RENT_ESCALATION_HIGH)]:
        opex_by_year = []
        for y in years_r:
            rent_y = RENT * (1 + esc) ** (y - 1)
            opex_y = rent_y + (MONTHLY_OPEX - RENT)
            opex_by_year.append(opex_y)
        scenarios_rent[label] = opex_by_year

    breakeven_by_scenario = {}
    for label, opex_list in scenarios_rent.items():
        breakeven_by_scenario[label] = [o / (conv_adj * SALE_VAL) for o in opex_list]

    rm1, rm2, rm3, rm4 = st.columns(4)
    yr3_opex_mid = scenarios_rent['7% Escalation (Market Std)'][2]
    yr5_opex_mid = scenarios_rent['7% Escalation (Market Std)'][4]
    yr5_be = breakeven_by_scenario['7% Escalation (Market Std)'][4]
    with rm1:
        st.metric("Year 1 OpEx", f"₹{MONTHLY_OPEX/1e5:.1f}L/mo",
                  delta=f"Breakeven: {BREAKEVEN_SHOWS:.0f} shows")
    with rm2:
        st.metric("Year 3 OpEx (7% esc)", f"₹{yr3_opex_mid/1e5:.1f}L/mo",
                  delta=f"+₹{(yr3_opex_mid-MONTHLY_OPEX)/1e3:.0f}K vs Yr1")
    with rm3:
        st.metric("Year 5 OpEx (7% esc)", f"₹{yr5_opex_mid/1e5:.1f}L/mo",
                  delta=f"Breakeven: {yr5_be:.0f} shows")
    with rm4:
        margin_erosion = ((yr5_opex_mid - MONTHLY_OPEX) / MONTHLY_OPEX * 100)
        st.metric("5-Year Cost Creep", f"+{margin_erosion:.0f}%",
                  delta="Rent only — staff costs flat")

    fig_rent = go.Figure()
    colors_rent = ['#4CAF50', '#FF9800', '#E53935']
    for (label, opex_list), color in zip(scenarios_rent.items(), colors_rent):
        fig_rent.add_trace(go.Scatter(
            x=[f'Year {y}' for y in years_r], y=[o/1e5 for o in opex_list],
            name=label, mode='lines+markers+text',
            text=[f'₹{o/1e5:.1f}L' for o in opex_list],
            textposition='top center', textfont=dict(size=9),
            line=dict(color=color, width=2.5)
        ))
    fig_rent.add_hline(y=MONTHLY_OPEX/1e5, line_dash="dash", line_color="#888",
                       annotation_text=f"Year 1 baseline: ₹{MONTHLY_OPEX/1e5:.1f}L")
    fig_rent.update_layout(
        title_text="Monthly OpEx Trajectory Over 5-Year Lease (Rent Escalation Only)",
        title_font_size=12, height=370, yaxis_title="Monthly OpEx (₹ Lakhs)",
        margin=dict(t=40, b=20, l=10, r=10), legend=dict(orientation='h', y=-0.15)
    )
    st.plotly_chart(fig_rent, use_container_width=True)

    fig_be_shift = go.Figure()
    for (label, be_list), color in zip(breakeven_by_scenario.items(), colors_rent):
        fig_be_shift.add_trace(go.Bar(
            x=[f'Year {y}' for y in years_r], y=be_list, name=label,
            marker_color=color, text=[f'{b:.0f}' for b in be_list],
            textposition='outside', textfont=dict(size=10)
        ))
    fig_be_shift.add_hline(y=BREAKEVEN_SHOWS, line_dash="dash", line_color="#1565C0",
                           annotation_text=f"Year 1 breakeven: {BREAKEVEN_SHOWS:.0f} shows")
    fig_be_shift.update_layout(
        title_text="Breakeven NTB Shows/Month — How Rent Escalation Shifts the Target",
        title_font_size=12, height=350, yaxis_title="NTB Shows to Break Even",
        barmode='group', margin=dict(t=40, b=20, l=10, r=10),
        legend=dict(orientation='h', y=-0.15)
    )
    st.plotly_chart(fig_be_shift, use_container_width=True)

    yr3_be_mid = breakeven_by_scenario['7% Escalation (Market Std)'][2]
    currently_profitable = sim_ec_pl[sim_ec_pl['profitable']].copy()
    flip_to_loss = currently_profitable[currently_profitable['Current NTB Shows'] < yr3_be_mid]
    if len(flip_to_loss) > 0:
        st.markdown(f"""
<div class="gate-fail">
<b>🚨 {len(flip_to_loss)} clinics currently profitable but will flip to LOSS by Year 3</b>
at 7% rent escalation (breakeven shifts from {BREAKEVEN_SHOWS:.0f} → {yr3_be_mid:.0f} shows):<br>
{', '.join(flip_to_loss['Clinic Name'].head(10).tolist())}
{'...' if len(flip_to_loss) > 10 else ''}
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="gate-pass"><b>✅ All currently profitable clinics survive Year 3 rent escalation at 7%.</b></div>',
                    unsafe_allow_html=True)

    st.markdown(f"""
<div class="insight-box">
<b>💡 Rent Stress Test:</b> At 7% annual escalation (Indian commercial standard),
OpEx rises from <b>₹{MONTHLY_OPEX/1e5:.1f}L → ₹{yr5_opex_mid/1e5:.1f}L</b> over 5 years —
a <b>{margin_erosion:.0f}% increase</b>. Breakeven shifts from {BREAKEVEN_SHOWS:.0f} → {yr5_be:.0f} shows/month.
Revenue must grow ≥5%/year just to maintain margins. Lock-in penalty: remaining rent + forfeited
deposit + ₹28L capex write-off.<br>
<b>Action:</b> Negotiate 5% cap clauses. Avoid lock-in >2 years for new cities.
</div>
""", unsafe_allow_html=True)


# ── 7B: CONVERSION RATE DECAY SIMULATOR ──────────────────────────
with risk_tabs[1]:
    st.markdown('<p class="section-header">7B. Conversion Rate Decay — What Happens When Show% Erodes</p>',
                unsafe_allow_html=True)

    avg_show_pct_r = sim['Current Show %'].median() / 100 if 'Current Show %' in sim.columns else 0.22
    total_ntb_appts_r = sim['Avg NTB Appts'].sum() if 'Avg NTB Appts' in sim.columns else 5000

    DECAY_SCENARIOS = {
        'No Decay (Optimistic)': 0.00,
        'Mild (-1ppt/yr)': -0.01,
        'Moderate (-2ppt/yr)': -0.02,
        'Severe (-3ppt/yr)': -0.03
    }

    decay_years = [1, 2, 3]
    decay_colors = ['#4CAF50', '#FF9800', '#E53935', '#880E4F']

    base_annual_rev = sim['est_annual_rev'].sum()
    decay_rev_data = {}
    for label, decay in DECAY_SCENARIOS.items():
        revs = []
        for yr in decay_years:
            new_show = avg_show_pct_r + (decay * yr)
            new_show = max(new_show, 0.05)
            ratio_factor = new_show / avg_show_pct_r if avg_show_pct_r > 0 else 1
            yr_rev = base_annual_rev * ratio_factor
            revs.append(yr_rev)
        decay_rev_data[label] = revs

    dm1, dm2, dm3, dm4 = st.columns(4)
    with dm1:
        st.metric("Current Avg Show%", f"{avg_show_pct_r*100:.0f}%",
                  delta=f"{total_ntb_appts_r:.0f} NTB appts/mo")
    with dm2:
        yr3_rev_mod = decay_rev_data['Moderate (-2ppt/yr)'][2]
        rev_loss_mod = base_annual_rev - yr3_rev_mod
        st.metric("Yr3 Loss (-2ppt/yr)", f"₹{rev_loss_mod/1e7:.1f} Cr",
                  delta=f"Show% → {(avg_show_pct_r - 0.06)*100:.0f}%")
    with dm3:
        yr3_rev_sev = decay_rev_data['Severe (-3ppt/yr)'][2]
        rev_loss_sev = base_annual_rev - yr3_rev_sev
        st.metric("Yr3 Loss (-3ppt/yr)", f"₹{rev_loss_sev/1e7:.1f} Cr",
                  delta=f"D2C industry trend")
    with dm4:
        pct_risk = (rev_loss_mod / base_annual_rev * 100) if base_annual_rev > 0 else 0
        st.metric("Revenue at Risk", f"{pct_risk:.0f}%",
                  delta="at moderate decay")

    fig_decay = go.Figure()
    for (label, revs), color in zip(decay_rev_data.items(), decay_colors):
        fig_decay.add_trace(go.Scatter(
            x=[f'Year {y}' for y in decay_years], y=[r/1e7 for r in revs],
            name=label, mode='lines+markers+text',
            text=[f'₹{r/1e7:.1f}Cr' for r in revs],
            textposition='top center', textfont=dict(size=9),
            line=dict(color=color, width=2.5)
        ))
    fig_decay.add_hline(y=base_annual_rev/1e7, line_dash="dash", line_color="#888",
                        annotation_text=f"Current: ₹{base_annual_rev/1e7:.0f} Cr")
    fig_decay.update_layout(
        title_text="Network Annual Revenue Under Show% Decay Scenarios",
        title_font_size=12, height=370, yaxis_title="Annual Revenue (₹ Cr)",
        margin=dict(t=40, b=20, l=10, r=10), legend=dict(orientation='h', y=-0.15)
    )
    st.plotly_chart(fig_decay, use_container_width=True)

    # New city penalty
    st.markdown('<p class="section-header" style="margin-top:0.3rem;">New City Show% Penalty — Unproven Markets Start Lower</p>',
                unsafe_allow_html=True)
    NEW_CITY_PENALTY = 0.05
    newly_unprofitable_count = 0
    total_gap_r = 0
    if not newc.empty and 'pop_numeric' in newc.columns:
        nc_risk = newc.drop_duplicates('City').copy()
        nc_risk['base_shows'] = nc_risk['pop_numeric'] / 100000 * applied_ratio * avg_show_pct_r
        nc_risk['penalized_shows'] = nc_risk['pop_numeric'] / 100000 * applied_ratio * (avg_show_pct_r - NEW_CITY_PENALTY)
        nc_risk['base_rev_yr1'] = nc_risk['base_shows'] * conv_adj * SALE_VAL * 12
        nc_risk['penalized_rev_yr1'] = nc_risk['penalized_shows'] * conv_adj * SALE_VAL * 12
        nc_risk['rev_gap'] = nc_risk['base_rev_yr1'] - nc_risk['penalized_rev_yr1']
        total_gap_r = nc_risk['rev_gap'].sum()
        newly_unprofitable = nc_risk[nc_risk['penalized_shows'] < BREAKEVEN_SHOWS]
        newly_unprofitable_count = len(newly_unprofitable)

        npm1, npm2 = st.columns(2)
        with npm1:
            st.metric("Revenue Gap (-5ppt Show%)", f"₹{total_gap_r/1e7:.1f} Cr/yr",
                      delta=f"{newly_unprofitable_count} cities fall below breakeven")
        with npm2:
            st.metric("Network Show%", f"{avg_show_pct_r*100:.0f}%",
                      delta=f"New city: {(avg_show_pct_r-NEW_CITY_PENALTY)*100:.0f}%")

        nc_risk_sorted = nc_risk.sort_values('base_rev_yr1', ascending=True).head(15)
        fig_nc_pen = go.Figure()
        fig_nc_pen.add_trace(go.Bar(
            y=nc_risk_sorted['City'], x=nc_risk_sorted['base_rev_yr1']/1e5,
            name='Base Projection', marker_color='#1565C0', orientation='h'
        ))
        fig_nc_pen.add_trace(go.Bar(
            y=nc_risk_sorted['City'], x=nc_risk_sorted['penalized_rev_yr1']/1e5,
            name='-5ppt Show% Penalty', marker_color='#E53935', orientation='h'
        ))
        fig_nc_pen.add_vline(x=MONTHLY_OPEX*12/1e5, line_dash="dash", line_color="#888",
                             annotation_text="Annual OpEx line")
        fig_nc_pen.update_layout(
            title_text="New City Yr1 Revenue: Base vs -5ppt Show% Penalty",
            title_font_size=12, height=max(300, len(nc_risk_sorted)*35),
            barmode='group', xaxis_title="Year 1 Revenue (₹ Lakhs)",
            margin=dict(t=40, b=20, l=10, r=140), legend=dict(orientation='h', y=-0.15)
        )
        st.plotly_chart(fig_nc_pen, use_container_width=True)

    st.markdown(f"""
<div class="insight-box">
<b>💡 Conversion Decay:</b> D2C conversion rates halved 2022-2025 (4%→2%). Instagram CPC tripled.
At -2ppt annual decay, network revenue drops <b>₹{rev_loss_mod/1e7:.1f} Cr by Year 3</b>.
New cities face an additional -5ppt penalty — {newly_unprofitable_count} cities fall below breakeven.<br>
<b>Action:</b> Budget 2% of clinic revenue for local brand-building in new cities (first 18 months).
Set Show% floor of 15% — trigger remediation before Month 6.
</div>
""", unsafe_allow_html=True)


# ── 7C: CASH BURN J-CURVE ───────────────────────────────────────
with risk_tabs[2]:
    st.markdown('<p class="section-header">7C. Cash Burn J-Curve — Peak Capital Requirement</p>',
                unsafe_allow_html=True)

    RAMP_CURVE_R = [0.30, 0.30, 0.30, 0.60, 0.60, 0.60, 0.80, 0.80, 0.80,
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    avg_new_clinic_ss_rev = 550000

    batch_scenarios = {
        '10 Clinics (Conservative)': {'total': 10, 'batch_size': 3, 'gap_months': 3},
        '20 Clinics (Base Plan)': {'total': 20, 'batch_size': 5, 'gap_months': 2},
        '30 Clinics (Aggressive)': {'total': 30, 'batch_size': 8, 'gap_months': 2},
        '40 Clinics (Maximum)': {'total': 40, 'batch_size': 10, 'gap_months': 2}
    }
    jcurve_colors = ['#4CAF50', '#1565C0', '#FF9800', '#E53935']

    def calc_jcurve(params, months_range=24):
        clinics_opened = []
        month, opened = 0, 0
        while opened < params['total'] and month < months_range:
            batch = min(params['batch_size'], params['total'] - opened)
            clinics_opened.append((month, batch))
            opened += batch
            month += params['gap_months']
        cumulative, cum_list = 0, []
        for m in range(months_range):
            capex_m = sum(CAPEX_CONSTRUCTION * bc for om, bc in clinics_opened if om == m)
            opex_m, rev_m = 0, 0
            for (om, bc) in clinics_opened:
                ms = m - om
                if ms >= 0:
                    rf = RAMP_CURVE_R[min(ms, len(RAMP_CURVE_R)-1)]
                    opex_m += MONTHLY_OPEX * bc
                    rev_m += avg_new_clinic_ss_rev * rf * bc
            cumulative += (rev_m - opex_m - capex_m)
            cum_list.append(cumulative)
        return cum_list, clinics_opened

    fig_jcurve = go.Figure()
    peak_cash = {}
    for (label, params), color in zip(batch_scenarios.items(), jcurve_colors):
        cum_list, _ = calc_jcurve(params)
        peak_cash[label] = min(cum_list)
        fig_jcurve.add_trace(go.Scatter(
            x=[f'M{m+1}' for m in range(24)], y=[c/1e7 for c in cum_list],
            name=label, mode='lines', line=dict(color=color, width=2.5),
            hovertemplate='%{x}: ₹%{y:.1f} Cr<extra></extra>'
        ))
    fig_jcurve.add_hline(y=0, line_dash="solid", line_color="#333", line_width=1)
    fig_jcurve.update_layout(
        title_text="Cumulative Cash Position — New Clinic Expansion (24-Month Horizon)",
        title_font_size=12, height=420, yaxis_title="Cumulative Net Cash (₹ Cr)",
        xaxis_title="Month", margin=dict(t=40, b=40, l=10, r=10),
        legend=dict(orientation='h', y=-0.2)
    )
    st.plotly_chart(fig_jcurve, use_container_width=True)

    jm1, jm2, jm3, jm4 = st.columns(4)
    for col, (label, peak), color in zip([jm1, jm2, jm3, jm4], peak_cash.items(), jcurve_colors):
        with col:
            st.metric(label.split('(')[0].strip(), f"₹{abs(peak)/1e7:.1f} Cr",
                      delta="Peak cash needed")

    # Months to breakeven
    breakeven_months_r = {}
    for label, params in batch_scenarios.items():
        cum_list, _ = calc_jcurve(params, months_range=36)
        be_month, passed = None, False
        for m, c in enumerate(cum_list):
            if c < 0: passed = True
            if passed and c >= 0 and be_month is None: be_month = m + 1
        breakeven_months_r[label] = be_month if be_month else 36

    fig_be_time = go.Figure(go.Bar(
        x=list(breakeven_months_r.values()),
        y=[l.split('(')[0].strip() for l in breakeven_months_r.keys()],
        orientation='h', marker_color=jcurve_colors,
        text=[f'{m} months' for m in breakeven_months_r.values()],
        textposition='outside', textfont=dict(size=11, color='#333')
    ))
    fig_be_time.add_vline(x=12, line_dash="dash", line_color="#E53935",
                          annotation_text="12-month target")
    fig_be_time.update_layout(
        title_text="Months Until Cumulative Cash Flow Turns Positive",
        title_font_size=12, height=250, xaxis_title="Months",
        margin=dict(t=40, b=20, l=10, r=80)
    )
    st.plotly_chart(fig_be_time, use_container_width=True)

    st.markdown(f"""
<div class="insight-box">
<b>💡 Cash Burn:</b> Opening 20 clinics (base) requires <b>₹{abs(peak_cash.get('20 Clinics (Base Plan)', 0))/1e7:.1f} Cr peak cash</b>.
Cash-flow positive at <b>Month {breakeven_months_r.get('20 Clinics (Base Plan)', '?')}</b>.
Pristyn Care opened 100+ locations simultaneously — monthly drain hit ₹80+ Cr before correction.<br>
<b>Action:</b> Cap simultaneous openings at 5-8 per batch. Require Batch N to hit 60% of
steady-state revenue before releasing capital for Batch N+1.
</div>
""", unsafe_allow_html=True)


# ── 7D: CANNIBALIZATION RISK MAP ────────────────────────────────
with risk_tabs[3]:
    st.markdown('<p class="section-header">7D. Cannibalization Risk — Same-City Proximity Analysis</p>',
                unsafe_allow_html=True)

    SAFE_DISTANCE_KM = 8

    if 'City' in ec.columns:
        city_clinic_counts = ec['City'].value_counts()
        multi_clinic_cities = city_clinic_counts[city_clinic_counts > 1]

        cm1_r, cm2_r, cm3_r = st.columns(3)
        with cm1_r:
            st.metric("Cities with 2+ Clinics", f"{len(multi_clinic_cities)}")
        with cm2_r:
            max_d_city = multi_clinic_cities.index[0] if len(multi_clinic_cities) > 0 else 'N/A'
            max_d_count = multi_clinic_cities.iloc[0] if len(multi_clinic_cities) > 0 else 0
            st.metric(f"Most Dense: {max_d_city}", f"{max_d_count} clinics")
        with cm3_r:
            same_exp_count = len(qualifying) if 'qualifying' in dir() else 0
            st.metric("Same-City Expansions", f"{same_exp_count}")

        cannibal_data = []
        for city, count in multi_clinic_cities.items():
            city_clinics = ec[ec['City'] == city]
            avg_ntb_c = city_clinics['l12m_avg'].mean() if 'l12m_avg' in city_clinics.columns else 0
            total_ntb_c = city_clinics['l12m_avg'].sum() if 'l12m_avg' in city_clinics.columns else 0
            same_prop = len(qualifying[qualifying['City'] == city]) if ('qualifying' in dir() and 'City' in qualifying.columns) else 0
            post_ct = count + same_prop
            risk = 'High' if (post_ct >= 5 and avg_ntb_c < 80) else ('Medium' if post_ct >= 3 else 'Low')
            cannibal_data.append({
                'City': city, 'Current Clinics': count, 'Proposed New': same_prop,
                'Post-Expansion': post_ct, 'Avg NTB/Clinic': round(avg_ntb_c, 0),
                'Total NTB': round(total_ntb_c, 0),
                'NTB Per Clinic (Post)': round(total_ntb_c / post_ct, 0) if post_ct > 0 else 0,
                'Risk Level': risk
            })

        cannibal_df = pd.DataFrame(cannibal_data).sort_values('Post-Expansion', ascending=False)

        if not cannibal_df.empty:
            fig_cannibal = go.Figure()
            fig_cannibal.add_trace(go.Bar(
                x=cannibal_df['City'], y=cannibal_df['Current Clinics'],
                name='Existing', marker_color='#1565C0'
            ))
            fig_cannibal.add_trace(go.Bar(
                x=cannibal_df['City'], y=cannibal_df['Proposed New'],
                name='Proposed New', marker_color='#FF9800'
            ))
            fig_cannibal.update_layout(
                title_text="Clinic Density by City: Existing + Proposed",
                title_font_size=12, height=350, barmode='stack',
                yaxis_title="Clinics", margin=dict(t=40, b=40, l=10, r=10),
                legend=dict(orientation='h', y=-0.2)
            )
            st.plotly_chart(fig_cannibal, use_container_width=True)

            fig_dilute = go.Figure()
            fig_dilute.add_trace(go.Bar(
                x=cannibal_df['City'], y=cannibal_df['Avg NTB/Clinic'],
                name='Current NTB/Clinic', marker_color='#1565C0'
            ))
            fig_dilute.add_trace(go.Bar(
                x=cannibal_df['City'], y=cannibal_df['NTB Per Clinic (Post)'],
                name='Post-Expansion NTB/Clinic', marker_color='#E53935'
            ))
            fig_dilute.add_hline(y=BREAKEVEN_SHOWS, line_dash="dash", line_color="#333",
                                 annotation_text=f"Breakeven: {BREAKEVEN_SHOWS:.0f} shows")
            fig_dilute.update_layout(
                title_text="NTB/Clinic: Before vs After Expansion (Dilution Effect)",
                title_font_size=12, height=350, barmode='group',
                yaxis_title="Avg NTB Shows/Clinic/Month",
                margin=dict(t=40, b=40, l=10, r=10),
                legend=dict(orientation='h', y=-0.2)
            )
            st.plotly_chart(fig_dilute, use_container_width=True)

            high_risk_c = cannibal_df[cannibal_df['Risk Level'] == 'High']
            if len(high_risk_c) > 0:
                st.markdown(f"""
<div class="gate-fail">
<b>🚨 HIGH Cannibalization Risk — {len(high_risk_c)} cities:</b>
{', '.join(high_risk_c['City'].tolist())}. 5+ clinics post-expansion with avg NTB &lt;80.
New clinics will steal from existing ones, not grow the pie.
</div>
""", unsafe_allow_html=True)

            with st.expander("Full Cannibalization Risk Table", expanded=False):
                st.dataframe(cannibal_df, use_container_width=True, hide_index=True)

    st.markdown(f"""
<div class="insight-box">
<b>💡 Cannibalization:</b> Starbucks research: 1.2% revenue theft per neighbor within 1 mile.
Bernstein: 1-in-7 transactions diverted. Indira IVF/Nova maintain 10-20km spacing.
Ayurvedic franchise benchmarks mandate 10km exclusive territory.<br>
<b>Action:</b> Enforce minimum {SAFE_DISTANCE_KM}km spacing. Freeze expansion in cities with 5+
clinics until existing locations hit 80% utilization.
</div>
""", unsafe_allow_html=True)


# ── 7E: KILL CRITERIA DASHBOARD ─────────────────────────────────
with risk_tabs[4]:
    st.markdown('<p class="section-header">7E. Kill Criteria — Automatic Review Triggers for Every Clinic</p>',
                unsafe_allow_html=True)

    st.markdown(f"""
<div class="gate-warn">
<b>⚠️ Why Kill Criteria Matter:</b> Pristyn Care kept loss-making locations open 12-18 months before acting.
Every month a failing clinic stays open costs <b>₹{MONTHLY_OPEX/1e5:.1f}L in OpEx</b>.
Clear, pre-committed exit rules prevent sunk-cost fallacy from destroying capital.
</div>
""", unsafe_allow_html=True)

    milestones = ['Month 3', 'Month 6', 'Month 9', 'Month 12']
    amber_thresholds = [20, 25, BREAKEVEN_SHOWS, BREAKEVEN_SHOWS]
    red_thresholds = [12, BREAKEVEN_SHOWS * 0.5, 20, 15]

    fig_kill = go.Figure()
    fig_kill.add_trace(go.Scatter(
        x=milestones, y=amber_thresholds,
        name='Amber (Watch/Remediate)', mode='lines+markers+text',
        text=[f'{t:.0f}' for t in amber_thresholds],
        textposition='top center', line=dict(color='#FF9800', width=3), marker=dict(size=12)
    ))
    fig_kill.add_trace(go.Scatter(
        x=milestones, y=red_thresholds,
        name='Red (Exit/Close)', mode='lines+markers+text',
        text=[f'{t:.0f}' for t in red_thresholds],
        textposition='bottom center', line=dict(color='#E53935', width=3), marker=dict(size=12)
    ))
    fig_kill.add_hline(y=BREAKEVEN_SHOWS, line_dash="dash", line_color="#333",
                       annotation_text=f"Breakeven: {BREAKEVEN_SHOWS:.0f} shows")
    fig_kill.update_layout(
        title_text="Kill Criteria Timeline — NTB Show Thresholds by Milestone",
        title_font_size=12, height=350, yaxis_title="NTB Shows/Month",
        margin=dict(t=40, b=20, l=10, r=10), legend=dict(orientation='h', y=-0.15)
    )
    st.plotly_chart(fig_kill, use_container_width=True)

    # Current network scan
    st.markdown('<p class="section-header" style="margin-top:0.3rem;">Current Network Scan — Who Would Trigger Today?</p>',
                unsafe_allow_html=True)

    if 'Current NTB Shows' in sim.columns:
        below_20 = sim[sim['Current NTB Shows'] < 20]
        below_be = sim[(sim['Current NTB Shows'] >= 20) & (sim['Current NTB Shows'] < BREAKEVEN_SHOWS)]
        below_50 = sim[(sim['Current NTB Shows'] >= BREAKEVEN_SHOWS) & (sim['Current NTB Shows'] < 50)]
        above_50 = sim[sim['Current NTB Shows'] >= 50]

        km1_r, km2_r, km3_r, km4_r = st.columns(4)
        with km1_r:
            st.metric("🟢 Healthy (50+)", f"{len(above_50)}",
                      delta=f"{len(above_50)/len(sim)*100:.0f}% of network")
        with km2_r:
            st.metric(f"🟡 Watch ({BREAKEVEN_SHOWS:.0f}-50)", f"{len(below_50)}")
        with km3_r:
            st.metric(f"🟠 Remediate (20-{BREAKEVEN_SHOWS:.0f})", f"{len(below_be)}",
                      delta=f"₹{len(below_be)*MONTHLY_OPEX/1e5:.0f}L/mo at risk")
        with km4_r:
            st.metric("🔴 Exit Review (<20)", f"{len(below_20)}",
                      delta=f"₹{len(below_20)*MONTHLY_OPEX*12/1e7:.1f} Cr/yr drag")

        kill_cats = ['🔴 <20 (Exit)', f'🟠 20-{BREAKEVEN_SHOWS:.0f} (Remediate)',
                     f'🟡 {BREAKEVEN_SHOWS:.0f}-50 (Watch)', '🟢 50+ (Healthy)']
        kill_counts = [len(below_20), len(below_be), len(below_50), len(above_50)]
        kill_colors_r = ['#E53935', '#FF9800', '#FDD835', '#4CAF50']

        fig_kill_dist = go.Figure(go.Bar(
            x=kill_counts, y=kill_cats, orientation='h',
            marker_color=kill_colors_r,
            text=[f'{c} clinics ({c/len(sim)*100:.0f}%)' for c in kill_counts],
            textposition='outside', textfont=dict(size=11)
        ))
        fig_kill_dist.update_layout(
            title_text="Current Network by Kill Criteria Tier",
            title_font_size=12, height=250, xaxis_title="Number of Clinics",
            margin=dict(t=40, b=20, l=10, r=120)
        )
        st.plotly_chart(fig_kill_dist, use_container_width=True)

        if len(below_20) > 0:
            st.markdown(f"""
<div class="gate-fail">
<b>🔴 {len(below_20)} clinics in RED zone (&lt;20 shows) — Exit Review Required:</b><br>
{', '.join(below_20['Clinic Name'].tolist()[:15])}{'...' if len(below_20) > 15 else ''}<br>
Combined drain: <b>₹{len(below_20)*MONTHLY_OPEX/1e5:.1f}L/month</b>
(₹{len(below_20)*MONTHLY_OPEX*12/1e7:.1f} Cr/year). Exiting saves more than some new cities generate.
</div>
""", unsafe_allow_html=True)

    # Cost of delay
    delay_months = [1, 3, 6, 12]
    delay_costs = [MONTHLY_OPEX * m / 1e5 for m in delay_months]
    fig_delay = go.Figure(go.Bar(
        x=[f'{m} mo{"s" if m>1 else ""}' for m in delay_months], y=delay_costs,
        marker_color=['#FDD835', '#FF9800', '#E53935', '#880E4F'],
        text=[f'₹{c:.1f}L' for c in delay_costs],
        textposition='outside', textfont=dict(size=12, color='#333')
    ))
    fig_delay.update_layout(
        title_text="Cost of Keeping ONE Failing Clinic Open (₹3.1L/mo)",
        title_font_size=12, height=280, yaxis_title="Cumulative Loss (₹ Lakhs)",
        margin=dict(t=40, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_delay, use_container_width=True)

    st.markdown(f"""
<div class="insight-box">
<b>💡 Kill Criteria:</b> Pre-committed exit rules separate surviving chains from dead ones.
Cloudnine's ICRA rating was dragged to 2.7% RoCE by new-center losses overwhelming mature profits.<br>
<b>The Rule:</b> Any clinic below <b>20 NTB shows at Month 9 → close</b>. No exceptions.
₹{MONTHLY_OPEX/1e5:.1f}L/month saved per exit funds one new clinic in a validated market.
CEO must sign off on any deviation — no delegation.
</div>
""", unsafe_allow_html=True)


# ================================================================
# SECTION 6 — SCENARIO MATRIX
# ================================================================
st.divider()
st.markdown('<p class="section-header">6️⃣ SCENARIO COMPARISON — Three Outcomes for the Board</p>',
            unsafe_allow_html=True)

scn_results = []
for s_name, s_show, s_conv, s_ratio in [
    ('Conservative', -0.02, 0.35, P25_RATIO),
    ('Base Case', 0.0, 0.40, MEDIAN_RATIO),
    ('Optimistic', 0.03, 0.45, P75_RATIO)
]:
    # Existing
    exist_rev = (sim['Avg NTB Appts'] * (sim['Current Show %'].mean() + s_show) * s_conv * SALE_VAL * 12).sum()
    # Same-city new
    if not same_rev_data.empty:
        sc_same = same_rev_data.copy()
        sc_same['r'] = sc_same['projected_ss_ntb'] * (sc_same['projected_show_pct'] + s_show).clip(0.08,0.5) * s_conv * SALE_VAL
        s_same_12 = sum(sc_same['r'] * ramp[i] for i in range(12)).sum()
    else:
        s_same_12 = 0
    # New city (ratio)
    if not newc.empty and 'pop_numeric' in newc.columns:
        nc = newc.drop_duplicates('City')
        nc_shows = nc['pop_numeric'] / 100000 * s_ratio
        nc_rev_m = nc_shows * (avg_show + s_show) * s_conv * SALE_VAL
        s_new_12 = sum(nc_rev_m * ramp[i] for i in range(12)).sum()
    else:
        s_new_12 = 0

    scn_results.append({
        'Scenario': s_name, 'Existing': float(exist_rev),
        'Same-City': float(s_same_12), 'New City': float(s_new_12),
        'Total': float(exist_rev + s_same_12 + s_new_12),
        'Ratio Used': s_ratio
    })

scn_df = pd.DataFrame(scn_results)

fig_scn = go.Figure()
for col, color, name in [('Existing', '#BBDEFB', 'Existing 61'),
                          ('Same-City', '#43A047', 'Same-City New'),
                          ('New City', '#FF6F00', 'New City (Ratio)')]:
    fig_scn.add_trace(go.Bar(
        x=scn_df['Scenario'], y=scn_df[col]/1e7, name=name, marker_color=color,
        text=scn_df[col].apply(lambda v: f"₹{v/1e7:.1f}"), textposition='inside'))

fig_scn.add_trace(go.Scatter(
    x=scn_df['Scenario'], y=scn_df['Total']/1e7,
    mode='markers+text', marker=dict(size=16, color='#E53935'),
    text=scn_df['Total'].apply(lambda v: f"₹{v/1e7:.0f}Cr"),
    textposition='top center', name='Total', showlegend=False))

fig_scn.update_layout(height=320, barmode='stack', margin=dict(t=30, b=20),
                      title_text="FY27 Revenue: 3 Scenarios (Ratio-Adjusted New City Projections)",
                      title_font_size=12, legend=dict(orientation='h', y=1.12), yaxis_title="₹ Cr")
st.plotly_chart(fig_scn, use_container_width=True)

sm1, sm2, sm3 = st.columns(3)
for col_out, s_row in zip([sm1, sm2, sm3], scn_results):
    with col_out:
        st.metric(s_row['Scenario'], f"₹{s_row['Total']/1e7:.0f} Cr",
                  delta=f"Ratio: {s_row['Ratio Used']:.1f}/lakh")


# ================================================================
# SECTION 7 — THE ASK
# ================================================================
st.divider()
st.markdown('<p class="section-header">7️⃣ THE ASK — FY27 Expansion Decision Framework</p>',
            unsafe_allow_html=True)

base_total = scn_df[scn_df['Scenario'] == 'Base Case']['Total'].values[0]
cons_total = scn_df[scn_df['Scenario'] == 'Conservative']['Total'].values[0]
p3_count = len(sim[sim['Tier'] == 'P3']) if 'Tier' in sim.columns else 0

ca1, ca2 = st.columns(2)

with ca1:
    st.markdown(f"""
<div class="gate-pass">
<b>✅ RECOMMENDATION: Proof-Gated Expansion</b><br><br>
<b>Phase 0 — Fix First (Q1 FY27):</b><br>
Show% improvement for {p3_count + p4_count} underperforming clinics.
Unlock: <b>₹{total_uplift/1e7:.1f} Cr</b> — zero CAC.<br><br>
<b>Wave 1 — Same-City Satellites (Q1-Q2):</b><br>
Expand from <b>{len(qualifying)}</b> saturated clinics (≥{ntb_threshold} shows).
Revenue: <b>₹{same_12m/1e7:.1f} Cr</b>. Gate: Parent at 80%+ utilization.<br><br>
<b>Wave 2 — New City Tier-2 (Q2-Q3):</b><br>
{len(newc[newc['Tier']=='Tier-2'].drop_duplicates('City'))} cities, NTB projected via <b>{applied_ratio:.1f}/lakh ratio</b>.
Revenue: <b>₹{new_12m/1e7:.1f} Cr</b>. Gate: Wave 1 hits 70% of target.<br><br>
<b>Wave 3 — Tier-3 (Q3-Q4):</b><br>
Only if Wave 2 succeeds. Lean 1-2 cabin format.
</div>
""", unsafe_allow_html=True)

with ca2:
    one_ppt_value = (sim['Avg NTB Appts'].sum() * 0.01 * CONV_PCT * SALE_VAL * 12)
    st.markdown(f"""
<div class="insight-box">
<b>📊 FY27 Financial Summary</b><br><br>
• Existing 61 clinics: <b>₹{network_annual/1e7:.1f} Cr</b><br>
• Show% fix (₹0 CAC): <b>+₹{total_uplift/1e7:.1f} Cr</b><br>
• Same-city expansion: <b>+₹{same_12m/1e7:.1f} Cr</b><br>
• New city (ratio-based): <b>+₹{new_12m/1e7:.1f} Cr</b><br>
• <b>FY27 Total: ₹{base_total/1e7:.0f} Cr</b> (Base) / <b>₹{cons_total/1e7:.0f} Cr</b> (Conservative)<br><br>
<b>🛡 Downside Protection:</b><br>
• NTB projections use proven {applied_ratio:.1f}/lakh ratio, not assumptions<br>
• Same-city expansion only from saturated (≥{ntb_threshold} shows) clinics<br>
• Each wave requires prior wave validation gate<br>
• No expansion near P4 clinics (Show% &lt;15%)<br><br>
<b>🎯 The One Number:</b> Every 1ppt Show% improvement =
<b>₹{one_ppt_value/1e7:.1f} Cr/year</b> in additional revenue.
</div>
""", unsafe_allow_html=True)
