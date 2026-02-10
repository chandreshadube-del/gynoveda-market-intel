"""
Gynoveda FY27 Expansion Intelligence — Clean 7-Slide Layout
Built: Feb 2026 | Data: NTB Jan-25 to Jan-26 | 61 Clinics
Uses pre-processed CSVs from data/ folder.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, os

st.set_page_config(page_title="Gynoveda FY27 Plan", layout="wide", page_icon="🏥")


# ── Indian Number Formatter ─────────────────────────────────────────────────
def fmt_inr(value, prefix="₹", decimals=1):
    """Format number in Indian notation: Cr / L / K / plain."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return f"{prefix}0"
    v = abs(value)
    sign = "-" if value < 0 else ""
    if v >= 1e7:
        return f"{sign}{prefix}{v/1e7:.{decimals}f} Cr"
    elif v >= 1e5:
        return f"{sign}{prefix}{v/1e5:.{decimals}f}L"
    elif v >= 1e3:
        return f"{sign}{prefix}{v/1e3:.{decimals}f}K"
    else:
        return f"{sign}{prefix}{v:.0f}"


def fmt_num(value, decimals=1):
    """Format plain number (no ₹): Cr / L / K / plain."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "0"
    v = abs(value)
    sign = "-" if value < 0 else ""
    if v >= 1e7:
        return f"{sign}{v/1e7:.{decimals}f} Cr"
    elif v >= 1e5:
        return f"{sign}{v/1e5:.{decimals}f}L"
    elif v >= 1e3:
        return f"{sign}{v/1e3:.{decimals}f}K"
    else:
        return f"{sign}{v:.0f}"

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1200px;}
    [data-testid="stMetric"] {background: #f8f9fa; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #FF6B35;}
    [data-testid="stMetric"] label {font-size: 0.75rem !important; color: #666;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.5rem !important; font-weight: 700;}
    .slide-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 16px 24px; border-radius: 10px; margin: 2rem 0 1rem 0;
        font-size: 1.1rem; font-weight: 600;
    }
    .slide-sub {color: #a0a0b0; font-size: 0.85rem; font-weight: 400; margin-top: 4px;}
    .insight-card {
        background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 16px;
        border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 0.9rem;
    }
    .insight-green {background: #d4edda; border-left-color: #28a745;}
    .insight-red {background: #f8d7da; border-left-color: #dc3545;}
    .insight-blue {background: #d1ecf1; border-left-color: #17a2b8;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stDeployButton {display: none;}
    .slide-sep {border-top: 2px solid #eee; margin: 2.5rem 0;}
</style>
""", unsafe_allow_html=True)

DATA_DIR = "data"

# ── DATA LOADING ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load all pre-processed CSV files."""
    d = {}
    d["clinic_perf"] = pd.read_csv(f"{DATA_DIR}/clinic_performance.csv")
    d["existing"] = pd.read_csv(f"{DATA_DIR}/existing_clinics_61.csv")
    d["show_analysis"] = pd.read_csv(f"{DATA_DIR}/show_pct_analysis.csv")
    d["show_impact"] = pd.read_csv(f"{DATA_DIR}/show_pct_impact_comparison.csv")
    d["show_rank"] = pd.read_csv(f"{DATA_DIR}/show_pct_rank_comparison.csv")
    d["master_state"] = pd.read_csv(f"{DATA_DIR}/master_state.csv")
    d["state_clinic"] = pd.read_csv(f"{DATA_DIR}/state_clinic_summary.csv")
    d["state_orders"] = pd.read_csv(f"{DATA_DIR}/state_orders_summary.csv")
    d["city_clinic"] = pd.read_csv(f"{DATA_DIR}/city_clinic_summary.csv")
    d["city_orders"] = pd.read_csv(f"{DATA_DIR}/city_orders_summary.csv")
    d["web_demand"] = pd.read_csv(f"{DATA_DIR}/web_order_demand.csv")
    d["clinic_zip"] = pd.read_csv(f"{DATA_DIR}/clinic_zip_summary.csv")
    d["expansion_same"] = pd.read_csv(f"{DATA_DIR}/expansion_same_city.csv")
    d["expansion_new"] = pd.read_csv(f"{DATA_DIR}/expansion_new_city.csv")
    d["pincode_clinic"] = pd.read_csv(f"{DATA_DIR}/pincode_clinic.csv")
    d["scenario"] = pd.read_csv(f"{DATA_DIR}/scenario_simulator_clinics.csv")
    d["year_trend"] = pd.read_csv(f"{DATA_DIR}/year_trend.csv")
    d["monthly_trend"] = pd.read_csv(f"{DATA_DIR}/clinic_monthly_trend.csv")

    with open(f"{DATA_DIR}/revenue_assumptions.json") as f:
        d["rev_assumptions"] = json.load(f)

    return d


data = load_data()
cp = data["clinic_perf"].copy()
ex = data["existing"]
sa = data["show_analysis"]
ms = data["master_state"]

# Convert all appt_/show_ columns to numeric (some have '-' for pre-launch months)
for col in cp.columns:
    if col.startswith("appt_") or col.startswith("show_"):
        cp[col] = pd.to_numeric(cp[col], errors="coerce").fillna(0)

# ── PROCESS CLINIC PERFORMANCE ──────────────────────────────────────────────
# Monthly columns: appt_YYYY-MM, show_YYYY-MM
month_cols = [c.replace("appt_", "") for c in cp.columns if c.startswith("appt_")]
last_month = month_cols[-1]  # 2026-01
l3m_months = month_cols[-3:]  # Nov-25, Dec-25, Jan-26

# Compute key metrics per clinic
cp["latest_appt"] = cp[f"appt_{last_month}"]
cp["latest_show"] = cp[f"show_{last_month}"]
cp["latest_ntb"] = (cp["latest_appt"] * cp["latest_show"]).astype(int)

# L3M averages
cp["l3m_appt"] = cp[[f"appt_{m}" for m in l3m_months]].mean(axis=1)
cp["l3m_show"] = cp[[f"show_{m}" for m in l3m_months]].mean(axis=1)
cp["l3m_ntb"] = (cp["l3m_appt"] * cp["l3m_show"]).astype(int)  # clinic visits (shows)

# Clinic capacity: max 150 shows (clinic visits) per clinic per month
cp["cabins"] = pd.to_numeric(cp["cabins"], errors="coerce").fillna(2).astype(int)
CLINIC_CAPACITY = 150  # max visits/month per clinic
cp["capacity"] = CLINIC_CAPACITY
cp["util_pct"] = cp["l3m_ntb"] / CLINIC_CAPACITY

# Network monthly trend from clinic data
network_monthly = []
for m in month_cols:
    appt_col = f"appt_{m}"
    show_col = f"show_{m}"
    total_appt = cp[appt_col].sum()
    # Weighted average show%
    valid = cp[cp[appt_col] > 0]
    if len(valid) > 0:
        weighted_show = (valid[appt_col] * valid[show_col]).sum() / valid[appt_col].sum()
    else:
        weighted_show = 0
    ntb = int(total_appt * weighted_show)
    network_monthly.append({
        "month": pd.Timestamp(f"{m}-01"), "appt": int(total_appt),
        "show_pct": weighted_show, "ntb": ntb
    })
df_network = pd.DataFrame(network_monthly)

# Map clinics to states via clinic_zip_summary (use highest-volume state, exclude '-')
czs = data["clinic_zip"]
czs_clean = czs[czs["State"].notna() & (czs["State"] != "-")]
state_by_vol = czs_clean.groupby(["Clinic_Loc", "State"])["total_qty"].sum().reset_index()
clinic_state_map = state_by_vol.sort_values("total_qty", ascending=False).drop_duplicates("Clinic_Loc").set_index("Clinic_Loc")["State"].to_dict()
cp["state"] = cp["clinic_name"].map(clinic_state_map)


# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ FY27 Controls")
    scenario = st.radio("Scenario", ["Conservative", "Base Case", "Optimistic"], index=1)
    scenario_mult = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.15}[scenario]

    st.markdown("---")
    show_threshold = st.slider("Same-City NTB Show Threshold", 100, 500, 150, 10)

    ntb_pop_ratio = st.radio(
        "NTB:Pop Ratio for New Cities",
        ["Median (3.8/lakh)", "Conservative (P25: 2.6/lakh)"],
        index=0,
        help="Ratio used to estimate monthly NTB potential for new cities based on population.",
    )
    ntb_ratio_val = 3.8 if "Median" in ntb_pop_ratio else 2.6
    rev_per_ntb = st.number_input("₹ Revenue per NTB Patient", value=22000, step=1000)
    show_to_conv = st.slider("Show → Purchase Conversion%", 50, 100, 75, 5,
                              help="Of patients who show up, what % convert to NTB purchase. Verified ~75-80% from clinic order data (Jul-25 to Jan-26).")
    monthly_opex = st.number_input("Monthly OpEx per Clinic (₹L)", value=3.1, step=0.1, format="%.1f")
    capex_per_clinic = st.number_input("Capex per Clinic (₹L)", value=28.0, step=1.0, format="%.1f")
    # Internal benchmark: P75 of active clinics (≥30 appt/mo)
    _active = cp[cp["l3m_appt"] >= 30]
    _p75 = int(round(_active["l3m_show"].quantile(0.75) * 100))
    industry_show = st.slider("Gynoveda Benchmark Show%", 10, 50, _p75, 1)
    _above_bench = (_active["l3m_show"] >= industry_show / 100).sum()
    st.caption(f"_Default {_p75}% = Gynoveda P75 (top-quartile of {len(_active)} active clinics). {_above_bench} clinics already achieve this._")

    st.markdown("---")
    st.caption(f"Data: Jan-25 to Jan-26 · {len(cp)} Clinics")
    st.markdown("---")
    st.markdown(
        '<div style="background:#f0f4ff;border-radius:6px;padding:10px;font-size:0.72rem;color:#444;">'
        '<b>📚 Data Model & Benchmark</b><br>'
        '<b>Funnel:</b> Appt Booked → Show% (~20%) → Clinic Visit → Conversion (75%) → NTB Purchase<br>'
        '<b>Show% Benchmark:</b> Gynoveda P75 of active clinics. Proven & achievable.<br>'
        '<b>Conversion:</b> Verified 75-80% from ZipData clinic orders (Jul-25 to Jan-26).'
        '</div>',
        unsafe_allow_html=True,
    )

# ── EARLY COMPUTATION (needed across slides) ──────────────────────────────
conversion_rate = show_to_conv / 100
opex_monthly = monthly_opex * 1e5
capex = capex_per_clinic * 1e5

# ── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🏥 Gynoveda FY27 Expansion Plan")

peak_ntb = df_network["ntb"].max()
latest_ntb = df_network["ntb"].iloc[-1]
ntb_decline = (latest_ntb - peak_ntb) / peak_ntb if peak_ntb > 0 else 0
network_show = cp["latest_show"].mean()
ntb_per_clinic = latest_ntb / len(cp) if len(cp) > 0 else 0
peak_per_clinic = peak_ntb / len(cp) if len(cp) > 0 else 0
latest_appt_total = df_network["appt"].iloc[-1]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("NTB Appt Booked (Jan-26)", fmt_num(latest_appt_total))
c2.metric("Clinic Visits (Jan-26)", fmt_num(latest_ntb), f"{ntb_decline:+.0%} from peak")
c3.metric("Network Show%", f"{network_show:.0%}", f"{'↑' if network_show > 0.18 else '↓'} vs 18% floor")
c4.metric("Active Clinics", f"{len(cp)}")
c5.metric("Visits/Clinic (Jan-26)", f"{ntb_per_clinic:.0f}", f"Peak was {peak_per_clinic:.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1: ONLINE vs CLINIC REACH
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">📍 SLIDE 1 — ONLINE vs CLINIC REACH'
    '<div class="slide-sub">Total order quantity by pincode: Website vs Clinics — showing reach gap</div></div>',
    unsafe_allow_html=True,
)

STATE_COORDS = {
    "Maharashtra": (19.75, 75.71), "Uttar Pradesh": (26.85, 80.95),
    "Karnataka": (15.32, 75.71), "Delhi": (28.70, 77.10),
    "Gujarat": (22.26, 71.19), "West Bengal": (22.99, 87.86),
    "Telangana": (18.11, 79.02), "Haryana": (29.06, 76.09),
    "Punjab": (31.15, 75.34), "Assam": (26.20, 92.94),
    "Madhya Pradesh": (22.97, 78.66), "Rajasthan": (27.02, 74.22),
    "Odisha": (20.95, 85.10), "Tamil Nadu": (11.13, 78.66),
    "Bihar": (25.10, 85.31), "Jharkhand": (23.61, 85.28),
    "Kerala": (10.85, 76.27), "Chhattisgarh": (21.28, 81.87),
    "Uttarakhand": (30.07, 79.02), "Andhra Pradesh": (15.91, 79.74),
    "Chandigarh": (30.73, 76.78), "Goa": (15.30, 74.12),
    "Himachal Pradesh": (31.10, 77.17), "Jammu and Kashmir": (33.78, 76.58),
    "Nagaland": (26.16, 94.56), "Meghalaya": (25.47, 91.37),
    "Arunachal Pradesh": (28.22, 94.73), "Tripura": (23.94, 91.99),
    "Manipur": (24.66, 93.91), "Mizoram": (23.16, 92.94),
    "Sikkim": (27.53, 88.51), "Pondicherry": (11.94, 79.81),
    "NAGALAND": (26.16, 94.56), "Jharkand": (23.61, 85.28),
}

# Build state comparison from master_state
ms_clean = ms[ms["state_geo"].notna() & (ms["state_geo"] != "-")].copy()
ms_clean["lat"] = ms_clean["state_geo"].map(lambda s: STATE_COORDS.get(s, (20, 78))[0])
ms_clean["lon"] = ms_clean["state_geo"].map(lambda s: STATE_COORDS.get(s, (20, 78))[1])
ms_clean["web_orders"] = ms_clean["total_orders"].fillna(0)
ms_clean["clinic_orders"] = ms_clean["clinic_firsttime_qty"].fillna(0)
ms_clean["total_all"] = ms_clean["web_orders"] + ms_clean["clinic_orders"]
ms_clean["clinic_share"] = np.where(ms_clean["total_all"] > 0, ms_clean["clinic_orders"] / ms_clean["total_all"], 0)
ms_clean = ms_clean.sort_values("total_all", ascending=False)

col_map1, col_map2 = st.columns(2)

with col_map1:
    st.markdown("**🌐 Website Orders by State**")
    fig_web = px.scatter_mapbox(
        ms_clean.head(20), lat="lat", lon="lon", size="web_orders",
        color="web_orders", hover_name="state_geo",
        color_continuous_scale="Blues", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_web.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Orders: %{marker.size:,}<extra></extra>"
    )
    fig_web.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_web, use_container_width=True)

with col_map2:
    st.markdown("**🏥 Clinic Orders by State**")
    fig_cli = px.scatter_mapbox(
        ms_clean.head(20), lat="lat", lon="lon", size="clinic_orders",
        color="clinic_orders", hover_name="state_geo",
        color_continuous_scale="Oranges", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_cli.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Clinic Orders: %{marker.size:,}<extra></extra>"
    )
    fig_cli.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_cli, use_container_width=True)

sm1, sm2, sm3, sm4 = st.columns(4)
total_web_pins = int(ms_clean["unique_customers_pincodes"].sum())
total_cli_pins = int(ms_clean["clinic_pincodes"].sum())
sm1.metric("Website Pincodes", fmt_num(total_web_pins))
sm2.metric("Clinic Pincodes", fmt_num(total_cli_pins))
sm3.metric("Website Orders", fmt_num(int(ms_clean['web_orders'].sum())))
sm4.metric("Clinic Orders (FirstTime)", fmt_num(int(ms_clean['clinic_orders'].sum())))

st.markdown("**State-Level Reach Comparison (Top 12)**")
top12 = ms_clean.head(12)[["state_geo", "web_orders", "unique_customers_pincodes", "clinic_orders", "clinic_pincodes", "clinic_share"]].copy()
top12.columns = ["State", "Website Orders", "Website Pincodes", "Clinic Orders", "Clinic Pincodes", "Clinic Share %"]
top12["Clinic Share %"] = (top12["Clinic Share %"] * 100).round(1)
for c in ["Website Orders", "Clinic Orders"]:
    top12[c] = top12[c].astype(int).apply(lambda x: fmt_num(x))
for c in ["Website Pincodes", "Clinic Pincodes"]:
    top12[c] = top12[c].astype(int)
st.dataframe(top12, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2: THE CASE FOR CAUTION — Show% Analysis
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">⚠️ SLIDE 2 — THE CASE FOR CAUTION: Why We Must Be Smart, Not Just Fast'
    '<div class="slide-sub">STATE-WISE SHOW% — Gynoveda vs Internal P75 Benchmark (Top-Quartile of Active Clinics)</div></div>',
    unsafe_allow_html=True,
)

