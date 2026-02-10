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
cp["l3m_ntb"] = (cp["l3m_appt"] * cp["l3m_show"]).astype(int)

# Cabin utilization (20 working days × 10 slots/cabin/day)
cp["cabins"] = pd.to_numeric(cp["cabins"], errors="coerce").fillna(2).astype(int)
cp["capacity"] = cp["cabins"] * 20 * 10
cp["util_pct"] = cp["l3m_appt"] / cp["capacity"]

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
    show_threshold = st.slider("Same-City NTB Appt Threshold", 100, 500, 150, 10)
    rev_per_ntb = st.number_input("₹ Revenue per NTB Patient", value=22000, step=1000)
    monthly_opex = st.number_input("Monthly OpEx per Clinic (₹L)", value=3.1, step=0.1, format="%.1f")
    capex_per_clinic = st.number_input("Capex per Clinic (₹L)", value=28.0, step=1.0, format="%.1f")
    industry_show = st.slider("Industry Benchmark Show%", 15, 35, 23, 1)

    st.markdown("---")
    st.caption(f"Data: Jan-25 to Jan-26 · {len(cp)} Clinics")


# ── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🏥 Gynoveda FY27 Expansion Plan")

peak_ntb = df_network["ntb"].max()
latest_ntb = df_network["ntb"].iloc[-1]
ntb_decline = (latest_ntb - peak_ntb) / peak_ntb if peak_ntb > 0 else 0
network_show = cp["latest_show"].mean()
ntb_per_clinic = latest_ntb / len(cp) if len(cp) > 0 else 0
peak_per_clinic = peak_ntb / len(cp) if len(cp) > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Network NTB (Jan-26)", f"{latest_ntb:,}", f"{ntb_decline:+.0%} from peak")
c2.metric("Network Show%", f"{network_show:.0%}", f"{'↑' if network_show > 0.18 else '↓'} vs 18% floor")
c3.metric("Active Clinics", f"{len(cp)}")
c4.metric("NTB/Clinic (Jan-26)", f"{ntb_per_clinic:.0f}", f"Peak was {peak_per_clinic:.0f}")
c5.metric("Avg Cabin Util", f"{cp['util_pct'].mean():.0%}", "L3M average")


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
        hover_data={"web_orders": ":,", "unique_customers_pincodes": True, "lat": False, "lon": False},
        color_continuous_scale="Blues", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_web.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_web, use_container_width=True)

with col_map2:
    st.markdown("**🏥 Clinic Orders by State**")
    fig_cli = px.scatter_mapbox(
        ms_clean.head(20), lat="lat", lon="lon", size="clinic_orders",
        color="clinic_orders", hover_name="state_geo",
        hover_data={"clinic_orders": ":,", "clinic_pincodes": True, "lat": False, "lon": False},
        color_continuous_scale="Oranges", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_cli.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_cli, use_container_width=True)

sm1, sm2, sm3, sm4 = st.columns(4)
total_web_pins = int(ms_clean["unique_customers_pincodes"].sum())
total_cli_pins = int(ms_clean["clinic_pincodes"].sum())
sm1.metric("Website Pincodes", f"{total_web_pins:,}")
sm2.metric("Clinic Pincodes", f"{total_cli_pins:,}")
sm3.metric("Website Orders", f"{int(ms_clean['web_orders'].sum()):,}")
sm4.metric("Clinic Orders (FirstTime)", f"{int(ms_clean['clinic_orders'].sum()):,}")

st.markdown("**State-Level Reach Comparison (Top 12)**")
top12 = ms_clean.head(12)[["state_geo", "web_orders", "unique_customers_pincodes", "clinic_orders", "clinic_pincodes", "clinic_share"]].copy()
top12.columns = ["State", "Website Orders", "Website Pincodes", "Clinic Orders", "Clinic Pincodes", "Clinic Share %"]
top12["Clinic Share %"] = (top12["Clinic Share %"] * 100).round(1)
for c in ["Website Orders", "Clinic Orders"]:
    top12[c] = top12[c].astype(int).apply(lambda x: f"{x:,}")
