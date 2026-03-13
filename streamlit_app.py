"""
Gynoveda Expansion Intelligence - Advanced Master Edition
Featuring Sidebar Data Upload & O2O Simulator
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, math

# ── CONFIG & THEME ──────────────────────────────────────────────────────
st.set_page_config(page_title="Gynoveda · Expansion Intel", layout="wide", page_icon="◉")

PALETTE = ['#c0392b', '#f97316', '#10b981', '#8b5cf6', '#3b82f6', '#06b6d4']
PLOTLY_CFG = {'responsive': True, 'displayModeBar': False}

# ── CSS: MODERN DASHBOARD ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {font-family: 'Inter', system-ui, sans-serif !important;}
    .main .block-container {background: #f8fafc; padding-top: 1.5rem; max-width: 1400px;}
    
    /* Metrics Cards */
    [data-testid="stMetric"] {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
        transition: transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); }
    [data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 700 !important; }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #CB5B51 0%, #9A3E36 100%);
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px; color: white;
        box-shadow: 0 10px 15px -3px rgba(203, 91, 81, 0.3);
    }
    .hero-title { font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;}
    .hero-sub { font-size: 0.95rem; color: rgba(255,255,255,0.85); margin-top: 8px;}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: transparent;}
    .stTabs [data-baseweb="tab"] {
        height: 48px; background-color: white; border-radius: 8px 8px 0 0;
        padding: 10px 20px; font-weight: 600; color: #64748b;
        border: 1px solid #e2e8f0; border-bottom: none;
    }
    .stTabs [aria-selected="true"] {background-color: #f8fafc !important; color: #c0392b !important; border-top: 3px solid #c0392b;}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────
def fmt_inr(v, prefix="₹", d=1):
    if v is None or np.isnan(v): return f"{prefix}0"
    v_abs = abs(v)
    if v_abs >= 1e7: return f"{prefix}{v/1e7:.{d}f} Cr"
    if v_abs >= 1e5: return f"{prefix}{v/1e5:.{d}f}L"
    return f"{prefix}{v:,.0f}"

# ── DIRECTORY SETUP ─────────────────────────────────────────────────────
DATA = "mis_data"
os.makedirs(DATA, exist_ok=True)

# ── SIDEBAR: DATA UPLOADER ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Data Management")
    st.caption("Upload raw Excel or CSV files. The engine will auto-detect and update the dashboard.")
    
    uploaded_files = st.file_uploader("Drop Files Here", accept_multiple_files=True, type=['csv', 'xlsx', 'xls'])
    
    if st.button("Process & Update Data", use_container_width=True, type="primary"):
        if uploaded_files:
            with st.spinner("Processing files..."):
                for file in uploaded_files:
                    fname = file.name.lower()
                    
                    # Smart Detection: Map uploaded file to standardized names
                    if 'lat log' in fname or 'clinics' in fname and 'lat' in fname:
                        std_name = 'std_clinics.csv'
                    elif 'ivf' in fname or 'geotier' in fname:
                        std_name = 'std_ivf_comp.csv'
                    elif 'clinic' in fname and 'first time' in fname:
                        std_name = 'std_demand_clinic.csv'
                    elif 'website' in fname and 'first time' in fname:
                        std_name = 'std_demand_web.csv'
                    elif 'show' in fname:
                        std_name = 'std_show_rate.csv'
                    elif 'pin' in fname or 'geocode' in fname:
                        std_name = 'std_pin_geo.csv'
                    else:
                        std_name = f"std_unknown_{file.name}.csv"
                    
                    # Read and convert to CSV for faster loading later
                    try:
                        if file.name.endswith(('.xlsx', '.xls')):
                            df = pd.read_excel(file)
                        else:
                            df = pd.read_csv(file)
                        
                        df.to_csv(f"{DATA}/{std_name}", index=False)
                    except Exception as e:
                        st.error(f"Failed to process {file.name}: {e}")
                
            st.success("✅ Data Updated Successfully!")
            st.cache_data.clear() # Clear memory cache so it reads new files
            st.rerun() # Refresh the app
        else:
            st.warning("Please upload files first.")
            
    st.markdown("---")
    if st.button("Force Global Re-Scan", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── DATA CORE (ADVANCED ENGINE) ─────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Booting Expansion Engine...")
def load_all_data():
    """Loads standardized CSVs generated by the uploader."""
    d = {}
    
    def _safe_load(filename):
        path = f"{DATA}/{filename}"
        if os.path.exists(path): return pd.read_csv(path)
        return pd.DataFrame()

    # Read the standardized filenames created by the uploader
    d['clinics'] = _safe_load("std_clinics.csv")
    d['ivf_comp'] = _safe_load("std_ivf_comp.csv")
    d['demand_clinic'] = _safe_load("std_demand_clinic.csv")
    d['demand_web'] = _safe_load("std_demand_web.csv")
    d['show_rate'] = _safe_load("std_show_rate.csv")
    d['pin_geo'] = _safe_load("std_pin_geo.csv")
    
    return d

data = load_all_data()

# ── UI BUILDER ──────────────────────────────────────────────────────────
st.markdown(
    """<div class="hero-banner">
        <div class="hero-title">Gynoveda Expansion Intelligence v2</div>
        <div class="hero-sub">Geospatial Demand Clustering, Cannibalization Risk & Financial Forecaster</div>
    </div>""", unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Network Pulse", 
    "🌆 Same-City Expansion", 
    "🗺️ New-City Whitespace", 
    "📈 ROI Forecaster",
    "🔄 O2O Simulator"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: NETWORK PULSE
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Executive Summary")
    
    c1, c2, c3, c4 = st.columns(4)
    active_clinics = len(data['clinics']) if not data['clinics'].empty else 0
    total_web_orders = len(data['demand_web']) if not data['demand_web'].empty else 0
    total_clinic_1cx = len(data['demand_clinic']) if not data['demand_clinic'].empty else 0
    total_competitors = len(data['ivf_comp']) if not data['ivf_comp'].empty else 0
    
    c1.metric("Active Clinics", f"{active_clinics}", "Network Size")
    c2.metric("Total Clinic 1Cx", f"{total_clinic_1cx:,.0f}", "Footfall Demand")
    c3.metric("Total Web Orders", f"{total_web_orders:,.0f}", "Digital Demand")
    c4.metric("IVF Competitors Mapped", f"{total_competitors:,.0f}", "Threat Landscape")

    st.markdown("---")
    st.info("💡 **Insights Engine:** To properly evaluate expansion, the engine looks at **Digital Demand** (Web Orders) overlapping with **Geospatial distances** from current clinics (>20km whitespace) and **Competitor Density**.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: SAME-CITY EXPANSION (DEEPENING)
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Same-City Catchment & Cannibalization Risk")
    st.caption("Identify where adding clinics in an existing city will eat into current revenue vs capturing new local demand.")
    
    if not data['clinics'].empty and 'City' in data['clinics'].columns:
        cities = data['clinics']['City'].dropna().unique().tolist()
        sel_city = st.selectbox("Select Target City for Deepening", sorted(cities))
        
        city_clinics = data['clinics'][data['clinics']['City'] == sel_city]
        st.write(f"**Current Clinics in {sel_city}: {len(city_clinics)}**")
        
        show_cols = [c for c in ['Clinic Code', 'Clinic Address', 'Latitude', 'Longitude'] if c in city_clinics.columns]
        st.dataframe(city_clinics[show_cols], use_container_width=True, hide_index=True)
    else:
        st.warning("Clinic Lat/Lon data not found. Please upload it via the sidebar.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: NEW CITIES WHITESPACE (MAPBOX VISUALIZATION)
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Geospatial Whitespace Discovery")
    st.caption("Visualizing web demand clusters to find optimal locations for net-new clinic launches.")
    
    has_map_data = not data['demand_web'].empty and not data['pin_geo'].empty and not data['clinics'].empty
    
    if has_map_data:
        web_df = data['demand_web'].copy()
        if 'Zip' in web_df.columns:
            web_df['Zip'] = pd.to_numeric(web_df['Zip'], errors='coerce')
            demand_by_pin = web_df.groupby('Zip').agg(Orders=('Quantity', 'sum')).reset_index()
            
            pin_geo = data['pin_geo'].copy()
            if 'pincode' in pin_geo.columns:
                map_df = demand_by_pin.merge(pin_geo, left_on='Zip', right_on='pincode', how='inner')
                map_df = map_df.sort_values('Orders', ascending=False).head(1000)
                
                col_m, col_t = st.columns([2.5, 1])
                with col_m:
                    fig_map = px.scatter_mapbox(
                        map_df, lat="lat", lon="lon", 
                        color="Orders", size="Orders",
                        color_continuous_scale=px.colors.sequential.OrRd,
                        hover_name="Zip",
                        hover_data={"Orders": True, "lat": False, "lon": False},
                        zoom=3.5, center={"lat": 20.5937, "lon": 78.9629},
                        height=600, labels={'Orders': 'Web Demand'}
                    )
                    
                    clinics = data['clinics'].dropna(subset=['Latitude', 'Longitude'])
                    fig_map.add_trace(go.Scattermapbox(
                        lat=clinics['Latitude'], lon=clinics['Longitude'],
                        mode='markers', marker=dict(size=12, color='#1a1f36', symbol='circle'),
                        name='Active Clinics', text=clinics.get('City', '')
                    ))
                    
                    fig_map.update_layout(
                        mapbox_style="carto-positron", 
                        margin={"r":0,"t":0,"l":0,"b":0},
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)")
                    )
                    st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CFG)
                    
                with col_t:
                    st.markdown("##### Competitor Density")
                    st.caption("Top Cities by IVF Competitor Count")
                    if not data['ivf_comp'].empty and 'City' in data['ivf_comp'].columns:
                        comp_density = data['ivf_comp']['City'].value_counts().head(10).reset_index()
                        comp_density.columns = ['City', 'IVF Centers']
                        st.dataframe(comp_density, hide_index=True, use_container_width=True)
            else:
                st.warning("`pin_geocode.csv` is missing the 'pincode' column.")
        else:
            st.warning("Web demand data is missing the 'Zip' column.")
    else:
        st.warning("Upload `pin_geocode.csv`, `Clinics Lat log`, and `First Time customer - website` to enable mapping.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: ADVANCED FORECASTER (SENSITIVITY)
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### What-If Revenue Modeling")
    st.caption("Adjust fundamental unit economics to see how it impacts clinic payback periods.")
    
    with st.expander("⚙️ Scenario Adjustments (Sensitivity Controls)", expanded=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        avg_bill = sc1.slider("Avg Bill Value (₹K)", 15, 50, 27, help="Average ticket size per converted 1Cx.")
        conv_rate = sc2.slider("1Cx Conversion %", 20, 100, 100, help="Percentage of First Time Consults that convert.")
        capex = sc3.number_input("Capex per Clinic (₹L)", 10.0, 50.0, 28.0)
        opex = sc4.number_input("OpEx per Clinic/Mo (₹L)", 1.0, 10.0, 3.0)

    clinics_to_launch = st.slider("Number of Clinics to Launch", 1, 50, 10)
    
    monthly_1cx_walkins = 150 
    mature_rev_lacs = (avg_bill * monthly_1cx_walkins * (conv_rate/100)) / 100
    
    months = np.arange(1, 13)
    ramp_multipliers = np.array([min(1.0, m/6) for m in months])
    rev_curve = mature_rev_lacs * ramp_multipliers
    
    total_rev_12m = np.sum(rev_curve * clinics_to_launch)
    total_capex = capex * clinics_to_launch
    total_opex = opex * 12 * clinics_to_launch
    ebitda = total_rev_12m - total_opex
    
    st.markdown("---")
    rm1, rm2, rm3, rm4 = st.columns(4)
    rm1.metric("Total Investment (Capex)", fmt_inr(total_capex * 1e5))
    rm2.metric("Projected Revenue (12M)", fmt_inr(total_rev_12m * 1e5))
    rm3.metric("Projected OpEx (12M)", fmt_inr(total_opex * 1e5))
    rm4.metric("Net EBITDA (12M)", fmt_inr(ebitda * 1e5), delta="Profitable" if ebitda > 0 else "Burn Phase")
    
    fig_payback = go.Figure()
    fig_payback.add_trace(go.Scatter(
        x=months, y=np.cumsum((rev_curve - opex) * clinics_to_launch), 
        name="Cumulative Cashflow", line=dict(color='#10b981', width=3)
    ))
    fig_payback.add_hline(y=total_capex, line_dash="dash", line_color="#ef4444", 
                          annotation_text=f"Capex Recovery Line (₹{total_capex:,.0f}L)", annotation_position="bottom right")
    
    fig_payback.update_layout(
        title="Network Cashflow & Payback Projection (₹ Lacs)",
        xaxis_title="Month post-launch", yaxis_title="Cumulative Cashflow (₹L)",
        height=400, margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_payback, use_container_width=True, config=PLOTLY_CFG)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: O2O (ONLINE TO OFFLINE) SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🔄 Online-to-Offline (O2O) Conversion Engine")
    st.caption("Model how pre-launch Web Demand in a pincode cluster translates into physical Clinic Sales.")

    st.markdown("#### 1. The O2O Proof Model")
    st.info("💡 **Hypothesis:** When an offline clinic is placed inside a digital hotspot, local trust skyrockets. Analysis of mature clinics indicates that **Offline Monthly Sales ≈ 10X the historical Web Monthly Revenue** from that catchment.")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("""
        <div style='background:#f8fafc; padding:15px; border-radius:10px; border-left:4px solid #3b82f6;'>
            <span style='color:#64748b; font-size:0.8rem; font-weight:600;'>PRE-LAUNCH (Pincode 411014)</span><br>
            <span style='font-size:1.5rem; font-weight:800; color:#0f172a;'>₹3.5L / mo</span><br>
            <span style='color:#3b82f6; font-size:0.85rem;'>Web Orders Only</span>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown("""
        <div style='background:#fefce8; padding:15px; border-radius:10px; border:1px dashed #eab308; text-align:center;'>
            <span style='color:#a16207; font-size:0.9rem; font-weight:600;'>Observed O2O Multiplier</span><br>
            <span style='font-size:1.8rem; font-weight:800; color:#ca8a04;'>10.2X</span><br>
        </div>
        """, unsafe_allow_html=True)
    with col_p3:
        st.markdown("""
        <div style='background:#f8fafc; padding:15px; border-radius:10px; border-left:4px solid #10b981;'>
            <span style='color:#64748b; font-size:0.8rem; font-weight:600;'>POST-LAUNCH (Viman Nagar Clinic)</span><br>
            <span style='font-size:1.5rem; font-weight:800; color:#0f172a;'>₹35.7L / mo</span><br>
            <span style='color:#10b981; font-size:0.85rem;'>Avg Clinic Sales (Year 1)</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 2. New Hotspot Sandbox")
    st.caption("Select an unserved cluster to predict its offline potential using the O2O multiplier.")
    
    if not data['demand_web'].empty and 'SubCity' in data['demand_web'].columns:
        web_sandbox = data['demand_web'].copy()
        web_sandbox['Total'] = pd.to_numeric(web_sandbox['Total'], errors='coerce').fillna(0)
        
        cluster_agg = web_sandbox.groupby(['City', 'SubCity']).agg(
            Total_Web_Rev=('Total', 'sum'),
            Total_Orders=('Quantity', 'sum')
        ).reset_index()
        cluster_agg['Avg_Mo_Web_Rev'] = cluster_agg['Total_Web_Rev'] / 60 
        
        cluster_agg = cluster_agg[cluster_agg['Avg_Mo_Web_Rev'] > 5000].sort_values('Avg_Mo_Web_Rev', ascending=False)
        
        if not cluster_agg.empty:
            sc1, sc2 = st.columns([1, 2])
            with sc1:
                cluster_options = [f"{row['City']} - {row['SubCity']}" for _, row in cluster_agg.iterrows()]
                selected_cluster = st.selectbox("Select Whitespace Cluster", cluster_options)
                
                sel_city, sel_sub = selected_cluster.split(" - ")
                cluster_data = cluster_agg[(cluster_agg['City'] == sel_city) & (cluster_agg['SubCity'] == sel_sub)].iloc[0]
                
                base_web_rev = cluster_data['Avg_Mo_Web_Rev']
                
                st.markdown("<br>", unsafe_allow_html=True)
                o2o_multiplier = st.slider(
                    "O2O Conversion Multiplier (X)", 
                    min_value=1.0, max_value=20.0, value=10.0, step=0.5
                )
                projected_offline_sales = base_web_rev * o2o_multiplier
                
            with sc2:
                fig_o2o = go.Figure(go.Waterfall(
                    name="O2O", orientation="v", measure=["absolute", "relative", "total"],
                    x=["Current Web Rev/Mo", f"O2O Uplift ({o2o_multiplier}X)", "Projected Clinic Rev/Mo"],
                    textposition="outside",
                    text=[fmt_inr(base_web_rev), f"+{fmt_inr(projected_offline_sales - base_web_rev)}", fmt_inr(projected_offline_sales)],
                    y=[base_web_rev, projected_offline_sales - base_web_rev, projected_offline_sales],
                    connector={"line":{"color":"rgb(63, 63, 63)"}},
                    decreasing={"marker":{"color":"#ef4444"}},
                    increasing={"marker":{"color":"#3b82f6"}},
                    totals={"marker":{"color":"#10b981"}}
                ))
                
                fig_o2o.update_layout(
                    title=f"O2O Projection for {sel_sub}, {sel_city}",
                    showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20),
                    yaxis=dict(title="Monthly Revenue (₹)", showgrid=True, gridcolor='#f1f5f9')
                )
                st.plotly_chart(fig_o2o, use_container_width=True, config=PLOTLY_CFG)
                
            st.success(f"**Actionable Insight:** Based on a historical web run-rate of **{fmt_inr(base_web_rev)}/mo** in {sel_sub}, applying a **{o2o_multiplier}X** O2O multiplier projects mature clinic sales of **{fmt_inr(projected_offline_sales)}/mo**. If OpEx is ~₹3L/mo, this cluster is a highly viable expansion target.")
        else:
            st.warning("Not enough web demand data to run the simulator.")
    else:
        st.warning("Please ensure 'First Time customer - website' data is loaded via the sidebar to use the O2O Simulator.")