col_trend, col_insight = st.columns([2, 1])
with col_trend:
    st.markdown("**Network Funnel Trend — Appointments vs Clinic Visits**")
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(
            x=df_network["month"], y=df_network["appt"],
            name="Appt Booked", marker_color="#B0BEC5", opacity=0.55,
            text=df_network["appt"].apply(lambda x: fmt_num(x)),
            textposition="outside",
            hovertemplate="<b>%{x|%b %Y}</b><br>Appt Booked: %{y:,}<extra></extra>",
        ), secondary_y=False,
    )
    fig_trend.add_trace(
        go.Bar(
            x=df_network["month"], y=df_network["ntb"],
            name="Clinic Visits (Shows)", marker_color="#FF6B35", opacity=0.85,
            text=df_network["ntb"].apply(lambda x: fmt_num(x)),
            textposition="outside",
            hovertemplate="<b>%{x|%b %Y}</b><br>Clinic Visits: %{y:,}<extra></extra>",
        ), secondary_y=False,
    )
    fig_trend.add_trace(
        go.Scatter(
            x=df_network["month"], y=df_network["show_pct"] * 100,
            name="Show %", line=dict(color="#1a73e8", width=3),
            mode="lines+markers",
            hovertemplate="<b>%{x|%b %Y}</b><br>Show%: %{y:.1f}%<extra></extra>",
        ), secondary_y=True,
    )
    fig_trend.update_layout(
        height=370, margin=dict(l=40, r=40, t=10, b=40),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    font=dict(size=12)),
        yaxis_title="Count", yaxis2_title="Show %",
        barmode="overlay",
        plot_bgcolor="white",
    )
    fig_trend.update_yaxes(range=[0, 35], secondary_y=True)
    fig_trend.update_xaxes(tickformat="%b %y")
    st.plotly_chart(fig_trend, use_container_width=True)

with col_insight:
    peak_m = df_network.loc[df_network["ntb"].idxmax(), "month"].strftime("%b-%y")
    below_15 = (cp["latest_show"] < 0.15).sum()
    latest_appt_network = df_network["appt"].iloc[-1]
    st.markdown(f"""
    <div class="insight-card insight-red">
    <strong>📊 The Funnel Says:</strong><br>
    • <b>{fmt_num(latest_appt_network)}</b> appts booked (Jan-26), only <b>{fmt_num(latest_ntb)}</b> visited ({network_show:.0%} Show%)<br>
    • Visits peaked at <b>{fmt_num(peak_ntb)}</b> ({peak_m}), now <b>{ntb_decline:+.0%}</b><br>
    • <b>{below_15}</b> clinics have Show% below 15%<br>
    • At 75% conversion, each lost visit = <b>{fmt_inr(0.75*rev_per_ntb)}</b> lost revenue
    </div>
    <div class="insight-card insight-blue">
    <strong>🎯 The answer:</strong> Not fewer or more clinics — <b>smarter clinics</b>.
    Fix the funnel: Appt → Show → Purchase.
    </div>
    """, unsafe_allow_html=True)

# State-wise Show% vs Industry Benchmark
state_show = (
    cp.groupby("state")
    .agg(avg_show=("l3m_show", "mean"), clinic_count=("clinic_name", "count"), total_ntb=("l3m_ntb", "sum"))
    .reset_index()
)
state_show = state_show[state_show["state"].notna() & (state_show["state"] != "-")]
state_show = state_show.sort_values("avg_show", ascending=True)
benchmark = industry_show / 100
state_show["gap"] = state_show["avg_show"] - benchmark
state_show["label"] = state_show.apply(
    lambda r: f"{r['avg_show']:.0%} ({int(r['clinic_count'])} cl)", axis=1
)

st.markdown("**Gynoveda Show% vs Internal P75 Benchmark — State-Wise**")

fig_show = go.Figure()
fig_show.add_trace(go.Bar(
    y=state_show["state"], x=state_show["avg_show"] * 100,
    orientation="h",
    marker_color=[("#4CAF50" if g >= 0 else "#FF6B35" if g >= -0.05 else "#dc3545") for g in state_show["gap"]],
    text=state_show["label"], textposition="outside",
    name="Gynoveda Actual",
    showlegend=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Show%: %{x:.1f}%<br>"
        "Gap vs Benchmark: %{customdata[0]:+.1f}ppt<br>"
        "Clinics: %{customdata[1]}<br>"
        "Monthly NTB: %{customdata[2]:,}"
        "<extra></extra>"
    ),
    customdata=np.column_stack([
        state_show["gap"] * 100,
        state_show["clinic_count"],
        state_show["total_ntb"],
    ]),
))
fig_show.add_vline(x=industry_show, line_dash="dash", line_color="#1a73e8", line_width=2)
fig_show.add_annotation(
    x=industry_show, y=1.02, yref="paper",
    text=f"◆ {industry_show}% Gynoveda P75 Benchmark", showarrow=False,
    font=dict(color="#1a73e8", size=12, family="Arial Black"),
)
fig_show.update_layout(
    height=max(380, len(state_show) * 35),
    margin=dict(l=130, r=100, t=30, b=40),
    xaxis_title="Show %", plot_bgcolor="white",
)
st.plotly_chart(fig_show, use_container_width=True)

above = (state_show["gap"] >= 0.02).sum()
at_std = ((state_show["gap"] >= -0.02) & (state_show["gap"] < 0.02)).sum()
below = (state_show["gap"] < -0.02).sum()

sc1, sc2, sc3 = st.columns(3)
sc1.markdown(f'<div class="insight-card insight-green"><b style="font-size:2rem;color:#28a745">{above}</b> states above standard</div>', unsafe_allow_html=True)
sc2.markdown(f'<div class="insight-card"><b style="font-size:2rem;color:#ffc107">{at_std}</b> states at standard (±2ppt)</div>', unsafe_allow_html=True)
sc3.markdown(f'<div class="insight-card insight-red"><b style="font-size:2rem;color:#dc3545">{below}</b> states below standard</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="background:#f0f4ff;border-left:3px solid #1a73e8;padding:10px 14px;border-radius:0 6px 6px 0;margin:12px 0;font-size:0.8rem;color:#555;">'
    f'<b>📚 Data Model:</b> '
    f'NTB Appt = total appointments booked. '
    f'<b>Show% = % who actually visit the clinic</b> (P75 benchmark: {industry_show}%). '
    f'Of those who show, <b>{show_to_conv}% convert to NTB purchase</b> (verified from ZipData Jul-25 to Jan-26). '
    f'Revenue per converted NTB = ₹{rev_per_ntb:,}.'
    '</div>',
    unsafe_allow_html=True,
)

with st.expander("📋 Full State-Wise Benchmark Detail"):
    detail = state_show[["state", "avg_show", "gap", "clinic_count", "total_ntb"]].copy()
    detail.columns = ["State", "Gynoveda Show%", "Gap vs Benchmark", "Clinics", "Monthly NTB"]
    detail["Gynoveda Show%"] = (detail["Gynoveda Show%"] * 100).round(1)
    detail["Gap vs Benchmark"] = (detail["Gap vs Benchmark"] * 100).round(1)
    detail = detail.sort_values("Gap vs Benchmark")
    st.dataframe(detail, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3: EXPANSION STRATEGY — Where to Open Next
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🗺️ EXPANSION STRATEGY — Where to Open Next'
    '<div class="slide-sub">Same-City Satellites & New City Opportunities</div></div>',
    unsafe_allow_html=True,
)

exp_tab1, exp_tab2 = st.tabs(["🏙️ Same-City Expansion", "🌍 New City Expansion"])

