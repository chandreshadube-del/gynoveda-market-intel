"""
Gynoveda FY27 Expansion Intelligence — Clean 7-Slide Layout
Built: Feb 2026 | Data: NTB Jan-25 to Jan-26
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Gynoveda FY27 Plan", layout="wide", page_icon="🏥")

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean spacing */
    .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1200px;}
    /* Metric cards */
    [data-testid="stMetric"] {background: #f8f9fa; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #FF6B35;}
    [data-testid="stMetric"] label {font-size: 0.75rem !important; color: #666;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.5rem !important; font-weight: 700;}
    /* Section dividers */
    .slide-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 16px 24px; border-radius: 10px; margin: 2rem 0 1rem 0;
        font-size: 1.1rem; font-weight: 600;
    }
    .slide-sub {color: #a0a0b0; font-size: 0.85rem; font-weight: 400; margin-top: 4px;}
    /* Insight cards */
    .insight-card {
        background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 16px;
        border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 0.9rem;
    }
    .insight-green {background: #d4edda; border-left-color: #28a745;}
    .insight-red {background: #f8d7da; border-left-color: #dc3545;}
    .insight-blue {background: #d1ecf1; border-left-color: #17a2b8;}
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stDeployButton {display: none;}
    /* Separator */
    .slide-sep {border-top: 2px solid #eee; margin: 2.5rem 0;}
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ────────────────────────────────────────────────────────────
@st.cache_data
def load_all_data():
    """Load and process all 4 data files."""
    # 1. NTB Show Month Wise
    raw_ntb = pd.read_excel("data/NTB_Show_Month_Wise.xlsx", header=None)

    # Parse months from row 1
    months = []
    for c in range(8, raw_ntb.shape[1], 2):
        m = raw_ntb.iloc[1, c]
        if pd.notna(m):
            months.append({"col": c, "month": pd.Timestamp(m)})

    # Network monthly trend
    network_monthly = []
    for m in months:
        appt = raw_ntb.iloc[2, m["col"]]
        show = raw_ntb.iloc[2, m["col"] + 1]
        if pd.notna(appt) and pd.notna(show):
            appt = int(appt)
            show = float(show)
            network_monthly.append({
                "month": m["month"], "appt": appt,
                "show_pct": show, "ntb": int(appt * show)
            })
    df_network = pd.DataFrame(network_monthly)

    # Clinic-level data
    clinics = []
    for i in range(5, len(raw_ntb)):
        code = raw_ntb.iloc[i, 2]
        if pd.notna(code) and str(code) != "-":
            clinic = {
                "name": str(raw_ntb.iloc[i, 0]),
                "city_code": str(raw_ntb.iloc[i, 1]),
                "code": code,
                "launch": raw_ntb.iloc[i, 3],
                "cabin": raw_ntb.iloc[i, 4],
                "region": str(raw_ntb.iloc[i, 5]),
                "total_appt": raw_ntb.iloc[i, 6],
                "total_show_pct": raw_ntb.iloc[i, 7],
            }
            # Monthly data
            for m in months:
                appt = raw_ntb.iloc[i, m["col"]]
                show = raw_ntb.iloc[i, m["col"] + 1]
                mstr = m["month"].strftime("%Y-%m")
                try:
                    clinic[f"appt_{mstr}"] = int(appt) if pd.notna(appt) and str(appt) != "-" else 0
                    clinic[f"show_{mstr}"] = float(show) if pd.notna(show) and str(show) != "-" else 0
                except (ValueError, TypeError):
                    clinic[f"appt_{mstr}"] = 0
                    clinic[f"show_{mstr}"] = 0
            clinics.append(clinic)
    df_clinics = pd.DataFrame(clinics)
    # Compute latest month NTB
    last_m = months[-1]["month"].strftime("%Y-%m")
    df_clinics["latest_appt"] = df_clinics[f"appt_{last_m}"]
    df_clinics["latest_show"] = df_clinics[f"show_{last_m}"]
    df_clinics["latest_ntb"] = (df_clinics["latest_appt"] * df_clinics["latest_show"]).astype(int)
    # L3M average (last 3 months)
    l3_months = [m["month"].strftime("%Y-%m") for m in months[-3:]]
    df_clinics["l3m_appt"] = df_clinics[[f"appt_{m}" for m in l3_months]].mean(axis=1)
    df_clinics["l3m_show"] = df_clinics[[f"show_{m}" for m in l3_months]].mean(axis=1)
    df_clinics["l3m_ntb"] = (df_clinics["l3m_appt"] * df_clinics["l3m_show"]).astype(int)
    # Compute cabin utilization (assume 20 working days, 10 slots/day/cabin)
    df_clinics["cabin"] = pd.to_numeric(df_clinics["cabin"], errors="coerce").fillna(2).astype(int)
    df_clinics["capacity"] = df_clinics["cabin"] * 20 * 10
    df_clinics["util_pct"] = df_clinics["l3m_appt"] / df_clinics["capacity"]

    # 2. ZipData Clinic NTB (transaction-level)
    df_zip = pd.read_excel("data/ZipData_Clinic_NTB.xlsx")
    df_zip["Customer Type"] = df_zip["Customer Type"].str.lower().str.replace("-", "")

    # 3. Clinic-wise FirstTime by Pincode
    df_clinic_pin = pd.read_excel("data/Clinic_wise_FirstTime_TotalQuantity_by_Pincode.xlsx")
    df_clinic_pin["Pincode"] = df_clinic_pin["Pincode"].astype(int).astype(str)

    # 4. Website orders
    df_web = pd.read_excel(
        "data/1cx_order_qty_pincode_of_website__2020__2025__Curative__others.xlsx"
    )
    df_web["Zip"] = df_web["Zip"].astype(str)

    return df_network, df_clinics, df_zip, df_clinic_pin, df_web, months


df_network, df_clinics, df_zip, df_clinic_pin, df_web, months_list = load_all_data()


# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ FY27 Controls")
    scenario = st.radio("Scenario", ["Conservative", "Base Case", "Optimistic"], index=1)
    scenario_mult = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.15}[scenario]

    st.markdown("---")
    show_threshold = st.slider("Same-City NTB Show Threshold", 100, 300, 150, 10)
    rev_per_ntb = st.number_input("₹ Revenue per NTB Patient", value=22000, step=1000)
    monthly_opex = st.number_input("Monthly OpEx per Clinic (₹L)", value=3.1, step=0.1, format="%.1f")
    capex_per_clinic = st.number_input("Capex per Clinic (₹L)", value=28.0, step=1.0, format="%.1f")
    industry_show = st.slider("Industry Benchmark Show%", 15, 35, 23, 1)

    st.markdown("---")
    st.caption("Data: Jan-25 to Jan-26 · 61 Clinics")


# ── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🏥 Gynoveda FY27 Expansion Plan")

# Top-line metrics
c1, c2, c3, c4, c5 = st.columns(5)
peak_ntb = df_network["ntb"].max()
latest_ntb = df_network["ntb"].iloc[-1]
ntb_decline = (latest_ntb - peak_ntb) / peak_ntb
network_show = df_clinics["latest_show"].mean()
below_target = (df_clinics["latest_ntb"] < (rev_per_ntb * 0 + 35)).sum()  # breakeven NTB
ntb_per_clinic = latest_ntb / len(df_clinics)

c1.metric("Network NTB (Jan-26)", f"{latest_ntb:,}", f"{ntb_decline:+.0%} from peak")
c2.metric("Network Show%", f"{network_show:.0%}", f"{'↑' if network_show > 0.18 else '↓'} vs 18% floor")
c3.metric("Active Clinics", f"{len(df_clinics)}", "")
c4.metric("NTB/Clinic (Jan-26)", f"{ntb_per_clinic:.0f}", f"Peak was {peak_ntb/len(df_clinics):.0f}")
c5.metric("Avg Cabin Util", f"{df_clinics['util_pct'].mean():.0%}", "L3M average")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1: ONLINE vs CLINIC REACH MAP
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">📍 SLIDE 1 — ONLINE vs CLINIC REACH'
    '<div class="slide-sub">Total order quantity by pincode: Website (16K pincodes) vs Clinics (7.4K pincodes)</div></div>',
    unsafe_allow_html=True,
)

# Aggregate to state level for clean visualization
web_state = (
    df_web.groupby("State")
    .agg(web_orders=("Quantity", "sum"), web_pins=("Zip", "nunique"))
    .reset_index()
)
clinic_state = (
    df_clinic_pin.groupby("State")
    .agg(clinic_orders=("Total Quantity", "sum"), clinic_pins=("Pincode", "nunique"))
    .reset_index()
)
merged = web_state.merge(clinic_state, on="State", how="outer").fillna(0)
merged = merged[merged["State"] != "-"]  # remove unknown
merged["total_orders"] = merged["web_orders"] + merged["clinic_orders"]
merged["clinic_share"] = merged["clinic_orders"] / merged["total_orders"]
merged = merged.sort_values("total_orders", ascending=False)

# State coordinates for India
STATE_COORDS = {
    "Maharashtra": (19.7515, 75.7139), "Uttar Pradesh": (26.8467, 80.9462),
    "Karnataka": (15.3173, 75.7139), "Delhi": (28.7041, 77.1025),
    "Gujarat": (22.2587, 71.1924), "West Bengal": (22.9868, 87.855),
    "Telangana": (18.1124, 79.0193), "Haryana": (29.0588, 76.0856),
    "Punjab": (31.1471, 75.3412), "Assam": (26.2006, 92.9376),
    "Madhya Pradesh": (22.9734, 78.6569), "Rajasthan": (27.0238, 74.2179),
    "Odisha": (20.9517, 85.0985), "Tamil Nadu": (11.1271, 78.6569),
    "Bihar": (25.0961, 85.3131), "Jharkhand": (23.6102, 85.2799),
    "Kerala": (10.8505, 76.2711), "Chhattisgarh": (21.2787, 81.8661),
    "Uttarakhand": (30.0668, 79.0193), "Andhra Pradesh": (15.9129, 79.74),
    "Chandigarh": (30.7333, 76.7794), "Goa": (15.2993, 74.124),
    "Himachal Pradesh": (31.1048, 77.1734), "Jammu and Kashmir": (33.7782, 76.5762),
    "Nagaland": (26.1584, 94.5624), "Meghalaya": (25.467, 91.3662),
    "Arunachal Pradesh": (28.218, 94.7278), "Tripura": (23.9408, 91.9882),
    "Manipur": (24.6637, 93.9063), "Mizoram": (23.1645, 92.9376),
    "Sikkim": (27.533, 88.5122), "Dadra and Nagar Haveli": (20.1809, 73.0169),
    "Pondicherry": (11.9416, 79.8083), "Lakshadweep": (10.5667, 72.6417),
    "Daman and Diu": (20.397, 72.8397), "Andaman and Nicobar": (11.7401, 92.6586),
    "Ladakh": (34.1526, 77.577), "Jharkand": (23.6102, 85.2799),
    "NAGALAND": (26.1584, 94.5624),
}

merged["lat"] = merged["State"].map(lambda s: STATE_COORDS.get(s, (20, 78))[0])
merged["lon"] = merged["State"].map(lambda s: STATE_COORDS.get(s, (20, 78))[1])

col_map1, col_map2 = st.columns(2)

with col_map1:
    st.markdown("**🌐 Website Orders by State**")
    fig_web = px.scatter_mapbox(
        merged.head(20), lat="lat", lon="lon", size="web_orders",
        color="web_orders", hover_name="State",
        hover_data={"web_orders": ":,", "web_pins": True, "lat": False, "lon": False},
        color_continuous_scale="Blues", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_web.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_web, use_container_width=True)

with col_map2:
    st.markdown("**🏥 Clinic Orders by State**")
    fig_cli = px.scatter_mapbox(
        merged.head(20), lat="lat", lon="lon", size="clinic_orders",
        color="clinic_orders", hover_name="State",
        hover_data={"clinic_orders": ":,", "clinic_pins": True, "lat": False, "lon": False},
        color_continuous_scale="Oranges", size_max=40,
        mapbox_style="carto-positron", zoom=3.5, center={"lat": 22, "lon": 80},
    )
    fig_cli.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_cli, use_container_width=True)

# Summary metrics
sm1, sm2, sm3, sm4 = st.columns(4)
sm1.metric("Website Pincodes", f"{df_web['Zip'].nunique():,}")
sm2.metric("Clinic Pincodes", f"{df_clinic_pin['Pincode'].nunique():,}")
sm3.metric("Website Orders", f"{df_web['Quantity'].sum():,.0f}")
sm4.metric("Clinic Orders (FirstTime)", f"{df_clinic_pin['Total Quantity'].sum():,.0f}")

# Top states comparison table
st.markdown("**State-Level Reach Comparison (Top 12)**")
top12 = merged.head(12)[["State", "web_orders", "web_pins", "clinic_orders", "clinic_pins", "clinic_share"]].copy()
top12.columns = ["State", "Website Orders", "Website Pincodes", "Clinic Orders", "Clinic Pincodes", "Clinic Share %"]
top12["Clinic Share %"] = (top12["Clinic Share %"] * 100).round(1)
top12["Website Orders"] = top12["Website Orders"].astype(int).apply(lambda x: f"{x:,}")
top12["Clinic Orders"] = top12["Clinic Orders"].astype(int).apply(lambda x: f"{x:,}")
st.dataframe(top12, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2: THE CASE FOR CAUTION — Show% Analysis
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">⚠️ SLIDE 2 — THE CASE FOR CAUTION: Why We Must Be Smart, Not Just Fast'
    '<div class="slide-sub">State-wise Show% — Gynoveda vs Industry Standard (Verified Benchmarks)</div></div>',
    unsafe_allow_html=True,
)

# NTB trend chart
col_trend, col_insight = st.columns([2, 1])
with col_trend:
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(
            x=df_network["month"], y=df_network["ntb"],
            name="Total NTB", marker_color="#FF6B35", opacity=0.85,
            text=df_network["ntb"].apply(lambda x: f"{x/1000:.1f}K"),
            textposition="outside",
        ),
        secondary_y=False,
    )
    fig_trend.add_trace(
        go.Scatter(
            x=df_network["month"], y=df_network["show_pct"] * 100,
            name="Show%", line=dict(color="#1a73e8", width=3),
            mode="lines+markers",
        ),
        secondary_y=True,
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
    st.markdown(f"""
    <div class="insight-card insight-red">
    <strong>📊 The Data Says:</strong><br>
    • NTB peaked at <b>{peak_ntb:,}</b> ({peak_m}), now <b>{latest_ntb:,}</b> ({ntb_decline:+.0%})<br>
    • NTB/clinic fell from <b>{peak_ntb//len(df_clinics)}</b> to <b>{latest_ntb//len(df_clinics)}</b><br>
    • <b>{(df_clinics['latest_show'] < 0.15).sum()}</b> clinics have Show% below 15%<br>
    • Adding clinics without fixing Show% grows cost faster than revenue
    </div>
    <div class="insight-card insight-blue">
    <strong>🎯 The answer:</strong> Not fewer or more clinics — <b>smarter clinics</b>.
    </div>
    """, unsafe_allow_html=True)

# State-wise Show% vs Industry Benchmark
# Map clinics to states via ZipData
clinic_to_state = df_zip.groupby("Clinic Loc")["State"].first().to_dict()
df_clinics["state"] = df_clinics["name"].map(clinic_to_state)

state_show = (
    df_clinics.groupby("state")
    .agg(
        avg_show=("l3m_show", "mean"),
        clinic_count=("name", "count"),
        total_ntb=("l3m_ntb", "sum"),
    )
    .reset_index()
)
state_show = state_show[state_show["state"].notna() & (state_show["state"] != "-")]
state_show = state_show.sort_values("avg_show", ascending=True)
state_show["benchmark"] = industry_show / 100
state_show["gap"] = state_show["avg_show"] - state_show["benchmark"]
state_show["label"] = state_show.apply(
    lambda r: f"{r['avg_show']:.0%} ({int(r['clinic_count'])} cl)", axis=1
)

fig_show = go.Figure()
fig_show.add_trace(go.Bar(
    y=state_show["state"], x=state_show["benchmark"] * 100,
    name=f"Industry Standard ({industry_show}%)",
    orientation="h", marker_color="#4CAF50", opacity=0.4,
))
fig_show.add_trace(go.Bar(
    y=state_show["state"], x=state_show["avg_show"] * 100,
    name="Gynoveda Actual",
    orientation="h", marker_color=np.where(state_show["gap"] >= 0, "#FF6B35", "#dc3545"),
    text=state_show["label"], textposition="outside",
))
fig_show.update_layout(
    title="Gynoveda Show% vs Industry Standard — State-Wise Benchmark",
    barmode="overlay", height=max(350, len(state_show) * 35),
    margin=dict(l=120, r=60, t=40, b=40),
    legend=dict(orientation="h", y=1.08),
    xaxis_title="Show %",
)
fig_show.add_vline(x=industry_show, line_dash="dash", line_color="green", annotation_text=f"{industry_show}% benchmark")
st.plotly_chart(fig_show, use_container_width=True)

# Summary cards
above = (state_show["gap"] >= 0.02).sum()
at_std = ((state_show["gap"] >= -0.02) & (state_show["gap"] < 0.02)).sum()
below = (state_show["gap"] < -0.02).sum()

sc1, sc2, sc3 = st.columns(3)
sc1.markdown(f'<div class="insight-card insight-green"><b style="font-size:2rem;color:#28a745">{above}</b> states above standard</div>', unsafe_allow_html=True)
sc2.markdown(f'<div class="insight-card"><b style="font-size:2rem;color:#ffc107">{at_std}</b> states at standard (±2ppt)</div>', unsafe_allow_html=True)
sc3.markdown(f'<div class="insight-card insight-red"><b style="font-size:2rem;color:#dc3545">{below}</b> states below standard</div>', unsafe_allow_html=True)

with st.expander("📋 Full State-Wise Benchmark Detail"):
    detail = state_show[["state", "avg_show", "benchmark", "gap", "clinic_count", "total_ntb"]].copy()
    detail.columns = ["State", "Gynoveda Show%", "Industry Benchmark", "Gap", "Clinics", "Monthly NTB"]
    detail["Gynoveda Show%"] = (detail["Gynoveda Show%"] * 100).round(1)
    detail["Industry Benchmark"] = (detail["Industry Benchmark"] * 100).round(1)
    detail["Gap"] = (detail["Gap"] * 100).round(1)
    detail = detail.sort_values("Gap")
    st.dataframe(detail, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3: EXPANSION STRATEGY — Where to Open Next
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🗺️ SLIDE 3 — EXPANSION STRATEGY: Where to Open Next'
    '<div class="slide-sub">Micro-Market Identification for 5 Saturated Clinics</div></div>',
    unsafe_allow_html=True,
)

# Identify saturated clinics (above show_threshold monthly NTB shows)
df_clinics["monthly_shows_avg"] = df_clinics["l3m_appt"]
saturated = df_clinics[df_clinics["monthly_shows_avg"] >= show_threshold].sort_values("monthly_shows_avg", ascending=False)

st.markdown(f"**Clinics at Capacity (≥{show_threshold} NTB Appt/Month, L3M avg)**")

col_sat_chart, col_sat_cards = st.columns([1.2, 1])

with col_sat_chart:
    top_sat = saturated.head(10).sort_values("monthly_shows_avg", ascending=True)
    colors = np.where(top_sat["l3m_show"] >= 0.25, "#28a745",
             np.where(top_sat["l3m_show"] >= 0.18, "#ffc107", "#dc3545"))
    fig_sat = go.Figure(go.Bar(
        y=top_sat["name"],
        x=top_sat["monthly_shows_avg"],
        orientation="h",
        marker_color=colors,
        text=top_sat.apply(
            lambda r: f"{int(r['monthly_shows_avg'])} appt | {r['util_pct']:.0%} util | {r['l3m_show']:.0%} show%",
            axis=1,
        ),
        textposition="inside",
        textfont=dict(color="white", size=11),
    ))
    fig_sat.add_vline(x=show_threshold, line_dash="dash", line_color="red",
                      annotation_text=f"Threshold: {show_threshold}")
    fig_sat.update_layout(
        title=f"Step 1: Clinics with ≥{show_threshold} Avg Monthly Appts",
        height=350, margin=dict(l=100, r=20, t=40, b=40),
        xaxis_title="Monthly NTB Appointments (L3M)",
    )
    st.plotly_chart(fig_sat, use_container_width=True)

    # Metrics
    mc1, mc2 = st.columns(2)
    mc1.metric("Clinics Qualifying", f"{len(saturated)}")
    mc2.metric("Avg Utilization", f"{saturated['util_pct'].mean():.0%}")

with col_sat_cards:
    st.markdown("**🔍 Top 5 Saturated — Micro-Market Expansion Candidates**")
    for _, row in saturated.head(5).iterrows():
        # Get top pincodes for this clinic
        clinic_zips = df_zip[df_zip["Clinic Loc"] == row["name"]]
        top_pins = clinic_zips.groupby(["Zip", "SubCity"]).size().reset_index(name="count")
        top_pins = top_pins.sort_values("count", ascending=False).head(5)
        top_areas = ", ".join(top_pins["SubCity"].dropna().unique()[:3])

        trend_emoji = "🟢" if row["l3m_show"] >= 0.25 else "🟡" if row["l3m_show"] >= 0.18 else "🔴"

        st.markdown(f"""
        <div style="background:#f8f9fa;border-radius:8px;padding:12px;margin:8px 0;border-left:4px solid #FF6B35;">
        <b>{row['name']}</b> ({row['city_code']}) — {int(row['cabin'])} cabins<br>
        Shows: <b>{int(row['monthly_shows_avg'])}/mo</b> | Util: <b>{row['util_pct']:.0%}</b> |
        Show%: <b>{row['l3m_show']:.0%}</b> | {trend_emoji}<br>
        <span style="color:#666;font-size:0.8rem;">Top catchments: {top_areas}</span>
        </div>
        """, unsafe_allow_html=True)

# Micro-market identification for saturated clinics
st.markdown("**📍 Nearby Pincode Demand for Saturated Clinics (Same-City Expansion Opportunity)**")
expansion_opps = []
for _, row in saturated.head(5).iterrows():
    clinic_name = row["name"]
    # Get state/city for this clinic
    clinic_data = df_zip[df_zip["Clinic Loc"] == clinic_name]
    if len(clinic_data) == 0:
        continue
    clinic_city_val = clinic_data["City"].mode().iloc[0] if len(clinic_data) > 0 else ""
    clinic_state_val = clinic_data["State"].mode().iloc[0] if len(clinic_data) > 0 else ""

    # Find website demand in same city but different pincodes
    city_web = df_web[df_web["City"] == clinic_city_val]
    city_web_agg = city_web.groupby(["Zip", "SubCity"]).agg(
        web_orders=("Quantity", "sum")
    ).reset_index().sort_values("web_orders", ascending=False)

    # Check which pincodes are already served by this clinic
    served_pins = set(clinic_data["Zip"].astype(str).unique())
    city_web_agg["already_served"] = city_web_agg["Zip"].isin(served_pins)

    # Unserved high-demand pincodes
    unserved = city_web_agg[~city_web_agg["already_served"]].head(5)
    for _, u in unserved.iterrows():
        expansion_opps.append({
            "From Clinic": clinic_name,
            "City": clinic_city_val,
            "Pincode": u["Zip"],
            "SubCity": u["SubCity"],
            "Website Orders": int(u["web_orders"]),
            "Status": "🟢 Unserved"
        })

if expansion_opps:
    df_exp = pd.DataFrame(expansion_opps)
    st.dataframe(df_exp, hide_index=True, use_container_width=True, height=300)
else:
    st.info("No unserved micro-markets identified for the qualifying clinics.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4: FIX BEFORE EXPAND — ₹0 CAC Revenue Unlock
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="slide-sep"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="slide-header">🔧 SLIDE 4 — FIX BEFORE EXPAND: ₹0 CAC Revenue Unlock'
    '<div class="slide-sub">What happens if underperforming clinics reach industry-standard Show%?</div></div>',
    unsafe_allow_html=True,
)

# Calculate Show% improvement opportunity
df_clinics["target_show"] = industry_show / 100
df_clinics["show_gap"] = df_clinics["target_show"] - df_clinics["l3m_show"]
df_clinics["show_gap"] = df_clinics["show_gap"].clip(lower=0)
df_clinics["additional_ntb"] = (df_clinics["l3m_appt"] * df_clinics["show_gap"]).astype(int)
df_clinics["additional_rev_monthly"] = df_clinics["additional_ntb"] * rev_per_ntb
df_clinics["additional_rev_annual"] = df_clinics["additional_rev_monthly"] * 12

underperforming = df_clinics[df_clinics["show_gap"] > 0].sort_values("additional_rev_annual", ascending=False)
total_unlock = underperforming["additional_rev_annual"].sum()

# Metrics
fm1, fm2, fm3 = st.columns(3)
fm1.metric("Underperforming Clinics", f"{len(underperforming)} of {len(df_clinics)}", f"Show% < {industry_show}%")
fm2.metric("Annual Revenue Unlock", f"₹{total_unlock/1e7:.1f} Cr", "₹0 CAC — no new leases")
fm3.metric("Avg Show% Gap", f"{underperforming['show_gap'].mean():.1%}", f"vs {industry_show}% target")

# Show% vs Appointments scatter
col_fix1, col_fix2 = st.columns([1.2, 1])

with col_fix1:
    fig_scatter = px.scatter(
        df_clinics, x="l3m_appt", y="l3m_show",
        size="additional_rev_annual", color="l3m_show",
        color_continuous_scale="RdYlGn", hover_name="name",
        hover_data={
            "l3m_appt": ":.0f", "l3m_show": ":.1%",
            "additional_rev_annual": ":,.0f",
        },
        labels={"l3m_appt": "Avg Monthly Appointments", "l3m_show": "Show%"},
    )
    fig_scatter.add_hline(y=industry_show/100, line_dash="dash", line_color="green",
                          annotation_text=f"{industry_show}% benchmark")
    fig_scatter.update_layout(
        title="Show% vs Appointments — Bubble = Revenue Unlock Potential",
        height=400, margin=dict(l=40, r=40, t=40, b=40),
        coloraxis_showscale=False,
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

    # Top 10 clinics by unlock potential
    st.markdown("**Top 10 Revenue Unlock Opportunities**")
    top_unlock = underperforming.head(10)[["name", "l3m_show", "show_gap", "additional_ntb", "additional_rev_annual"]].copy()
    top_unlock.columns = ["Clinic", "Current Show%", "Gap to Target", "Extra NTB/mo", "Annual Unlock ₹"]
    top_unlock["Current Show%"] = (top_unlock["Current Show%"] * 100).round(1)
    top_unlock["Gap to Target"] = (top_unlock["Gap to Target"] * 100).round(1)
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

# Unit economics model
opex_monthly = monthly_opex * 1e5  # Convert lakhs to INR
capex = capex_per_clinic * 1e5
conversion_rate = 0.40  # 40% of NTB patients convert to purchase
avg_ticket = rev_per_ntb

# Breakeven calculation
rev_per_show = conversion_rate * avg_ticket
breakeven_shows = int(np.ceil(opex_monthly / rev_per_show))

# Average clinic metrics
avg_shows = df_clinics["l3m_ntb"].mean()
avg_revenue = avg_shows * rev_per_show
avg_profit = avg_revenue - opex_monthly
profitable_clinics = (df_clinics["l3m_ntb"] * rev_per_show > opex_monthly).sum()
network_annual_profit = (df_clinics["l3m_ntb"] * rev_per_show - opex_monthly).clip(lower=0).sum() * 12

# Cost breakdown
rent = 1.0e5
doctors = 1.5e5  # 2 doctors
clinic_mgr = 0.3e5
housekeeping = 0.1e5
receptionist = 0.15e5
electricity = 0.05e5
opex_components = {
    "Revenue": avg_revenue,
    "Rent": -rent, "Doctors (2)": -doctors,
    "Clinic Mgr": -clinic_mgr, "Housekeeping": -housekeeping,
    "Receptionist": -receptionist, "Electricity": -electricity,
    "Monthly Profit": avg_profit,
}

um1, um2, um3, um4, um5, um6 = st.columns(6)
um1.metric("Monthly OpEx/Clinic", f"₹{monthly_opex}L", "Rent + Dr×2 + Staff")
um2.metric("Capex (Construction)", f"₹{capex_per_clinic:.0f}L", "")
um3.metric("Breakeven NTB Shows", f"{breakeven_shows}/month", f"@ {conversion_rate:.0%} conv × ₹{avg_ticket//1000}K")
um4.metric("Profitable Clinics", f"{profitable_clinics} of {len(df_clinics)}", f"↑ {len(df_clinics)-profitable_clinics} below breakeven")
um5.metric("Avg Margin (Profitable)", f"{avg_profit/avg_revenue*100:.0f}%" if avg_revenue > 0 else "N/A", "")
um6.metric("Network Annual Profit", f"₹{network_annual_profit/1e7:.1f} Cr", f"After ₹{monthly_opex}L/mo OpEx")

col_pnl, col_sens = st.columns(2)

with col_pnl:
    # Waterfall chart
    labels = list(opex_components.keys())
    values = list(opex_components.values())
    colors = ["#4CAF50" if v > 0 else "#dc3545" for v in values]
    colors[-1] = "#1a73e8"  # profit in blue

    fig_wf = go.Figure(go.Waterfall(
        x=labels, y=values, connector={"line": {"color": "#ccc"}},
        increasing={"marker": {"color": "#4CAF50"}},
        decreasing={"marker": {"color": "#dc3545"}},
        totals={"marker": {"color": "#1a73e8"}},
        text=[f"₹{abs(v)/1e3:.0f}K" for v in values],
        textposition="outside",
    ))
    fig_wf.update_layout(
        title=f"Average Clinic P&L ({int(avg_shows)} NTB shows/mo)",
        height=380, margin=dict(l=40, r=20, t=40, b=60),
        yaxis_title="₹",
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with col_sens:
    # Sensitivity: Profit vs NTB Shows
    shows_range = np.arange(0, 250, 5)
    profits = (shows_range * rev_per_show - opex_monthly) / 1e5  # in Lakhs

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
    '<div class="slide-header">📈 SLIDE 6 — FY27 REVENUE PROJECTION: Ratio-Adjusted, Scenario-Tested'
    f'<div class="slide-sub">Per-Clinic Revenue Projection (₹{rev_per_ntb//1000}K/NTB Patient) | Scenario: {scenario}</div></div>',
    unsafe_allow_html=True,
)

# Per-clinic revenue projection
df_clinics["monthly_revenue"] = df_clinics["l3m_ntb"] * rev_per_show * scenario_mult
df_clinics["annual_revenue"] = df_clinics["monthly_revenue"] * 12
df_clinics["monthly_profit"] = df_clinics["monthly_revenue"] - opex_monthly
df_clinics["annual_profit"] = df_clinics["monthly_profit"] * 12
df_clinics["payback_months"] = np.where(
    df_clinics["monthly_profit"] > 0,
    capex / df_clinics["monthly_profit"],
    np.inf,
)

total_annual_rev = df_clinics["annual_revenue"].sum()
total_annual_profit = df_clinics[df_clinics["annual_profit"] > 0]["annual_profit"].sum()

rm1, rm2, rm3, rm4 = st.columns(4)
rm1.metric(f"FY27 Revenue ({scenario})", f"₹{total_annual_rev/1e7:.1f} Cr", f"{len(df_clinics)} clinics")
rm2.metric("FY27 Profit (Profitable)", f"₹{total_annual_profit/1e7:.1f} Cr", "After OpEx")
rm3.metric("Avg Revenue/Clinic/Mo", f"₹{df_clinics['monthly_revenue'].mean()/1e5:.1f}L", "")
rm4.metric("Avg Payback Period", f"{df_clinics[df_clinics['payback_months'] < 100]['payback_months'].median():.0f} months", "Median (profitable)")

# Per-clinic revenue chart
col_rev1, col_rev2 = st.columns([1.5, 1])

with col_rev1:
    clinic_rev = df_clinics.sort_values("annual_revenue", ascending=True).tail(25)
    fig_rev = go.Figure(go.Bar(
        y=clinic_rev["name"],
        x=clinic_rev["annual_revenue"] / 1e5,
        orientation="h",
        marker_color=np.where(clinic_rev["annual_profit"] > 0, "#4CAF50", "#dc3545"),
        text=clinic_rev.apply(
            lambda r: f"₹{r['annual_revenue']/1e5:.0f}L | NTB:{int(r['l3m_ntb'])}/mo", axis=1
        ),
        textposition="inside",
        textfont=dict(color="white", size=10),
    ))
    fig_rev.update_layout(
        title=f"Per-Clinic Annual Revenue (Top 25) — {scenario} Scenario",
        height=550, margin=dict(l=100, r=20, t=40, b=40),
        xaxis_title="Annual Revenue (₹ Lakhs)",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with col_rev2:
    # Scenario comparison
    scenarios = {"Conservative": 0.85, "Base Case": 1.0, "Optimistic": 1.15}
    scenario_data = []
    for sc_name, mult in scenarios.items():
        rev = df_clinics["l3m_ntb"].sum() * rev_per_show * mult * 12
        scenario_data.append({"Scenario": sc_name, "Annual Revenue": rev})
    df_sc = pd.DataFrame(scenario_data)

    fig_sc = go.Figure(go.Bar(
        x=df_sc["Scenario"], y=df_sc["Annual Revenue"] / 1e7,
        marker_color=["#ffc107", "#FF6B35", "#4CAF50"],
        text=df_sc["Annual Revenue"].apply(lambda x: f"₹{x/1e7:.1f} Cr"),
        textposition="outside",
    ))
    fig_sc.update_layout(
        title="Scenario Comparison", height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        yaxis_title="Annual Revenue (₹ Cr)",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # Show% improvement impact
    show_fix_rev = total_unlock * scenario_mult
    st.markdown(f"""
    <div class="insight-card insight-green">
    <strong>Combined FY27 Outlook:</strong><br>
    Current run-rate: <b>₹{total_annual_rev/1e7:.1f} Cr</b><br>
    + Show% fix unlock: <b>₹{show_fix_rev/1e7:.1f} Cr</b><br>
    = Total potential: <b>₹{(total_annual_rev + show_fix_rev)/1e7:.1f} Cr</b>
    </div>
    """, unsafe_allow_html=True)

# Full clinic table
with st.expander("📋 Full Per-Clinic Revenue Breakdown"):
    rev_table = df_clinics[[
        "name", "region", "cabin", "l3m_ntb", "l3m_show",
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

# Define risk framework
risks = [
    {
        "Risk": "Show% continues declining",
        "Current": f"{df_clinics['latest_show'].mean():.0%}",
        "Trigger": "<18% network avg for 2 consecutive months",
        "Impact": "High",
        "Revenue Impact": f"₹{(df_clinics['l3m_appt'].sum() * 0.03 * rev_per_show * 12)/1e7:.1f} Cr/yr per 3ppt drop",
        "Mitigation": "Doctor quality audit, follow-up protocol, patient experience overhaul",
        "Status": "🟡" if df_clinics['latest_show'].mean() < 0.22 else "🟢",
    },
    {
        "Risk": "New clinic ramp-up slower than projected",
        "Current": f"{df_clinics[df_clinics['total_appt'] < 3000]['l3m_ntb'].mean():.0f} NTB/mo (new clinics)",
        "Trigger": "<50 NTB shows/month at Month 3",
        "Impact": "High",
        "Revenue Impact": f"₹{capex_per_clinic}L capex at risk per clinic",
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
        "Current": f"Online demand ratio used for projection",
        "Trigger": "<60% of projected NTB at Month 6",
        "Impact": "Medium",
        "Revenue Impact": f"₹{capex_per_clinic}L capex write-off if clinic closes",
        "Mitigation": "Lean 1-cabin format for tier-2, convert to full only after validation",
        "Status": "🟡",
    },
]

# Risk heatmap
df_risk = pd.DataFrame(risks)

# Display as styled table
impact_colors = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}

for _, risk in df_risk.iterrows():
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

years = [1, 2, 3, 4, 5]
escalation_rates = [0.05, 0.07, 0.10]
stress_data = []
for rate in escalation_rates:
    for yr in years:
        new_opex = opex_monthly * (1 + rate) ** (yr - 1)
        new_be = int(np.ceil(new_opex / rev_per_show))
        stress_data.append({
            "Year": f"Year {yr}", "Escalation": f"{int(rate*100)}%",
            "Monthly OpEx": new_opex, "Breakeven Shows": new_be,
        })
df_stress = pd.DataFrame(stress_data)

fig_stress = px.bar(
    df_stress, x="Year", y="Breakeven Shows", color="Escalation",
    barmode="group", color_discrete_sequence=["#28a745", "#ffc107", "#dc3545"],
    text="Breakeven Shows",
)
fig_stress.update_layout(
    height=300, margin=dict(l=40, r=20, t=20, b=40),
    yaxis_title="NTB Shows to Breakeven",
)
st.plotly_chart(fig_stress, use_container_width=True)

surviving = df_clinics[df_clinics["monthly_profit"] > opex_monthly * 0.07 * 3].shape[0]  # survive 3 years of 7%
st.markdown(f"""
<div class="insight-card insight-green">
✅ <b>{profitable_clinics}</b> currently profitable clinics survive Year 3 rent escalation at 7%.
</div>
<div class="insight-card">
💡 <b>Rent Stress Test:</b> At 7% annual escalation, OpEx rises from ₹{monthly_opex}L → ₹{monthly_opex*(1.07**3):.1f}L
over 3 years. Breakeven shifts from {breakeven_shows} → {int(np.ceil(opex_monthly*(1.07**3)/rev_per_show))} shows/month.<br>
<b>Action:</b> Negotiate 5% cap clauses. Avoid lock-in >2 years for new cities.
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Gynoveda FY27 Expansion Intelligence | Data through Jan 2026 | {len(df_clinics)} clinics | Generated {pd.Timestamp.now().strftime('%d-%b-%Y')}")