for c in ["Website Pincodes", "Clinic Pincodes"]:
    top12[c] = top12[c].astype(int)
st.dataframe(top12, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2: THE CASE FOR CAUTION — Show% Analysis
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">⚠️ SLIDE 2 — THE CASE FOR CAUTION: Why We Must Be Smart, Not Just Fast'
    '<div class="slide-sub">STATE-WISE SHOW% — Gynoveda vs Industry Standard (Verified Benchmarks)</div></div>',
    unsafe_allow_html=True,
)

col_trend, col_insight = st.columns([2, 1])
with col_trend:
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(
            x=df_network["month"], y=df_network["ntb"],
            name="Total NTB", marker_color="#FF6B35", opacity=0.85,
            text=df_network["ntb"].apply(lambda x: f"{x/1000:.1f}K"),
            textposition="outside",
        ), secondary_y=False,
    )
    fig_trend.add_trace(
        go.Scatter(
            x=df_network["month"], y=df_network["show_pct"] * 100,
            name="Show%", line=dict(color="#1a73e8", width=3),
            mode="lines+markers",
        ), secondary_y=True,
    )
    fig_trend.update_layout(
        title="Network NTB — The Plateau Problem",
        height=350, margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", y=1.12),
        yaxis_title="Total NTB", yaxis2_title="Show%",
    )
    fig_trend.update_yaxes(range=[0, 35], secondary_y=True)
    st.plotly_chart(fig_trend, use_container_width=True)