# ── TAB 1: SAME-CITY EXPANSION ───────────────────────────────────────────
with exp_tab1:
    saturated = cp[cp["l3m_appt"] >= show_threshold].sort_values("l3m_appt", ascending=False)

    st.markdown(f"### Same-City — Clinics at Capacity (≥{show_threshold} NTB Shows/Month)")

    col_sat_chart, col_sat_cards = st.columns([1.2, 1])

    with col_sat_chart:
        # Step 1: Saturated clinics bar chart
        st.markdown(f"**Step 1: Clinics with ≥{show_threshold} Avg Monthly NTB Shows**")
        top_sat = saturated.head(10).sort_values("l3m_ntb", ascending=True)
        bar_colors = ["#28a745" if s >= 0.25 else "#ffc107" if s >= 0.18 else "#dc3545"
                      for s in top_sat["l3m_show"]]
        fig_sat = go.Figure(go.Bar(
            y=top_sat["clinic_name"], x=top_sat["l3m_ntb"], orientation="h",
            marker_color=bar_colors,
            text=top_sat.apply(
                lambda r: f"{r['l3m_ntb']} shows | {r['util_pct']:.0%} util | {r['l3m_show']:.0%} show%",
                axis=1,
            ),
            textposition="inside", textfont=dict(color="white", size=11),
        ))
        fig_sat.add_vline(x=show_threshold, line_dash="dash", line_color="red",
                          annotation_text=f"Threshold: {show_threshold}")
        fig_sat.update_layout(
            height=380, margin=dict(l=110, r=20, t=10, b=40),
            xaxis_title="Monthly NTB Shows",
        )
        st.plotly_chart(fig_sat, use_container_width=True)
        mc1, mc2 = st.columns(2)
        mc1.metric("Clinics Qualify", f"{len(saturated)}")
        mc2.metric("Avg Utilization", f"{saturated['util_pct'].mean():.0%}")

    with col_sat_cards:
        czs = data["clinic_zip"]
        for _, row in saturated.head(5).iterrows():
            clinic_zips = czs[czs["Clinic_Loc"] == row["clinic_name"]]
            top_cities = clinic_zips.sort_values("total_qty", ascending=False).head(3)
            top_areas = ", ".join(top_cities["City"].dropna().unique()[:3])
            city_label = clinic_state_map.get(row["clinic_name"], row.get("city_code", ""))
            trend_emoji = "🟢" if row["l3m_show"] >= 0.25 else "🟡" if row["l3m_show"] >= 0.18 else "🔴"
            st.markdown(f"""
            <div style="background:#f8f9fa;border-radius:8px;padding:12px;margin:8px 0;border-left:4px solid #FF6B35;">
            <b>{row['clinic_name']}</b> ({city_label}) — {int(row['cabins'])} cabins<br>
            Shows: <b>{row['l3m_ntb']}/mo</b> | Util: <b>{row['util_pct']:.0%}</b> |
            Show%: <b>{row['l3m_show']:.1%}</b> | {trend_emoji}
            <span style="color:#888;">Declining L3M</span><br>
            </div>
            """, unsafe_allow_html=True)

    # Step 2: Micro-markets for saturated clinics
    st.markdown("---")
    st.markdown("**Step 2: Micro-Market Identification for Saturated Clinics**")
    exp_same = data["expansion_same"]

    # Map city codes to expansion_same city names
    _code_to_city = {
        "MUM": "Mumbai", "NDL": "Delhi", "BLR": "Bengaluru", "HYD": "Hyderabad",
        "KOL": "Kolkata", "AHM": "Ahmedabad", "PUN": "Pune", "LKO": "Lucknow",
        "SUR": "Surat", "PAT": "Patna", "THN": "Mumbai", "NVM": "Mumbai",
    }

    # Group saturated clinics by parent city
    micro_by_city = {}
    for _, row in saturated.iterrows():
        cc = str(row.get("city_code", ""))
        parent_city = _code_to_city.get(cc, cc)
        if parent_city in exp_same["City"].values:
            if parent_city not in micro_by_city:
                micro_by_city[parent_city] = {"shows": 0, "count": len(exp_same[exp_same["City"] == parent_city])}
            micro_by_city[parent_city]["shows"] += row["l3m_ntb"]

    if micro_by_city:
        mc_list = [{"city": k, "parent_shows": v["shows"], "micro_count": v["count"]}
                   for k, v in micro_by_city.items()]
        mc_df = pd.DataFrame(mc_list).sort_values("parent_shows", ascending=False).head(6)
        col_mc, col_mc_info = st.columns([1, 1])
        with col_mc:
            fig_mc = go.Figure(go.Bar(
                y=mc_df["city"][::-1], x=mc_df["micro_count"][::-1], orientation="h",
                marker_color="#28a745",
                text=mc_df.apply(
                    lambda r: f"{r['micro_count']} pins | Parent: {r['parent_shows']} shows/mo", axis=1
                ).values[::-1],
                textposition="inside", textfont=dict(color="white"),
            ))
            fig_mc.update_layout(
                title="Step 2: Proposed Micro-Markets by Saturated City",
                height=300, margin=dict(l=100, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_mc, use_container_width=True)
        with col_mc_info:
            total_no_shows = saturated["l3m_appt"].sum() - saturated["l3m_ntb"].sum()
            recoverable = int(total_no_shows * 0.30)
            recovery_rev = recoverable * conversion_rate * rev_per_ntb
            st.markdown(f"""
            <div style="background:#fff3cd;border-radius:8px;padding:16px;border-left:4px solid #ff6b35;">
            <b>📍 No-Show Recovery Logic:</b><br><br>
            These {len(saturated)} clinics book <b>{int(saturated['l3m_appt'].sum()):,}</b> NTB appointments/mo
            but only <b>{int(saturated['l3m_ntb'].sum()):,}</b> show up.<br><br>
            <b>{int(total_no_shows):,} patients/month</b> are no-shows from these saturated clinics.
            Distance and travel time are primary barriers.<br><br>
            Satellite clinics in top no-show pincodes can recover an estimated
            <b>30%</b> of these patients → <b>{fmt_inr(recovery_rev)}/month</b> in recovered revenue.<br><br>
            <b>This is not new CAC — these patients are already acquired.</b>
            </div>
            """, unsafe_allow_html=True)

    # City-level micro-market expanders
    unique_cities_same = exp_same["City"].unique()
    for city_name in unique_cities_same[:6]:
        city_rows = exp_same[exp_same["City"] == city_name]
        with st.expander(f"📍 {city_name} — {len(city_rows)} Micro-Markets"):
            st.dataframe(
                city_rows[["S.No", "Micro-Market Pincode", "Micro-Market Area",
                           "Expansion Rationale", "National IVFs Present", "Regional IVFs Present"]],
                hide_index=True, use_container_width=True,
            )

# ── TAB 2: NEW CITY EXPANSION ────────────────────────────────────────────
with exp_tab2:
    exp_new = data["expansion_new"]

    # Aggregate by city
    new_cities = exp_new.groupby(["City", "State", "Tier"]).agg(
        web_orders=("Web Order Qty", "first"),
        population=("Est. Population", "first"),
        proj_ntb=("Projected Monthly NTB", "first"),
        locations=("Pincode", "count"),
    ).reset_index().sort_values("web_orders", ascending=False)

    # Revenue projections
    new_cities["monthly_rev"] = (new_cities["proj_ntb"] * conversion_rate * rev_per_ntb).astype(int)
    new_cities["annual_rev"] = new_cities["monthly_rev"] * 12
    new_cities["monthly_profit"] = new_cities["monthly_rev"] - opex_monthly
    new_cities["profitable"] = new_cities["monthly_profit"] > 0

    total_new_annual = new_cities["annual_rev"].sum()
    total_new_profit = new_cities[new_cities["profitable"]]["monthly_profit"].sum() * 12
    profitable_count = new_cities["profitable"].sum()

    st.markdown("### New City Expansion — Untapped Markets with Online Demand")

    # Header metrics
    nc1, nc2, nc3, nc4 = st.columns(4)
    nc1.metric("New City Candidates", f"{len(new_cities)}", f"{new_cities['locations'].sum()} micro-markets")
    nc2.metric("Total Web Orders", fmt_num(new_cities["web_orders"].sum()), "All-time 1cx orders")
    nc3.metric("Projected Annual Revenue", fmt_inr(total_new_annual), f"@ {ntb_pop_ratio.split('(')[0].strip()} ratio")
    nc4.metric("Profitable Cities", f"{profitable_count} of {len(new_cities)}", f"Above ₹{opex_monthly/1e5:.1f}L OpEx")

    col_nc_chart, col_nc_info = st.columns([1.5, 1])

    with col_nc_chart:
        # Top cities bar chart by online demand
        nc_sorted = new_cities.sort_values("web_orders", ascending=True)
        tier_colors = {"Tier-2": "#1a73e8", "Tier-3": "#34a853"}
        fig_nc = go.Figure(go.Bar(
            y=nc_sorted["City"],
            x=nc_sorted["web_orders"],
            orientation="h",
            marker_color=[tier_colors.get(t, "#999") for t in nc_sorted["Tier"]],
            text=nc_sorted.apply(
                lambda r: f"{r['web_orders']:,} orders | {r['Tier']} | ₹{r['annual_rev']/1e5:.0f}L/yr",
                axis=1,
            ),
            textposition="inside",
            textfont=dict(color="white", size=11),
        ))
        fig_nc.update_layout(
            title="New City Opportunities — Ranked by Online Demand (1cx Orders)",
            height=500, margin=dict(l=130, r=20, t=40, b=40),
            xaxis_title="All-Time Web Orders",
        )
        st.plotly_chart(fig_nc, use_container_width=True)

    with col_nc_info:
        # Tier breakdown
        tier_summary = new_cities.groupby("Tier").agg(
            cities=("City", "count"),
            total_rev=("annual_rev", "sum"),
            avg_orders=("web_orders", "mean"),
        ).reset_index()

        st.markdown("""
        <div style="background:#e8f5e9;border-radius:8px;padding:16px;border-left:4px solid #28a745;">
        <b>🌍 New City Strategy:</b><br><br>
        <b>Selection Criteria:</b><br>
        • ≥850+ all-time web orders (proven online demand)<br>
        • No existing Gynoveda clinic within 50km<br>
        • Population ≥1.5 lakh (addressable market)<br>
        • IVF competitor presence confirms fertility demand<br><br>
        <b>Revenue Model:</b><br>
        NTB Projected = Population × NTB:Pop ratio<br>
        Monthly Rev = NTB × 75% Conv × ₹22K/patient<br><br>
        <b>Rollout:</b> 5 micro-market pincodes scouted per city<br>
        for optimal clinic placement.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        for _, tier_row in tier_summary.iterrows():
            tier_label = tier_row["Tier"]
            color = "#1a73e8" if "2" in tier_label else "#34a853"
            st.markdown(f"""
            <div style="background:#f8f9fa;border-radius:6px;padding:10px;margin:6px 0;border-left:4px solid {color};">
            <b>{tier_label}</b>: {tier_row['cities']} cities |
            ₹{tier_row['total_rev']/1e7:.1f} Cr/yr |
            Avg {tier_row['avg_orders']:.0f} orders
            </div>
            """, unsafe_allow_html=True)

    # Revenue projection table
    st.markdown("---")
    st.markdown("**Per-City Revenue Projection**")
    proj_df = new_cities[["City", "State", "Tier", "web_orders", "population",
                          "proj_ntb", "monthly_rev", "annual_rev", "profitable"]].copy()
    proj_df.columns = ["City", "State", "Tier", "Web Orders", "Est. Population",
                       "Proj. NTB/mo", "Monthly Rev (₹)", "Annual Rev (₹)", "Profitable"]
    proj_df["Monthly Rev (₹)"] = proj_df["Monthly Rev (₹)"].apply(lambda x: f"₹{x/1e5:.1f}L")
    proj_df["Annual Rev (₹)"] = proj_df["Annual Rev (₹)"].apply(lambda x: f"₹{x/1e5:.0f}L")
    proj_df["Profitable"] = proj_df["Profitable"].map({True: "✅", False: "❌"})
    st.dataframe(proj_df, hide_index=True, use_container_width=True, height=400)

    # Expandable city-level micro-market details
    st.markdown("---")
    st.markdown("**Micro-Market Scouting — 5 Locations per City**")
    for city_name in new_cities["City"]:
        city_data = exp_new[exp_new["City"] == city_name]
        city_info = new_cities[new_cities["City"] == city_name].iloc[0]
        with st.expander(f"🌍 {city_name} ({city_info['State']}) — {city_info['Tier']} | "
                         f"{city_info['web_orders']:,} orders | ₹{city_info['annual_rev']/1e5:.0f}L/yr"):
            st.dataframe(
                city_data[["Pincode", "Area Name", "Location Rationale",
                           "National IVFs", "Regional IVFs"]],
                hide_index=True, use_container_width=True,
            )

    # Summary callout
    st.markdown(f"""
    <div style="background:#e8f5e9;border-radius:8px;padding:16px;margin-top:16px;border-left:4px solid #28a745;">
    <b>💰 New City Portfolio Impact:</b><br>
    {len(new_cities)} new cities × 5 micro-market options each = {new_cities['locations'].sum()} scouted locations<br>
    Projected Annual Revenue: <b>{fmt_inr(total_new_annual)}</b> |
    Profitable: <b>{profitable_count}/{len(new_cities)}</b> cities above ₹{opex_monthly/1e5:.1f}L OpEx breakeven<br>
    Combined with Same-City expansion, this creates a comprehensive national footprint strategy.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4: FIX BEFORE EXPAND — ₹0 CAC Revenue Unlock
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🔧 SLIDE 4 — FIX BEFORE EXPAND: ₹0 CAC Revenue Unlock'
    '<div class="slide-sub">What happens if underperforming clinics reach our own top-quartile Show%?</div></div>',
    unsafe_allow_html=True,
)

target_show = industry_show / 100
cp["show_gap"] = (target_show - cp["l3m_show"]).clip(lower=0)
conversion_rate = show_to_conv / 100
rev_per_show = conversion_rate * rev_per_ntb
cp["additional_visits"] = (cp["l3m_appt"] * cp["show_gap"]).astype(int)
cp["additional_purchases"] = (cp["additional_visits"] * conversion_rate).astype(int)
cp["additional_rev_annual"] = cp["additional_purchases"] * rev_per_ntb * 12

underperforming = cp[cp["show_gap"] > 0].sort_values("additional_rev_annual", ascending=False)
total_unlock = underperforming["additional_rev_annual"].sum()
total_extra_visits = underperforming["additional_visits"].sum()
total_extra_purchases = underperforming["additional_purchases"].sum()

fm1, fm2, fm3, fm4 = st.columns(4)
fm1.metric("Underperforming Clinics", f"{len(underperforming)} of {len(cp)}", f"Show% < {industry_show}%")
fm2.metric("Extra Visits/mo Unlocked", fmt_num(total_extra_visits), f"@ {industry_show}% Show%")
fm3.metric("Extra NTB Purchases/mo", fmt_num(total_extra_purchases), f"@ {show_to_conv}% conversion")
fm4.metric("Annual Revenue Unlock", fmt_inr(total_unlock), "₹0 CAC — no new leases")

col_fix1, col_fix2 = st.columns([1.2, 1])

with col_fix1:
    fig_scatter = px.scatter(
        cp, x="l3m_appt", y="l3m_show",
        size=cp["additional_rev_annual"].clip(lower=1),
        color="l3m_show", color_continuous_scale="RdYlGn",
        hover_name="clinic_name",
        labels={"l3m_appt": "Avg Monthly Appointments", "l3m_show": "Show%"},
    )
    fig_scatter.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Appointments: %{x:.0f}/mo<br>"
            "Show%: %{y:.1%}<br>"
            "Unlock: ₹%{marker.size:,.0f}/yr"
            "<extra></extra>"
        )
    )
    fig_scatter.add_hline(y=target_show, line_dash="dash", line_color="green",
                          annotation_text=f"{industry_show}% P75 benchmark")
    fig_scatter.update_layout(
        title="Show% vs Appointments — Bubble = Revenue Unlock Potential",
        height=400, margin=dict(l=40, r=40, t=40, b=40), coloraxis_showscale=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_fix2:
    st.markdown(f"""
    <div class="insight-card insight-green">
    <strong>💰 {fmt_inr(total_unlock)} unlock</strong> from Show% fixes across
    <b>{len(underperforming)}</b> clinics — zero new leases, zero CAC.<br>
    <b>{total_extra_visits:,}</b> extra visits/mo → <b>{total_extra_purchases:,}</b> NTB purchases/mo @ {show_to_conv}% conversion.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Top 10 Revenue Unlock Opportunities**")
    top_unlock = underperforming.head(10)[["clinic_name", "l3m_show", "show_gap", "additional_visits", "additional_purchases", "additional_rev_annual"]].copy()
    top_unlock.columns = ["Clinic", "Current Show%", "Gap", "Extra Visits/mo", "Extra NTB/mo", "Annual Unlock ₹"]
    top_unlock["Current Show%"] = (top_unlock["Current Show%"] * 100).round(1)
    top_unlock["Gap"] = (top_unlock["Gap"] * 100).round(1)
    top_unlock["Annual Unlock ₹"] = top_unlock["Annual Unlock ₹"].apply(lambda x: fmt_inr(x))
    st.dataframe(top_unlock, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# COMPUTATION BLOCK — Existing clinic metrics needed by Risk Scorecard (Slide 7)
# ═══════════════════════════════════════════════════════════════════════════
opex_monthly = monthly_opex * 1e5
capex = capex_per_clinic * 1e5
rev_per_show = conversion_rate * rev_per_ntb
breakeven_visits = int(np.ceil(opex_monthly / rev_per_show))
avg_visits = cp["l3m_ntb"].mean()
profitable_clinics = (cp["l3m_ntb"] * rev_per_show > opex_monthly).sum()
rent = 1.0e5

cp["monthly_purchases"] = (cp["l3m_ntb"] * conversion_rate).astype(int)
cp["monthly_revenue"] = cp["monthly_purchases"] * rev_per_ntb * scenario_mult
cp["annual_revenue"] = cp["monthly_revenue"] * 12
cp["monthly_profit"] = cp["monthly_revenue"] - opex_monthly
cp["annual_profit"] = cp["monthly_profit"] * 12
cp["payback_months"] = np.where(cp["monthly_profit"] > 0, capex / cp["monthly_profit"], np.inf)

total_annual_rev = cp["annual_revenue"].sum()

# ═══════════════════════════════════════════════════════════════════════════
# EXPANSION MODEL — Same-City Satellites & New City Projections
# ═══════════════════════════════════════════════════════════════════════════
# Ramp schedule for new clinics (% of steady-state per month)
ramp_schedule = [0.33, 0.55, 0.66, 0.77, 0.88, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
y1_factor = sum(ramp_schedule)  # ~10.19 months of SS equivalent

# Map city codes to expansion city names
_code_exp_map = {
    "MUM": "Mumbai", "THN": "Mumbai", "NVM": "Mumbai",
    "NDL": "Delhi", "BLR": "Bengaluru", "HYD": "Hyderabad", "SEC": "Hyderabad",
    "KOL": "Kolkata", "AHM": "Ahmedabad", "PUN": "Pune",
    "LKO": "Lucknow", "SUR": "Surat", "PAT": "Patna",
}
cp["exp_city"] = cp["city_code"].map(_code_exp_map)

# Max NTB shows per expansion city (from existing clinic performance)
city_max_shows = cp.dropna(subset=["exp_city"]).groupby("exp_city")["l3m_ntb"].max().to_dict()

# ── SAME-CITY SATELLITE MODEL ─────────────────────────────────────────────
exp_same = data["expansion_same"]
same_city_clinics = []
for _, row in exp_same.iterrows():
    city = row["City"]
    parent_max = city_max_shows.get(city, 100)
    sat_shows = int(parent_max / 2)  # each satellite = 50% of best parent
    ss_monthly = sat_shows * conversion_rate * rev_per_ntb
    y1_rev = ss_monthly * y1_factor
    monthly_ramp = [int(ss_monthly * r) for r in ramp_schedule]
    same_city_clinics.append({
        "location": f"{city} - {row['Micro-Market Area']}",
        "city": city,
        "pincode": row["Micro-Market Pincode"],
        "shows_mo": sat_shows,
        "ss_monthly": ss_monthly,
        "y1_rev": y1_rev,
        **{f"M{i+1}": monthly_ramp[i] for i in range(12)},
    })
df_same = pd.DataFrame(same_city_clinics).sort_values("y1_rev", ascending=False)
total_same_y1 = df_same["y1_rev"].sum()

# ── NEW CITY MODEL ─────────────────────────────────────────────────────────
exp_new = data["expansion_new"]
new_city_summary = exp_new.groupby(["City", "State", "Tier"]).agg(
    web_orders=("Web Order Qty", "first"),
    proj_ntb=("Projected Monthly NTB", "first"),
    n_locations=("Pincode", "count"),
).reset_index()

new_city_clinics = []
for _, row in new_city_summary.iterrows():
    # proj_ntb = total city demand; per-clinic = divide by locations
    per_clinic_shows = int(row["proj_ntb"] / row["n_locations"])
    ss_monthly = per_clinic_shows * conversion_rate * rev_per_ntb
    y1_rev = ss_monthly * y1_factor
    monthly_ramp = [int(ss_monthly * r) for r in ramp_schedule]
    for _, loc_row in exp_new[exp_new["City"] == row["City"]].iterrows():
        new_city_clinics.append({
            "location": f"{row['City']} - {loc_row['Area Name']}",
            "city": row["City"],
            "state": row["State"],
            "tier": row["Tier"],
            "pincode": loc_row["Pincode"],
            "shows_mo": per_clinic_shows,
            "ss_monthly": ss_monthly,
            "y1_rev": y1_rev,
            **{f"M{i+1}": monthly_ramp[i] for i in range(12)},
        })
df_new = pd.DataFrame(new_city_clinics).sort_values("y1_rev", ascending=False)
total_new_y1 = df_new["y1_rev"].sum()

# Show% fix revenue (from Slide 4)
show_fix_rev = total_unlock * scenario_mult

# Combined
fy27_total = total_annual_rev + show_fix_rev + total_same_y1 + total_new_y1


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5: EXPANSION REVENUE — Per-Clinic Projections
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">📊 SLIDE 5 — EXPANSION REVENUE PROJECTION (₹22K/NTB Patient)'
    f'<div class="slide-sub">Same-City Satellites + New City Clinics | Ramp: 3-month setup → 12-month steady state | Scenario: {scenario}</div></div>',
    unsafe_allow_html=True,
)

# ── Revenue Waterfall + Monthly Ramp (side by side) ────────────────────────
col_wf, col_ramp = st.columns([1, 1])

with col_wf:
    wf_labels = ["Existing 61\nClinics", "Show% Fix\n(₹0 CAC)", "Same-City\nNew", "New City\n(Ratio)", "FY27 Total"]
    wf_values = [total_annual_rev, show_fix_rev, total_same_y1, total_new_y1, fy27_total]
    wf_measures = ["relative", "relative", "relative", "relative", "total"]

    fig_wf = go.Figure(go.Waterfall(
        x=wf_labels, y=[v / 1e7 for v in wf_values],
        measure=wf_measures,
        connector={"line": {"color": "#ccc"}},
        increasing={"marker": {"color": "#4CAF50"}},
        totals={"marker": {"color": "#1a73e8"}},
        text=[fmt_inr(v) for v in wf_values],
        textposition="outside",
    ))
    fig_wf.update_layout(
        title="FY27 Revenue Build-Up", height=400,
        margin=dict(l=40, r=20, t=40, b=60), yaxis_title="₹ Cr",
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with col_ramp:
    # Monthly cumulative ramp chart (same-city + new city combined)
    months = [f"{'Apr May Jun Jul Aug Sep Oct Nov Dec Jan Feb Mar'.split()[i]}-26" if i < 9
              else f"{'Apr May Jun Jul Aug Sep Oct Nov Dec Jan Feb Mar'.split()[i]}-27"
              for i in range(12)]
    monthly_same = [sum(r) for r in zip(*[
        [int(row[f"M{m+1}"]) for m in range(12)] for _, row in df_same.iterrows()
    ])] if len(df_same) > 0 else [0]*12
    monthly_new = [sum(r) for r in zip(*[
        [int(row[f"M{m+1}"]) for m in range(12)] for _, row in df_new.iterrows()
    ])] if len(df_new) > 0 else [0]*12
    monthly_combined = [s + n for s, n in zip(monthly_same, monthly_new)]
    cumulative = [sum(monthly_combined[:i+1]) for i in range(12)]

    fig_ramp = go.Figure()
    fig_ramp.add_trace(go.Bar(
        x=months, y=[v / 1e7 for v in monthly_combined],
        name="Monthly Revenue", marker_color="#4CAF50", opacity=0.7,
    ))
    fig_ramp.add_trace(go.Scatter(
        x=months, y=[v / 1e7 for v in cumulative],
        name="Cumulative", mode="lines+markers",
        line=dict(color="#dc3545", width=3), yaxis="y2",
    ))
    fig_ramp.update_layout(
        title="Expansion Revenue Ramp — Monthly + Cumulative",
        height=400, margin=dict(l=40, r=60, t=40, b=60),
        yaxis=dict(title="Monthly (₹ Cr)", side="left"),
        yaxis2=dict(title="Cumulative (₹ Cr)", side="right", overlaying="y"),
        legend=dict(x=0, y=1.1, orientation="h"),
    )
    st.plotly_chart(fig_ramp, use_container_width=True)


# ── Per-Clinic Revenue Projection (tabs) ──────────────────────────────────
st.markdown(f"### 📈 Per-Clinic Revenue Projection ({fmt_inr(rev_per_ntb)}/NTB Patient)")
rev_tab1, rev_tab2 = st.tabs(["Same-City New Clinics", "New City Clinics"])

with rev_tab1:
    target_annual = 44 * 1e5 * 12  # ₹528L/yr = ₹44L/mo target
    top25_same = df_same.head(25).sort_values("y1_rev", ascending=True)
    fig_same_bar = go.Figure(go.Bar(
        y=top25_same["location"],
        x=top25_same["y1_rev"] / 1e5,
        orientation="h",
        marker_color="#4CAF50",
        text=top25_same.apply(
            lambda r: f"₹{r['y1_rev']/1e5:.0f}L/yr | {r['shows_mo']} shows/mo | ₹{r['ss_monthly']/1e5:.1f}L/mo SS",
            axis=1,
        ),
        textposition="inside", textfont=dict(color="white", size=10),
    ))
    fig_same_bar.add_vline(x=target_annual / 1e5, line_dash="dash", line_color="red",
                           annotation_text=f"Target: ₹{target_annual/1e5:.0f}L/yr")
    fig_same_bar.update_layout(
        title=f"Same-City: Top 25 New Clinics — Year 1 Revenue Projection",
        height=650, margin=dict(l=200, r=20, t=40, b=40),
        xaxis_title="Year 1 Revenue (₹ Lakhs)",
    )
    st.plotly_chart(fig_same_bar, use_container_width=True)

    st.markdown(f"""
    <div class="insight-card">
    <b>Same-City Portfolio:</b> {len(df_same)} satellite locations across {df_same['city'].nunique()} cities |
    Year 1 Revenue: <b>{fmt_inr(total_same_y1)}</b> |
    Avg per clinic: <b>₹{df_same['y1_rev'].mean()/1e5:.0f}L/yr</b> |
    Ramp: 3-month setup → 12-month steady state
    </div>
    """, unsafe_allow_html=True)

with rev_tab2:
    # Deduplicate to show one bar per city (first/best location)
    new_by_city = df_new.drop_duplicates("city").sort_values("y1_rev", ascending=True)
    fig_new_bar = go.Figure(go.Bar(
        y=new_by_city["city"],
        x=new_by_city["y1_rev"] / 1e5,
        orientation="h",
        marker_color=["#1a73e8" if t == "Tier-2" else "#34a853" for t in new_by_city["tier"]],
        text=new_by_city.apply(
            lambda r: f"₹{r['y1_rev']/1e5:.0f}L/yr | {r['shows_mo']} shows/mo | {r['tier']} | ₹{r['ss_monthly']/1e5:.1f}L/mo SS",
            axis=1,
        ),
        textposition="inside", textfont=dict(color="white", size=11),
    ))
    fig_new_bar.add_vline(x=target_annual / 1e5, line_dash="dash", line_color="red",
                          annotation_text=f"Target: ₹{target_annual/1e5:.0f}L/yr")
    fig_new_bar.update_layout(
        title="New City: Per-City Year 1 Revenue (1 clinic per city initially)",
        height=500, margin=dict(l=130, r=20, t=40, b=40),
        xaxis_title="Year 1 Revenue (₹ Lakhs)",
    )
    st.plotly_chart(fig_new_bar, use_container_width=True)

    st.markdown(f"""
    <div class="insight-card">
    <b>New City Portfolio:</b> {new_by_city['city'].nunique()} cities ({(new_by_city['tier']=='Tier-2').sum()} Tier-2,
    {(new_by_city['tier']=='Tier-3').sum()} Tier-3) |
    Year 1 Revenue: <b>{fmt_inr(total_new_y1)}</b> |
    Phase 1: 1 clinic/city → expand after Month 6 validation
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6: EXPANSION FINANCIAL SUMMARY — Combined FY27 Outlook
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">💰 SLIDE 6 — COMBINED FY27 OUTLOOK: Revenue Streams + Investment Summary'
    f'<div class="slide-sub">Existing Network + Show% Fix + Same-City Satellites + New City Expansion | {scenario}</div></div>',
    unsafe_allow_html=True,
)

# ── Header metrics ─────────────────────────────────────────────────────────
om1, om2, om3, om4, om5 = st.columns(5)
om1.metric("Existing 61 Clinics", fmt_inr(total_annual_rev), "Current run-rate")
om2.metric("Show% Fix (₹0 CAC)", fmt_inr(show_fix_rev), f"{len(underperforming)} clinics")
om3.metric("Same-City Satellites", fmt_inr(total_same_y1), f"{len(df_same)} locations")
om4.metric("New City Clinics", fmt_inr(total_new_y1), f"{new_by_city['city'].nunique()} cities")
om5.metric("FY27 Total Potential", fmt_inr(fy27_total), "All streams combined")

# ── Monthly Revenue Ramp — Top 10 Same-City (heatmap) ─────────────────────
st.markdown("---")
st.markdown("**Monthly Revenue Ramp — Top 10 Same-City Clinics (₹ Lakhs)**")

top10_same = df_same.head(10)
ramp_data = []
for _, row in top10_same.iterrows():
    ramp_row = {"Location": row["location"]}
    for m in range(12):
        month_label = f"M{m+1}"
        ramp_row[month_label] = f"₹{row[month_label]/1e5:.0f}L"
    ramp_row["Year 1"] = f"₹{row['y1_rev']/1e5:.0f}L"
    ramp_data.append(ramp_row)
df_ramp_display = pd.DataFrame(ramp_data)
st.dataframe(df_ramp_display, hide_index=True, use_container_width=True)

# ── Investment Analysis ────────────────────────────────────────────────────
st.markdown("---")
col_inv, col_combined = st.columns([1, 1])

with col_inv:
    total_new_clinics = len(df_same.drop_duplicates("location")) + new_by_city["city"].nunique()
    total_capex = total_new_clinics * capex
    total_annual_opex = total_new_clinics * opex_monthly * 12
    total_exp_rev_y1 = total_same_y1 + total_new_y1
    total_exp_profit_y1 = total_exp_rev_y1 - total_annual_opex
    avg_payback = capex / ((total_exp_rev_y1 / total_new_clinics / 12) - opex_monthly) if total_exp_rev_y1 > total_annual_opex else float('inf')

    st.markdown("**🏗️ Investment Summary**")
    inv_data = {
        "Metric": [
            "New Clinics (Same-City + New City)",
            "Total Capex Investment",
            "Annual OpEx (all new clinics)",
            "Year 1 Expansion Revenue",
            "Year 1 Expansion Profit",
            "Avg Capex Payback Period",
            "Breakeven Visits / Clinic",
        ],
        "Value": [
            f"{total_new_clinics} clinics",
            fmt_inr(total_capex),
            fmt_inr(total_annual_opex),
            fmt_inr(total_exp_rev_y1),
            fmt_inr(total_exp_profit_y1),
            f"{avg_payback:.0f} months" if avg_payback < 100 else "N/A",
            f"{breakeven_visits} visits/month",
        ],
    }
    st.dataframe(pd.DataFrame(inv_data), hide_index=True, use_container_width=True)

with col_combined:
    st.markdown("**📊 Combined FY27 Outlook**")
    streams = pd.DataFrame({
        "Revenue Stream": ["Existing 61 Clinics", "Show% Fix (₹0 CAC)", "Same-City Satellites", "New City Expansion"],
        "Annual Revenue": [total_annual_rev, show_fix_rev, total_same_y1, total_new_y1],
    })
    streams["₹ Crore"] = streams["Annual Revenue"].apply(lambda x: f"₹{x/1e7:.1f} Cr")
    streams["% of Total"] = (streams["Annual Revenue"] / fy27_total * 100).apply(lambda x: f"{x:.0f}%")
    st.dataframe(streams[["Revenue Stream", "₹ Crore", "% of Total"]], hide_index=True, use_container_width=True)

    st.markdown(f"""
    <div style="background:#1a1a2e;color:white;padding:16px;border-radius:8px;margin-top:12px;text-align:center;">
    <span style="font-size:0.9rem;">Total FY27 Revenue Potential</span><br>
    <span style="font-size:1.8rem;font-weight:700;letter-spacing:0.5px;">{fmt_inr(fy27_total)}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Scenario Comparison for Expansion ──────────────────────────────────────
st.markdown("---")
col_sc, col_note = st.columns([1.2, 1])

with col_sc:
    sc_mults = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.15}
    sc_data = []
    for label, mult in sc_mults.items():
        sc_exist = total_annual_rev * mult / scenario_mult  # adjust for current mult
        sc_fix = show_fix_rev * mult / scenario_mult
        sc_same = total_same_y1 * mult
        sc_new = total_new_y1 * mult
        sc_data.append({"Scenario": label, "Total": (sc_exist + sc_fix + sc_same + sc_new) / 1e7})

    df_sc = pd.DataFrame(sc_data)
    fig_sc = go.Figure(go.Bar(
        x=df_sc["Scenario"], y=df_sc["Total"],
        marker_color=["#ffc107", "#FF6B35", "#4CAF50"],
        text=df_sc["Total"].apply(lambda x: f"₹{x:.1f} Cr"), textposition="outside",
    ))
    fig_sc.update_layout(
        title="FY27 Scenario Comparison (All Streams)",
        height=350, margin=dict(l=40, r=20, t=40, b=40),
        yaxis_title="Annual Revenue (₹ Cr)",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

with col_note:
    st.markdown(f"""
    <div style="background:#f8f9fa;border-radius:8px;padding:16px;border-left:4px solid #1a73e8;">
    <b>📋 Key Assumptions:</b><br><br>
    <b>Existing Clinics:</b> {len(cp)} clinics at L3M run-rate × {show_to_conv}% conversion × ₹{rev_per_ntb:,}/NTB<br><br>
    <b>Show% Fix:</b> Underperforming clinics raised to {industry_show}% benchmark — ₹0 CAC, zero new leases<br><br>
    <b>Same-City Satellites:</b> Each satellite captures 50% of city's best-performing parent clinic's NTB volume<br><br>
    <b>New City:</b> NTB projected from population × {ntb_pop_ratio.split('(')[0].strip()} NTB:Pop ratio, divided across {exp_new['Pincode'].nunique()} scouted locations<br><br>
    <b>Ramp:</b> 3-month setup → linear ramp to 100% by Month 6 → full steady-state M6-M12<br><br>
    <b>Unit Economics:</b> OpEx ₹{monthly_opex}L/mo | Capex ₹{capex_per_clinic}L | Breakeven: {breakeven_visits} visits/mo
    </div>
    """, unsafe_allow_html=True)

with st.expander("📋 Full Same-City Expansion Revenue Breakdown"):
    same_display = df_same[["location", "city", "shows_mo", "ss_monthly", "y1_rev"]].copy()
    same_display.columns = ["Location", "City", "Shows/mo", "SS Monthly (₹)", "Year 1 Rev (₹)"]
    same_display["SS Monthly (₹)"] = same_display["SS Monthly (₹)"].apply(lambda x: f"₹{x/1e5:.1f}L")
    same_display["Year 1 Rev (₹)"] = same_display["Year 1 Rev (₹)"].apply(lambda x: f"₹{x/1e5:.0f}L")
    st.dataframe(same_display, hide_index=True, use_container_width=True, height=400)

with st.expander("📋 Full New City Expansion Revenue Breakdown"):
    new_display = df_new.drop_duplicates("city")[["city", "state", "tier", "shows_mo", "ss_monthly", "y1_rev"]].copy()
    new_display.columns = ["City", "State", "Tier", "Shows/mo", "SS Monthly (₹)", "Year 1 Rev (₹)"]
    new_display["SS Monthly (₹)"] = new_display["SS Monthly (₹)"].apply(lambda x: f"₹{x/1e5:.1f}L")
    new_display["Year 1 Rev (₹)"] = new_display["Year 1 Rev (₹)"].apply(lambda x: f"₹{x/1e5:.0f}L")
    st.dataframe(new_display, hide_index=True, use_container_width=True, height=400)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7: RISK SCORECARD
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🚨 SLIDE 7 — RISK SCORECARD: What Could Go Wrong (and How We\'ll Know)'
    '<div class="slide-sub">Early warning indicators and contingency triggers</div></div>',
    unsafe_allow_html=True,
)

new_clinic_avg = cp[cp["total_appts"] < 3000]["l3m_ntb"].mean()
new_clinic_avg = f"{new_clinic_avg:.0f}" if pd.notna(new_clinic_avg) else "N/A"

risks = [
    {
        "Risk": "Show% continues declining",
        "Current": f"{cp['latest_show'].mean():.0%}",
        "Trigger": "<18% network avg for 2 consecutive months",
        "Impact": "High",
        "Revenue Impact": f"{fmt_inr(cp['l3m_appt'].sum() * 0.03 * rev_per_show * 12)}/yr per 3ppt drop",
        "Mitigation": "Doctor quality audit, follow-up protocol, patient experience overhaul",
        "Status": "🟡" if cp["latest_show"].mean() < 0.22 else "🟢",
    },
    {
        "Risk": "New clinic ramp-up slower than projected",
        "Current": f"{new_clinic_avg} visits/mo (new clinics)",
        "Trigger": f"<{breakeven_visits} visits/month at Month 3 (breakeven)",
        "Impact": "High",
        "Revenue Impact": f"{fmt_inr(capex)} capex at risk per clinic",
        "Mitigation": "Phase gate model — no new lease until Month 3 validation",
        "Status": "🟡",
    },
    {
        "Risk": "Rent escalation erodes margins",
        "Current": f"{fmt_inr(rent)} avg rent",
        "Trigger": ">7% annual escalation",
        "Impact": "Medium",
        "Revenue Impact": f"Breakeven shifts from {breakeven_visits} to {int(breakeven_visits*1.15)} visits at 7% escalation over 3 yrs",
        "Mitigation": "Negotiate 5% cap clauses, avoid >2yr lock-in for new cities",
        "Status": "🟢",
    },
    {
        "Risk": "Cannibalization from same-city expansion",
        "Current": f"{len(saturated)} clinics above threshold",
        "Trigger": ">15% appt decline in parent clinic after opening nearby",
        "Impact": "Medium",
        "Revenue Impact": "Net revenue neutral if new clinic doesn't add incremental demand",
        "Mitigation": "5km minimum separation, overlapping pincode analysis before approval",
        "Status": "🟡",
    },
    {
        "Risk": "Doctor attrition in new clinics",
        "Current": "2 doctors per clinic standard",
        "Trigger": "Doctor vacancy >2 weeks in any clinic",
        "Impact": "High",
        "Revenue Impact": "100% revenue loss during vacancy",
        "Mitigation": "Bench of 5-10% extra doctors, retention bonuses tied to Show%",
        "Status": "🟡",
    },
    {
        "Risk": "Conversion% drops below 70%",
        "Current": f"{show_to_conv}% (verified Jul-25 to Jan-26)",
        "Trigger": f"<70% for 2 months (breakeven shifts from {breakeven_visits} to {int(np.ceil(opex_monthly / (0.70 * rev_per_ntb)))} visits)",
        "Impact": "High",
        "Revenue Impact": f"Each 5ppt drop = {fmt_inr(cp['l3m_ntb'].sum() * 0.05 * rev_per_ntb * 12)}/yr network loss",
        "Mitigation": "Doctor consultation quality audit, product mix optimization, patient satisfaction tracking",
        "Status": "🟢",
    },
    {
        "Risk": "Tier-2 city demand overestimated",
        "Current": "Online demand ratio used for projection",
        "Trigger": f"<60% of projected visits at Month 6",
        "Impact": "Medium",
        "Revenue Impact": f"{fmt_inr(capex)} capex write-off if clinic closes",
        "Mitigation": "Lean 1-cabin format for tier-2, convert to full only after validation",
        "Status": "🟡",
    },
]

impact_colors = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}
for risk in risks:
    imp_color = impact_colors.get(risk["Impact"], "#666")
    st.markdown(f"""
    <div style="background:#f8f9fa;border-radius:8px;padding:14px;margin:8px 0;border-left:5px solid {imp_color};">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <b>{risk['Status']} {risk['Risk']}</b>
            <span style="background:{imp_color};color:white;padding:2px 8px;border-radius:4px;margin-left:8px;font-size:0.75rem;">{risk['Impact']}</span>
        </div>
    </div>
    <div style="margin-top:6px;font-size:0.85rem;color:#444;">
        <b>Current:</b> {risk['Current']} &nbsp;|&nbsp; <b>Trigger:</b> {risk['Trigger']}<br>
        <b>Revenue Impact:</b> {risk['Revenue Impact']}<br>
        <b>Mitigation:</b> {risk['Mitigation']}
    </div>
    </div>
    """, unsafe_allow_html=True)

# Rent stress test
st.markdown("---")
st.markdown("**🏗️ Rent Stress Test — 5-Year OpEx Escalation**")

stress_data = []
for rate in [0.05, 0.07, 0.10]:
    for yr in range(1, 6):
        new_opex = opex_monthly * (1 + rate) ** (yr - 1)
        stress_data.append({
            "Year": f"Year {yr}", "Escalation": f"{int(rate*100)}%",
            "Breakeven Visits": int(np.ceil(new_opex / rev_per_show)),
        })
df_stress = pd.DataFrame(stress_data)

fig_stress = px.bar(
    df_stress, x="Year", y="Breakeven Visits", color="Escalation",
    barmode="group", color_discrete_sequence=["#28a745", "#ffc107", "#dc3545"],
    text="Breakeven Visits",
)
fig_stress.update_layout(height=300, margin=dict(l=40, r=20, t=20, b=40), yaxis_title="Clinic Visits to Breakeven")
st.plotly_chart(fig_stress, use_container_width=True)

yr3_opex = monthly_opex * (1.07 ** 3)
yr3_be = int(np.ceil(opex_monthly * (1.07 ** 3) / rev_per_show))
st.markdown(f"""
<div class="insight-card insight-green">
✅ <b>{profitable_clinics}</b> currently profitable clinics survive Year 3 rent escalation at 7%.
</div>
<div class="insight-card">
💡 <b>Rent Stress Test:</b> At 7% annual escalation, OpEx rises from {fmt_inr(opex_monthly)} → {fmt_inr(yr3_opex * 1e5)}
over 3 years. Breakeven shifts from {breakeven_visits} → {yr3_be} visits/month.<br>
<b>Action:</b> Negotiate 5% cap clauses. Avoid lock-in >2 years for new cities.
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"Gynoveda FY27 Expansion Intelligence | Data through Jan 2026 | {len(cp)} clinics | Funnel: Appt → {_p75}% Show → {show_to_conv}% Conv → ₹{rev_per_ntb:,}/NTB | Generated {pd.Timestamp.now().strftime('%d-%b-%Y')}")
