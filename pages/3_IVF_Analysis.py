"""
Expansion Intelligence Platform — IVF Market Analysis
=======================================================
Healthcare vertical only. Detailed IVF and fertility market
analysis with state-level breakdowns, competitor mapping, and
gap market identification.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import get_vertical, has_module
from db import load_table

st.set_page_config(page_title="IVF Market Analysis — Healthcare", page_icon="🧬", layout="wide")

V = st.session_state.get("vertical", "healthcare")
if V != "healthcare":
    st.warning("IVF Market Analysis is only available under the **Healthcare** vertical. Switch to Healthcare in the sidebar.")
    st.stop()

vc = get_vertical(V)
pri = vc["color_primary"]
st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">🏥 Healthcare</span>', unsafe_allow_html=True)
st.title("🧬 IVF & Fertility Market Deep Dive")

# ── State-Level IVF Market Data ────────────────────────────────────
states_data = {
    "Maharashtra": {"pop_cr": 12.3, "fertility_rate": 1.7, "ivf_centres": 250, "market_cr": 1800, "unmet_pct": 68},
    "Uttar Pradesh": {"pop_cr": 23.1, "fertility_rate": 2.4, "ivf_centres": 120, "market_cr": 900, "unmet_pct": 82},
    "Karnataka": {"pop_cr": 6.8, "fertility_rate": 1.7, "ivf_centres": 140, "market_cr": 1100, "unmet_pct": 62},
    "Tamil Nadu": {"pop_cr": 7.7, "fertility_rate": 1.6, "ivf_centres": 160, "market_cr": 1200, "unmet_pct": 58},
    "Andhra Pradesh": {"pop_cr": 5.3, "fertility_rate": 1.6, "ivf_centres": 80, "market_cr": 600, "unmet_pct": 72},
    "Telangana": {"pop_cr": 3.9, "fertility_rate": 1.6, "ivf_centres": 110, "market_cr": 850, "unmet_pct": 65},
}

state_df = pd.DataFrame([
    {"State": s, **d} for s, d in states_data.items()
])

# KPIs
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("States Covered", len(states_data))
with c2:
    st.metric("Total IVF Centres", f"{state_df['ivf_centres'].sum():,}")
with c3:
    st.metric("Combined Market", f"₹{state_df['market_cr'].sum():,} Cr")
with c4:
    st.metric("Avg Unmet Need", f"{state_df['unmet_pct'].mean():.0f}%")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 State Comparison", "🏢 Competitor Landscape", "📈 Market Projections"])

with tab1:
    st.subheader("State-Level IVF Market Comparison")

    metric_choice = st.selectbox("Compare by", ["ivf_centres", "market_cr", "unmet_pct", "pop_cr"],
                                  format_func=lambda x: {"ivf_centres": "IVF Centres", "market_cr": "Market Size (₹ Cr)",
                                                         "unmet_pct": "Unmet Need %", "pop_cr": "Population (Cr)"}.get(x, x))
    fig = px.bar(state_df.sort_values(metric_choice, ascending=False),
                 x="State", y=metric_choice, color="unmet_pct",
                 color_continuous_scale="RdYlGn_r", text=metric_choice)
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(height=400, xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(state_df, use_container_width=True, hide_index=True)

    # Bubble chart: Pop vs Centres vs Market
    st.subheader("Population vs IVF Infrastructure — Bubble Map")
    fig_bubble = px.scatter(state_df, x="pop_cr", y="ivf_centres", size="market_cr",
                            color="unmet_pct", hover_name="State",
                            color_continuous_scale="RdYlGn_r",
                            labels={"pop_cr": "Population (Cr)", "ivf_centres": "IVF Centres",
                                    "market_cr": "Market Size (₹ Cr)", "unmet_pct": "Unmet Need %"})
    fig_bubble.update_layout(height=450)
    st.plotly_chart(fig_bubble, use_container_width=True)

with tab2:
    st.subheader("🏢 Major IVF Chains — National Footprint")

    chains = pd.DataFrame({
        "Chain": ["Indira IVF", "Nova IVF", "Birla Fertility", "Crysta IVF",
                  "Cloudnine", "Milann", "Bloom IVF"],
        "Centres": [130, 78, 45, 40, 35, 10, 8],
        "States": [18, 15, 12, 10, 8, 4, 3],
        "Revenue_Cr": [450, 380, 200, 120, 300, 80, 50],
        "Segment": ["Budget", "Mid-Premium", "Premium", "Budget-Mid",
                     "Premium", "Premium", "Premium"],
        "Key_States": ["Pan-India", "MH, KA, TN, DL", "MH, DL, KA", "UP, MH, RJ",
                       "KA, MH, TN", "KA", "MH, GJ"]
    })

    fig_chains = px.bar(chains.sort_values("Centres", ascending=True),
                        x="Centres", y="Chain", orientation='h',
                        color="Segment", text="Centres")
    fig_chains.update_layout(height=350, yaxis_title="")
    st.plotly_chart(fig_chains, use_container_width=True)

    st.dataframe(chains, use_container_width=True, hide_index=True)

    # M&A Timeline
    st.subheader("🔄 Recent M&A Activity (2023-2025)")
    ma_data = pd.DataFrame({
        "Year": [2023, 2023, 2024, 2024, 2024, 2025],
        "Acquirer": ["Nova IVF", "Birla Fertility", "Indira IVF", "Cloudnine",
                     "PE Fund (undisclosed)", "HCG / Milann"],
        "Target": ["3 single-doctor clinics", "Fertile Solutions (DL)",
                    "Regional chain (UP, 5 centres)", "IVF unit (Chennai)",
                    "Bloom IVF (minority stake)", "Standalone in Pune"],
        "Deal_Cr": [25, 80, 45, 60, 120, 35],
        "Strategic_Rationale": ["Geographic fill", "Delhi NCR density",
                                "Tier-2 UP penetration", "South expansion",
                                "Growth capital", "West India entry"]
    })
    st.dataframe(ma_data, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📈 IVF Market Growth Projections (2024-2032)")

    years = list(range(2024, 2033))
    conservative = [5500 * (1.15 ** i) for i in range(9)]
    base = [5500 * (1.22 ** i) for i in range(9)]
    optimistic = [5500 * (1.28 ** i) for i in range(9)]

    proj = pd.DataFrame({"Year": years, "Conservative (15%)": conservative,
                          "Base (22%)": base, "Optimistic (28%)": optimistic})

    fig_proj = go.Figure()
    for col, color in [("Conservative (15%)", "#95a5a6"), ("Base (22%)", pri), ("Optimistic (28%)", "#27ae60")]:
        fig_proj.add_trace(go.Scatter(x=proj["Year"], y=proj[col], mode='lines+markers',
                                       name=col, line=dict(width=2)))
    fig_proj.update_layout(height=400, yaxis_title="Market Size (₹ Cr)", xaxis_title="")
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("""
    **Key Drivers:** Insurance coverage expansion, increasing awareness, delayed marriages,
    urbanization, government IVF subsidies, and technology adoption (AI-assisted embryo selection).
    """)
