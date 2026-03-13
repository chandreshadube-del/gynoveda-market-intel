"""
Gynoveda Expansion Intelligence - Advanced Master Edition
Featuring Demographic Penetration, Phased Forecaster, Unified GIS & Smoothed O2O Engine
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
                    elif 'pop' in fname or 'demographic' in fname or 'indian_cities' in fname:
                        std_name = 'std_population.csv'
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
                
                # Auto-correct column names
                for v in ['city', 'city name', 'clinic city', 'name of city']:
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
                
                # Auto-catch Population column
                pop_cols = [c for c in df.columns if 'pop' in str(c).lower()]
                if pop_cols and 'Population' not in df.columns:
                    df.rename(columns={pop_cols[0]: 'Population'}, inplace=True)
                    if df['Population'].dtype == 'object':
                        df['Population'] = pd.to_numeric(df['Population'].astype(str).str.replace(',', '', regex=False), errors='coerce')
                        
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
    d['population'] = _safe_load("std_population.csv")
    
    return d

data = load_all_data()

# ── UI BUILDER ──────────────────────────────────────────────────────────
st.markdown(
    """<div class="hero-banner">
        <div class="hero-title">Gynoveda Expansion Intelligence v2</div>
        <div class="hero-sub">Geospatial Demand Clustering, Demographic Penetration & Financial Forecaster</div>
    </div>""", unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Network Pulse", 
    "🌆 Same-City Expansion", 
    "🚀 New-City Expansion", 
    "📈 Phased ROI Forecaster",
    "🔄 Pincode Look-Alike O2O"
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
    st.info("💡 **Insights Engine:** To properly evaluate expansion, the engine looks at **Digital Demand** (Web Orders) overlapping with **Geospatial distances** from current clinics (>20km whitespace), **Competitor Density**, and **Demographic Penetration**.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: SAME-CITY EXPANSION (DEEPENING)
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Same-City Catchment & Cannibalization Risk")
    st.caption("Evaluate local catchment areas and competitor density before adding a new clinic to an existing market.")
    
    if not data['clinics'].empty and 'City' in data['clinics'].columns:
        data['clinics']['City'] = data['clinics']['City'].astype(str).str.title().str.strip()
        cities = data['clinics']['City'].dropna().unique().tolist()
        
        if len(cities) > 0:
            sel_city = st.selectbox("Select Target City for Deepening", sorted(cities))
            city_clinics = data['clinics'][data['clinics']['City'] == sel_city].copy()
            
            st.write(f"**Active Clinics in {sel_city}: {len(city_clinics)}**")
            show_cols = [c for c in ['Clinic Code', 'Clinic Address', 'Latitude', 'Longitude'] if c in city_clinics.columns]
            st.dataframe(city_clinics[show_cols], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown(f"#### 🗺️ Local Map: {sel_city}")
            
            t1, t2 = st.columns(2)
            show_demand = t1.toggle("🔥 Show Pincode Demand", value=True)
            show_comp = t2.toggle("🏥 Show IVF Competitors", value=True)
            
            fig_map = go.Figure()
            
            # --- Same-City Demand Layer ---
            if show_demand and not data['pin_geo'].empty:
                w_df = pd.DataFrame()
                c_df = pd.DataFrame()
                
                if not data['demand_web'].empty and 'City' in data['demand_web'].columns:
                    w_df = data['demand_web'][data['demand_web']['City'].astype(str).str.title().str.strip() == sel_city].copy()
                if not data['demand_clinic'].empty and 'City' in data['demand_clinic'].columns:
                    c_df = data['demand_clinic'][data['demand_clinic']['City'].astype(str).str.title().str.strip() == sel_city].copy()
                    
                w_agg = w_df.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Web_1Cx'}) if not w_df.empty else pd.DataFrame(columns=['Zip', 'Web_1Cx'])
                c_agg = c_df.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Clinic_1Cx'}) if not c_df.empty else pd.DataFrame(columns=['Zip', 'Clinic_1Cx'])
                
                w_agg['Zip'] = pd.to_numeric(w_agg['Zip'], errors='coerce')
                c_agg['Zip'] = pd.to_numeric(c_agg['Zip'], errors='coerce')
                
                demand_pin = pd.merge(w_agg, c_agg, on='Zip', how='outer').fillna(0)
                demand_pin['Total_1Cx'] = demand_pin['Web_1Cx'] + demand_pin['Clinic_1Cx']
                
                if not demand_pin.empty:
                    pin_geo = data['pin_geo'].copy()
                    map_df = demand_pin.merge(pin_geo, left_on='Zip', right_on='pincode', how='inner')
                    
                    if not map_df.empty:
                        sizeref = 2.0 * map_df['Total_1Cx'].max() / (35.**2) if map_df['Total_1Cx'].max() > 0 else 1
                        fig_map.add_trace(go.Scattermapbox(
                            lat=map_df["lat"], lon=map_df["lon"], mode='markers',
                            marker=dict(size=map_df["Total_1Cx"], sizemode='area', sizeref=sizeref, sizemin=4,
                                        color=map_df["Total_1Cx"], colorscale="OrRd", showscale=True,
                                        colorbar=dict(title="Local 1Cx", x=0.02, y=0.5, len=0.7)),
                            text="<b>Zip: " + map_df["Zip"].astype(int).astype(str) + "</b><br>Total 1Cx: " + map_df["Total_1Cx"].astype(int).astype(str),
                            name='Patient Demand', hoverinfo='text'
                        ))

            # --- Same-City Competitor Layer ---
            if show_comp and not data['ivf_comp'].empty and 'City' in data['ivf_comp'].columns:
                ivf_df = data['ivf_comp'][data['ivf_comp']['City'].astype(str).str.title().str.strip() == sel_city].dropna(subset=['Latitude', 'Longitude'])
                if not ivf_df.empty:
                    fig_map.add_trace(go.Scattermapbox(
                        lat=ivf_df['Latitude'], lon=ivf_df['Longitude'], mode='markers',
                        marker=dict(size=8, color='#64748b'), name='IVF Competitors',
                        text="<b>" + ivf_df.get('Clinic_Name', 'IVF Center').astype(str) + "</b>", hoverinfo='text'
                    ))

            # --- Active Clinics Layer ---
            if 'Latitude' in city_clinics.columns and 'Longitude' in city_clinics.columns:
                valid_clinics = city_clinics.dropna(subset=['Latitude', 'Longitude'])
                if not valid_clinics.empty:
                    fig_map.add_trace(go.Scattermapbox(
                        lat=valid_clinics['Latitude'], lon=valid_clinics['Longitude'], mode='markers+text',
                        marker=dict(size=18, color='#1a1f36'), name='Our Clinics',
                        text=valid_clinics.get('Clinic Code', 'Clinic').astype(str), textposition="bottom center", hoverinfo='text'
                    ))
                    center_lat = valid_clinics['Latitude'].mean()
                    center_lon = valid_clinics['Longitude'].mean()
                else:
                    center_lat, center_lon = 20.5937, 78.9629
            else:
                center_lat, center_lon = 20.5937, 78.9629

            fig_map.update_layout(
                mapbox=dict(style="carto-positron", center=dict(lat=center_lat, lon=center_lon), zoom=10),
                margin={"r":0,"t":0,"l":0,"b":0}, height=500,
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, bgcolor="rgba(255,255,255,0.85)")
            )
            st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.warning("No valid cities found in the Clinics file.")
    else:
        st.warning("Clinic Lat/Lon data not found. Please upload it via the sidebar.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: NEW-CITY EXPANSION (WHITESPACE DISCOVERY)
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🚀 New-City Expansion (Whitespace Discovery)")
    st.caption("Identify entirely new markets driven by high organic digital demand, clinic spillover, competitor density, and **Total Addressable Population**.")
    
    has_new_city_data = (not data['demand_web'].empty or not data['demand_clinic'].empty) and not data['clinics'].empty
    
    if has_new_city_data:
        
        # 1. Identify Active Cities
        data['clinics']['City'] = data['clinics']['City'].astype(str).str.title().str.strip()
        active_cities = set(data['clinics']['City'].dropna().unique())
        
        # 2. Extract Web Demand per City
        df_w = data['demand_web'].copy() if not data['demand_web'].empty else pd.DataFrame(columns=['City', 'Customer ID', 'Zip'])
        if 'City' in df_w.columns:
            df_w['City'] = df_w['City'].astype(str).str.title().str.strip()
            web_demand = df_w.groupby('City').agg(Web_Patients=('Customer ID', 'nunique')).reset_index()
        else:
            web_demand = pd.DataFrame(columns=['City', 'Web_Patients'])
            
        # 3. Extract Clinic Spillover (Travel Demand)
        df_c = data['demand_clinic'].copy() if not data['demand_clinic'].empty else pd.DataFrame(columns=['City', 'Customer ID', 'Zip'])
        if 'City' in df_c.columns:
            df_c['City'] = df_c['City'].astype(str).str.title().str.strip()
            clinic_spillover = df_c.groupby('City').agg(Travel_Patients=('Customer ID', 'nunique')).reset_index()
        else:
            clinic_spillover = pd.DataFrame(columns=['City', 'Travel_Patients'])
            
        # 4. Extract IVF Density
        df_ivf = data['ivf_comp'].copy() if not data['ivf_comp'].empty else pd.DataFrame(columns=['City', 'Clinic_Name'])
        if 'City' in df_ivf.columns:
            df_ivf['City'] = df_ivf['City'].astype(str).str.title().str.strip()
            ivf_density = df_ivf.groupby('City').agg(IVF_Centers=('Clinic_Name', 'nunique')).reset_index()
        else:
            ivf_density = pd.DataFrame(columns=['City', 'IVF_Centers'])
            
        # 5. Merge Demand Data into Unserved Pool
        unserved = pd.merge(web_demand, clinic_spillover, on='City', how='outer').fillna(0)
        unserved = pd.merge(unserved, ivf_density, on='City', how='outer').fillna(0)
        
        # 6. Extract Demographic Population Data
        df_pop = data.get('population', pd.DataFrame())
        if not df_pop.empty and 'City' in df_pop.columns and 'Population' in df_pop.columns:
            df_pop['City'] = df_pop['City'].astype(str).str.title().str.strip()
            df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce').fillna(0)
            city_pop = df_pop.groupby('City')['Population'].sum().reset_index()
            unserved = pd.merge(unserved, city_pop, on='City', how='left')
        else:
            unserved['Population'] = np.nan
        
        # Drop active cities from the expansion list
        unserved = unserved[~unserved['City'].isin(active_cities)]
        unserved = unserved[~unserved['City'].isin(['Nan', 'None', '-', '', 'NaN'])]
        
        # Calculate Total Demand (Web + Travel)
        unserved['Total_Demand'] = unserved['Web_Patients'] + unserved['Travel_Patients']
        unserved = unserved[unserved['Total_Demand'] > 0].sort_values('Total_Demand', ascending=False)
        
        if not unserved.empty:
            st.markdown("##### Opportunity Breakdown")
            
            # Format dropdown with high-level stats
            city_options = [f"{row['City']} (Total Demand: {int(row['Total_Demand']):,} | IVF: {int(row['IVF_Centers'])})" for _, row in unserved.iterrows()]
            sel_new_city_str = st.selectbox("Select Prospective New City", city_options)
            sel_new_city = sel_new_city_str.split(" (")[0]
            
            city_stats = unserved[unserved['City'] == sel_new_city].iloc[0]
            
            nc1, nc2, nc3, nc4, nc5 = st.columns(5)
            nc1.metric("Total Local Demand", f"{int(city_stats['Total_Demand']):,}", "Unique Patients")
            nc2.metric("Digital Demand", f"{int(city_stats['Web_Patients']):,}", "Web Orders")
            nc3.metric("Clinic Spillover", f"{int(city_stats['Travel_Patients']):,}", "Travelled to other cities")
            nc4.metric("IVF Competitors", f"{int(city_stats['IVF_Centers']):,}", "Market Saturation", delta_color="inverse")
            
            if pd.notna(city_stats.get('Population')) and city_stats['Population'] > 0:
                pop_val = city_stats['Population']
                penetration = (city_stats['Total_Demand'] / pop_val) * 100000 
                nc5.metric("Total Population", f"{pop_val/1e5:.1f}L", f"{penetration:.1f} pts per 100k")
            else:
                nc5.metric("Total Population", "No Data", "Upload Population CSV")
            
            st.markdown("---")
            st.markdown(f"#### 🗺️ Whitespace Map: {sel_new_city}")
            
            t1, t2 = st.columns(2)
            show_demand_new = t1.toggle("🔥 Show Digital & Spillover Hotspots", value=True, key='tog_d_new')
            show_comp_new = t2.toggle("🏥 Show IVF Competitors", value=True, key='tog_c_new')
            
            fig_new_map = go.Figure()
            lat_list, lon_list = [], []
            
            # --- New-City Demand Layer ---
            if show_demand_new and not data['pin_geo'].empty:
                w_df_new = df_w[df_w['City'] == sel_new_city].copy()
                c_df_new = df_c[df_c['City'] == sel_new_city].copy()
                
                w_agg_new = pd.DataFrame(columns=['Zip', 'Web_1Cx'])
                if not w_df_new.empty and 'Zip' in w_df_new.columns:
                    w_df_new['Zip'] = pd.to_numeric(w_df_new['Zip'], errors='coerce')
                    w_agg_new = w_df_new.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Web_1Cx'})
                    
                c_agg_new = pd.DataFrame(columns=['Zip', 'Travel_1Cx'])
                if not c_df_new.empty and 'Zip' in c_df_new.columns:
                    c_df_new['Zip'] = pd.to_numeric(c_df_new['Zip'], errors='coerce')
                    c_agg_new = c_df_new.groupby('Zip')['Customer ID'].nunique().reset_index().rename(columns={'Customer ID': 'Travel_1Cx'})
                    
                demand_pin_new = pd.merge(w_agg_new, c_agg_new, on='Zip', how='outer').fillna(0)
                demand_pin_new['Total_1Cx'] = demand_pin_new['Web_1Cx'] + demand_pin_new['Travel_1Cx']
                
                if not demand_pin_new.empty:
                    pin_geo = data['pin_geo'].copy()
                    map_df_new = demand_pin_new.merge(pin_geo, left_on='Zip', right_on='pincode', how='inner')
                    
                    if not map_df_new.empty:
                        sizeref = 2.0 * map_df_new['Total_1Cx'].max() / (35.**2) if map_df_new['Total_1Cx'].max() > 0 else 1
                        fig_new_map.add_trace(go.Scattermapbox(
                            lat=map_df_new["lat"], lon=map_df_new["lon"], mode='markers',
                            marker=dict(size=map_df_new["Total_1Cx"], sizemode='area', sizeref=sizeref, sizemin=6,
                                        color=map_df_new["Total_1Cx"], colorscale="OrRd", showscale=True,
                                        colorbar=dict(title="Total Demand", x=0.02, y=0.5, len=0.7)),
                            text="<b>Zip: " + map_df_new["Zip"].astype(int).astype(str) + "</b><br>" +
                                 "Web Patients: " + map_df_new["Web_1Cx"].astype(int).astype(str) + "<br>" +
                                 "Spillover Patients: " + map_df_new["Travel_1Cx"].astype(int).astype(str),
                            name='Patient Demand', hoverinfo='text'
                        ))
                        lat_list.extend(map_df_new['lat'].tolist())
                        lon_list.extend(map_df_new['lon'].tolist())

            # --- New-City Competitor Layer ---
            if show_comp_new and not df_ivf.empty and 'Latitude' in df_ivf.columns and 'Longitude' in df_ivf.columns:
                ivf_df_new = df_ivf[df_ivf['City'] == sel_new_city].dropna(subset=['Latitude', 'Longitude'])
                if not ivf_df_new.empty:
                    fig_new_map.add_trace(go.Scattermapbox(
                        lat=ivf_df_new['Latitude'], lon=ivf_df_new['Longitude'], mode='markers',
                        marker=dict(size=8, color='#64748b'), name='IVF Competitors',
                        text="<b>" + ivf_df_new.get('Clinic_Name', 'IVF Center').astype(str) + "</b>", hoverinfo='text'
                    ))
                    lat_list.extend(ivf_df_new['Latitude'].tolist())
                    lon_list.extend(ivf_df_new['Longitude'].tolist())
            
            # Auto-center map based on available points
            if lat_list and lon_list:
                center_lat = sum(lat_list) / len(lat_list)
                center_lon = sum(lon_list) / len(lon_list)
            else:
                center_lat, center_lon = 20.5937, 78.9629 # Default India
                
            fig_new_map.update_layout(
                mapbox=dict(style="carto-positron", center=dict(lat=center_lat, lon=center_lon), zoom=10),
                margin={"r":0,"t":0,"l":0,"b":0}, height=500,
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, bgcolor="rgba(255,255,255,0.85)")
            )
            st.plotly_chart(fig_new_map, use_container_width=True, config=PLOTLY_CFG)
            
            # Show Competitor Density Table for this specific city
            if not df_ivf.empty and show_comp_new:
                st.markdown("##### Known Competitors in this Whitespace")
                ivf_show = df_ivf[df_ivf['City'] == sel_new_city]
                if not ivf_show.empty:
                    show_cols = [c for c in ['Clinic_Name', 'Brand_Name', 'Final_Tier', 'Area/Locality'] if c in ivf_show.columns]
                    st.dataframe(ivf_show[show_cols], hide_index=True, use_container_width=True)
                else:
                    st.caption("No registered IVF competitors found in this city's database.")
        else:
            st.info("No unserved cities found with active web demand.")
    else:
        st.warning("Upload `Clinics Lat log`, `First Time customer - clinic`, and `First Time customer - website` to enable New-City Discovery.")

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

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: PINCODE LOOK-ALIKE O2O ENGINE (SMOOTHED APPLES-TO-APPLES MATCHING)
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🔄 Pincode Look-Alike O2O Engine")
    st.caption("Matches unserved pincode hotspots to historical clusters to project accurate physical clinic revenues.")

    if not data['demand_clinic'].empty and not data['demand_web'].empty:
        
        st.markdown("#### 1. Proven O2O Multipliers (Served Clusters)")
        st.info("The engine isolates the specific web demand in the exact local SubCity where a clinic was launched, calculating a highly accurate Apples-to-Apples O2O Multiplier for that local cluster.")
        
        # Parse data safely
        df_c = data['demand_clinic'].copy()
        df_w = data['demand_web'].copy()
        df_c['Total'] = pd.to_numeric(df_c['Total'], errors='coerce')
        df_w['Total'] = pd.to_numeric(df_w['Total'], errors='coerce')
        df_c['Date'] = pd.to_datetime(df_c['Date'], errors='coerce')
        df_w['Date'] = pd.to_datetime(df_w['Date'], errors='coerce')
        df_w['Zip'] = pd.to_numeric(df_w['Zip'], errors='coerce')
        
        # 1. Map Clinic Loc to its primary physical SubCity (Cluster)
        clinic_subcity_map = df_c.groupby('Clinic Loc')['SubCity'].agg(lambda x: x.mode().iloc[0] if len(x.mode())>0 else None).reset_index()
        
        # 2. Calculate Actual Clinic Revenue
        clinic_rev = df_c.groupby('Clinic Loc').agg(
            Total_Clinic_Rev=('Total', 'sum'),
            Min_Date=('Date', 'min'),
            Max_Date=('Date', 'max')
        ).reset_index()
        clinic_rev['Months_Active'] = ((clinic_rev['Max_Date'] - clinic_rev['Min_Date']).dt.days / 30).clip(lower=1)
        clinic_rev['Avg_Mo_Clinic_Rev'] = clinic_rev['Total_Clinic_Rev'] / clinic_rev['Months_Active']
        
        served_clusters = pd.merge(clinic_rev, clinic_subcity_map, on='Clinic Loc', how='inner').dropna(subset=['SubCity'])
        
        # 3. Calculate Web Demand for ALL SubCities
        web_subcity = df_w.groupby('SubCity').agg(
            Total_Web_Rev=('Total', 'sum'),
            Web_Unique_Patients=('Customer ID', 'nunique'),
            Min_Date=('Date', 'min'),
            Max_Date=('Date', 'max')
        ).reset_index()
        web_subcity['Months_Active'] = ((web_subcity['Max_Date'] - web_subcity['Min_Date']).dt.days / 30).clip(lower=1)
        web_subcity['Avg_Mo_Web_Rev'] = web_subcity['Total_Web_Rev'] / web_subcity['Months_Active']
        web_subcity['Avg_Mo_Web_Patients'] = web_subcity['Web_Unique_Patients'] / web_subcity['Months_Active']
        
        # 4. Merge Served Clinics with their specific Web SubCity Demand
        o2o_clusters = pd.merge(served_clusters, web_subcity[['SubCity', 'Avg_Mo_Web_Rev', 'Avg_Mo_Web_Patients']], on='SubCity', how='inner')
        o2o_clusters = o2o_clusters[(o2o_clusters['Avg_Mo_Web_Rev'] > 0) & (o2o_clusters['Avg_Mo_Web_Patients'] > 0)]
        o2o_clusters['O2O_Multiplier'] = o2o_clusters['Avg_Mo_Clinic_Rev'] / o2o_clusters['Avg_Mo_Web_Rev']
        o2o_clusters = o2o_clusters.sort_values('Avg_Mo_Clinic_Rev', ascending=False)
        
        # Display top clusters chart
        plot_df = o2o_clusters.head(15) 
        fig_o2o_proof = make_subplots(specs=[[{"secondary_y": True}]])
        fig_o2o_proof.add_trace(go.Bar(x=plot_df['Clinic Loc'], y=plot_df['Avg_Mo_Web_Rev']/100000, name='Local Web Rev (₹L)', marker_color='#3b82f6'), secondary_y=False)
        fig_o2o_proof.add_trace(go.Bar(x=plot_df['Clinic Loc'], y=plot_df['Avg_Mo_Clinic_Rev']/100000, name='Actual Clinic Rev (₹L)', marker_color='#10b981'), secondary_y=False)
        fig_o2o_proof.add_trace(go.Scatter(x=plot_df['Clinic Loc'], y=plot_df['O2O_Multiplier'], name='O2O Multiplier (X)', mode='lines+markers+text',
                                           text=plot_df['O2O_Multiplier'].round(1).astype(str) + "X", textposition="top center",
                                           line=dict(color='#f97316', width=3), marker=dict(size=8)), secondary_y=True)

        fig_o2o_proof.update_layout(
            barmode='group', height=450, title='Actual Offline vs Online Performance by Local Catchment',
            margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_o2o_proof.update_yaxes(title_text="Avg Monthly Rev (₹ Lacs)", secondary_y=False)
        fig_o2o_proof.update_yaxes(title_text="O2O Multiplier (X)", secondary_y=True, range=[0, plot_df['O2O_Multiplier'].max() * 1.2])
        st.plotly_chart(fig_o2o_proof, use_container_width=True, config=PLOTLY_CFG)

        # --- 2. Pincode Hotspot Look-Alike Sandbox ---
        st.markdown("---")
        st.markdown("#### 2. Pincode Hotspot Look-Alike Engine (Smoothed & Safe)")
        st.caption("Select an unserved Pincode. The engine finds the 3 'Served Clinic Clusters' with the closest matching historical Unique Web Patients to apply a blended, safe O2O multiplier (extreme anomalies >75X are automatically removed).")
        
        if 'Zip' in df_w.columns:
            # Group unserved web demand by Zip Code
            unserved_pins = df_w.groupby('Zip').agg(
                Total_Web_Rev=('Total', 'sum'),
                Web_Unique_Patients=('Customer ID', 'nunique'),
                City=('City', 'first'),
                SubCity=('SubCity', 'first')
            ).reset_index()
            
            # Using 60 months as standard timeline for website
            unserved_pins['Avg_Mo_Web_Rev'] = unserved_pins['Total_Web_Rev'] / 60 
            unserved_pins['Avg_Mo_Web_Patients'] = unserved_pins['Web_Unique_Patients'] / 60
            
            # Merge Population data if available
            df_pop = data.get('population', pd.DataFrame())
            if not df_pop.empty and 'Zip' in df_pop.columns and 'Population' in df_pop.columns:
                df_pop['Zip'] = pd.to_numeric(df_pop['Zip'], errors='coerce')
                df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')
                pin_pop = df_pop.groupby('Zip')['Population'].sum().reset_index()
                unserved_pins = pd.merge(unserved_pins, pin_pop, on='Zip', how='left')
            else:
                unserved_pins['Population'] = np.nan
            
            # Remove zips that fall inside already served SubCities
            active_subcities = set(o2o_clusters['SubCity'].unique())
            unserved_pins = unserved_pins[~unserved_pins['SubCity'].isin(active_subcities)].copy()
            unserved_pins = unserved_pins[unserved_pins['Avg_Mo_Web_Patients'] >= 0.5].sort_values('Avg_Mo_Web_Patients', ascending=False)
            
            if not unserved_pins.empty:
                
                # --- The FIXED Core Matchmaking Function ---
                # 1. Filter out extreme outliers (e.g., > 75X multiplier)
                safe_o2o_clusters = o2o_clusters[o2o_clusters['O2O_Multiplier'] <= 75].copy()
                
                def find_lookalike_smoothed(web_patients):
                    if safe_o2o_clusters.empty: 
                        return "None", 0, 1.0
                    
                    # 2. Absolute differences in patient counts
                    diffs = np.abs(safe_o2o_clusters['Avg_Mo_Web_Patients'] - web_patients)
                    
                    # 3. Get the indices of the 3 closest matching clinics (K-Nearest Neighbors)
                    closest_3_idx = diffs.nsmallest(3).index
                    
                    # 4. Data for these 3 closest clinics
                    closest_clinics = safe_o2o_clusters.loc[closest_3_idx]
                    
                    # 5. Blend (Average) their multipliers
                    blended_multiplier = closest_clinics['O2O_Multiplier'].mean()
                    
                    primary_match_name = closest_clinics.iloc[0]['Clinic Loc']
                    primary_match_pts = closest_clinics.iloc[0]['Avg_Mo_Web_Patients']
                    
                    return primary_match_name, primary_match_pts, blended_multiplier
                
                sc1, sc2 = st.columns([1, 2])
                with sc1:
                    cluster_options = [f"{int(row['Zip'])} ({row['City']} - {row['SubCity']}) [{row['Avg_Mo_Web_Patients']:.1f} pts/mo]" for _, row in unserved_pins.head(500).iterrows()]
                    selected_cluster_str = st.selectbox("Select Unserved Pincode Hotspot", cluster_options)
                    
                    sel_zip = int(selected_cluster_str.split(" ")[0])
                    cluster_data = unserved_pins[unserved_pins['Zip'] == sel_zip].iloc[0]
                    
                    base_web_rev = cluster_data['Avg_Mo_Web_Rev']
                    base_web_patients = cluster_data['Avg_Mo_Web_Patients']
                    
                    # Apply the new Smoothed Look-Alike Match
                    sim_clinic, sim_clinic_pts, blended_mult = find_lookalike_smoothed(base_web_patients)
                    projected_offline_sales = base_web_rev * blended_mult
                    
                    st.success(f"**🤖 Smoothed Look-Alike Match Found!**\n\nThis pincode mirrors the demand profile of **{sim_clinic}**.\n\nTo prevent extreme outliers, the engine blended the 3 closest historical clinic profiles, resulting in a safe O2O Multiplier of **{blended_mult:.1f}X**.")
                    
                with sc2:
                    fig_o2o = go.Figure(go.Waterfall(
                        name="O2O", orientation="v", measure=["absolute", "relative", "total"],
                        x=["Current Web Rev/Mo", f"O2O Uplift ({blended_mult:.1f}X)", "Projected Clinic Rev/Mo"],
                        textposition="outside",
                        text=[fmt_inr(base_web_rev), f"+{fmt_inr(projected_offline_sales - base_web_rev)}", fmt_inr(projected_offline_sales)],
                        y=[base_web_rev, projected_offline_sales - base_web_rev, projected_offline_sales],
                        connector={"line":{"color":"rgb(63, 63, 63)"}},
                        decreasing={"marker":{"color":"#ef4444"}},
                        increasing={"marker":{"color":"#3b82f6"}},
                        totals={"marker":{"color":"#10b981"}}
                    ))
                    
                    fig_o2o.update_layout(
                        title=f"Apples-to-Apples O2O Projection for Pincode {sel_zip}",
                        showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20),
                        yaxis=dict(title="Monthly Revenue (₹)", showgrid=True, gridcolor='#f1f5f9')
                    )
                    st.plotly_chart(fig_o2o, use_container_width=True, config=PLOTLY_CFG)
                    
                with st.expander("View Top 100 Pincode Hotspots & Look-Alike Projections"):
                    # Vectorized applying function for the table
                    unserved_pins[['LookAlike_Clinic', 'LookAlike_Web_Pts', 'Applied_Multiplier']] = unserved_pins['Avg_Mo_Web_Patients'].apply(lambda x: pd.Series(find_lookalike_smoothed(x)))
                    unserved_pins['Projected_Clinic_Rev'] = unserved_pins['Avg_Mo_Web_Rev'] * unserved_pins['Applied_Multiplier']
                    
                    # Include Penetration calculation if population data was successfully mapped
                    if 'Population' in unserved_pins.columns and unserved_pins['Population'].notna().any():
                        unserved_pins['Penetration (pts/100k)'] = (unserved_pins['Avg_Mo_Web_Patients'] / unserved_pins['Population']) * 100000
                        disp_cols = ['Zip', 'City', 'SubCity', 'Avg_Mo_Web_Patients', 'Population', 'Penetration (pts/100k)', 'LookAlike_Clinic', 'Projected_Clinic_Rev']
                    else:
                        disp_cols = ['Zip', 'City', 'SubCity', 'Avg_Mo_Web_Patients', 'Avg_Mo_Web_Rev', 'LookAlike_Clinic', 'Projected_Clinic_Rev']
                        
                    st.dataframe(
                        unserved_pins[disp_cols].head(100).rename(columns={
                            'Avg_Mo_Web_Patients': 'Web Patients/Mo',
                            'Avg_Mo_Web_Rev': 'Web Rev/Mo (₹)',
                            'LookAlike_Clinic': 'Matched Clinic Profile',
                            'Projected_Clinic_Rev': 'Projected Clinic Rev/Mo (₹)'
                        }).style.format({
                            'Zip': "{:.0f}",
                            'Web Patients/Mo': "{:.1f}",
                            'Web Rev/Mo (₹)': "₹{:,.0f}",
                            'Population': "{:,.0f}",
                            'Penetration (pts/100k)': "{:.1f}",
                            'Projected Clinic Rev/Mo (₹)': "₹{:,.0f}"
                        }),
                        hide_index=True, use_container_width=True
                    )
            else:
                st.warning("Not enough unserved web demand data to run the simulator.")
    else:
        st.warning("Please ensure both 'Clinic' and 'Website' demand data are loaded via the sidebar to use the Dynamic O2O Engine.")

# ── FOOTER ─────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("v18.0-Advanced Edition | System Active")
if st.sidebar.button("Force Global Re-Scan"):
    st.cache_data.clear()
    st.rerun()