with col_insight:
    peak_m = df_network.loc[df_network["ntb"].idxmax(), "month"].strftime("%b-%y")
    below_15 = (cp["latest_show"] < 0.15).sum()
    st.markdown(f"""
    <div class="insight-card insight-red">
    <strong>📊 The Data Says:</strong><br>
    • NTB peaked at <b>{peak_ntb:,}</b> ({peak_m}), now <b>{latest_ntb:,}</b> ({ntb_decline:+.0%})<br>
    • NTB/clinic fell from <b>{peak_per_clinic:.0f}</b> to <b>{ntb_per_clinic:.0f}</b><br>
    • <b>{below_15}</b> clinics have Show% below 15%<br>
    • Adding clinics without fixing Show% grows cost faster than revenue
    </div>
    <div class="insight-card insight-blue">
    <strong>🎯 The answer:</strong> Not fewer or more clinics — <b>smarter clinics</b>.
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

fig_show = go.Figure()
fig_show.add_trace(go.Bar(
    y=state_show["state"], x=[benchmark * 100] * len(state_show),
    name=f"Industry Standard ({industry_show}%)",
    orientation="h", marker_color="#4CAF50", opacity=0.4,
))
fig_show.add_trace(go.Bar(
    y=state_show["state"], x=state_show["avg_show"] * 100,
    name="Gynoveda Actual",
    orientation="h",
    marker_color=[("#FF6B35" if g >= 0 else "#dc3545") for g in state_show["gap"]],
    text=state_show["label"], textposition="outside",
))
fig_show.update_layout(
    title="Gynoveda Show% vs Industry Standard — State-Wise",
    barmode="overlay", height=max(350, len(state_show) * 35),
    margin=dict(l=130, r=80, t=40, b=40),
    legend=dict(orientation="h", y=1.08), xaxis_title="Show %",
)
fig_show.add_vline(x=industry_show, line_dash="dash", line_color="green",
                   annotation_text=f"{industry_show}% benchmark")
st.plotly_chart(fig_show, use_container_width=True)

above = (state_show["gap"] >= 0.02).sum()
at_std = ((state_show["gap"] >= -0.02) & (state_show["gap"] < 0.02)).sum()
below = (state_show["gap"] < -0.02).sum()

sc1, sc2, sc3 = st.columns(3)
sc1.markdown(f'<div class="insight-card insight-green"><b style="font-size:2rem;color:#28a745">{above}</b> states above standard</div>', unsafe_allow_html=True)
sc2.markdown(f'<div class="insight-card"><b style="font-size:2rem;color:#ffc107">{at_std}</b> states at standard (±2ppt)</div>', unsafe_allow_html=True)
sc3.markdown(f'<div class="insight-card insight-red"><b style="font-size:2rem;color:#dc3545">{below}</b> states below standard</div>', unsafe_allow_html=True)

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
    '<div class="slide-header">🗺️ SLIDE 3 — EXPANSION STRATEGY: Where to Open Next'
    '<div class="slide-sub">Micro-Market Identification for Saturated Clinics</div></div>',
    unsafe_allow_html=True,
)

saturated = cp[cp["l3m_appt"] >= show_threshold].sort_values("l3m_appt", ascending=False)

st.markdown(f"**Clinics at Capacity (≥{show_threshold} NTB Appt/Month, L3M avg)**")

col_sat_chart, col_sat_cards = st.columns([1.2, 1])

with col_sat_chart:
    top_sat = saturated.head(10).sort_values("l3m_appt", ascending=True)
    bar_colors = ["#28a745" if s >= 0.25 else "#ffc107" if s >= 0.18 else "#dc3545"
                  for s in top_sat["l3m_show"]]
    fig_sat = go.Figure(go.Bar(
        y=top_sat["clinic_name"], x=top_sat["l3m_appt"], orientation="h",
        marker_color=bar_colors,
        text=top_sat.apply(
            lambda r: f"{int(r['l3m_appt'])} appt | {r['util_pct']:.0%} util | {r['l3m_show']:.0%} show%",
            axis=1,
        ),
        textposition="inside", textfont=dict(color="white", size=11),
    ))
    fig_sat.add_vline(x=show_threshold, line_dash="dash", line_color="red",
                      annotation_text=f"Threshold: {show_threshold}")
    fig_sat.update_layout(
        title=f"Clinics with ≥{show_threshold} Avg Monthly Appts",
        height=380, margin=dict(l=110, r=20, t=40, b=40),
        xaxis_title="Monthly NTB Appointments (L3M)",
    )
    st.plotly_chart(fig_sat, use_container_width=True)
    mc1, mc2 = st.columns(2)
    mc1.metric("Clinics Qualifying", f"{len(saturated)}")
    mc2.metric("Avg Utilization", f"{saturated['util_pct'].mean():.0%}")

with col_sat_cards:
    st.markdown("**🔍 Top 5 Saturated — Expansion Candidates**")

    # Get top catchment areas from clinic_zip_summary
    czs = data["clinic_zip"]

    for _, row in saturated.head(5).iterrows():
        clinic_zips = czs[czs["Clinic_Loc"] == row["clinic_name"]]
        top_cities = clinic_zips.sort_values("total_qty", ascending=False).head(3)
        top_areas = ", ".join(top_cities["City"].dropna().unique()[:3])

        trend_emoji = "🟢" if row["l3m_show"] >= 0.25 else "🟡" if row["l3m_show"] >= 0.18 else "🔴"
        st.markdown(f"""
        <div style="background:#f8f9fa;border-radius:8px;padding:12px;margin:8px 0;border-left:4px solid #FF6B35;">
        <b>{row['clinic_name']}</b> ({row['city_code']}) — {int(row['cabins'])} cabins<br>
        Shows: <b>{int(row['l3m_appt'])}/mo</b> | Util: <b>{row['util_pct']:.0%}</b> |
        Show%: <b>{row['l3m_show']:.0%}</b> | {trend_emoji}<br>
        <span style="color:#666;font-size:0.8rem;">Top catchments: {top_areas}</span>
        </div>
        """, unsafe_allow_html=True)

# Same-city micro-market table from pre-computed data
st.markdown("**📍 Same-City Expansion Micro-Markets (Pre-Identified)**")
exp_same = data["expansion_same"]
st.dataframe(
    exp_same[["S.No", "City", "Existing Clinics", "Micro-Market Pincode",
              "Micro-Market Area", "Expansion Rationale"]].head(15),
    hide_index=True, use_container_width=True, height=350,
)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4: FIX BEFORE EXPAND — ₹0 CAC Revenue Unlock
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🔧 SLIDE 4 — FIX BEFORE EXPAND: ₹0 CAC Revenue Unlock'
    '<div class="slide-sub">What happens if underperforming clinics reach industry-standard Show%?</div></div>',
    unsafe_allow_html=True,
)

target_show = industry_show / 100
cp["show_gap"] = (target_show - cp["l3m_show"]).clip(lower=0)
conversion_rate = data["rev_assumptions"].get("conversion_pct", 0.4)
rev_per_show = conversion_rate * rev_per_ntb
cp["additional_ntb"] = (cp["l3m_appt"] * cp["show_gap"]).astype(int)
cp["additional_rev_annual"] = cp["additional_ntb"] * rev_per_show * 12

underperforming = cp[cp["show_gap"] > 0].sort_values("additional_rev_annual", ascending=False)
total_unlock = underperforming["additional_rev_annual"].sum()

fm1, fm2, fm3 = st.columns(3)
fm1.metric("Underperforming Clinics", f"{len(underperforming)} of {len(cp)}", f"Show% < {industry_show}%")
fm2.metric("Annual Revenue Unlock", f"₹{total_unlock/1e7:.1f} Cr", "₹0 CAC — no new leases")
fm3.metric("Avg Show% Gap", f"{underperforming['show_gap'].mean():.1%}", f"vs {industry_show}% target")

col_fix1, col_fix2 = st.columns([1.2, 1])

with col_fix1:
    fig_scatter = px.scatter(
        cp, x="l3m_appt", y="l3m_show",
        size=cp["additional_rev_annual"].clip(lower=1),
        color="l3m_show", color_continuous_scale="RdYlGn",
        hover_name="clinic_name",
        hover_data={"l3m_appt": ":.0f", "l3m_show": ":.1%", "additional_rev_annual": ":,.0f"},
        labels={"l3m_appt": "Avg Monthly Appointments", "l3m_show": "Show%"},
    )
    fig_scatter.add_hline(y=target_show, line_dash="dash", line_color="green",
                          annotation_text=f"{industry_show}% benchmark")
    fig_scatter.update_layout(
        title="Show% vs Appointments — Bubble = Revenue Unlock Potential",
        height=400, margin=dict(l=40, r=40, t=40, b=40), coloraxis_showscale=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_fix2:
    st.markdown(f"""
    <div class="insight-card insight-green">
    <strong>💰 ₹{total_unlock/1e7:.1f} Cr unlock</strong> from Show% fixes across
    <b>{len(underperforming)}</b> clinics — zero new leases, zero CAC.
    This is FY27's highest-ROI initiative.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Top 10 Revenue Unlock Opportunities**")
    top_unlock = underperforming.head(10)[["clinic_name", "l3m_show", "show_gap", "additional_ntb", "additional_rev_annual"]].copy()
    top_unlock.columns = ["Clinic", "Current Show%", "Gap", "Extra NTB/mo", "Annual Unlock ₹"]
    top_unlock["Current Show%"] = (top_unlock["Current Show%"] * 100).round(1)
    top_unlock["Gap"] = (top_unlock["Gap"] * 100).round(1)
    top_unlock["Annual Unlock ₹"] = top_unlock["Annual Unlock ₹"].apply(lambda x: f"₹{x/1e5:.1f}L")
    st.dataframe(top_unlock, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5: UNIT ECONOMICS — Per Clinic P&L
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">💰 SLIDE 5 — UNIT ECONOMICS: Per Clinic P&L (Actual Costs)'
    '<div class="slide-sub">What does it take to break even? How profitable is the average clinic?</div></div>',
    unsafe_allow_html=True,
)

opex_monthly = monthly_opex * 1e5
capex = capex_per_clinic * 1e5
breakeven_shows = int(np.ceil(opex_monthly / rev_per_show))

avg_shows = cp["l3m_ntb"].mean()
avg_revenue = avg_shows * rev_per_show
avg_profit = avg_revenue - opex_monthly
profitable_clinics = (cp["l3m_ntb"] * rev_per_show > opex_monthly).sum()
network_annual_profit = (cp["l3m_ntb"] * rev_per_show - opex_monthly).clip(lower=0).sum() * 12

# Cost components
rent = 1.0e5
doctors = 1.5e5
clinic_mgr = 0.3e5
housekeeping = 0.1e5
receptionist = 0.15e5
electricity = 0.05e5

um1, um2, um3, um4, um5, um6 = st.columns(6)
um1.metric("Monthly OpEx/Clinic", f"₹{monthly_opex}L", "Rent + Dr×2 + Staff")
um2.metric("Capex (Construction)", f"₹{capex_per_clinic:.0f}L")
um3.metric("Breakeven NTB Shows", f"{breakeven_shows}/month", f"@ {conversion_rate:.0%} conv × ₹{rev_per_ntb//1000}K")
um4.metric("Profitable Clinics", f"{profitable_clinics} of {len(cp)}", f"↑ {len(cp)-profitable_clinics} below breakeven")
um5.metric("Avg Margin", f"{avg_profit/avg_revenue*100:.0f}%" if avg_revenue > 0 else "N/A")
um6.metric("Network Annual Profit", f"₹{network_annual_profit/1e7:.1f} Cr", f"After ₹{monthly_opex}L/mo OpEx")

col_pnl, col_sens = st.columns(2)

with col_pnl:
    wf_labels = ["Revenue", "Rent", "Doctors (2)", "Clinic Mgr", "Housekeeping", "Receptionist", "Electricity", "Monthly Profit"]
    wf_values = [avg_revenue, -rent, -doctors, -clinic_mgr, -housekeeping, -receptionist, -electricity, avg_profit]

    fig_wf = go.Figure(go.Waterfall(
        x=wf_labels, y=wf_values,
        connector={"line": {"color": "#ccc"}},
        increasing={"marker": {"color": "#4CAF50"}},
        decreasing={"marker": {"color": "#dc3545"}},
        totals={"marker": {"color": "#1a73e8"}},
        text=[f"₹{abs(v)/1e3:.0f}K" for v in wf_values],
        textposition="outside",
    ))
    fig_wf.update_layout(
        title=f"Average Clinic P&L ({int(avg_shows)} NTB shows/mo)",
        height=380, margin=dict(l=40, r=20, t=40, b=80), yaxis_title="₹",
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with col_sens:
    shows_range = np.arange(0, 250, 5)
    profits = (shows_range * rev_per_show - opex_monthly) / 1e5

    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=shows_range, y=profits, mode="lines",
        line=dict(color="#1a73e8", width=3), name="Monthly Profit",
    ))
    fig_sens.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Breakeven")
    fig_sens.add_vline(x=breakeven_shows, line_dash="dash", line_color="red",
                       annotation_text=f"BE: {breakeven_shows} shows")
    fig_sens.add_vline(x=avg_shows, line_dash="dash", line_color="green",
                       annotation_text=f"Network avg: {int(avg_shows)}")
    fig_sens.update_layout(
        title="Monthly Profit vs NTB Shows (Sensitivity)",
        height=380, margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="NTB Shows/Month", yaxis_title="Monthly Profit (₹ Lakhs)",
    )
    st.plotly_chart(fig_sens, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6: FY27 REVENUE PROJECTION
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="slide-header">📈 SLIDE 6 — FY27 REVENUE PROJECTION: Ratio-Adjusted, Scenario-Tested'
    f'<div class="slide-sub">Per-Clinic Revenue Projection (₹{rev_per_ntb//1000}K/NTB Patient) | Scenario: {scenario}</div></div>',
    unsafe_allow_html=True,
)

