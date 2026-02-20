"""
Gynoveda Expansion Intelligence
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, json, math

st.set_page_config(page_title="Gynoveda · Expansion Intel", layout="wide", page_icon="◉")

# ── Formatting helpers ──────────────────────────────────────────────────
def fmt_inr(v, prefix="₹", d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return f"{prefix}0"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e7: return f"{sign}{prefix}{v/1e7:.{d}f} Cr"
    if v >= 1e5: return f"{sign}{prefix}{v/1e5:.{d}f}L"
    if v >= 1e3: return f"{sign}{prefix}{v/1e3:.{d}f}K"
    return f"{sign}{prefix}{v:.0f}"

def fmt_num(v, d=0):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "0"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e5: return f"{sign}{v/1e5:.{d+1}f}L"
    if v >= 1e3: return f"{sign}{v/1e3:.{d}f}K"
    return f"{sign}{v:.0f}"

def pct(v, d=0):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "0%"
    return f"{v*100:.{d}f}%" if abs(v) < 1 else f"{v:.{d}f}%"

PLOTLY_CFG = {'responsive': True, 'displayModeBar': False, 'staticPlot': False}

# Plotly layout defaults — clean, minimal
# NOTE: Do NOT include xaxis/yaxis/margin here — they conflict with per-chart overrides
CHART_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#333"),
    legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=11)),
    title=dict(text='', font=dict(size=14, color="#555")),
)

def _apply_layout(fig, **overrides):
    """Apply CHART_LAYOUT + sensible axis defaults, then overrides."""
    defaults = dict(
        margin=dict(l=40, r=20, t=44, b=50),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False),
    )
    defaults.update(CHART_LAYOUT)
    # Convert string title to dict format for consistency
    if 'title' in overrides and isinstance(overrides['title'], str):
        overrides['title'] = dict(text=overrides['title'], font=dict(size=14, color="#555"))
    defaults.update(overrides)
    fig.update_layout(**defaults)

PALETTE = ['#c0392b', '#f97316', '#10b981', '#8b5cf6', '#3b82f6', '#06b6d4']

# ── City mapping ────────────────────────────────────────────────────────
CITY_NAMES = {
    'AGR': 'Agra', 'AHM': 'Ahmedabad', 'AMR': 'Amritsar', 'ASN': 'Asansol',
    'AUR': 'Aurangabad', 'BBS': 'Bhubaneswar', 'BLR': 'Bengaluru', 'BPL': 'Bhopal',
    'CDG': 'Chandigarh', 'CHE': 'Chennai', 'DDN': 'Dehradun', 'DMR': 'Dimapur',
    'FDB': 'Faridabad', 'GHZ': 'Ghaziabad', 'GUR': 'Gurugram', 'GUW': 'Guwahati',
    'HYD': 'Hyderabad', 'IND': 'Indore', 'ITR': 'Itanagar', 'JAI': 'Jaipur',
    'JAL': 'Jalandhar', 'KLN': 'Kalyan', 'KNP': 'Kanpur', 'KOL': 'Kolkata',
    'LDH': 'Ludhiana', 'LKO': 'Lucknow', 'MAR': 'Goa', 'MRT': 'Meerut',
    'MUM': 'Mumbai', 'MYS': 'Mysuru', 'NAG': 'Nagpur', 'NDL': 'Delhi',
    'NOI': 'Noida', 'NSK': 'Nashik', 'NVM': 'Navi Mumbai', 'PAT': 'Patna',
    'PRY': 'Prayagraj', 'PUN': 'Pune', 'RAI': 'Raipur', 'RJK': 'Rajkot',
    'RNC': 'Ranchi', 'SEC': 'Secunderabad', 'SGU': 'Siliguri', 'SUR': 'Surat',
    'THN': 'Thane', 'VAD': 'Vadodara', 'VAR': 'Varanasi',
}

SERVED_CITY_ALIASES = {
    'AGR': {'Agra'}, 'AHM': {'Ahmedabad'}, 'AMR': {'Amritsar'},
    'ASN': {'Purba Bardhaman', 'Asansol'},
    'AUR': {'Aurangabad', 'Chhatrapati Sambhajinagar'},
    'BBS': {'Khorda', 'Bhubaneswar'},
    'BLR': {'Bengaluru', 'Bangalore'},
    'BPL': {'Bhopal'}, 'CDG': {'Chandigarh'},
    'CHE': {'Chennai', 'Madras'},
    'DDN': {'Dehradun'}, 'DMR': {'Dimapur'},
    'FDB': {'Faridabad'}, 'GHZ': {'Ghaziabad'},
    'GUR': {'Gurgaon', 'Gurugram'},
    'GUW': {'Kamrup', 'Guwahati'},
    'HYD': {'Hyderabad', 'Secunderabad'},
    'IND': {'Indore'},
    'ITR': {'Papum Pare', 'Itanagar'},
    'JAI': {'Jaipur'}, 'JAL': {'Jalandhar'},
    'KLN': {'Mumbai', 'Kalyan', 'Thane'},
    'KNP': {'Kanpur'},
    'KOL': {'North 24 Parganas', 'Kolkata', 'Calcutta', 'Barasat'},
    'LDH': {'Ludhiana'}, 'LKO': {'Lucknow'},
    'MAR': {'Goa', 'Margao', 'South Goa', 'North Goa', 'Panaji'},
    'MRT': {'Meerut'},
    'MUM': {'Mumbai', 'Bombay', 'Thane', 'Kalyan', 'Navi Mumbai'},
    'MYS': {'Mysuru', 'Mysore'},
    'NAG': {'Nagpur'}, 'NDL': {'Delhi', 'New Delhi'},
    'NOI': {'Gautam Buddha Nagar', 'Noida', 'Greater Noida'},
    'NSK': {'Nashik'},
    'NVM': {'Navi Mumbai', 'Panvel', 'Raigarh(MH)', 'Raigarh'},
    'PAT': {'Patna'},
    'PRY': {'Allahabad', 'Prayagraj'},
    'PUN': {'Pune'}, 'RAI': {'Raipur'},
    'RJK': {'Rajkot'}, 'RNC': {'Ranchi'},
    'SEC': {'Hyderabad', 'Secunderabad'},
    'SGU': {'Darjiling', 'Darjeeling', 'Siliguri'},
    'SUR': {'Surat'},
    'THN': {'Mumbai', 'Thane', 'Mira Road', 'Kalyan'},
    'VAD': {'Vadodara'},
    'VAR': {'Varanasi', 'Benaras', 'Kashi'},
}

def _match_city_to_code(city_name):
    if not city_name or not isinstance(city_name, str):
        return None
    city_l = city_name.lower().strip()
    for code, aliases in SERVED_CITY_ALIASES.items():
        if any(a.lower() == city_l for a in aliases):
            return code
    return None

CLINIC_COORDS = {
    'Malad': (19.187, 72.849), 'Dadar': (19.018, 72.848), 'Thane': (19.218, 72.978),
    'Khadakpada': (19.244, 73.136), 'Virar': (19.456, 72.812), 'Mira Rd': (19.281, 72.872),
    'Kharghar': (19.047, 73.070),
    'JP Ng': (12.906, 77.586), 'Basaveshwar': (13.019, 77.535),
    'Kalyan Ng': (13.027, 77.595), 'Whitefield': (12.970, 77.750),
    'Lajpat': (28.567, 77.237), 'Rajouri': (28.636, 77.123),
    'Viman': (18.568, 73.914), 'PCMC': (18.630, 73.813), 'Kondhwa': (18.479, 73.893),
    'Madhapur': (17.448, 78.392), 'Kalasiguda': (17.440, 78.501),
    'Badakdev': (23.040, 72.530), 'Nikol': (23.049, 72.661),
    'Gomati': (26.857, 80.955), 'Alambagh': (26.815, 80.911),
    'Adajan': (21.187, 72.799), 'Vesu': (21.155, 72.771),
    'Ballygunge': (22.527, 88.358), 'New Town': (22.593, 88.480), 'Howrah': (22.596, 88.264),
    'Sec-51': (28.576, 77.342), 'Raj Ng': (28.675, 77.437),
    'Faridabad': (28.409, 77.318), 'Sec-46': (28.443, 77.065),
    'Sec-35': (30.730, 76.769), 'AB Rd': (22.720, 75.858), 'Arera Cly': (23.234, 77.435),
    'Dharam': (21.153, 79.087), 'Canada': (20.005, 73.790), 'Kailash Ng': (19.876, 75.343),
    'Ring Rd': (22.296, 70.802), 'Anna Ng': (13.086, 80.215), 'Jayalakshmipuram': (12.311, 76.640),
    'LalKothi': (26.883, 75.797), 'Civil Lines': (27.188, 78.008), 'Model Town': (26.468, 80.350),
    'Mall Rd': (31.636, 74.873), 'Jalandhar': (31.326, 75.577), 'Gurudev Ng': (30.907, 75.857),
    'Begambagh': (28.988, 77.705), 'Ballupur Rd': (30.340, 78.029),
    'Janpath': (20.296, 85.824), 'Kanka': (23.368, 85.347), 'Kankarbagh': (25.596, 85.174),
    'Elegin Rd': (25.432, 81.846), 'Mahmoorganj': (25.318, 82.997),
    'Shankar Ng': (21.234, 81.660), 'Sevoke Rd': (26.713, 88.430),
    'ABCPoint': (26.184, 91.746), 'Dimapur': (25.907, 93.727),
    'Itanagar': (27.084, 93.610), 'Margao': (15.283, 73.957),
    'Alkapuri': (22.315, 73.189),
}

def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _haversine_vec(lat1, lon1, lat2_arr, lon2_arr):
    """Vectorized haversine: one point vs arrays of points. Returns km array."""
    R = 6371.0
    rlat1 = np.radians(lat1)
    rlat2 = np.radians(lat2_arr)
    dlat = rlat2 - rlat1
    dlon = np.radians(lon2_arr) - np.radians(lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))

# ── CSS — Modern Dashboard ─────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global */
    html, body, [class*="css"] {font-family: 'Inter', system-ui, -apple-system, sans-serif !important;}
    .block-container {padding-top: 0.5rem; padding-bottom: 1rem; max-width: 1260px;}
    .main .block-container {background: #f4f6f9;}
    .stApp {background: #f4f6f9;}
    /* Hide white band but keep sidebar toggle */
    header[data-testid="stHeader"] {background: transparent !important; backdrop-filter: none !important;}
    [data-testid="stSidebarCollapsedControl"] {top: 0.5rem;}

    /* ── Sidebar — dark navy ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f36 0%, #151929 100%) !important;
    }
    [data-testid="stSidebar"] * {color: #b0b7c3 !important;}
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;
        color: #6b7280 !important; margin-top: 1rem;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stFileUploader label {
        color: #8b95a5 !important; font-size: 0.78rem;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.04); border-radius: 8px;
        border: 1px dashed rgba(255,255,255,0.1); padding: 8px;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #e0e4ea !important;
    }

    /* ── Metric cards — elevated white cards ── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    }
    [data-testid="stMetric"] label {
        font-size: 0.7rem !important; color: #6b7280 !important;
        text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem !important; font-weight: 700; color: #111827 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {font-size: 0.72rem !important;}

    /* ── Hide Streamlit chrome ── */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}

    /* ── Tabs — modern pill-style ── */
    div[data-testid="stTabs"] {
        background: #ffffff; border-radius: 12px; padding: 4px 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }
    div[data-testid="stTabs"] button {
        font-size: 0.82rem; font-weight: 500; color: #6b7280;
        border-radius: 8px 8px 0 0; padding: 10px 18px;
        transition: all 0.15s ease;
    }
    div[data-testid="stTabs"] button:hover {color: #374151; background: #f9fafb;}
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #c0392b !important; font-weight: 600;
        border-bottom: 2.5px solid #c0392b !important;
        background: transparent;
    }

    /* ── Expanders — card style ── */
    details[data-testid="stExpander"] {
        background: #ffffff; border-radius: 10px; border: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 0.5rem;
    }
    details[data-testid="stExpander"] summary {font-weight: 500; color: #374151;}

    /* ── Tables — clean ── */
    [data-testid="stDataFrame"] {
        border-radius: 10px; overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* ── Headings ── */
    h1, h2, h3 {font-weight: 700 !important; color: #111827 !important;}
    h5 {font-size: 0.95rem !important; font-weight: 600 !important; color: #374151 !important;}

    /* ── Section dividers ── */
    hr {border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0;}

    /* ── Hero banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #CB5B51 0%, #9A3E36 100%);
        border-radius: 14px; padding: 28px 32px; margin-bottom: 1.2rem;
        color: #fff; position: relative; overflow: hidden;
        box-shadow: 0 4px 16px rgba(203,91,81,0.25);
    }
    .hero-banner::after {
        content: ''; position: absolute; top: -50px; right: -50px;
        width: 180px; height: 180px; border-radius: 50%;
        background: rgba(255,255,255,0.05);
    }
    .hero-banner .hero-title {
        font-size: 1.6rem; font-weight: 800; letter-spacing: -0.3px;
        line-height: 1.2; margin: 0;
    }
    .hero-banner .hero-sub {
        font-size: 0.82rem; color: rgba(255,255,255,0.7); margin-top: 6px;
    }

    /* ── Plotly charts in white cards ── */
    [data-testid="stPlotlyChart"] {
        background: #ffffff; border-radius: 12px; padding: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* ── Section cards — wrap content sections ── */
    .dash-card {
        background: #ffffff; border-radius: 12px; padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .dash-card h5 {margin-top: 0 !important;}

    /* ── Buttons ── */
    .stButton > button {
        background: #c0392b; color: #fff; border: none;
        border-radius: 8px; font-weight: 600; font-size: 0.8rem;
        padding: 8px 20px; transition: all 0.15s ease;
    }
    .stButton > button:hover {background: #a93226; color: #fff;}

    /* ── Mobile ── */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {flex-direction: column !important;}
        [data-testid="column"] {width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important;}
        .block-container {padding-left: 0.8rem !important; padding-right: 0.8rem !important; max-width: 100% !important;}
        [data-testid="stMetric"] {padding: 10px 14px; margin-bottom: 4px;}
        [data-testid="stMetric"] label {font-size: 0.6rem !important;}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.1rem !important;}
        .hero-banner {padding: 20px 18px;}
        .hero-banner .hero-title {font-size: 1.3rem;}
        div[data-testid="stTabs"] {padding: 2px 4px 0;}
    }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ────────────────────────────────────────────────────────
DATA = "mis_data"
os.makedirs(DATA, exist_ok=True)

# ── Excel Processing (unchanged logic) ──────────────────────────────────
def process_mis_excel(file_bytes):
    import io, datetime
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    df_gs = pd.read_excel(xls, sheet_name='Goal Sales')
    clinics = df_gs.iloc[1:]
    master = clinics[['Area','Code','Tier','City','Region','Zone','V1','Launch','Age','Cabins']].copy()
    master.columns = ['area','code','tier','city','region','zone','v1','launch','age','cabins']
    master['code'] = pd.to_numeric(master['code'], errors='coerce').fillna(0).astype(int)
    master['cabins'] = pd.to_numeric(master['cabins'], errors='coerce').fillna(1).astype(int)
    master['launch'] = pd.to_datetime(master['launch'], errors='coerce').dt.strftime('%Y-%m-%d')
    master = master[master['code'] > 0]
    master.to_csv(f'{DATA}/clinic_master.csv', index=False)
    valid_codes = set(master['code'].tolist())
    master_area_to_code = dict(zip(master['area'].str.lower().str.strip(), master['code']))
    master_areas = set(master_area_to_code.keys())
    def extract_by_area(sheet_name):
        df = pd.read_excel(xls, sheet_name=sheet_name)
        date_cols = [c for c in df.columns if isinstance(c, (pd.Timestamp, datetime.datetime))]
        df['_area_key'] = df['Area'].astype(str).str.lower().str.strip()
        clinic_rows = df[df['_area_key'].isin(master_areas)].copy()
        result = pd.DataFrame()
        result['area'] = clinic_rows['Area'].values
        result['code'] = clinic_rows['_area_key'].map(master_area_to_code).astype(int).values
        seen = set()
        for dc in date_cols:
            ms = pd.Timestamp(dc).strftime('%Y-%m')
            if ms not in seen and ms <= '2026-12':
                result[ms] = pd.to_numeric(clinic_rows[dc], errors='coerce').fillna(0).values
                seen.add(ms)
        return result
    for sheet, fname in [('SalesMTD','clinic_sales_mtd'),('1Cx','clinic_1cx'),
                          ('rCx','clinic_rcx'),('CAC','clinic_cac'),('LTV','clinic_ltv')]:
        try:
            df = extract_by_area(sheet)
            df.to_csv(f'{DATA}/{fname}.csv', index=False)
        except: pass
    try:
        df_eb = pd.read_excel(xls, sheet_name='Ebitda Trend')
        area_col = df_eb.columns[0]
        df_eb['_ak'] = df_eb[area_col].astype(str).str.lower().str.strip()
        clinic_pl = df_eb[df_eb['_ak'].isin(master_areas)].copy()
        pl_out = pd.DataFrame()
        pl_out['area'] = clinic_pl[area_col].values
        pl_out['code'] = clinic_pl['_ak'].map(master_area_to_code).astype(int).values
        if 'Fy26' in clinic_pl.columns:
            pl_out['fy26_ebitda_pct'] = pd.to_numeric(clinic_pl['Fy26'], errors='coerce').fillna(0).values
        try:
            sales_df = pd.read_csv(f'{DATA}/clinic_sales_mtd.csv')
            fy26_cols = [c for c in sales_df.columns if c >= '2025-04' and c <= '2026-03' and c not in ['area','code']]
            if fy26_cols:
                sales_df['fy26_sales_l'] = sales_df[fy26_cols].sum(axis=1) * 100
                pl_out = pl_out.merge(sales_df[['code','fy26_sales_l']], on='code', how='left')
                if 'fy26_sales_l' in pl_out.columns:
                    pl_out['fy26_tacos_l'] = pl_out['fy26_sales_l'] * (1 - pl_out.get('fy26_ebitda_pct', 0))
        except: pass
        pl_out.to_csv(f'{DATA}/clinic_pl.csv', index=False)
    except: pass
    try:
        import datetime
        rows = []
        df_sm = pd.read_excel(xls, sheet_name='SalesMTD')
        date_cols = [c for c in df_sm.columns if isinstance(c, (pd.Timestamp, datetime.datetime))]
        for dc in date_cols:
            ms = pd.Timestamp(dc).strftime('%Y-%m')
            if ms <= '2026-12':
                rows.append({
                    'month': ms,
                    'clinics_cr': float(pd.to_numeric(df_sm.iloc[2][dc], errors='coerce') or 0),
                    'video_cr': float(pd.to_numeric(df_sm.iloc[1][dc], errors='coerce') or 0)
                })
        net_df = pd.DataFrame(rows)
        for sheet, col_name in [('1Cx','clinics_1cx'),('rCx','clinics_rcx')]:
            df_cx = pd.read_excel(xls, sheet_name=sheet)
            cx_dates = [c for c in df_cx.columns if isinstance(c, (pd.Timestamp, datetime.datetime))]
            cx_map = {}
            for dc in cx_dates:
                ms = pd.Timestamp(dc).strftime('%Y-%m')
                if ms <= '2026-12':
                    cx_map[ms] = float(pd.to_numeric(df_cx.iloc[2][dc], errors='coerce') or 0)
            net_df[col_name] = net_df['month'].map(cx_map).fillna(0)
        net_df.to_csv(f'{DATA}/network_monthly.csv', index=False)
    except: pass
    try:
        sales_df = pd.read_csv(f'{DATA}/clinic_sales_mtd.csv')
        cx1_df = pd.read_csv(f'{DATA}/clinic_1cx.csv')
        master_df = pd.read_csv(f'{DATA}/clinic_master.csv')
        for src_df, val_label, out_name, agg_col in [
            (sales_df, 'avg_sales_cr', 'sales_ramp_curve', 'avg_sales_l'),
            (cx1_df, 'avg_1cx', '1cx_ramp_curve', None)
        ]:
            merged = src_df.merge(master_df[['code','launch']], on='code', how='left')
            m_cols = [c for c in src_df.columns if c not in ['area','code']]
            ramp_all = []
            for _, row in merged.iterrows():
                launch = pd.to_datetime(row['launch'])
                for m in m_cols:
                    mdt = pd.to_datetime(m + '-01')
                    mn = (mdt.year - launch.year)*12 + (mdt.month - launch.month)
                    if mn >= 0 and row[m] > 0:
                        ramp_all.append({'month_num': mn, 'val': row[m]})
            if ramp_all:
                df_r = pd.DataFrame(ramp_all)
                agg = df_r.groupby('month_num').agg(avg_val=('val','mean'), clinics=('val','count')).reset_index()
                if agg_col == 'avg_sales_l':
                    agg.rename(columns={'avg_val':'avg_sales_cr'}, inplace=True)
                    agg['avg_sales_l'] = agg['avg_sales_cr'] * 100
                else:
                    agg.rename(columns={'avg_val':'avg_1cx'}, inplace=True)
                agg = agg[agg['month_num'] <= 30].sort_values('month_num')
                agg.to_csv(f'{DATA}/{out_name}.csv', index=False)
    except: pass
    return True

def process_firsttime_excel(file_bytes):
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.to_csv(f'{DATA}/pincode_firsttime.csv', index=False)
    return True

def process_zipdata_excel(file_bytes):
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    pin_demand = df.groupby(['Clinic Loc','Zip','SubCity','City','State']).agg(
        qty=('Quantity','sum'), revenue=('Total','sum')
    ).reset_index()
    pin_demand.to_csv(f'{DATA}/clinic_pincode_demand.csv', index=False)
    return True

def process_web_orders_excel(file_bytes):
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    web_city = df.groupby('City').agg(
        total_orders=('Quantity','sum'), total_revenue=('Total','sum'),
        unique_pincodes=('Zip','nunique')
    ).reset_index().sort_values('total_orders', ascending=False)
    web_city.to_csv(f'{DATA}/web_city_demand.csv', index=False)
    df['year'] = pd.to_datetime(df['Date']).dt.year
    web_pin = df.groupby(['year','Zip','City','State']).agg(
        orders=('Quantity','sum'), revenue=('Total','sum')
    ).reset_index()
    web_pin.to_csv(f'{DATA}/web_pincode_yearly.csv', index=False)
    return True


# ── Excel Processors: Analysis Suite, Competitor/Rent, Clinic Addresses ──

def process_analysis_suite_excel(file_bytes):
    """Process Gynoveda_8_Analysis_Suite.xlsx → 4 CSVs."""
    import io
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    _sheet_map = {s.lower(): s for s in xls.sheet_names}
    _written = []
    # 1. Clinic Leaderboard
    for key in ['1. clinic leaderboard', 'clinic leaderboard']:
        if key in _sheet_map:
            pd.read_excel(xls, sheet_name=_sheet_map[key]).to_csv(f'{DATA}/clinic_leaderboard.csv', index=False)
            _written.append('clinic_leaderboard'); break
    # 3. Patient Catchment
    for key in ['3. patient catchment', 'patient catchment']:
        if key in _sheet_map:
            pd.read_excel(xls, sheet_name=_sheet_map[key]).to_csv(f'{DATA}/patient_catchment.csv', index=False)
            _written.append('patient_catchment'); break
    # 6. Competitor Proximity
    for key in ['6. competitor proximity', 'competitor proximity']:
        if key in _sheet_map:
            pd.read_excel(xls, sheet_name=_sheet_map[key]).to_csv(f'{DATA}/competitor_proximity.csv', index=False)
            _written.append('competitor_proximity'); break
    return _written

def process_competitor_rent_excel(file_bytes):
    """Process Gynoveda_Competitor_Rent_Data.xlsx → 2 CSVs."""
    import io
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    _sheet_map = {s.lower(): s for s in xls.sheet_names}
    _written = []
    for key in ['ivf competitor locations', 'ivf competitors']:
        if key in _sheet_map:
            pd.read_excel(xls, sheet_name=_sheet_map[key]).to_csv(f'{DATA}/ivf_competitors.csv', index=False)
            _written.append('ivf_competitors'); break
    for key in ['rent benchmarks by city', 'rent benchmarks']:
        if key in _sheet_map:
            pd.read_excel(xls, sheet_name=_sheet_map[key]).to_csv(f'{DATA}/rent_benchmarks.csv', index=False)
            _written.append('rent_benchmarks'); break
    return _written

def process_clinic_address_excel(file_bytes):
    """Process Clinic address.xlsx → clinic_addresses.csv."""
    import io
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=None)
    # Find the header row (contains 'Clinic Code' or 'City')
    hdr_idx = 0
    for i in range(min(5, len(df))):
        row_vals = [str(v).lower() for v in df.iloc[i].values if pd.notna(v)]
        if any('clinic code' in v or 'city name' in v or 'opening date' in v for v in row_vals):
            hdr_idx = i; break
    df.columns = df.iloc[hdr_idx]
    df = df.iloc[hdr_idx + 1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    # Standardize column names
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if 'area' in cl and 'code' not in cl: col_map[c] = 'area'
        elif cl in ['city', 'city name']: col_map[c] = 'city'
        elif cl == 'state': col_map[c] = 'state'
        elif 'clinic code' in cl and 'new' not in cl: col_map[c] = 'clinic_code'
        elif 'new clinic' in cl or 'new_clinic' in cl: col_map[c] = 'new_clinic_code'
        elif 'opening' in cl or 'date' in cl: col_map[c] = 'opening_date'
        elif 'address' in cl: col_map[c] = 'address'
        elif 'landmark' in cl: col_map[c] = 'landmark'
        elif 'location' in cl: col_map[c] = 'location'
    if col_map:
        df = df.rename(columns=col_map)
    # Keep only rows with a valid city
    if 'city' in df.columns:
        df = df[df['city'].notna() & (df['city'].astype(str).str.strip() != '')]
    keep_cols = [c for c in ['area','city','state','clinic_code','new_clinic_code','opening_date','address','landmark','location'] if c in df.columns]
    df[keep_cols].to_csv(f'{DATA}/clinic_addresses.csv', index=False)
    return True


def _detect_and_process(file_bytes, file_name):
    """Auto-detect Excel file type from sheet names / columns and process accordingly."""
    import io
    fname_lower = file_name.lower()
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets_lower = {s.lower() for s in xls.sheet_names}
    df0 = pd.read_excel(xls, sheet_name=0, nrows=5)
    cols_lower = {str(c).lower().strip() for c in df0.columns}

    # ── 1. Clinic MIS — has 'Goal Sales' and 'SalesMTD' sheets
    if 'goal sales' in sheets_lower and 'salesmtd' in sheets_lower:
        process_mis_excel(file_bytes)
        return 'Clinic MIS'

    # ── 2. Analysis Suite — has numbered analysis sheets
    if any(k in sheets_lower for k in ['1. clinic leaderboard', 'clinic leaderboard', '3. patient catchment', 'patient catchment', '6. competitor proximity', 'competitor proximity']):
        written = process_analysis_suite_excel(file_bytes)
        return f'Analysis Suite ({len(written)} datasets)'

    # ── 3. Competitor/Rent Data — has 'IVF Competitor Locations' or 'Rent Benchmarks'
    if any(k in sheets_lower for k in ['ivf competitor locations', 'rent benchmarks by city']):
        written = process_competitor_rent_excel(file_bytes)
        return f'Competitor & Rent ({len(written)} datasets)'

    # ── 4. ZipData — has 'Clinic Loc', 'Zip', 'Quantity' columns
    if 'clinic loc' in cols_lower and 'zip' in cols_lower and 'quantity' in cols_lower:
        process_zipdata_excel(file_bytes)
        return 'Zip Demand'

    # ── 5. Web Orders — has 'Date', 'Quantity', 'Zip', 'Customer ID' columns but no 'Clinic Loc'
    if 'date' in cols_lower and 'quantity' in cols_lower and 'zip' in cols_lower and 'clinic loc' not in cols_lower:
        process_web_orders_excel(file_bytes)
        return 'Web Orders'

    # ── 6. FirstTime Pincodes — has 'Pincode' and 'Total Quantity'
    if 'pincode' in cols_lower and 'total quantity' in cols_lower:
        process_firsttime_excel(file_bytes)
        return 'First-Time Pincodes'

    # ── 7. Clinic Address — has 'Rule' sheet or columns like 'Clinic Code', 'Opening Date'
    if 'rule' in sheets_lower or 'clinic code' in cols_lower or 'opening date' in cols_lower:
        try:
            process_clinic_address_excel(file_bytes)
            return 'Clinic Addresses'
        except:
            pass

    # ── 8. CEI MicroMarkets — has 'D-Score (Deepening)' or 'Micro-Market Revenue' sheets
    if any(k in sheets_lower for k in ['d-score (deepening)', 'e-score (expansion)', 'micro-market revenue']):
        import shutil, io as _io
        _dest = os.path.join('mis_data', 'Gynoveda_CEI_v31_MicroMarkets.xlsx')
        with open(_dest, 'wb') as _f:
            _f.write(file_bytes)
        return 'CEI MicroMarkets Model'

    # ── 9. Fallback: check filename hints
    if 'address' in fname_lower or 'addr' in fname_lower:
        process_clinic_address_excel(file_bytes)
        return 'Clinic Addresses'
    if 'firsttime' in fname_lower or 'first_time' in fname_lower or 'first time' in fname_lower:
        process_firsttime_excel(file_bytes)
        return 'First-Time Pincodes'

    return None  # Unrecognized


# ── Sidebar: Upload ──────────────────────────────────────────────────────
with st.sidebar:
    with st.expander("📂  Update data", expanded=False):
        st.caption("Drop all Excel files at once — auto-detected")
        _uploaded_files = st.file_uploader(
            "Upload Excel files", type=['xlsx', 'xls'],
            accept_multiple_files=True, key='bulk_upload',
            label_visibility="collapsed",
        )

        if _uploaded_files:
            st.info(f"{len(_uploaded_files)} file{'s' if len(_uploaded_files) > 1 else ''} ready")

        if st.button("Process & refresh", type="primary", use_container_width=True, disabled=not _uploaded_files):
            processed, skipped, errors = [], [], []
            progress = st.progress(0, text="Starting...")
            for i, uf in enumerate(_uploaded_files):
                progress.progress((i + 1) / len(_uploaded_files), text=f"Detecting {uf.name}...")
                try:
                    result = _detect_and_process(uf.getvalue(), uf.name)
                    if result:
                        processed.append(f"{uf.name} → {result}")
                    else:
                        skipped.append(uf.name)
                except Exception as e:
                    errors.append(f"{uf.name}: {e}")
            progress.empty()
            if processed:
                st.success(f"✓ {len(processed)} processed")
                for p in processed:
                    st.caption(f"  {p}")
                # Bust ALL cached data — increment version counter + clear cache
                st.session_state['_data_ver'] = st.session_state.get('_data_ver', 0) + 1
                st.cache_data.clear()
                st.rerun()
            for s in skipped:
                st.warning(f"⚠ {s} — not recognized")
            for e in errors:
                st.error(e)


# ── Load CSVs ────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_all(_ver=0):
    """Load all CSVs. _ver param busts cache when data is re-uploaded."""
    d = {}
    d['master'] = pd.read_csv(f'{DATA}/clinic_master.csv')
    d['sales'] = pd.read_csv(f'{DATA}/clinic_sales_mtd.csv')
    d['cx1'] = pd.read_csv(f'{DATA}/clinic_1cx.csv')
    d['rcx'] = pd.read_csv(f'{DATA}/clinic_rcx.csv')
    d['cac'] = pd.read_csv(f'{DATA}/clinic_cac.csv')
    d['ltv'] = pd.read_csv(f'{DATA}/clinic_ltv.csv')
    d['pl'] = pd.read_csv(f'{DATA}/clinic_pl.csv')
    _net_raw = pd.read_csv(f'{DATA}/network_monthly.csv')
    _net_raw = _net_raw.sort_values('month').drop_duplicates(subset=['month'], keep='first')
    d['network'] = _net_raw
    d['ramp_sales'] = pd.read_csv(f'{DATA}/sales_ramp_curve.csv')
    d['ramp_1cx'] = pd.read_csv(f'{DATA}/1cx_ramp_curve.csv')
    d['pin_ft'] = pd.read_csv(f'{DATA}/pincode_firsttime.csv')
    d['pin_demand'] = pd.read_csv(f'{DATA}/clinic_pincode_demand.csv')
    d['web_city'] = pd.read_csv(f'{DATA}/web_city_demand.csv')
    d['web_pin'] = pd.read_csv(f'{DATA}/web_pincode_yearly.csv')
    _u1cx_path = f'{DATA}/web_pincode_unique_1cx.csv'
    d['web_unique_1cx'] = pd.read_csv(_u1cx_path) if os.path.exists(_u1cx_path) else pd.DataFrame(columns=['pin_int', 'unique_1cx', 'total_orders', 'total_revenue'])
    _cup_path = f'{DATA}/clinic_pincode_unique_patients.csv'
    d['clinic_unique_patients'] = pd.read_csv(_cup_path) if os.path.exists(_cup_path) else pd.DataFrame(columns=['pin_int', 'unique_clinic_patients', 'clinic_orders', 'clinic_revenue', 'clinics_visited'])
    # ── New enrichment datasets ──
    def _safe_csv(name, fallback_cols):
        p = f'{DATA}/{name}'
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=fallback_cols)
    d['competitor_prox'] = _safe_csv('competitor_proximity.csv', ['Clinic','City','IVF Centres in City','Threat Level'])
    d['rent_bench'] = _safe_csv('rent_benchmarks.csv', ['City','Tier','Avg_Rent_PSF_Month_INR','Monthly_Rent_Estimate_Low','Monthly_Rent_Estimate_High'])
    # expansion_scorecard removed per user request
    d['clinic_addr'] = _safe_csv('clinic_addresses.csv', ['area','city','address','landmark'])
    d['patient_catch'] = _safe_csv('patient_catchment.csv', ['Clinic','City','Total Visits','Unique Pins','Pins for 80%','Top10 Conc%'])
    d['clinic_lb'] = _safe_csv('clinic_leaderboard.csv', ['Clinic','City','Code','Latest Sales(₹Cr)','Attainment%','3M Growth%','CAC(₹K)'])
    d['ivf_comp'] = _safe_csv('ivf_competitors.csv', ['Chain_Name','Centre_City','Centre_Location','Approx_Lat','Approx_Lon','IVF_Cost_INR_Low','IVF_Cost_INR_High'])
    return d

data = load_all(_ver=st.session_state.get('_data_ver', 0))
master = data['master']
sales = data['sales']
cx1 = data['cx1']
rcx = data['rcx']
net = data['network'].copy()
ramp_s = data['ramp_sales']
ramp_c = data['ramp_1cx']
pin_demand = data['pin_demand']

pin_geo = pd.DataFrame(columns=['pincode','lat','lon'])
for _gp in [f'{DATA}/pin_geocode.csv',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA, 'pin_geocode.csv')]:
    if os.path.exists(_gp):
        pin_geo = pd.read_csv(_gp)
        break

pin_ft = data['pin_ft']
web_city = data['web_city']
web_pin = data['web_pin']
# ntb_show removed — 1Cx is source of truth for first-visit patients

s_months = sorted([c for c in sales.columns if c not in ['area','code']])
active_months = [m for m in s_months if (sales[m] > 0).sum() > 0]
latest_month = active_months[-1] if active_months else '2025-12'
l3m = active_months[-3:] if len(active_months) >= 3 else active_months
l6m = active_months[-6:] if len(active_months) >= 6 else active_months

# ── SCORING ENGINE (unchanged logic) ─────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def build_city_scores(_ver=0):
    web_demand = web_city.copy()
    web_demand['City_lower'] = web_demand['City'].str.lower().str.strip()
    max_orders = web_demand['total_orders'].max()
    web_demand['demand_score'] = (web_demand['total_orders'] / max_orders * 100).clip(0, 100)
    city_perf = []
    for city_code in master['city'].unique():
        city_clinics = master[master['city'] == city_code]
        city_sales = sales[sales['code'].isin(city_clinics['code'])]
        city_1cx = cx1[cx1['code'].isin(city_clinics['code'])]
        l3m_rev = city_sales[l3m].sum(axis=1).mean() if len(city_sales) > 0 and all(m in city_sales.columns for m in l3m) else 0
        if len(active_months) >= 6:
            prior_3m = active_months[-6:-3]
            prior_rev = city_sales[prior_3m].sum(axis=1).mean() if len(city_sales) > 0 and all(m in city_sales.columns for m in prior_3m) else 0
            growth = ((l3m_rev - prior_rev) / prior_rev) if prior_rev > 0 else 0
        else:
            growth = 0
        cx_months = [c for c in cx1.columns if c not in ['area','code']]
        cx_l3m = cx_months[-3:] if len(cx_months) >= 3 else cx_months
        l3m_1cx = city_1cx[cx_l3m].sum(axis=1).mean() if len(city_1cx) > 0 else 0
        total_cabins = city_clinics['cabins'].sum()
        sales_per_cabin = (l3m_rev * 100) / total_cabins if total_cabins > 0 else 0
        city_areas = city_clinics['area'].tolist()
        city_pins = pin_demand[pin_demand['Clinic Loc'].isin(city_areas)]['Zip'].nunique()
        city_name = CITY_NAMES.get(city_code, city_code)
        pl = data['pl']
        city_pl = pl[pl['code'].isin(city_clinics['code'])]
        avg_ebitda = city_pl['fy26_ebitda_pct'].mean() if len(city_pl) > 0 else 0
        city_perf.append({
            'city_code': city_code, 'city_name': city_name,
            'clinics': len(city_clinics), 'total_cabins': total_cabins,
            'l3m_rev_cr': l3m_rev, 'l3m_1cx': l3m_1cx, 'growth_pct': growth,
            'sales_per_cabin_l': sales_per_cabin, 'pincodes_served': city_pins,
            'avg_ebitda_pct': avg_ebitda
        })
    df_city = pd.DataFrame(city_perf)
    name_to_code = {}
    for code, primary in CITY_NAMES.items():
        name_to_code[primary.lower()] = code
    for code, aliases in SERVED_CITY_ALIASES.items():
        for alias in aliases:
            name_to_code[alias.lower()] = code
    web_demand['matched_code'] = web_demand['City_lower'].map(name_to_code)
    web_agg = web_demand.groupby('matched_code').agg(
        web_orders=('total_orders', 'sum'), web_revenue=('total_revenue', 'sum'),
        demand_score=('demand_score', 'max')
    ).reset_index().rename(columns={'matched_code': 'city_code'})
    df_city = df_city.merge(web_agg, on='city_code', how='left').fillna(0)
    def norm(s):
        mn, mx = s.min(), s.max()
        return ((s - mn) / (mx - mn) * 100).fillna(0) if mx > mn else pd.Series(50, index=s.index)
    df_city['d1_demand'] = norm(df_city['web_orders'])
    df_city['d2_revenue'] = norm(df_city['l3m_rev_cr'])
    df_city['d3_growth'] = norm(df_city['growth_pct'].clip(-0.5, 2))
    df_city['d4_capacity'] = norm(df_city['sales_per_cabin_l'])
    clinic_demand_by_city = pin_demand.merge(
        master[['area','city']].rename(columns={'area':'Clinic Loc'}), on='Clinic Loc', how='left'
    ).groupby('city')['qty'].sum().reset_index().rename(columns={'city':'city_code','qty':'clinic_demand'})
    df_city = df_city.merge(clinic_demand_by_city, on='city_code', how='left').fillna(0)
    df_city['o2o_ratio'] = df_city['clinic_demand'] / df_city['web_orders'].replace(0, 1)
    df_city['d5_o2o'] = norm(df_city['o2o_ratio'].clip(0, 20))
    df_city['d6_whitespace'] = norm(100 - df_city['pincodes_served'].clip(0, 500) / 5)
    df_city['d7_ebitda'] = norm(df_city['avg_ebitda_pct'].clip(-0.1, 0.5))
    df_city['cei_same'] = (
        df_city['d1_demand'] * 0.25 + df_city['d2_revenue'] * 0.20 +
        df_city['d3_growth'] * 0.15 + df_city['d4_capacity'] * 0.15 +
        df_city['d5_o2o'] * 0.10 + df_city['d6_whitespace'] * 0.10 + df_city['d7_ebitda'] * 0.05
    )
    existing_codes = set(master['city'].unique())
    new_cities = web_demand[web_demand['matched_code'].isna() | ~web_demand['matched_code'].isin(existing_codes)].copy()
    new_cities = new_cities.groupby('City').agg(
        total_orders=('total_orders', 'sum'), total_revenue=('total_revenue', 'sum'),
        unique_pincodes=('City', 'count')
    ).reset_index()
    new_cities['d1_demand'] = norm(new_cities['total_orders'])
    new_cities['d2_revenue_potential'] = norm(new_cities['total_revenue'])
    web_pin_city = web_pin.groupby(['City','year']).agg(orders=('orders','sum')).reset_index()
    growth_by_city = []
    for city in new_cities['City'].unique():
        city_trend = web_pin_city[web_pin_city['City'].str.lower() == city.lower()].sort_values('year')
        if len(city_trend) >= 2:
            recent = city_trend[city_trend['year'] >= 2023]['orders'].sum()
            older = city_trend[city_trend['year'] < 2023]['orders'].sum()
            g = (recent - older) / older if older > 0 else 0
        else:
            g = 0
        growth_by_city.append({'City': city, 'trend_growth': g})
    df_growth = pd.DataFrame(growth_by_city)
    new_cities = new_cities.merge(df_growth, on='City', how='left').fillna(0)
    new_cities['d3_growth'] = norm(new_cities['trend_growth'].clip(-1, 5))
    # E-score dimensions (computed here; final weighted score computed post-cache with session_state weights)
    # Dim 1: Spillover — from CEI_E1_Spillover_Demand.xlsx (or fallback to demand proxy)
    _e1_path = os.path.join('mis_data', 'CEI_E1_Spillover_Demand.xlsx')
    if os.path.exists(_e1_path):
        try:
            _e1_raw = pd.read_excel(_e1_path, header=None)
            _e1_hdr = None
            for _ei, _er in _e1_raw.iterrows():
                if 'Rank' in [str(v).strip() for v in _er.values if pd.notna(v)]:
                    _e1_hdr = _ei; break
            if _e1_hdr is not None:
                _e1_data = pd.read_excel(_e1_path, header=_e1_hdr)
                _e1_data = _e1_data[_e1_data['City'].notna()].copy()
                _e1_data['City_lower'] = _e1_data['City'].str.strip().str.lower()
                new_cities['City_lower'] = new_cities['City'].str.strip().str.lower()
                _e1_map = _e1_data.set_index('City_lower')['E1 Score'].to_dict()
                new_cities['e_spillover_raw'] = new_cities['City_lower'].map(_e1_map).fillna(0)
                new_cities['e_spillover'] = norm(new_cities['e_spillover_raw'])
                new_cities.drop(columns=['City_lower'], inplace=True, errors='ignore')
            else:
                new_cities['e_spillover'] = new_cities['d1_demand']
        except Exception:
            new_cities['e_spillover'] = new_cities['d1_demand']
    else:
        new_cities['e_spillover'] = new_cities['d1_demand']
    # Dim 2: Combined Demand = d2_revenue_potential (proxy: total revenue)
    new_cities['e_demand'] = new_cities['d2_revenue_potential']
    # Dim 3: PCOS Heat Index — from CEI_D2_PCOS_Heat_Index.xlsx
    _e_pcos_path = os.path.join('mis_data', 'CEI_D2_PCOS_Heat_Index.xlsx')
    if os.path.exists(_e_pcos_path):
        try:
            _ep_raw = pd.read_excel(_e_pcos_path, header=None)
            _ep_hdr = None
            for _epi, _epr in _ep_raw.iterrows():
                if 'Rank' in [str(v).strip() for v in _epr.values if pd.notna(v)]:
                    _ep_hdr = _epi; break
            if _ep_hdr is not None:
                _ep_data = pd.read_excel(_e_pcos_path, header=_ep_hdr)
                _ep_data = _ep_data[_ep_data['City'].notna()].copy()
                _ep_data['City_lower'] = _ep_data['City'].str.strip().str.lower()
                new_cities['City_lower'] = new_cities['City'].str.strip().str.lower()
                _ep_map = _ep_data.set_index('City_lower')['D2 Score'].to_dict()
                new_cities['e_pcos_raw'] = new_cities['City_lower'].map(_ep_map).fillna(0)
                new_cities['e_pcos'] = norm(new_cities['e_pcos_raw'])
                new_cities.drop(columns=['City_lower'], inplace=True, errors='ignore')
            else:
                new_cities['e_pcos'] = 50.0
        except Exception:
            new_cities['e_pcos'] = 50.0
    else:
        new_cities['e_pcos'] = 50.0
    # Dim 4: Competitive Whitespace — from CEI_E3_Competitive_Whitespace.xlsx
    _e3_path = os.path.join('mis_data', 'CEI_E3_Competitive_Whitespace.xlsx')
    if os.path.exists(_e3_path):
        try:
            _e3_raw = pd.read_excel(_e3_path, header=None)
            _e3_hdr = None
            for _e3i, _e3r in _e3_raw.iterrows():
                if 'Rank' in [str(v).strip() for v in _e3r.values if pd.notna(v)]:
                    _e3_hdr = _e3i; break
            if _e3_hdr is not None:
                _e3_data = pd.read_excel(_e3_path, header=_e3_hdr)
                _e3_data = _e3_data[_e3_data['City'].notna()].copy()
                _e3_data['City_lower'] = _e3_data['City'].str.strip().str.lower()
                new_cities['City_lower'] = new_cities['City'].str.strip().str.lower()
                _e3_map = _e3_data.set_index('City_lower')['E3 Score'].to_dict()
                new_cities['e_comp_ws_raw'] = new_cities['City_lower'].map(_e3_map).fillna(0)
                new_cities['e_comp_ws'] = norm(new_cities['e_comp_ws_raw'])
                new_cities.drop(columns=['City_lower'], inplace=True, errors='ignore')
            else:
                new_cities['e_comp_ws'] = 50.0
        except Exception:
            new_cities['e_comp_ws'] = 50.0
    else:
        new_cities['e_comp_ws'] = 50.0
    # Dim 5: Catchment Density — from CEI_D1_Catchment_Density.xlsx
    _e_catch_path = os.path.join('mis_data', 'CEI_D1_Catchment_Density.xlsx')
    if os.path.exists(_e_catch_path):
        try:
            _ec_raw = pd.read_excel(_e_catch_path, header=None)
            _ec_hdr = None
            for _eci, _ecr in _ec_raw.iterrows():
                if 'Rank' in [str(v).strip() for v in _ecr.values if pd.notna(v)]:
                    _ec_hdr = _eci; break
            if _ec_hdr is not None:
                _ec_data = pd.read_excel(_e_catch_path, header=_ec_hdr)
                _ec_data = _ec_data[_ec_data['City'].notna()].copy()
                _ec_data['City_lower'] = _ec_data['City'].str.strip().str.lower()
                new_cities['City_lower'] = new_cities['City'].str.strip().str.lower()
                _ec_map = _ec_data.set_index('City_lower')['D1 Score'].to_dict()
                new_cities['e_catchment_raw'] = new_cities['City_lower'].map(_ec_map).fillna(0)
                new_cities['e_catchment'] = norm(new_cities['e_catchment_raw'])
                new_cities.drop(columns=['City_lower'], inplace=True, errors='ignore')
            else:
                new_cities['e_catchment'] = 50.0
        except Exception:
            new_cities['e_catchment'] = 50.0
    else:
        new_cities['e_catchment'] = 50.0
    # Default equal-weight CEI (overridden post-cache with session_state weights)
    new_cities['cei_new'] = (
        new_cities['e_spillover'] * 0.20 + new_cities['e_demand'] * 0.20 +
        new_cities['e_pcos'] * 0.20 + new_cities['e_comp_ws'] * 0.20 + new_cities['e_catchment'] * 0.20
    )
    return df_city.sort_values('cei_same', ascending=False), new_cities.sort_values('cei_new', ascending=False)


@st.cache_data(ttl=300, show_spinner=False)
def build_cannibalization_matrix(_ver=0):
    multi_clinic_cities = master.groupby('city').filter(lambda x: len(x) >= 2)['city'].unique()
    results = []
    for city in multi_clinic_cities:
        city_clinics = master[master['city'] == city]['area'].tolist()
        clinic_pins = {}
        clinic_pin_vol = {}
        for clinic in city_clinics:
            cdata = pin_demand[pin_demand['Clinic Loc'] == clinic]
            clinic_pins[clinic] = set(cdata['Zip'].unique())
            clinic_pin_vol[clinic] = cdata.groupby('Zip')['qty'].sum().sort_values(ascending=False)
        for i, c1 in enumerate(city_clinics):
            for c2 in city_clinics[i+1:]:
                overlap = clinic_pins.get(c1, set()) & clinic_pins.get(c2, set())
                union = clinic_pins.get(c1, set()) | clinic_pins.get(c2, set())
                overlap_pct = len(overlap) / len(union) if len(union) > 0 else 0
                overlap_rev_c1 = pin_demand[(pin_demand['Clinic Loc'] == c1) & (pin_demand['Zip'].isin(overlap))]['revenue'].sum()
                overlap_rev_c2 = pin_demand[(pin_demand['Clinic Loc'] == c2) & (pin_demand['Zip'].isin(overlap))]['revenue'].sum()
                dist_km = None
                if c1 in CLINIC_COORDS and c2 in CLINIC_COORDS:
                    lat1, lon1 = CLINIC_COORDS[c1]
                    lat2, lon2 = CLINIC_COORDS[c2]
                    dist_km = round(_haversine_km(lat1, lon1, lat2, lon2), 1)
                vol1 = clinic_pin_vol.get(c1, pd.Series(dtype=float))
                vol2 = clinic_pin_vol.get(c2, pd.Series(dtype=float))
                vol1_total = vol1.sum()
                vol2_total = vol2.sum()
                vol1_shared = vol1.reindex(list(overlap)).sum() if overlap and vol1_total else 0
                vol2_shared = vol2.reindex(list(overlap)).sum() if overlap and vol2_total else 0
                vol_overlap_a = vol1_shared / vol1_total if vol1_total else 0
                vol_overlap_b = vol2_shared / vol2_total if vol2_total else 0
                avg_vol_overlap = (vol_overlap_a + vol_overlap_b) / 2
                top10_c1 = set(vol1.head(10).index) if len(vol1) > 0 else set()
                top10_c2 = set(vol2.head(10).index) if len(vol2) > 0 else set()
                shared_core = top10_c1 & top10_c2
                core_count = len(shared_core)
                if core_count >= 3: risk = 'Critical'
                elif core_count >= 1 or (dist_km is not None and dist_km < 5): risk = 'High'
                elif avg_vol_overlap > 0.7: risk = 'Medium'
                elif avg_vol_overlap > 0.4: risk = 'Low'
                else: risk = 'Minimal'
                results.append({
                    'city': CITY_NAMES.get(city, city), 'city_code': city,
                    'clinic_1': c1, 'clinic_2': c2, 'distance_km': dist_km,
                    'shared_pincodes': len(overlap), 'total_pincodes': len(union),
                    'overlap_pct': overlap_pct,
                    'overlap_revenue': overlap_rev_c1 + overlap_rev_c2,
                    'vol_overlap_a': vol_overlap_a, 'vol_overlap_b': vol_overlap_b,
                    'avg_vol_overlap': avg_vol_overlap,
                    'core_shared': core_count,
                    'core_pins': ', '.join(str(int(p)) for p in shared_core) if shared_core else '',
                    'risk_level': risk,
                })
    return pd.DataFrame(results)


_same_cached, _new_cached = build_city_scores(_ver=st.session_state.get('_data_ver', 0))
same_city_scores = _same_cached.copy()
new_city_scores = _new_cached.copy()
cannibal_matrix = build_cannibalization_matrix(_ver=st.session_state.get('_data_ver', 0))


@st.cache_data(ttl=300, show_spinner=False)
def build_whitespace_dual_signal(dist_threshold_km=20, _ver=0):
    if len(pin_geo) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    geo_lookup = dict(zip(pin_geo['pincode'].astype(int), zip(pin_geo['lat'], pin_geo['lon'])))
    clinic_list = list(CLINIC_COORDS.items())

    # Vectorized nearest-clinic computation (~100x faster)
    clinic_names = [c[0] for c in clinic_list]
    clinic_lats = np.array([c[1][0] for c in clinic_list])
    clinic_lons = np.array([c[1][1] for c in clinic_list])

    pin_keys = list(geo_lookup.keys())
    pin_lats = np.array([geo_lookup[p][0] for p in pin_keys])
    pin_lons = np.array([geo_lookup[p][1] for p in pin_keys])

    pin_dist = {}
    pin_nearest = {}
    for i, pin in enumerate(pin_keys):
        dists = _haversine_vec(pin_lats[i], pin_lons[i], clinic_lats, clinic_lons)
        idx = np.argmin(dists)
        pin_dist[pin] = round(float(dists[idx]), 1)
        pin_nearest[pin] = clinic_names[idx]

    far_pins = {p for p, d in pin_dist.items() if d > dist_threshold_km}
    def _clean_pin(p):
        try:
            v = int(float(p))
            return v if 100000 <= v <= 999999 else None
        except Exception:
            return None
    pd_copy = pin_demand.copy()
    pd_copy['pin_int'] = pd_copy['Zip'].apply(_clean_pin)
    ntb_far = pd_copy[pd_copy['pin_int'].isin(far_pins)]
    _has_subcity = 'SubCity' in ntb_far.columns and ntb_far['SubCity'].notna().any()
    _micro_map = {}
    if _has_subcity:
        _subcity_vol = ntb_far.groupby(['City', 'SubCity'])['qty'].sum().reset_index()
        _subcity_vol = _subcity_vol[_subcity_vol['SubCity'].notna() & (_subcity_vol['SubCity'] != '-') & (_subcity_vol['SubCity'] != '')]
        for _city_name, _grp in _subcity_vol.groupby('City'):
            _top3 = _grp.nlargest(3, 'qty')
            _micro_map[_city_name] = ', '.join(f"{r['SubCity']} ({int(r['qty'])})" for _, r in _top3.iterrows())
    ntb_agg = ntb_far.groupby('pin_int').agg(
        ntb_qty=('qty', 'sum'), ntb_rev=('revenue', 'sum'),
        clinics_visited=('Clinic Loc', 'nunique'),
        primary_clinic=('Clinic Loc', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '?'),
        city=('City', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '?'),
        state=('State', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '?'),
    ).reset_index()
    wp = data.get('web_pin', pd.DataFrame())
    if len(wp) > 0 and 'Zip' in wp.columns:
        wp['pin_int'] = wp['Zip'].apply(_clean_pin)
        web_far = wp[wp['pin_int'].isin(far_pins)]
        _web_agg_dict = {'web_orders': ('orders', 'sum')}
        if 'revenue' in web_far.columns:
            _web_agg_dict['web_rev'] = ('revenue', 'sum')
        else:
            _web_agg_dict['web_rev'] = ('orders', 'sum')
        web_agg = web_far.groupby('pin_int').agg(**_web_agg_dict).reset_index()
    else:
        web_agg = pd.DataFrame(columns=['pin_int', 'web_orders', 'web_rev'])
    combined = ntb_agg.merge(web_agg, on='pin_int', how='outer', indicator=True)
    dual = combined[combined['_merge'] == 'both'].copy()
    # Merge unique 1Cx web customer counts per pincode
    _u1cx = data.get('web_unique_1cx', pd.DataFrame())
    if len(_u1cx) > 0 and 'pin_int' in _u1cx.columns:
        dual = dual.merge(_u1cx[['pin_int', 'unique_1cx']], on='pin_int', how='left')
        dual['unique_1cx'] = dual['unique_1cx'].fillna(0).astype(int)
    else:
        dual['unique_1cx'] = 0
    # Merge unique clinic patient counts per pincode
    _cup = data.get('clinic_unique_patients', pd.DataFrame())
    if len(_cup) > 0 and 'pin_int' in _cup.columns:
        dual = dual.merge(_cup[['pin_int', 'unique_clinic_patients']], on='pin_int', how='left')
        dual['unique_clinic_patients'] = dual['unique_clinic_patients'].fillna(0).astype(int)
    else:
        dual['unique_clinic_patients'] = 0
    dual['dist_km'] = dual['pin_int'].map(pin_dist)
    dual['nearest_clinic'] = dual['pin_int'].map(pin_nearest)
    dual['combined_score'] = dual['ntb_qty'].fillna(0) * 0.5 + dual['web_orders'].fillna(0) * 0.5
    dual['_weight'] = dual['ntb_qty'].fillna(0) + dual['web_orders'].fillna(0)
    dual['_wd'] = dual['dist_km'].fillna(0) * dual['_weight']
    city_agg = dual.groupby(['city', 'state']).agg(
        pincodes=('pin_int', 'nunique'), total_ntb=('ntb_qty', 'sum'),
        total_web=('web_orders', 'sum'), unique_1cx=('unique_1cx', 'sum'),
        unique_clinic_patients=('unique_clinic_patients', 'sum'),
        ntb_rev=('ntb_rev', 'sum'),
        web_rev=('web_rev', 'sum'), score=('combined_score', 'sum'),
        _wd_sum=('_wd', 'sum'), _w_sum=('_weight', 'sum'),
    ).reset_index()
    city_agg['avg_dist'] = (city_agg['_wd_sum'] / city_agg['_w_sum'].replace(0, 1)).round(1)
    city_agg.drop(columns=['_wd_sum', '_w_sum'], inplace=True)
    _clinic_weight = dual.groupby(['city', 'state', 'nearest_clinic'])['_weight'].sum().reset_index()
    _clinic_weight = _clinic_weight.sort_values('_weight', ascending=False).drop_duplicates(subset=['city', 'state'], keep='first')
    _clinic_weight = _clinic_weight.rename(columns={'nearest_clinic': 'source_clinic'})[['city', 'state', 'source_clinic']]
    city_agg = city_agg.merge(_clinic_weight, on=['city', 'state'], how='left')
    city_agg['top_micro_markets'] = city_agg['city'].map(_micro_map).fillna('')
    city_agg = city_agg.sort_values('score', ascending=False)
    existing_city_codes = set(master['city'].tolist())
    city_names_reverse = {name: code for code, name in CITY_NAMES.items()}
    def _has_clinic(city_name):
        if city_name in city_names_reverse:
            return city_names_reverse[city_name] in existing_city_codes
        for code, aliases in SERVED_CITY_ALIASES.items():
            if any(a.lower() == city_name.lower() for a in aliases):
                if code in existing_city_codes:
                    return True
        return False
    city_agg['has_clinic'] = city_agg['city'].apply(_has_clinic)
    new_cities = city_agg[~city_agg['has_clinic'] & (city_agg['city'] != '-')].copy()
    existing_underserved = city_agg[city_agg['has_clinic']].copy()
    return dual, new_cities, existing_underserved


# ── Sidebar: Defaults + Advanced toggle ──────────────────────────────────
# Sensible defaults — most users never need to change these
_DEF_CAPEX = 28.0; _DEF_OPEX = 3.0; _DEF_BILL_VALUE = 27.0; _DEF_1CX_CONV = 100
_DEF_METRO_R = 5.0; _DEF_T2_R = 8.0; _DEF_WS_DIST = 20.0
# D-score weights (Same-City CEI) — 6 dimensions matching Excel model
_DEF_W_CX1 = 26; _DEF_W_REV_CLINIC = 21; _DEF_W_COMB_DEMAND = 15; _DEF_W_CATCHMENT_BREADTH = 14; _DEF_W_SHOW_RATE = 12; _DEF_W_PCOS = 12
# E-score weights (New-City CEI) — 5 dimensions, each default 20%
_DEF_W_SPILLOVER = 20; _DEF_W_NC_DEMAND = 20; _DEF_W_NC_PCOS = 20; _DEF_W_COMP_WS = 20; _DEF_W_NC_CATCHMENT = 20
_INDIAN_STATES = {
    'andhra pradesh','arunachal pradesh','assam','bihar','chhattisgarh',
    'goa','gujarat','haryana','himachal pradesh','jharkhand','karnataka',
    'kerala','madhya pradesh','maharashtra','manipur','meghalaya','mizoram',
    'nagaland','odisha','punjab','rajasthan','sikkim','tamil nadu',
    'telangana','tripura','uttar pradesh','uttarakhand','west bengal',
    'delhi','chandigarh','puducherry','jammu & kashmir','jammu and kashmir',
    'ladakh','andaman and nicobar islands','lakshadweep',
    'dadra and nagar haveli and daman and diu',
    'the government of nct of delhi','nct of delhi',
}

with st.sidebar:
    st.caption(f"{active_months[0]} → {active_months[-1]}  ·  {len(master)} clinics  ·  CEI v2")

# Read D-score weights (Same-City) from session_state — 6 dimensions
w_cx1 = st.session_state.get('w_cx1', _DEF_W_CX1)
w_rev_clinic = st.session_state.get('w_rev_clinic', _DEF_W_REV_CLINIC)
w_comb_demand = st.session_state.get('w_comb_demand', _DEF_W_COMB_DEMAND)
w_catchment_breadth = st.session_state.get('w_catchment_breadth', _DEF_W_CATCHMENT_BREADTH)
w_show_rate = st.session_state.get('w_show_rate', _DEF_W_SHOW_RATE)
w_pcos = st.session_state.get('w_pcos', _DEF_W_PCOS)
metro_radius = st.session_state.get('sg_metro', _DEF_METRO_R)
tier2_radius = st.session_state.get('sg_t2', _DEF_T2_R)
whitespace_dist_km = st.session_state.get('sg_ws', _DEF_WS_DIST)
# Read E-score weights (New-City) from session_state
w_spillover = st.session_state.get('w_spillover', _DEF_W_SPILLOVER)
w_nc_demand = st.session_state.get('w_nc_demand', _DEF_W_NC_DEMAND)
w_nc_pcos = st.session_state.get('w_nc_pcos', _DEF_W_NC_PCOS)
w_comp_ws = st.session_state.get('w_comp_ws', _DEF_W_COMP_WS)
w_nc_catchment = st.session_state.get('w_nc_catchment', _DEF_W_NC_CATCHMENT)

# Normalize D-score weights (Same-City) — 6 dimensions
_wd_total = w_cx1 + w_rev_clinic + w_comb_demand + w_catchment_breadth + w_show_rate + w_pcos
if _wd_total > 0:
    wd_cx1_n = w_cx1 / _wd_total
    wd_rev_n = w_rev_clinic / _wd_total
    wd_demand_n = w_comb_demand / _wd_total
    wd_catch_b_n = w_catchment_breadth / _wd_total
    wd_show_n = w_show_rate / _wd_total
    wd_pcos_n = w_pcos / _wd_total
else:
    wd_cx1_n = 0.26; wd_rev_n = 0.21; wd_demand_n = 0.15
    wd_catch_b_n = 0.14; wd_show_n = 0.12; wd_pcos_n = 0.12

# Normalize E-score weights (New-City)
_we_total = w_spillover + w_nc_demand + w_nc_pcos + w_comp_ws + w_nc_catchment
if _we_total > 0:
    we_spill_n = w_spillover / _we_total
    we_demand_n = w_nc_demand / _we_total
    we_pcos_n = w_nc_pcos / _we_total
    we_comp_n = w_comp_ws / _we_total
    we_catch_n = w_nc_catchment / _we_total
else:
    we_spill_n = we_demand_n = we_pcos_n = we_comp_n = we_catch_n = 0.20

# ── Pre-compute whitespace ───────────────────────────────────────────────
ws_dual, ws_new_cities, ws_existing_underserved = build_whitespace_dual_signal(dist_threshold_km=whitespace_dist_km, _ver=st.session_state.get('_data_ver', 0))

# ── Merge E-score dimensions from new_city_scores into ws_new_cities ──
if len(ws_new_cities) > 0 and len(new_city_scores) > 0:
    _escore_cols = ['e_spillover', 'e_demand', 'e_pcos', 'e_comp_ws', 'e_catchment', 'cei_new']
    _available = [c for c in _escore_cols if c in new_city_scores.columns]
    if _available:
        _nc_lookup = new_city_scores.copy()
        _nc_lookup['_join_key'] = _nc_lookup['City'].str.strip().str.lower()
        _nc_lookup = _nc_lookup.drop_duplicates(subset='_join_key', keep='first')
        ws_new_cities['_join_key'] = ws_new_cities['city'].str.strip().str.lower()
        for col in _available:
            _col_map = _nc_lookup.set_index('_join_key')[col].to_dict()
            ws_new_cities[col] = ws_new_cities['_join_key'].map(_col_map).fillna(0)
        ws_new_cities.drop(columns=['_join_key'], inplace=True, errors='ignore')

# ── E-score recompute with session_state weights (post-cache) ──
if len(ws_new_cities) > 0 and all(c in ws_new_cities.columns for c in ['e_spillover', 'e_demand', 'e_pcos', 'e_comp_ws', 'e_catchment']):
    ws_new_cities['cei_new'] = (
        ws_new_cities['e_spillover'] * we_spill_n +
        ws_new_cities['e_demand'] * we_demand_n +
        ws_new_cities['e_pcos'] * we_pcos_n +
        ws_new_cities['e_comp_ws'] * we_comp_n +
        ws_new_cities['e_catchment'] * we_catch_n
    )
    ws_new_cities = ws_new_cities.sort_values('cei_new', ascending=False)

# ── CEI v2 recompute ─────────────────────────────────────────────────────
if len(ws_existing_underserved) > 0:
    _eu = ws_existing_underserved.copy()
    _eu['city_code'] = _eu['city'].apply(_match_city_to_code)
    _eu_valid = _eu[_eu['city_code'].notna()]
    if len(_eu_valid) > 0:
        _eu_agg = _eu_valid.groupby('city_code').agg(
            underserved_ntb=('total_ntb', 'sum'), underserved_web=('total_web', 'sum'),
            underserved_rev=('ntb_rev', 'sum'), underserved_pins=('pincodes', 'sum'),
            underserved_avg_dist=('avg_dist', 'mean'),
        ).reset_index()
        same_city_scores = same_city_scores.merge(_eu_agg, on='city_code', how='left')
    else:
        for c in ['underserved_ntb','underserved_web','underserved_rev','underserved_pins','underserved_avg_dist']:
            same_city_scores[c] = 0
else:
    for c in ['underserved_ntb','underserved_web','underserved_rev','underserved_pins','underserved_avg_dist']:
        same_city_scores[c] = 0

same_city_scores[['underserved_ntb','underserved_web','underserved_rev','underserved_pins']] = \
    same_city_scores[['underserved_ntb','underserved_web','underserved_rev','underserved_pins']].fillna(0)
same_city_scores['underserved_avg_dist'] = same_city_scores['underserved_avg_dist'].fillna(0)

def _norm_v2(s):
    mn, mx = s.min(), s.max()
    return ((s - mn) / (mx - mn) * 100).fillna(0) if mx > mn else pd.Series(50, index=s.index)

# ── 1Cx per clinic per month (from clinic_1cx.csv) ──
_cx1_months = [c for c in cx1.columns if c not in ['area', 'code']]
_cx1_l12m_cols = _cx1_months[-12:] if len(_cx1_months) >= 12 else _cx1_months
_n_cx1_months = max(len(_cx1_l12m_cols), 1)
_cx1_city_rows = []
for _cc in same_city_scores['city_code']:
    _cc_clinics = master[master['city'] == _cc]['code'].tolist()
    _cc_cx1 = cx1[cx1['code'].isin(_cc_clinics)]
    if len(_cc_cx1) > 0 and len(_cx1_l12m_cols) > 0:
        _cc_avg = _cc_cx1[_cx1_l12m_cols].sum(axis=1).mean() / _n_cx1_months
    else:
        _cc_avg = 0
    _cx1_city_rows.append(_cc_avg)
same_city_scores['cx1_per_clinic_month'] = _cx1_city_rows


# ── D-score: 6-dimension Same-City CEI (matches Excel model) ──
# Dim 1 (P1): 1Cx per Clinic — patient load (26%)
same_city_scores['d_cx1'] = _norm_v2(same_city_scores['cx1_per_clinic_month'])
# Dim 2 (P3): Rev/Clinic — revenue per clinic (21%)
same_city_scores['rev_per_clinic'] = (same_city_scores['l3m_rev_cr'] / same_city_scores['clinics'].replace(0, 1))
same_city_scores['d_rev_clinic'] = _norm_v2(same_city_scores['rev_per_clinic'])
# Dim 3 (D1): Combined Demand — clinic+web orders per lakh women, from CEI_D1_Catchment_Density.xlsx (15%)
_d1_path = os.path.join('mis_data', 'CEI_D1_Catchment_Density.xlsx')
if os.path.exists(_d1_path):
    try:
        _d1_raw = pd.read_excel(_d1_path, header=None)
        _d1_hdr = None
        for _di, _dr in _d1_raw.iterrows():
            if 'Rank' in [str(v).strip() for v in _dr.values if pd.notna(v)]:
                _d1_hdr = _di; break
        if _d1_hdr is not None:
            _d1_data = pd.read_excel(_d1_path, header=_d1_hdr)
            _d1_data = _d1_data[_d1_data['City'].notna()].copy()
            _d1_data['_city_code'] = _d1_data['City'].apply(_match_city_to_code)
            _d1_data = _d1_data[_d1_data['_city_code'].notna()]
            _d1_map = _d1_data.set_index('_city_code')['D1 Score'].to_dict()
            same_city_scores['comb_demand_raw'] = same_city_scores['city_code'].map(_d1_map).fillna(50)
            same_city_scores['d_comb_demand'] = _norm_v2(same_city_scores['comb_demand_raw'])
        else:
            same_city_scores['comb_demand_raw'] = 50; same_city_scores['d_comb_demand'] = 50.0
    except Exception:
        same_city_scores['comb_demand_raw'] = 50; same_city_scores['d_comb_demand'] = 50.0
else:
    same_city_scores['comb_demand_raw'] = 50; same_city_scores['d_comb_demand'] = 50.0
# Dim 4 (P2): Catchment Breadth — orders per catchment pincode (14%)
same_city_scores['orders_per_pin'] = (
    same_city_scores['clinic_demand'] / same_city_scores['pincodes_served'].replace(0, 1)
)
same_city_scores['d_catchment_breadth'] = _norm_v2(same_city_scores['orders_per_pin'])
# Dim 5 (P4): Show Rate — appointment show-up percentage (12%)
_show_path = os.path.join('mis_data', 'ntb_show_clinic.csv')
if os.path.exists(_show_path):
    try:
        _show_data = pd.read_csv(_show_path)
        _show_city_avg = _show_data.groupby('city')['show_pct'].mean().to_dict()
        same_city_scores['show_rate'] = same_city_scores['city_code'].map(_show_city_avg).fillna(
            _show_data['show_pct'].mean() if len(_show_data) > 0 else 0.20
        )
    except Exception:
        same_city_scores['show_rate'] = 0.20
else:
    same_city_scores['show_rate'] = 0.20
same_city_scores['d_show_rate'] = _norm_v2(same_city_scores['show_rate'])
# Dim 6 (D2): PCOS Heat Index — addressable PCOS patient pool (12%)
_pcos_path = os.path.join('mis_data', 'CEI_D2_PCOS_Heat_Index.xlsx')
if os.path.exists(_pcos_path):
    try:
        _pcos_raw = pd.read_excel(_pcos_path, header=None)
        _pcos_hdr = None
        for _pi, _pr in _pcos_raw.iterrows():
            if 'Rank' in [str(v).strip() for v in _pr.values if pd.notna(v)]:
                _pcos_hdr = _pi; break
        if _pcos_hdr is not None:
            _pcos_data = pd.read_excel(_pcos_path, header=_pcos_hdr)
            _pcos_data = _pcos_data[_pcos_data['City'].notna()].copy()
            _pcos_data['_city_code'] = _pcos_data['City'].apply(_match_city_to_code)
            _pcos_data = _pcos_data[_pcos_data['_city_code'].notna()]
            _pcos_map = _pcos_data.set_index('_city_code')['D2 Score'].to_dict()
            same_city_scores['pcos_heat_index'] = same_city_scores['city_code'].map(_pcos_map).fillna(50)
            same_city_scores['d_pcos'] = _norm_v2(same_city_scores['pcos_heat_index'])
        else:
            same_city_scores['pcos_heat_index'] = 50; same_city_scores['d_pcos'] = 50.0
    except Exception:
        same_city_scores['pcos_heat_index'] = 50; same_city_scores['d_pcos'] = 50.0
else:
    same_city_scores['pcos_heat_index'] = 50; same_city_scores['d_pcos'] = 50.0

# D-score = weighted sum of 6 normalized dimensions (Excel model)
same_city_scores['cei_same'] = (
    same_city_scores['d_cx1'] * wd_cx1_n +
    same_city_scores['d_rev_clinic'] * wd_rev_n +
    same_city_scores['d_comb_demand'] * wd_demand_n +
    same_city_scores['d_catchment_breadth'] * wd_catch_b_n +
    same_city_scores['d_show_rate'] * wd_show_n +
    same_city_scores['d_pcos'] * wd_pcos_n
)
same_city_scores = same_city_scores.sort_values('cei_same', ascending=False)


st.markdown(
    """<div class="hero-banner">
        <div class="hero-title">Gynoveda Expansion Intelligence</div>
        <div class="hero-sub">Clinic network analytics &amp; new-market opportunity engine</div>
    </div>""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Same-City", "New Cities", "Forecaster"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW — Glanceable in 3 seconds
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    net_df = net.copy()
    net_df['month'] = pd.to_datetime(net_df['month'])
    net_df = net_df.sort_values('month')
    net_df = net_df[net_df['clinics_cr'] > 0]
    latest_net = net_df.iloc[-1] if len(net_df) > 0 else {}
    prev_net = net_df.iloc[-2] if len(net_df) > 1 else {}
    l12m = net_df.tail(12)
    l12m_total_rev = l12m['clinics_cr'].sum()
    # Use clinic_1cx.csv as source of truth (network_monthly has duplicate rows + zero-month gaps)
    _l12m_months = l12m['month'].dt.strftime('%Y-%m').tolist()
    _cx1_cols = [c for c in cx1.columns if c not in ['area', 'code']]
    _cx1_l12m = [c for c in _cx1_cols if c in _l12m_months]
    l12m_total_1cx = cx1[_cx1_l12m].sum().sum() if _cx1_l12m else 0
    active_clinics = (sales[latest_month] > 0).sum() if latest_month in sales.columns else len(master)
    avg_ebitda = data['pl']['fy26_ebitda_pct'].mean() if 'fy26_ebitda_pct' in data['pl'].columns else 0

    # ── Revenue trend (full-width) ──
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=net_df['month'], y=net_df['clinics_cr'],
        marker_color=PALETTE[0], opacity=0.85, name='Clinic',
    ))
    if 'video_cr' in net_df.columns:
        fig.add_trace(go.Bar(
            x=net_df['month'], y=net_df['video_cr'],
            marker_color=PALETTE[1], opacity=0.7, name='Video',
        ))
    _apply_layout(fig, height=280, barmode='stack',
                  title="Monthly Revenue (Cr)",
                  margin=dict(l=40, r=10, t=36, b=30),
                  yaxis=dict(title="", showgrid=True, gridcolor='#f0f0f0', zeroline=False))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)

    # ── KPIs row ──
    _k1, _k2, _k3 = st.columns(3)
    _k1.metric("L12M Revenue", fmt_inr(l12m_total_rev * 1e7),
              help="Total clinic network revenue for the last 12 months.")
    _k2.metric("1Cx", fmt_num(l12m_total_1cx),
              help="Total 1Cx (first-time customer) visits across all clinics in the last 12 months.")
    _k3.metric("Active", f"{int(active_clinics)} clinics",
              help="Number of clinics with non-zero revenue in the latest month.")

    # ── TOP EXPANSION PICKS — the answer in 3 seconds ──
    col_s, col_n = st.columns(2)
    top_same = same_city_scores.head(5)

    with col_s:
        st.markdown("##### 🏥 Add clinics in")
        for _, row in top_same.iterrows():
            cei = row['cei_same']
            _cx1v = row.get('cx1_per_clinic_month', 0)
            st.markdown(
                f"<div style='padding:8px 0;border-bottom:1px solid #f0f0f0'>"
                f"<span style='font-size:1.05rem;font-weight:700;color:#1a1a1a'>{row['city_name']}</span>"
                f"<span style='float:right;font-size:0.82rem;color:#c0392b;font-weight:600'>CEI {cei:.0f}</span><br>"
                f"<span style='font-size:0.78rem;color:#999'>{_cx1v:.0f} 1Cx/clinic/mo · {int(row['clinics'])} clinics</span>"
                f"</div>", unsafe_allow_html=True
            )

    with col_n:
        st.markdown("##### 🌐 Enter new cities")
        # Use ws_new_cities (dual-signal whitespace) — sorted by E-score (CEI)
        if len(ws_new_cities) > 0:
            _ov_new = ws_new_cities.copy()
            _ov_new['city'] = _ov_new['city'].fillna('').astype(str).str.strip()
            _ov_bad = {'', 'nan', 'none', '?', '-', 'null', 'undefined', 'None', 'NaN'}
            _ov_new = _ov_new[~_ov_new['city'].isin(_ov_bad)]
            if 'cei_new' in _ov_new.columns:
                _ov_new = _ov_new.sort_values('cei_new', ascending=False)
            _ov_new = _ov_new.head(5)
            for _, row in _ov_new.iterrows():
                _ov_cei = int(round(row.get('cei_new', 0))) if pd.notna(row.get('cei_new', 0)) else 0
                _ov_demand = int(row.get('total_ntb', 0)) + int(row.get('total_web', 0))
                st.markdown(
                    f"<div style='padding:8px 0;border-bottom:1px solid #f0f0f0'>"
                    f"<span style='font-size:1.05rem;font-weight:700;color:#1a1a1a'>{row['city']}</span>"
                    f"<span style='float:right;font-size:0.82rem;color:#f97316;font-weight:600'>CEI {_ov_cei}</span><br>"
                    f"<span style='font-size:0.78rem;color:#999'>{fmt_num(_ov_demand)} demand (clinic + web)</span>"
                    f"</div>", unsafe_allow_html=True
                )
        else:
            for _, row in new_city_scores.head(5).iterrows():
                st.markdown(
                    f"<div style='padding:8px 0;border-bottom:1px solid #f0f0f0'>"
                    f"<span style='font-size:1.05rem;font-weight:700;color:#1a1a1a'>{row['City']}</span>"
                    f"<span style='float:right;font-size:0.82rem;color:#f97316;font-weight:600'>CEI {row['cei_new']:.0f}</span><br>"
                    f"<span style='font-size:0.78rem;color:#999'>{fmt_num(row['total_orders'])} web orders</span>"
                    f"</div>", unsafe_allow_html=True
                )

    # ── Clinic Leaderboard ──
    _lb = data['clinic_lb']
    if len(_lb) > 0:
        with st.expander("Clinic Leaderboard"):
            _lb_display = _lb.head(15).copy()
            # Compute L12M Avg Sale (Lacs) from sales data
            if 'Code' in _lb_display.columns and len(sales) > 0:
                _lb_l12m_cols = active_months[-12:] if len(active_months) >= 12 else active_months
                _lb_l12m_cols = [c for c in _lb_l12m_cols if c in sales.columns]
                if _lb_l12m_cols:
                    _sales_code = sales.copy()
                    _sales_code['_l12m_avg_cr'] = _sales_code[_lb_l12m_cols].mean(axis=1)
                    _sales_code['L12M Avg Sale (₹L)'] = (_sales_code['_l12m_avg_cr'] * 100).round(1)  # Cr → Lacs
                    _code_avg = _sales_code[['code', 'L12M Avg Sale (₹L)']].copy()
                    _code_avg['code'] = _code_avg['code'].astype(str)
                    _lb_display['Code'] = _lb_display['Code'].astype(str)
                    _lb_display = _lb_display.merge(_code_avg, left_on='Code', right_on='code', how='left').drop(columns=['code'], errors='ignore')
            # Compute Avg Mo 1Cx from Total NTB Visits
            _n_active_months = len(active_months) if len(active_months) > 0 else 12
            if 'Total NTB Visits' in _lb_display.columns:
                _lb_display['Avg Mo 1Cx'] = (_lb_display['Total NTB Visits'] / _n_active_months).apply(
                    lambda x: f"{x:.0f}" if pd.notna(x) else "—")
            _lb_cols = ['Clinic', 'City']
            if 'L12M Avg Sale (₹L)' in _lb_display.columns:
                _lb_cols.append('L12M Avg Sale (₹L)')
            if 'Avg Mo 1Cx' in _lb_display.columns:
                _lb_cols.append('Avg Mo 1Cx')
            st.dataframe(
                _lb_display[[c for c in _lb_cols if c in _lb_display.columns]],
                use_container_width=True, height=350, hide_index=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: SAME-CITY EXPANSION
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    # ── City Rankings bar chart (CEI Score) ──
    st.markdown("##### City Rankings (CEI Score)")
    _sc_bar = same_city_scores[['city_name', 'cei_same']].copy()
    _sc_bar['CEI'] = _sc_bar['cei_same'].round(0).astype(int)
    _sc_bar = _sc_bar.sort_values('CEI', ascending=True)
    fig_sc_bar = go.Figure(go.Bar(
        x=_sc_bar['CEI'], y=_sc_bar['city_name'],
        orientation='h', marker_color=PALETTE[0], opacity=0.85,
        text=_sc_bar['CEI'], textposition='outside',
    ))
    _apply_layout(fig_sc_bar,
        height=max(300, len(_sc_bar) * 28),
        margin=dict(l=120, r=40, t=10, b=20),
        xaxis=dict(title="CEI Score", showgrid=True, gridcolor='#f0f0f0', zeroline=False),
        yaxis=dict(title="", showgrid=False, zeroline=False),
    )
    with st.container(height=250):
        st.plotly_chart(fig_sc_bar, use_container_width=True, config=PLOTLY_CFG)

    # ── Ranked city list (collapsible) ──
    with st.expander("City CEI Rankings", expanded=False):
        _sc_rank = same_city_scores[['city_name', 'clinics', 'cei_same']].copy()
        _sc_rank['CEI'] = _sc_rank['cei_same'].round(0).astype(int)
        _sc_rank = _sc_rank.sort_values('CEI', ascending=False).reset_index(drop=True)
        _sc_rank.insert(0, 'Rank', range(1, len(_sc_rank) + 1))
        _sc_rank = _sc_rank.rename(columns={'city_name': 'City', 'clinics': 'Clinics'})
        st.dataframe(
            _sc_rank[['Rank', 'City', 'Clinics', 'CEI']],
            use_container_width=True, hide_index=True,
        )

    # ── City Deep-Dive ──
    st.markdown("##### City Detail")
    city_options = same_city_scores['city_name'].tolist()
    selected_city = st.selectbox("City", city_options, key='same_city_select', label_visibility='collapsed',
                                  help="Select a city where Gynoveda already operates. Ranked by CEI score (highest expansion potential first).")
    city_data = same_city_scores[same_city_scores['city_name'] == selected_city].iloc[0]
    _cx1_clinic = city_data.get('cx1_per_clinic_month', 0)

    _cd_left, _cd_right = st.columns([1, 1])
    with _cd_left:
        _cd1, _cd2 = st.columns(2)
        _cd1.metric("CEI Score", f"{city_data['cei_same']:.0f}/100",
                  help="D-score (0–100). Weighted composite of 6 dimensions: 1Cx/Clinic, Rev/Clinic, Combined Demand, Catchment Breadth, Show Rate, and PCOS Heat.")
        _cd2.metric("1Cx/Clinic/Mo", f"{_cx1_clinic:.0f}",
                  help="Average first-time customer visits per clinic per month.")
    with _cd_right:
        # Radar chart — 6 D-score dimensions for selected city
        _radar_dims = ['1Cx/Clinic', 'Rev/Clinic', 'Comb Demand', 'Catch Breadth', 'Show Rate', 'PCOS Heat']
        _radar_vals = [
            city_data.get('d_cx1', 50),
            city_data.get('d_rev_clinic', 50),
            city_data.get('d_comb_demand', 50),
            city_data.get('d_catchment_breadth', 50),
            city_data.get('d_show_rate', 50),
            city_data.get('d_pcos', 50),
        ]
        _radar_vals_closed = _radar_vals + [_radar_vals[0]]
        _radar_dims_closed = _radar_dims + [_radar_dims[0]]
        fig_radar = go.Figure(go.Scatterpolar(
            r=_radar_vals_closed, theta=_radar_dims_closed,
            fill='toself', fillcolor='rgba(204,54,0,0.15)',
            line=dict(color='#CC3600', width=2),
            marker=dict(size=5, color='#CC3600'),
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='#e5e7eb'),
                angularaxis=dict(gridcolor='#e5e7eb', linecolor='#e5e7eb'),
                bgcolor='rgba(0,0,0,0)',
            ),
            showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=240,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_CFG)

    # ── Cannibalization ──
    if len(cannibal_matrix) > 0:
        city_code = same_city_scores[same_city_scores['city_name'] == selected_city]['city_code'].values[0]
        city_cannibal = cannibal_matrix[cannibal_matrix['city_code'] == city_code].copy()
        if len(city_cannibal) > 0:
            st.markdown("---")
            st.markdown("##### Cannibalization Risk")

            city_tier = master[master['city'] == city_code]['tier'].values
            is_metro = any(t in ['Metro', 'Tier-1'] for t in city_tier) if len(city_tier) > 0 else False
            radius_threshold = metro_radius if is_metro else tier2_radius

            dist_pairs = city_cannibal[city_cannibal['distance_km'].notna()].copy()
            if len(dist_pairs) > 0:
                def _risk_tier(r):
                    if r in ('Critical', 'High'): return 'High'
                    if r == 'Medium': return 'Medium'
                    return 'Low'
                dist_pairs['tier'] = dist_pairs['risk_level'].apply(_risk_tier)
                dist_pairs = dist_pairs.sort_values('avg_vol_overlap', ascending=False)
                _tier_badge = {'High': '#ef4444', 'Medium': '#f97316', 'Low': '#22c55e'}

                # Clean card layout — one row per clinic pair
                _rows_html = ""
                for _, p in dist_pairs.iterrows():
                    _ov = p['avg_vol_overlap'] * 100
                    _d = p['distance_km']
                    _t = p['tier']
                    _c = _tier_badge[_t]
                    _too_close = _d < radius_threshold
                    _dist_warn = f"<span style='color:#ef4444;font-weight:600'>{_d:.1f} km ⚠</span>" if _too_close else f"{_d:.1f} km"
                    _rows_html += (
                        f"<div style='display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0;gap:12px'>"
                        f"  <span style='background:{_c};color:#fff;font-size:0.65rem;font-weight:600;"
                        f"    padding:3px 10px;border-radius:10px;min-width:52px;text-align:center'>{_t}</span>"
                        f"  <span style='flex:1;font-weight:600;font-size:0.92rem;color:#1a1a1a'>"
                        f"    {p['clinic_1']} <span style='color:#bbb;font-weight:400'>↔</span> {p['clinic_2']}</span>"
                        f"  <span style='font-size:0.82rem;color:#666;min-width:60px;text-align:right'>{_dist_warn}</span>"
                        f"  <span style='font-size:0.82rem;color:#666;min-width:80px;text-align:right'>{_ov:.0f}% overlap</span>"
                        f"  <span style='font-size:0.78rem;color:#999;min-width:70px;text-align:right'>{int(p['shared_pincodes'])} pins shared</span>"
                        f"</div>"
                    )
                st.markdown(
                    f"<div style='background:#fafafa;border-radius:8px;padding:4px 16px;border:1px solid #eee'>"
                    f"{_rows_html}</div>",
                    unsafe_allow_html=True
                )
                # Summary line
                _high_ct = (dist_pairs['tier'] == 'High').sum()
                if _high_ct > 0:
                    st.caption(f"⚠ {_high_ct} high-risk pair{'s' if _high_ct > 1 else ''} — consider territory rebalancing or consolidation")

    # ── Competitor & Rent ──
    _comp = data['competitor_prox']
    _city_name_for_comp = selected_city
    _sel_city_code = str(city_data.get('city_code', '')).upper()
    _city_comp = _comp[_comp['City'].str.upper() == _sel_city_code]
    if len(_city_comp) == 0:
        _city_comp = _comp[_comp['City'].str.lower() == _city_name_for_comp.lower()]
    _ivf = data['ivf_comp']
    _city_ivf = _ivf[_ivf['Centre_City'].str.lower() == _city_name_for_comp.lower()] if len(_ivf) > 0 else pd.DataFrame()
    _has_comp = len(_city_comp) > 0 or len(_city_ivf) > 0
    if _has_comp:
        st.markdown("---")
        st.markdown("##### IVF Competitor Landscape")

        # Classify IVF competitors: Branded (National Chain), Regional (Regional Chain + Hospital Chain), Non-Branded (Local/Regional Specialist)
        _brand_map = {
            'National Chain': 'Branded',
            'Hospital Chain': 'Regional',
            'Regional Chain': 'Regional',
            'Local Specialist': 'Non-Branded',
            'Regional Specialist': 'Non-Branded',
        }
        # Get threat info from competitor proximity data
        _threat = str(_city_comp.iloc[0].get('Threat Level', 'N/A')).upper() if len(_city_comp) > 0 else 'N/A'
        _threat_color = {'HIGH': '#ef4444', 'MEDIUM': '#f97316', 'LOW': '#22c55e'}.get(_threat, '#888')

        if len(_city_ivf) > 0 and 'Brand_Type' in _city_ivf.columns:
            _city_ivf_c = _city_ivf.copy()
            _city_ivf_c['Category'] = _city_ivf_c['Brand_Type'].map(_brand_map).fillna('Non-Branded')
            _branded = _city_ivf_c[_city_ivf_c['Category'] == 'Branded']
            _regional = _city_ivf_c[_city_ivf_c['Category'] == 'Regional']
            _nonbranded = _city_ivf_c[_city_ivf_c['Category'] == 'Non-Branded']

            # Summary metrics — 3 columns
            _mi1, _mi2, _mi3 = st.columns(3)
            with _mi1:
                st.metric("Branded (National)", len(_branded),
                          help="National IVF chains (e.g. Indira IVF, Nova). High brand awareness — directly compete for patients. More branded competitors = tougher market to enter.")
                if len(_branded) > 0:
                    _top_branded = _branded['Chain_Name'].value_counts().head(3)
                    st.caption(' · '.join(f"{n} ({c})" for n, c in _top_branded.items()))
            with _mi2:
                st.metric("Regional / Hospital", len(_regional),
                          help="Hospital-attached and regional IVF chain centres. Less brand power than national chains but often have established patient trust through the parent hospital.")
                if len(_regional) > 0:
                    _top_regional = _regional['Chain_Name'].value_counts().head(3)
                    st.caption(' · '.join(f"{n} ({c})" for n, c in _top_regional.items()))
            with _mi3:
                st.metric("Non-Branded (Local)", len(_nonbranded),
                          help="Local specialist clinics and small independent IVF providers. Lower brand recognition — Gynoveda's Ayurvedic differentiation is strongest against these.")
                if len(_nonbranded) > 0:
                    _top_local = _nonbranded['Chain_Name'].value_counts().head(3)
                    st.caption(' · '.join(f"{n} ({c})" for n, c in _top_local.items()))

            # Threat badge
            st.markdown(
                f"<div style='margin:10px 0 6px'>"
                f"<span style='background:{_threat_color};color:#fff;font-size:0.7rem;font-weight:600;"
                f"padding:2px 10px;border-radius:10px'>{_threat} competition</span>"
                f"<span style='margin-left:10px;font-size:0.8rem;color:#888'>"
                f"{len(_city_ivf_c)} centres · {_city_ivf_c['Chain_Name'].nunique()} chains</span></div>",
                unsafe_allow_html=True
            )

            # Detail table
            with st.expander(f"All IVF centres in {selected_city} ({len(_city_ivf_c)})"):
                _ivf_display = _city_ivf_c.copy()
                if 'Proximity_to_Gynoveda_Clinic' in _ivf_display.columns:
                    _ivf_display['Distance'] = _ivf_display['Proximity_to_Gynoveda_Clinic'].fillna('—')
                _show_cols = ['Chain_Name', 'Category', 'Centre_Location', 'Distance']
                _show_cols = [c for c in _show_cols if c in _ivf_display.columns]
                st.dataframe(
                    _ivf_display[_show_cols].rename(columns={
                        'Chain_Name': 'Chain', 'Centre_Location': 'Location'
                    }).sort_values('Category'),
                    use_container_width=True, hide_index=True,
                )
        else:
            # No IVF detail data — show summary from competitor proximity
            _ivf_count = int(_city_comp.iloc[0].get('IVF Centres in City', 0)) if len(_city_comp) > 0 else 0
            _chains = int(_city_comp.iloc[0].get('Chains Present', 0)) if len(_city_comp) > 0 else 0
            if _ivf_count > 0:
                st.metric("IVF Centres in City", _ivf_count,
                          help="Total number of IVF centres operating in this city from the competitor proximity dataset. Higher count = more saturated market for fertility services.")
                st.markdown(
                    f"<span style='background:{_threat_color};color:#fff;font-size:0.7rem;font-weight:600;"
                    f"padding:2px 10px;border-radius:10px'>{_threat} competition</span>"
                    f"<span style='margin-left:10px;font-size:0.8rem;color:#888'>{_chains} chains</span>",
                    unsafe_allow_html=True
                )
            else:
                st.caption("No IVF competitor data available for this city")

    # ── CEI Weights & Safeguards ──
    with st.expander("⚙ CEI Weights & Safeguards", expanded=False):
        st.caption("CEI dimensions (Same-City)")
        _wc1, _wc2, _wc3, _wc4, _wc5, _wc6 = st.columns(6)
        _wc1.number_input("1Cx/Clinic", value=_DEF_W_CX1, step=1, min_value=0, max_value=100, key='w_cx1',
                           help="Weight (%) — Patient load: are clinics overloaded?")
        _wc2.number_input("Rev/Clinic", value=_DEF_W_REV_CLINIC, step=1, min_value=0, max_value=100, key='w_rev_clinic',
                           help="Weight (%) — Is this city commercially proven?")
        _wc3.number_input("Comb Demand", value=_DEF_W_COMB_DEMAND, step=1, min_value=0, max_value=100, key='w_comb_demand',
                           help="Weight (%) — Total Gynoveda demand (clinic + web per lakh women).")
        _wc4.number_input("Catch Breadth", value=_DEF_W_CATCHMENT_BREADTH, step=1, min_value=0, max_value=100, key='w_catchment_breadth',
                           help="Weight (%) — How many pincodes are patients coming from?")
        _wc5.number_input("Show Rate", value=_DEF_W_SHOW_RATE, step=1, min_value=0, max_value=100, key='w_show_rate',
                           help="Weight (%) — Are patients showing up for appointments?")
        _wc6.number_input("PCOS Heat", value=_DEF_W_PCOS, step=1, min_value=0, max_value=100, key='w_pcos',
                           help="Weight (%) — Size of the addressable PCOS patient pool.")
        st.caption("Safeguards")
        _sg1, _sg2, _sg3 = st.columns(3)
        _sg1.number_input("Metro (km)", value=_DEF_METRO_R, step=1.0, format="%.0f", key='sg_metro',
                           help="Distance threshold for metro cities.")
        _sg2.number_input("Tier-2 (km)", value=_DEF_T2_R, step=1.0, format="%.0f", key='sg_t2',
                           help="Distance threshold for Tier-2 cities.")
        _sg3.number_input("Whitespace", value=_DEF_WS_DIST, step=5.0, format="%.0f", key='sg_ws',
                           help="Distance threshold for new-city whitespace detection.")

    # ── Recommended Micro-Markets (Same-City) — from CEI Excel ──
    st.markdown("---")
    with st.expander("Prospect Micro-Markets (Same-City)", expanded=False):
        st.caption("Micro-market expansion opportunities in served cities, ranked by Tier then D-Score. Source: CEI v3.1 model.")
        _mm_xlsx = os.path.join('mis_data', 'Gynoveda_CEI_v31_MicroMarkets.xlsx')
        if os.path.exists(_mm_xlsx):
            try:
                _mm_raw = pd.read_excel(_mm_xlsx, sheet_name='Micro-Market Revenue', header=4)
                _mm_raw = _mm_raw[_mm_raw['#'].notna()].copy()
                # Filter out micro-markets where Gynoveda already has a clinic
                _existing_areas = set(master['area'].str.strip().str.lower())
                if 'Micro-Market Name' in _mm_raw.columns:
                    _mm_raw = _mm_raw[~_mm_raw['Micro-Market Name'].str.strip().str.lower().isin(_existing_areas)]
                _mm_display_cols = []
                if '#' in _mm_raw.columns:
                    _mm_raw = _mm_raw.rename(columns={'#': 'Rank'})
                    _mm_raw['Rank'] = _mm_raw['Rank'].astype(int)
                    _mm_display_cols.append('Rank')
                if 'Tier' in _mm_raw.columns:
                    _mm_display_cols.append('Tier')
                if 'City' in _mm_raw.columns:
                    _mm_display_cols.append('City')
                if 'Micro-Market Name' in _mm_raw.columns:
                    _mm_display_cols.append('Micro-Market Name')
                if 'Zone' in _mm_raw.columns:
                    _mm_display_cols.append('Zone')
                if 'D-Score' in _mm_raw.columns:
                    _ds_max = _mm_raw['D-Score'].max()
                    _mm_raw['CEI Score'] = ((_mm_raw['D-Score'] * 100 / _ds_max) if _ds_max > 0 else 0).round(0).astype(int)
                    _mm_display_cols.append('CEI Score')
                if _mm_display_cols:
                    st.dataframe(
                        _mm_raw[_mm_display_cols],
                        use_container_width=True, hide_index=True,
                        height=min(700, 35 + len(_mm_raw) * 35),
                    )
                else:
                    st.caption("Micro-market data format not recognized.")
            except Exception as _mm_err:
                st.caption(f"Could not load micro-market data: {_mm_err}")
        else:
            st.caption("Place `Gynoveda_CEI_v31_MicroMarkets.xlsx` in `mis_data/` to see micro-market prospects.")



# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: NEW CITIES
# ═══════════════════════════════════════════════════════════════════════════
with tab3:

    if len(ws_dual) > 0:
        # ── Prepare clean data (used across all sections) ──
        _ws_dual_cities = ws_new_cities[(ws_new_cities['total_ntb'] > 0) & (ws_new_cities['total_web'] > 0)].copy()
        _ws_dual_cities = _ws_dual_cities[
            _ws_dual_cities['state'].str.strip().str.lower().isin(_INDIAN_STATES)
        ]
        if 'avg_dist' in _ws_dual_cities.columns:
            _ws_dual_cities = _ws_dual_cities[_ws_dual_cities['avg_dist'] >= 10]
        _ws_top100 = _ws_dual_cities.head(100)
        _ws_cities = len(_ws_top100)

        _ws_clean = _ws_top100.copy()
        _ws_clean['city'] = _ws_clean['city'].fillna('').astype(str).str.strip()
        _bad = {'', 'nan', 'none', '?', '-', 'null', 'undefined', 'None', 'NaN'}
        _ws_clean = _ws_clean[~_ws_clean['city'].isin(_bad)]
        _ws_clean['total_ntb'] = pd.to_numeric(_ws_clean['total_ntb'], errors='coerce').fillna(0).astype(int)
        _ws_clean['total_web'] = pd.to_numeric(_ws_clean['total_web'], errors='coerce').fillna(0).astype(int)
        _has_uniq = 'unique_clinic_patients' in _ws_clean.columns and 'unique_1cx' in _ws_clean.columns and _ws_clean['unique_clinic_patients'].sum() > 0
        if _has_uniq:
            _ws_clean['_bar_clinic'] = pd.to_numeric(_ws_clean['unique_clinic_patients'], errors='coerce').fillna(0).astype(int)
            _ws_clean['_bar_web'] = pd.to_numeric(_ws_clean['unique_1cx'], errors='coerce').fillna(0).astype(int)
        else:
            _ws_clean['_bar_clinic'] = _ws_clean['total_ntb']
            _ws_clean['_bar_web'] = _ws_clean['total_web']
        _ws_clean['combined'] = _ws_clean['_bar_clinic'] + _ws_clean['_bar_web']
        if 'cei_new' in _ws_clean.columns:
            _ws_clean = _ws_clean.sort_values('cei_new', ascending=False)
        else:
            _ws_clean = _ws_clean.sort_values('combined', ascending=False)
        _ws_clean['CEI'] = _ws_clean['cei_new'].fillna(0).round(0).astype(int) if 'cei_new' in _ws_clean.columns else 0

        if len(_ws_clean) > 0:
            # ── City Rankings bar chart (CEI Score) ──
            st.markdown("##### City Rankings (CEI Score)")
            _nc_bar = _ws_clean[['city', 'CEI']].drop_duplicates(subset='city', keep='first').copy()
            _nc_bar = _nc_bar.sort_values('CEI', ascending=False).head(25)
            _nc_bar = _nc_bar.sort_values('CEI', ascending=True)
            fig_nc_bar = go.Figure(go.Bar(
                x=_nc_bar['CEI'], y=_nc_bar['city'],
                orientation='h', marker_color=PALETTE[1], opacity=0.85,
                text=_nc_bar['CEI'], textposition='outside',
            ))
            _apply_layout(fig_nc_bar,
                height=max(300, len(_nc_bar) * 28),
                margin=dict(l=140, r=40, t=10, b=20),
                xaxis=dict(title="CEI Score", showgrid=True, gridcolor='#f0f0f0', zeroline=False),
                yaxis=dict(title="", showgrid=False, zeroline=False),
            )
            with st.container(height=250):
                st.plotly_chart(fig_nc_bar, use_container_width=True, config=PLOTLY_CFG)

            # ── Ranked city list (collapsible) ──
            with st.expander("City CEI Rankings", expanded=False):
                _rank_df = _ws_clean[['city', 'CEI']].drop_duplicates(subset='city', keep='first').copy()
                if 'state' in _ws_clean.columns:
                    _rank_df.insert(1, 'State', _ws_clean.drop_duplicates(subset='city', keep='first')['state'].values)
                if 'pincodes' in _ws_clean.columns:
                    _rank_df['Pincodes'] = _ws_clean.drop_duplicates(subset='city', keep='first')['pincodes'].astype(int).values
                _rank_df = _rank_df.sort_values('CEI', ascending=False).reset_index(drop=True)
                _rank_df.insert(0, 'Rank', range(1, len(_rank_df) + 1))
                _rank_df = _rank_df.rename(columns={'city': 'City'})
                st.dataframe(
                    _rank_df, use_container_width=True, hide_index=True,
                )

            # ── 5. City Detail — selectbox + placard + radar ──
            st.markdown("##### City Detail")
            _nc_city_options = _ws_clean['city'].tolist()
            _nc_selected = st.selectbox("City", _nc_city_options, key='new_city_select', label_visibility='collapsed',
                                         help="Select a new-city candidate. Ranked by E-score (highest expansion potential first).")
            _nc_sel_data = _ws_clean[_ws_clean['city'] == _nc_selected].iloc[0] if _nc_selected in _ws_clean['city'].values else _ws_clean.iloc[0]

            _nc_left, _nc_right = st.columns([1, 1])
            with _nc_left:
                _nc_d1, _nc_d2 = st.columns(2)
                _nc_d1.metric("E-score", f"{int(_nc_sel_data.get('CEI', 0))}/100",
                              help="E-score (0–100). Weighted composite of Spillover, Combined Demand, PCOS Heat Index, Competitive Whitespace, and Catchment Density.")
                _nc_demand_total = int(_nc_sel_data.get('combined', 0))
                _nc_d2.metric("Total Demand", fmt_num(_nc_demand_total),
                              help="Combined clinic patients (20+ km) and web 1Cx orders from this city.")
                _nc_d3, _nc_d4 = st.columns(2)
                _nc_rev = _nc_sel_data.get('ntb_rev', 0) + _nc_sel_data.get('web_rev', 0)
                _nc_d3.metric("Revenue Signal", fmt_inr(_nc_rev),
                              help="Total revenue from clinic patients traveling 20+ km + web orders.")
                _nc_pins = int(_nc_sel_data.get('pincodes', 0))
                _nc_d4.metric("Pincodes", fmt_num(_nc_pins),
                              help="Number of unique pincodes with demand signal in this city.")

            with _nc_right:
                # Radar chart — E-score dimensions for selected city
                _nc_radar_dims = ['Spillover', 'Comb Demand', 'PCOS Heat', 'Comp WS', 'Catchment']
                _nc_radar_vals = [
                    _nc_sel_data.get('e_spillover', 50),
                    _nc_sel_data.get('e_demand', 50),
                    _nc_sel_data.get('e_pcos', 50),
                    _nc_sel_data.get('e_comp_ws', 50),
                    _nc_sel_data.get('e_catchment', 50),
                ]
                _nc_radar_vals_closed = _nc_radar_vals + [_nc_radar_vals[0]]
                _nc_radar_dims_closed = _nc_radar_dims + [_nc_radar_dims[0]]
                fig_nc_radar = go.Figure(go.Scatterpolar(
                    r=_nc_radar_vals_closed, theta=_nc_radar_dims_closed,
                    fill='toself', fillcolor='rgba(249,115,22,0.15)',
                    line=dict(color='#f97316', width=2),
                    marker=dict(size=5, color='#f97316'),
                ))
                fig_nc_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor='#e5e7eb'),
                        angularaxis=dict(gridcolor='#e5e7eb', linecolor='#e5e7eb'),
                        bgcolor='rgba(0,0,0,0)',
                    ),
                    showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=240,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_nc_radar, use_container_width=True, config=PLOTLY_CFG)

            # ── CEI Weights & Safeguards (collapsed expander) ──
            with st.expander("⚙ CEI Weights & Safeguards", expanded=False):
                st.caption("CEI dimensions (New-City)")
                _ec1, _ec2, _ec3, _ec4, _ec5 = st.columns(5)
                _ec1.number_input("Spillover", value=_DEF_W_SPILLOVER, step=5, min_value=0, max_value=100, key='w_spillover',
                                   help="Weight (%) for spillover demand — patients traveling to other cities for care.")
                _ec2.number_input("Combined Demand", value=_DEF_W_NC_DEMAND, step=5, min_value=0, max_value=100, key='w_nc_demand',
                                   help="Weight (%) for combined web + clinic demand signal.")
                _ec3.number_input("PCOS Heat", value=_DEF_W_NC_PCOS, step=5, min_value=0, max_value=100, key='w_nc_pcos',
                                   help="Weight (%) for PCOS Heat Index — addressable patient pool size.")
                _ec4.number_input("Comp Whitespace", value=_DEF_W_COMP_WS, step=5, min_value=0, max_value=100, key='w_comp_ws',
                                   help="Weight (%) for competitive whitespace — fewer IVF clinics = easier entry.")
                _ec5.number_input("Catchment", value=_DEF_W_NC_CATCHMENT, step=5, min_value=0, max_value=100, key='w_nc_catchment',
                                   help="Weight (%) for catchment density — existing Gynoveda demand per lakh women.")

            # ── 7. 50 Prospect Locations (New Cities) ──
            if 'top_micro_markets' in _ws_clean.columns:
                st.markdown("---")
                with st.expander("50 Prospect Locations (New Cities)", expanded=False):
                    st.caption("Top 50 expansion-ready cities with key localities, ranked by CEI Score.")
                    import re as _re
                    _nc_micro_rows = []
                    for _, _nc_row in _ws_clean.iterrows():
                        _nc_city = str(_nc_row.get('city', ''))
                        _nc_state = str(_nc_row.get('state', ''))
                        _nc_cei = round(_nc_row.get('cei_new', 0)) if pd.notna(_nc_row.get('cei_new', 0)) else 0
                        _nc_areas = str(_nc_row.get('top_micro_markets', ''))
                        if _nc_areas and _nc_areas not in ('', 'nan'):
                            for _area_part in _nc_areas.split(','):
                                _area_part = _area_part.strip()
                                if _area_part:
                                    _m = _re.match(r'^(.+?)\s*\((\d+)\)$', _area_part)
                                    _locality = _m.group(1).strip() if _m else _area_part
                                    _nc_micro_rows.append({
                                        'City': _nc_city, 'State': _nc_state, 'CEI': int(_nc_cei),
                                        'Locality': _locality,
                                    })
                    if _nc_micro_rows:
                        _nc_micro_df = pd.DataFrame(_nc_micro_rows)
                        # Group localities by city — deduplicate
                        _nc_grouped = _nc_micro_df.groupby(['City', 'State', 'CEI']).agg(
                            Localities=('Locality', lambda x: ', '.join(dict.fromkeys(x)))
                        ).reset_index()
                        _nc_grouped = _nc_grouped.sort_values('CEI', ascending=False).head(50)
                        _nc_grouped.insert(0, 'Rank', range(1, len(_nc_grouped) + 1))
                        st.dataframe(
                            _nc_grouped[['Rank', 'City', 'State', 'CEI', 'Localities']],
                            use_container_width=True, hide_index=True, height=min(700, 35 + len(_nc_grouped) * 35),
                        )

    elif len(pin_geo) == 0:
        st.info("Upload `pin_geocode.csv` to `mis_data/` to enable new-city analysis.")
    else:
        st.info("No new-city whitespace detected at current distance threshold.")



# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: REVENUE FORECASTER
# ═══════════════════════════════════════════════════════════════════════════
with tab4:

    # No @st.fragment — widget changes must trigger full page rerun
    # so that North Star banner + New Cities card update in sync
    def _forecaster():
        st.markdown("##### Revenue Forecaster")
        st.caption("Model the 12-month financial impact of clinic expansion. "
                   f"Assumptions: Capex ₹{_DEF_CAPEX:.0f}L · OpEx ₹{_DEF_OPEX:.0f}L/mo (rent + staff + electricity + misc) · "
                   f"Mature rev ₹40L/mo (same-city) · ₹30L/mo (new-city).")

        # ── Fixed assumptions (not user-configurable) ──
        bill_value_k = _DEF_BILL_VALUE
        cx1_conv_pct = _DEF_1CX_CONV
        capex_same = capex_new = _DEF_CAPEX
        same_opex = new_opex = _DEF_OPEX

        # ── Scenario Toggle ──
        _scenario_options = {"Conservative (0.8×)": 0.8, "Base (1.0×)": 1.0, "Aggressive (1.2×)": 1.2}
        _scenario_choice = st.radio("Scenario", list(_scenario_options.keys()), index=1,
                                     horizontal=True, key='scenario_toggle',
                                     help="Conservative: 20% revenue haircut. Base: as-is. Aggressive: 20% revenue uplift.")
        scenario_mult_same = scenario_mult_new = _scenario_options[_scenario_choice]

        # ── Compute ramp shape (0→1 normalized) from historical data ──
        _ramp_raw = ramp_s[ramp_s['month_num'] <= 11].copy() if len(ramp_s) > 0 else pd.DataFrame()
        _ramp_peak = _ramp_raw['avg_sales_l'].max() if len(_ramp_raw) > 0 else 1.0
        _ramp_shape = (_ramp_raw['avg_sales_l'] / _ramp_peak).tolist() if len(_ramp_raw) > 0 else []

        same_steady = 40.0   # Mature same-city clinic rev (₹L/mo)
        new_steady = 30.0   # Mature new-city clinic rev (₹L/mo)

        # Read input widgets from session_state (widgets rendered below chart)
        n_same = st.session_state.get('n_same', 0)
        same_per_mo = st.session_state.get('same_pm', 1)
        n_new = st.session_state.get('n_new', 30)
        new_per_mo = st.session_state.get('new_pm', 3)

        # ── Build launch schedules ──
        def _build_schedule(n, per_mo):
            """Generate list of (launch_month, batch_size). Starts at month 1, capped at month 11."""
            sched = []
            rem = n; lm = 1
            while rem > 0 and lm < 12:
                batch = min(per_mo, rem)
                sched.append((lm, batch))
                rem -= batch; lm += 1
            return sched

        sched_same = _build_schedule(n_same, same_per_mo)
        sched_new = _build_schedule(n_new, new_per_mo)

        # New-city ramp penalty: starts at 60%, converges to 100% by month 12
        def _new_ramp_penalty(age):
            return min(0.6 + (age / 12) * 0.4, 1.0)

        # ── Revenue for a single clinic at a given age ──
        def _clinic_rev(age, steady, is_new=False, sc_mult=1.0):
            """Use historical ramp SHAPE scaled to user's steady-rev target.
            Month 0 of a clinic (opening month) capped at 10% — realistic first-month revenue."""
            if age < len(_ramp_shape):
                shape_val = _ramp_shape[age]
                if age == 0:
                    shape_val = min(shape_val, 0.10)
                base = shape_val * steady
            else:
                base = steady
            penalty = _new_ramp_penalty(age) if is_new else 1.0
            return base * penalty * sc_mult

        # ── 12-month projection ──
        proj = []
        cum_rev = cum_opex = cum_ebitda = 0
        for m in range(12):
            s_rev = s_act = 0
            for launch_m, batch in sched_same:
                age = m - launch_m
                if age < 0: continue
                s_act += batch
                s_rev += _clinic_rev(age, same_steady, sc_mult=scenario_mult_same) * batch

            n_rev = n_act = 0
            for launch_m, batch in sched_new:
                age = m - launch_m
                if age < 0: continue
                n_act += batch
                n_rev += _clinic_rev(age, new_steady, is_new=True, sc_mult=scenario_mult_new) * batch

            t_rev = s_rev + n_rev
            t_opex = (same_opex * s_act) + (new_opex * n_act)
            ebitda = t_rev - t_opex
            cum_rev += t_rev; cum_opex += t_opex; cum_ebitda += ebitda

            proj.append({
                'month': m + 1, 'same_rev': round(s_rev, 1), 'new_rev': round(n_rev, 1),
                'total_rev': round(t_rev, 1), 'total_opex': round(t_opex, 1),
                'ebitda': round(ebitda, 1), 'cum_ebitda': round(cum_ebitda, 1),
                'same_active': s_act, 'new_active': n_act,
            })

        df = pd.DataFrame(proj)
        total_n = n_same + n_new
        total_capex = capex_same * n_same + capex_new * n_new

        # ── Key answers ──
        _be_rows = df[df['ebitda'] > 0]
        be_month = int(_be_rows.iloc[0]['month']) if len(_be_rows) > 0 else None
        _payback_rows = df[df['cum_ebitda'] >= total_capex]
        payback_month = int(_payback_rows.iloc[0]['month']) if len(_payback_rows) > 0 else None
        rev_12m = df['total_rev'].sum()
        opex_12m = df['total_opex'].sum()
        ebitda_12m = df['ebitda'].sum()
        same_12m = df['same_rev'].sum()
        new_12m = df['new_rev'].sum()

        # ── 1Cx bridge calculation ──
        _mature_rev_same_rs = same_steady * 1e5
        _1cx_per_patient = bill_value_k * 1000
        _1cx_needed_same = int(_mature_rev_same_rs / _1cx_per_patient) if _1cx_per_patient > 0 else 0
        _mature_rev_new_rs = new_steady * 1e5
        _1cx_needed_new = int(_mature_rev_new_rs / _1cx_per_patient) if _1cx_per_patient > 0 else 0

        # ── Summary strip (TOP — revenue breakdown) ──
        _ebitda_color = '#10b981' if ebitda_12m >= 0 else '#ef4444'
        _same_pct = (same_12m / rev_12m * 100) if rev_12m > 0 else 0
        _new_pct = 100 - _same_pct

        _c1, _c2, _c3, _c4 = st.columns(4)
        _c1.metric("Same-City (12M)", fmt_inr(same_12m * 1e5), f"{_same_pct:.0f}% of total",
                   help="Total revenue from same-city expansion clinics over 12 months. These clinics ramp faster because of existing brand recognition in the city.")
        _c2.metric("New-City (12M)", fmt_inr(new_12m * 1e5), f"{_new_pct:.0f}% of total",
                   help="Total revenue from new-city expansion clinics over 12 months. Ramps slower (60% penalty in opening month, converging to 100% by Month 12) due to brand-building in unfamiliar markets.")
        _c3.metric("Total OpEx (12M)", fmt_inr(opex_12m * 1e5),
                   help="Total operating expenses for all expansion clinics over 12 months. ₹3L/mo per clinic (same for both city types). Includes rent, staff, electricity, misc.")
        _c4.metric("Net EBITDA (12M)", fmt_inr(ebitda_12m * 1e5),
                    delta_color="normal" if ebitda_12m >= 0 else "inverse",
                    help="Total Revenue minus Total OpEx over the 12-month period. Positive = expansion is cash-flow positive overall. Negative = expansion requires ongoing investment beyond Capex.")

        # ── Metric cards ──
        st.markdown("---")
        _m1, _m2, _m3 = st.columns(3)
        _capex_detail = f"{n_same}×₹{capex_same:.0f}L + {n_new}×₹{capex_new:.0f}L" if n_same > 0 else f"{n_new} clinics × ₹{capex_new:.0f}L"
        _m1.metric("Total Capex", fmt_inr(total_capex * 1e5), _capex_detail,
                   help=f"One-time setup cost at ₹{_DEF_CAPEX:.0f}L per clinic.")
        _m2.metric("12M Revenue", fmt_inr(rev_12m * 1e5),
                   help="Total projected revenue across all clinics over the 12-month forecast period.")
        _m3.metric("Capex Recovered", f"Month {payback_month}" if payback_month else "Beyond 12",
                   help="Month when cumulative EBITDA equals total Capex invested.")

        # ── MAIN CHART — clean bar chart (revenue vs opex) ──
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['month'], y=df['same_rev'],
            name='Same-City Rev', marker_color=PALETTE[0], opacity=0.85,
        ))
        fig.add_trace(go.Bar(
            x=df['month'], y=df['new_rev'],
            name='New-City Rev', marker_color=PALETTE[1], opacity=0.85,
        ))
        fig.add_trace(go.Scatter(
            x=df['month'], y=df['total_opex'],
            name='Total OpEx', mode='lines+markers',
            line=dict(color='#374151', width=2.5), marker=dict(size=5, symbol='diamond'),
        ))
        if be_month:
            fig.add_vline(x=be_month, line_dash="dash", line_color=PALETTE[2], line_width=1.5,
                          annotation_text=f"Break-even M{be_month}",
                          annotation_font=dict(size=11, color=PALETTE[2]),
                          annotation_position="top right")

        _apply_layout(fig, height=420, barmode='stack',
                      margin=dict(l=50, r=20, t=30, b=50),
                      xaxis=dict(title="Month", dtick=1, tickvals=list(range(1, 13)),
                                 showgrid=False, zeroline=False),
                      yaxis=dict(title="₹ Lakhs / month", showgrid=True, gridcolor='#f0f0f0',
                                 zeroline=True, zerolinecolor='#ddd'))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)
        st.caption("Bars = Revenue (red=same-city, orange=new-city stacked). Dark line = Total OpEx. When bars exceed the line → profitable month.")

        # ── Same-City | New-City input widgets (below chart, above funnel) ──
        st.markdown("---")
        _col_same, _col_div, _col_new = st.columns([10, 1, 10])

        with _col_same:
            st.markdown(
                "<div style='background:#fff;border-radius:10px;padding:16px 20px;"
                "box-shadow:0 1px 3px rgba(0,0,0,0.06);border-left:3px solid #c0392b'>"
                "<span style='font-weight:700;font-size:0.95rem;color:#c0392b'>Same-City Expansion</span><br>"
                "<span style='font-size:0.75rem;color:#888'>Cities where Gynoveda already operates</span>"
                "</div>", unsafe_allow_html=True
            )
            _s1, _s2 = st.columns(2)
            _s1.number_input("Clinics to add", value=0, step=1, min_value=0, max_value=100, key='n_same',
                             help="New clinics in cities where Gynoveda already operates. Faster patient ramp due to existing brand awareness.")
            _s2.number_input("Open per month", value=1, step=1, min_value=1, max_value=10, key='same_pm',
                             help="Clinics launched per month. Start from Month 1.")

        with _col_div:
            st.markdown("<div style='border-left:1px solid #e5e7eb;height:160px;margin:0 auto'></div>",
                        unsafe_allow_html=True)

        with _col_new:
            st.markdown(
                "<div style='background:#fff;border-radius:10px;padding:16px 20px;"
                "box-shadow:0 1px 3px rgba(0,0,0,0.06);border-left:3px solid #f97316'>"
                "<span style='font-weight:700;font-size:0.95rem;color:#f97316'>New-City Expansion</span><br>"
                "<span style='font-size:0.75rem;color:#888'>Cities with no Gynoveda clinic — slower ramp</span>"
                "</div>", unsafe_allow_html=True
            )
            _n1, _n2 = st.columns(2)
            _n1.number_input("Clinics to add", value=30, step=1, min_value=0, max_value=100, key='n_new',
                             help="New clinics in cities with no Gynoveda presence. Slower ramp (60% penalty Month 1) due to brand-building.")
            _n2.number_input("Open per month", value=3, step=1, min_value=1, max_value=10, key='new_pm',
                             help="Clinics launched per month. Start from Month 1.")

        # ── Patient Funnel Bridge — shows what each clinic needs ──
        st.markdown(
            f"""<div style='background:linear-gradient(135deg,#fef3c7,#fff7ed);border-radius:8px;padding:14px 18px;margin:8px 0;border-left:3px solid #f59e0b'>
            <span style='font-weight:600;font-size:0.85rem;color:#92400e'>📐 Patient Funnel Bridge</span>
            <table style='width:100%;margin-top:6px;font-size:0.8rem;color:#78350f;border-collapse:collapse'>
            <tr style='border-bottom:1px solid #fde68a'>
                <td style='padding:4px 0'></td>
                <td style='font-weight:600;padding:4px 8px'>1Cx Needed</td>
                <td style='padding:4px 0'>× ₹{bill_value_k:.0f}K =</td>
                <td style='font-weight:700;padding:4px 8px'>Revenue</td>
            </tr>
            <tr>
                <td style='color:#c0392b;font-weight:600;padding:4px 0'>Same-City</td>
                <td style='font-weight:700;padding:4px 8px'>{_1cx_needed_same}/mo</td>
                <td></td>
                <td style='font-weight:700;padding:4px 8px'>₹{same_steady:.0f}L/mo</td>
            </tr>
            <tr>
                <td style='color:#f97316;font-weight:600;padding:4px 0'>New-City</td>
                <td style='font-weight:700;padding:4px 8px'>{_1cx_needed_new}/mo</td>
                <td></td>
                <td style='font-weight:700;padding:4px 8px'>₹{new_steady:.0f}L/mo</td>
            </tr>
            </table>
            <span style='font-size:0.72rem;color:#a16207;margin-top:4px;display:block'>Based on MIS patterns: 1AoV ≈ ₹{bill_value_k:.0f}K</span>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Per-clinic unit economics reference ──
        with st.expander("📊 Per-Clinic Ramp Curve"):
            st.caption("How revenue ramps for a single clinic — shape from historical data, scaled to your Mature Rev targets. Month 0 capped at 10%.")
            _months_range = list(range(min(12, len(_ramp_shape) + 2)))
            def _capped_shape(i):
                if i < len(_ramp_shape):
                    return min(_ramp_shape[i], 0.10) if i == 0 else _ramp_shape[i]
                return 1.0
            _same_curve = [_capped_shape(i) * same_steady * scenario_mult_same for i in _months_range]
            _new_curve = [_capped_shape(i) * new_steady * _new_ramp_penalty(i) * scenario_mult_new for i in _months_range]

            fig_r = go.Figure()
            fig_r.add_trace(go.Scatter(
                x=_months_range, y=_same_curve,
                mode='lines+markers', name=f'Same-City → ₹{same_steady:.0f}L',
                line=dict(color=PALETTE[0], width=2.5), marker=dict(size=5),
            ))
            fig_r.add_trace(go.Scatter(
                x=_months_range, y=_new_curve,
                mode='lines+markers', name=f'New-City → ₹{new_steady:.0f}L',
                line=dict(color=PALETTE[1], width=2.5), marker=dict(size=5),
            ))
            # OpEx reference lines
            fig_r.add_hline(y=same_opex, line_dash="dash", line_color=PALETTE[0], line_width=1,
                            annotation_text=f"Same OpEx ₹{same_opex:.1f}L",
                            annotation_font=dict(size=10, color=PALETTE[0]))
            fig_r.add_hline(y=new_opex, line_dash="dash", line_color=PALETTE[1], line_width=1,
                            annotation_text=f"New OpEx ₹{new_opex:.1f}L",
                            annotation_font=dict(size=10, color=PALETTE[1]))
            _apply_layout(fig_r, height=280,
                          margin=dict(l=45, r=20, t=10, b=40),
                          xaxis=dict(title="Month since opening", showgrid=False, zeroline=False),
                          yaxis=dict(title="₹L/mo per clinic", showgrid=True, gridcolor='#f0f0f0', zeroline=False))
            st.plotly_chart(fig_r, use_container_width=True, config=PLOTLY_CFG)
            st.caption("When the revenue curve crosses its OpEx line → that clinic type becomes individually profitable.")

        # ── Monthly breakdown — collapsed ──
        with st.expander("📋 Monthly Breakdown"):
            _tbl = df.copy()
            _tbl['Same Rev'] = _tbl['same_rev'].apply(lambda x: f"₹{x:.1f}L")
            _tbl['New Rev'] = _tbl['new_rev'].apply(lambda x: f"₹{x:.1f}L")
            _tbl['Total Rev'] = _tbl['total_rev'].apply(lambda x: f"₹{x:.1f}L")
            _tbl['OpEx'] = _tbl['total_opex'].apply(lambda x: f"₹{x:.1f}L")
            _tbl['EBITDA'] = _tbl['ebitda'].apply(lambda x: f"₹{x:+.1f}L")
            _tbl['Cum EBITDA'] = _tbl['cum_ebitda'].apply(lambda x: f"₹{x:+.1f}L")
            _tbl['Clinics'] = _tbl['same_active'] + _tbl['new_active']
            st.dataframe(
                _tbl[['month', 'Clinics', 'Same Rev', 'New Rev', 'Total Rev', 'OpEx', 'EBITDA', 'Cum EBITDA']].rename(
                    columns={'month': 'Month'}
                ),
                use_container_width=True, height=350, hide_index=True,
            )

    _forecaster()


# ── Footer ──
st.caption(f"Data: {active_months[0]} → {active_months[-1]}  ·  {len(master)} clinics  ·  CEI v2")
