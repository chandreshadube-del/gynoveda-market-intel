"""
Gynoveda Expansion Intelligence - Advanced Master Edition
Featuring Auto-Healing Data Uploader, Phased Forecaster & Unified GIS
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

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
    
    [data-testid="stMetric"] {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
        transition: transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); }
    [data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 700 !important; }
    
    .hero-banner {
        background: linear-gradient(135deg, #CB5B51 0%, #9A3E36 100%);
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px; color: white;
        box-shadow: 0 10px 15px -3px rgba(203, 91, 81, 0.3);
    }
    .hero-title { font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;}
    .hero-sub { font-size: 0.95rem; color: rgba(255,255,255,0.85); margin-top: 8px;}
    
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

# ── SIDEBAR: AUTO-HEALING DATA UPLOADER ─────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Data Management")
    st.caption("Upload raw Excel or CSV files. The engine will auto-detect and correct column formats.")
    
    uploaded_files = st.file_uploader("Drop Files Here", accept_multiple_files=True, type=['csv', 'xlsx', 'xls'])
    
    if st.button("Process & Update Data", use_container_width=True, type="primary"):
        if uploaded_files:
            file_logs = []
            with st.spinner("Analyzing and standardizing files..."):
                for file in uploaded_files:
                    fname = file.name.lower()
                    
                    if 'ivf' in fname or 'geotier' in fname:
                        std_name = 'std_ivf_comp.csv'
                    elif 'first time' in fname or 'customer' in fname:
                        if 'clinic' in fname:
                            std_name = 'std_demand_clinic.csv'
                        else:
                            std_name = 'std_demand_web.csv'
                    elif 'website' in fname or ('web' in fname and 'first time' in fname):
                        std_name = 'std_demand_web.csv'
                    elif 'show' in fname:
                        std_name = 'std_show_rate.csv'
                    elif 'pin' in fname or 'geocode' in fname:
                        std_name = 'std_pin_geo.csv'
                    elif 'lat' in fname or 'lon' in fname or 'log' in fname or 'clinic' in fname:
                        std_name = 'std_clinics.csv'
                    else:
                        std_name = f"std_unknown_{file.name}.csv"
                    
                    try:
                        if file.name.endswith(('.xlsx', '.xls')):
                            sheets = pd.read_excel(file, sheet_name=None)
                            df = None
                            for s_name, s_df in sheets.items():
                                if not s_df.empty and len(s_df.columns) > 2:
                                    df = s_df
                                    break
                            if df is None:
                                df = list(sheets.values())[0]
                        else:
                            df = pd.read_csv(file)
                        
                        df.to_csv(f"{DATA}/{std_name}", index=False)
                        file_logs.append(f"✅ **{std_name}** ({len(df)} rows)")
                    except Exception as e:
                        file_logs.append(f"❌ Error with {file.name}: {e}")
                
            st.session_state['upload_logs'] = file_logs
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("Please upload files first.")
            
    if 'upload_logs' in st.session_state:
        with st.expander("🔍 Last Upload Diagnostics", expanded=True):
            for log in st.session_state['upload_logs']:
                st.markdown(log)

    st.markdown("---")
    if st.button("Force Global Re-Scan", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── DATA CORE (ADVANCED AUTO-CLEAN ENGINE) ──────────────────────────────
@st.cache_data(ttl=300, show_spinner="Booting Expansion Engine...")
def load_all_data():
    d = {}
    def _safe_load(filename):
        path = f"{DATA}/{filename}"
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                df.columns = df.columns.str.strip()
                col_lower = {str(c).lower().strip(): c for c in df.columns}
                
                for v in ['city', 'city name', 'clinic city']:
                    if v in col_lower and 'City' not in df.columns:
                        df.rename(columns={col_lower[v]: 'City'}, inplace=True); break
                for v in ['latitude', 'lat']:
                    if v in col_lower and 'Latitude' not in df.columns:
                        df.rename(columns={col_lower[v]: 'Latitude'}, inplace=True); break
                for v in ['longitude', 'lon', 'long', 'lng']:
                    if v in col_lower and 'Longitude' not in df.columns:
                        df.rename(columns={col_lower[v]: 'Longitude'}, inplace=True); break
                for v in ['clinic code', 'code']:
                    if v in col_lower and 'Clinic Code' not in df.columns:
                        df.rename(columns={col_lower[v]: 'Clinic Code'}, inplace=True); break
                        
                return df
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

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

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Network Pulse", 
    "🌆 Same-City Expansion", 
    "🗺️ Unified GIS Map", 
    "📈 Phased ROI Forecaster"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: NETWORK PULSE
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Executive Summary")
    
    active_clinics = len(data['clinics']) if not data['clinics'].empty else 0
    total_competitors = len(data['ivf_comp']) if not data['ivf_comp'].empty else 0
    
    if not data['demand_clinic'].empty and 'Customer ID' in data['demand_clinic'].columns:
        total_clinic_1cx = data['demand_clinic']['Customer ID'].nunique()
    else:
        total_clinic_1cx = 0
        
    if not data['demand_web'].empty and 'Customer ID' in data['demand_web'].columns:
        total_web_orders = data['demand_web']['Customer ID'].nunique()
    else:
        total_web_orders = len(data['demand_web']) if not data['demand_web'].empty else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Clinics", f"{active_clinics}", "Network Size")
    c2.metric("Unique Clinic 1Cx", f"{total_clinic_1cx:,.0f}", "Unique Offline Patients")
    c3.metric("Unique Web Customers", f"{total_web_orders:,.0f}", "Unique Digital Demand")
    c4.metric("IVF Competitors", f"{total_competitors:,.0f}", "Threat Landscape")

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
        if len(cities) > 0:
            sel_city = st.selectbox("Select Target City for Deepening", sorted(cities))
            
            city_clinics = data['clinics'][data['clinics']['City'] == sel_city]
            st.write(f"**Current Clinics in {sel_city}: {len(city_clinics)}**")
            
            show_cols = [c for c in ['Clinic Code', 'Clinic Address', 'Latitude', 'Longitude'] if c in city_clinics.columns]
            st.dataframe(city_clinics[show_cols], use_container_width=True, hide_index=True)
        else:
            st.warning("No valid cities found in the Clinics file.")
    else:
        st.warning("Clinic Lat/Lon data not found or formatted incorrectly. Please check the sidebar diagnostics.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: UNIFIED GIS MAP (WHITESPACE DISCOVERY)
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Unified Geospatial Demand Discovery")
    st.caption("A layered Mapbox engine showing Web 1Cx & Clinic 1Cx Pincodes + Active Clinics + IVF Competitors.")
    
    has_map_data = (not data['demand_web'].empty or not data['demand_clinic'].empty) and not data['pin_geo'].empty
    
    if has_map_data:
        web_df = data['demand_web'].copy() if not data['demand_web'].empty else pd.DataFrame(columns=['Zip', 'Customer ID'])
        web_df['Zip'] = pd.to_numeric(web_df.get('Zip', pd.Series()), errors='coerce')
        web_agg = web_df.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Web_1Cx'})
        
        clinic_df = data['demand_clinic'].copy() if not data['demand_clinic'].empty else pd.DataFrame(columns=['Zip', 'Customer ID'])
        clinic_df['Zip'] = pd.to_numeric(clinic_df.get('Zip', pd.Series()), errors='coerce')
        clinic_agg = clinic_df.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Clinic_1Cx'})
        
        demand_by_pin = pd.merge(web_agg, clinic_agg, on='Zip', how='outer').fillna(0)
        demand_by_pin['Total_1Cx'] = demand_by_pin['Web_1Cx'] + demand_by_pin['Clinic_1Cx']
        
        pin_geo = data['pin_geo'].copy()
        if 'pincode' in pin_geo.columns:
            map_df = demand_by_pin.merge(pin_geo, left_on='Zip', right_on='pincode', how='inner')
            map_df = map_df.sort_values('Total_1Cx', ascending=False).head(2000)
            
            col_m, col_t = st.columns([2.5, 1])
            with col_m:
                fig_map = go.Figure()

                max_1cx = map_df['Total_1Cx'].max()
                sizeref = 2.0 * max_1cx / (35.**2) if max_1cx > 0 else 1
                
                fig_map.add_trace(go.Scattermapbox(
                    lat=map_df["lat"], lon=map_df["lon"],
                    mode='markers',
                    marker=dict(
                        size=map_df["Total_1Cx"],
                        sizemode='area', sizeref=sizeref, sizemin=4,
                        color=map_df["Total_1Cx"], colorscale="OrRd", showscale=True,
                        colorbar=dict(title="Total 1Cx", x=0.02, y=0.5, len=0.7)
                    ),
                    text="<b>Zip: " + map_df["Zip"].astype(int).astype(str) + "</b><br>" + 
                         "Online 1Cx: " + map_df["Web_1Cx"].astype(int).astype(str) + "<br>" + 
                         "Clinic 1Cx: " + map_df["Clinic_1Cx"].astype(int).astype(str) + "<br>" + 
                         "Total 1Cx: " + map_df["Total_1Cx"].astype(int).astype(str),
                    name='Patient Demand', hoverinfo='text'
                ))
                
                if not data['ivf_comp'].empty and 'Latitude' in data['ivf_comp'].columns and 'Longitude' in data['ivf_comp'].columns:
                    ivf_df = data['ivf_comp'].dropna(subset=['Latitude', 'Longitude'])
                    fig_map.add_trace(go.Scattermapbox(
                        lat=ivf_df['Latitude'], lon=ivf_df['Longitude'],
                        mode='markers',
                        marker=dict(size=6, color='#64748b'), 
                        name='IVF Competitors',
                        text="<b>" + ivf_df.get('Clinic_Name', 'IVF Center').astype(str) + "</b>",
                        hoverinfo='text'
                    ))

                if not data['clinics'].empty and 'Latitude' in data['clinics'].columns and 'Longitude' in data['clinics'].columns:
                    clinics_df = data['clinics'].dropna(subset=['Latitude', 'Longitude'])
                    fig_map.add_trace(go.Scattermapbox(
                        lat=clinics_df['Latitude'], lon=clinics_df['Longitude'],
                        mode='markers',
                        marker=dict(size=14, color='#1a1f36'),
                        name='Gynoveda Clinics',
                        text="<b>" + clinics_df.get('City', 'Clinic').astype(str) + "</b>",
                        hoverinfo='text'
                    ))

                fig_map.update_layout(
                    mapbox=dict(style="carto-positron", center=dict(lat=20.5937, lon=78.9629), zoom=3.8),
                    margin={"r":0,"t":0,"l":0,"b":0}, height=600,
                    legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, bgcolor="rgba(255,255,255,0.85)")
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
        st.warning("Upload `pin_geocode.csv`, `Clinics Lat log`, and Demand Datasets to enable the Unified GIS Map.")

    st.markdown("---")
    st.markdown("#### 📅 Year-wise & Pincode-wise Demand Trend")
    st.caption("Analyzing historical growth in top Zip Codes to ensure demand is accelerating, not flattening.")
    
    if not data['demand_web'].empty and 'Date' in data['demand_web'].columns and 'Zip' in data['demand_web'].columns:
        trend_df = data['demand_web'].copy()
        trend_df['Year'] = pd.to_datetime(trend_df['Date'], errors='coerce').dt.year.fillna(0).astype(int)
        trend_df = trend_df[trend_df['Year'] > 2000]
        
        trend_df['Zip'] = trend_df['Zip'].astype(str).str.replace(".0", "", regex=False)
        trend_df['Quantity'] = pd.to_numeric(trend_df['Quantity'], errors='coerce').fillna(1)

        yearly_pin_demand = trend_df.groupby(['Year', 'Zip']).agg(Total_Quantity=('Quantity', 'sum')).reset_index()
        top_pins = yearly_pin_demand.groupby('Zip')['Total_Quantity'].sum().nlargest(15).index.tolist()
        plot_data = yearly_pin_demand[yearly_pin_demand['Zip'].isin(top_pins)].copy()
        plot_data['Year'] = plot_data['Year'].astype(str)

        fig_trend = px.bar(
            plot_data, x='Zip', y='Total_Quantity', color='Year', barmode='group',
            color_discrete_sequence=px.colors.sequential.Plasma,
            title="Top 15 Web Demand Pincodes: Year-over-Year Growth"
        )
        
        fig_trend.update_layout(
            xaxis_title="Pincode (Zip)", yaxis_title="Total Order Quantity",
            legend_title="Year", height=450, xaxis={'categoryorder':'total descending'}
        )
        
        st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CFG)
    else:
        st.warning("Missing 'Date' or 'Zip' columns in Website Demand dataset.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: PHASED ROI FORECASTER (12-MONTH HORIZON)
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Phase-Wise ROI Forecaster (12 Months)")
    st.caption("Model your cashflow dynamically based on staggered, month-by-month clinic launches over a 1-year period.")
    
    with st.expander("⚙️ Unit Economics Controls", expanded=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        avg_bill = sc1.slider("Avg Bill Value (₹K)", 15, 50, 27, help="Average ticket size per converted 1Cx.")
        conv_rate = sc2.slider("1Cx Conversion %", 20, 100, 100, help="Percentage of First Time Consults that convert.")
        capex = sc3.number_input("Capex per Clinic (₹L)", 10.0, 50.0, 28.0)
        opex = sc4.number_input("OpEx per Clinic/Mo (₹L)", 1.0, 10.0, 3.0)

    st.markdown("#### 📅 12-Month Launch Schedule & Cashflow")
    
    n_months_proj = 12
    months_labels = pd.date_range(start="2026-04-01", periods=n_months_proj, freq='MS').strftime("%b '%y").tolist()
    
    if "launch_schedule" not in st.session_state:
        default_launches = [0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
        st.session_state["launch_schedule"] = pd.DataFrame({
            "Month": months_labels,
            "Clinics to Launch": default_launches
        })
    
    c_sched, c_metrics = st.columns([1, 3])
    
    with c_sched:
        st.caption("Edit launches per month (Double click to edit):")
        edited_schedule = st.data_editor(
            st.session_state["launch_schedule"],
            column_config={
                "Month": st.column_config.Column(disabled=True),
                "Clinics to Launch": st.column_config.NumberColumn(min_value=0, max_value=20, step=1)
            },
            hide_index=True, height=450, use_container_width=True,
            key="launch_grid_editor"
        )
        
        st.session_state["launch_schedule"] = edited_schedule
        launches = edited_schedule["Clinics to Launch"].values
        
    with c_metrics:
        monthly_1cx_walkins = 150 
        mature_rev_lacs = (avg_bill * monthly_1cx_walkins * (conv_rate/100)) / 100
        ramp_multipliers = np.array([min(1.0, m/6) for m in range(n_months_proj)])
        
        total_rev_arr = np.zeros(n_months_proj)
        total_opex_arr = np.zeros(n_months_proj)
        total_capex_arr = np.zeros(n_months_proj)
        active_clinics_arr = np.zeros(n_months_proj)
        
        for t in range(n_months_proj):
            total_capex_arr[t] = launches[t] * capex
            active_clinics_arr[t] = np.sum(launches[:t+1])
            total_opex_arr[t] = active_clinics_arr[t] * opex
            for i in range(t+1):
                if launches[i] > 0:
                    age = t - i
                    total_rev_arr[t] += launches[i] * mature_rev_lacs * ramp_multipliers[age]
                    
        ebitda_arr = total_rev_arr - total_opex_arr
        net_cashflow_arr = ebitda_arr - total_capex_arr
        cum_cashflow_arr = np.cumsum(net_cashflow_arr)
        
        total_capex_overall = np.sum(total_capex_arr)
        total_rev_overall = np.sum(total_rev_arr)
        total_ebitda_overall = np.sum(ebitda_arr)
        max_burn = np.min(cum_cashflow_arr) 
        
        rm1, rm2, rm3, rm4 = st.columns(4)
        rm1.metric("Total Capex Needs", fmt_inr(total_capex_overall * 1e5))
        rm2.metric("Projected Rev (12M)", fmt_inr(total_rev_overall * 1e5))
        rm3.metric("Max Capital Burn", fmt_inr(abs(max_burn) * 1e5), "Peak Investment Required", delta_color="inverse")
        rm4.metric("Net EBITDA (12M)", fmt_inr(total_ebitda_overall * 1e5), delta="Profitable" if total_ebitda_overall > 0 else "Burn Phase")
        
        fig_phased = go.Figure()
        fig_phased.add_trace(go.Bar(x=months_labels, y=total_rev_arr, name="Revenue", marker_color='#3b82f6', opacity=0.8))
        fig_phased.add_trace(go.Bar(x=months_labels, y=-total_capex_arr, name="CapEx (-)", marker_color='#ef4444', opacity=0.8))
        fig_phased.add_trace(go.Scatter(x=months_labels, y=total_opex_arr, name="OpEx", line=dict(color='#f97316', width=2, dash='dot')))
        fig_phased.add_trace(go.Scatter(x=months_labels, y=cum_cashflow_arr, name="Cum. Cashflow (J-Curve)", line=dict(color='#10b981', width=3)))
        fig_phased.add_hline(y=0, line_color='black', line_width=1)
        fig_phased.update_layout(
            title=f"12-Month Staggered Cashflow & ROI (Total {int(np.sum(launches))} Clinics)",
            barmode='relative', height=400, margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="₹ Lacs"
        )
        st.plotly_chart(fig_phased, use_container_width=True, config=PLOTLY_CFG)

# ── FOOTER ─────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("v10.0-Advanced Edition | System Active")
if st.sidebar.button("Force Global Re-Scan"):
    st.cache_data.clear()
    st.rerun()