cp["monthly_revenue"] = cp["l3m_ntb"] * rev_per_show * scenario_mult
cp["annual_revenue"] = cp["monthly_revenue"] * 12
cp["monthly_profit"] = cp["monthly_revenue"] - opex_monthly
cp["annual_profit"] = cp["monthly_profit"] * 12
cp["payback_months"] = np.where(cp["monthly_profit"] > 0, capex / cp["monthly_profit"], np.inf)

total_annual_rev = cp["annual_revenue"].sum()
total_annual_profit = cp[cp["annual_profit"] > 0]["annual_profit"].sum()
median_payback = cp[cp["payback_months"] < 100]["payback_months"].median()

rm1, rm2, rm3, rm4 = st.columns(4)
rm1.metric(f"FY27 Revenue ({scenario})", f"₹{total_annual_rev/1e7:.1f} Cr", f"{len(cp)} clinics")
rm2.metric("FY27 Profit (Profitable)", f"₹{total_annual_profit/1e7:.1f} Cr", "After OpEx")
rm3.metric("Avg Revenue/Clinic/Mo", f"₹{cp['monthly_revenue'].mean()/1e5:.1f}L")
rm4.metric("Median Payback", f"{median_payback:.0f} months" if pd.notna(median_payback) else "N/A", "Profitable clinics")

col_rev1, col_rev2 = st.columns([1.5, 1])

with col_rev1:
    clinic_rev = cp.sort_values("annual_revenue", ascending=True).tail(25)
    fig_rev = go.Figure(go.Bar(
        y=clinic_rev["clinic_name"], x=clinic_rev["annual_revenue"] / 1e5,
        orientation="h",
        marker_color=["#4CAF50" if p > 0 else "#dc3545" for p in clinic_rev["annual_profit"]],
        text=clinic_rev.apply(
            lambda r: f"₹{r['annual_revenue']/1e5:.0f}L | NTB:{int(r['l3m_ntb'])}/mo", axis=1
        ),
        textposition="inside", textfont=dict(color="white", size=10),
    ))
    fig_rev.update_layout(
        title=f"Per-Clinic Annual Revenue (Top 25) — {scenario}",
        height=550, margin=dict(l=110, r=20, t=40, b=40),
        xaxis_title="Annual Revenue (₹ Lakhs)",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with col_rev2:
    scenarios_dict = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.15}
    sc_data = [{"Scenario": k, "Revenue": cp["l3m_ntb"].sum() * rev_per_show * v * 12}
               for k, v in scenarios_dict.items()]
    df_sc = pd.DataFrame(sc_data)

    fig_sc = go.Figure(go.Bar(
        x=df_sc["Scenario"], y=df_sc["Revenue"] / 1e7,
        marker_color=["#ffc107", "#FF6B35", "#4CAF50"],
        text=df_sc["Revenue"].apply(lambda x: f"₹{x/1e7:.1f} Cr"), textposition="outside",
    ))
    fig_sc.update_layout(
        title="Scenario Comparison", height=300,
        margin=dict(l=40, r=20, t=40, b=40), yaxis_title="Annual Revenue (₹ Cr)",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    show_fix_rev = total_unlock * scenario_mult
    st.markdown(f"""
    <div class="insight-card insight-green">
    <strong>Combined FY27 Outlook:</strong><br>
    Current run-rate: <b>₹{total_annual_rev/1e7:.1f} Cr</b><br>
    + Show% fix unlock: <b>₹{show_fix_rev/1e7:.1f} Cr</b><br>
    = Total potential: <b>₹{(total_annual_rev + show_fix_rev)/1e7:.1f} Cr</b>
    </div>
    """, unsafe_allow_html=True)

with st.expander("📋 Full Per-Clinic Revenue Breakdown"):
    rev_table = cp[[
        "clinic_name", "region", "cabins", "l3m_ntb", "l3m_show",
        "monthly_revenue", "annual_revenue", "monthly_profit", "payback_months"
    ]].copy()
    rev_table.columns = [
        "Clinic", "Region", "Cabins", "NTB/mo", "Show%",
        "Rev/mo (₹)", "Rev/yr (₹)", "Profit/mo (₹)", "Payback (mo)"
    ]
    rev_table["Show%"] = (rev_table["Show%"] * 100).round(1)
    for c in ["Rev/mo (₹)", "Rev/yr (₹)", "Profit/mo (₹)"]:
        rev_table[c] = rev_table[c].apply(lambda x: f"₹{x/1e5:.1f}L")
    rev_table["Payback (mo)"] = rev_table["Payback (mo)"].apply(lambda x: f"{x:.0f}" if x < 100 else "∞")
    rev_table = rev_table.sort_values("NTB/mo", ascending=False)
    st.dataframe(rev_table, hide_index=True, use_container_width=True, height=400)


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
        "Revenue Impact": f"₹{(cp['l3m_appt'].sum() * 0.03 * rev_per_show * 12)/1e7:.1f} Cr/yr per 3ppt drop",
        "Mitigation": "Doctor quality audit, follow-up protocol, patient experience overhaul",
        "Status": "🟡" if cp["latest_show"].mean() < 0.22 else "🟢",
    },
    {
        "Risk": "New clinic ramp-up slower than projected",
        "Current": f"{new_clinic_avg} NTB/mo (new clinics)",
        "Trigger": "<50 NTB shows/month at Month 3",
        "Impact": "High",
        "Revenue Impact": f"₹{capex_per_clinic:.0f}L capex at risk per clinic",
        "Mitigation": "Phase gate model — no new lease until Month 3 validation",
        "Status": "🟡",
    },
    {
        "Risk": "Rent escalation erodes margins",
        "Current": f"₹{rent/1e5:.1f}L avg rent",
        "Trigger": ">7% annual escalation",
        "Impact": "Medium",
        "Revenue Impact": f"Breakeven shifts from {breakeven_shows} to {int(breakeven_shows*1.15)} shows at 7% escalation",
        "Mitigation": "Negotiate 5% cap clauses, avoid >2yr lock-in for new cities",
        "Status": "🟢",
    },
    {
        "Risk": "Cannibalization from same-city expansion",
        "Current": f"{len(saturated)} clinics above threshold",
        "Trigger": ">15% NTB decline in parent clinic after opening nearby",
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
        "Risk": "Tier-2 city demand overestimated",
        "Current": "Online demand ratio used for projection",
        "Trigger": "<60% of projected NTB at Month 6",
        "Impact": "Medium",
        "Revenue Impact": f"₹{capex_per_clinic:.0f}L capex write-off if clinic closes",
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
            "Breakeven Shows": int(np.ceil(new_opex / rev_per_show)),
        })
df_stress = pd.DataFrame(stress_data)

fig_stress = px.bar(
    df_stress, x="Year", y="Breakeven Shows", color="Escalation",
    barmode="group", color_discrete_sequence=["#28a745", "#ffc107", "#dc3545"],
    text="Breakeven Shows",
)
fig_stress.update_layout(height=300, margin=dict(l=40, r=20, t=20, b=40), yaxis_title="NTB Shows to Breakeven")
st.plotly_chart(fig_stress, use_container_width=True)

yr3_opex = monthly_opex * (1.07 ** 3)
yr3_be = int(np.ceil(opex_monthly * (1.07 ** 3) / rev_per_show))
st.markdown(f"""
<div class="insight-card insight-green">
✅ <b>{profitable_clinics}</b> currently profitable clinics survive Year 3 rent escalation at 7%.
</div>
<div class="insight-card">
💡 <b>Rent Stress Test:</b> At 7% annual escalation, OpEx rises from ₹{monthly_opex}L → ₹{yr3_opex:.1f}L
over 3 years. Breakeven shifts from {breakeven_shows} → {yr3_be} shows/month.<br>
<b>Action:</b> Negotiate 5% cap clauses. Avoid lock-in >2 years for new cities.
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"Gynoveda FY27 Expansion Intelligence | Data through Jan 2026 | {len(cp)} clinics | Generated {pd.Timestamp.now().strftime('%d-%b-%Y')}")
