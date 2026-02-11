"""
Gynoveda North Star — Expansion Intelligence Dashboard
=======================================================
Composite scoring engine for same-city & new-city expansion decisions.
Replaces prior Clinic Intelligence app with forward-looking analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, json

st.set_page_config(page_title="Gynoveda Expansion Intelligence", layout="wide", page_icon="🧭")
import streamlit.components.v1 as components

# ── PLAUSIBLE ANALYTICS (privacy-friendly, cookie-free) ──────────────
try:
    PLAUSIBLE_DOMAIN = st.secrets["analytics"]["domain"]
except Exception:
    PLAUSIBLE_DOMAIN = ""

if PLAUSIBLE_DOMAIN:
    components.html(f"""
    <script defer data-domain="{PLAUSIBLE_DOMAIN}" src="https://plausible.io/js/script.js"></script>
    """, height=0)

# ── AUTHENTICATION GATE ──────────────────────────────────────────────
# Reads viewer identity from Streamlit Community Cloud (viewer auth must be ON)
# Plus optional email allowlist as a second layer of access control
_user_email = ""
try:
    _user_email = st.experimental_user.email or ""
except Exception:
    pass

# Optional allowlist — if configured, only these emails can access
try:
    _allowed = [e.strip().lower() for e in st.secrets["auth"]["allowed_emails"] if e.strip()]
except Exception:
    _allowed = []

if _allowed and _user_email and _user_email.lower() not in _allowed:
    st.markdown("## ⛔ Access Denied")
    st.error(f"**{_user_email}** is not authorized to view this dashboard. Contact your admin.")
    st.stop()

if _allowed and not _user_email:
    st.markdown("## 🔐 Gynoveda Expansion Intelligence")
    st.info("Please sign in via your Streamlit Cloud account to access this dashboard.")
    st.stop()

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

# City code → full name mapping
CITY_NAMES = {
    'MUM':'Mumbai','NDL':'Delhi','BLR':'Bengaluru','HYD':'Hyderabad','PUN':'Pune',
    'KOL':'Kolkata','CHE':'Chennai','THN':'Thane','NOI':'Noida','AHM':'Ahmedabad',
    'SUR':'Surat','JAI':'Jaipur','LKO':'Lucknow','NAG':'Nagpur','PAT':'Patna',
    'GUR':'Gurugram','IND':'Indore','BPL':'Bhopal','LDH':'Ludhiana','CDG':'Chandigarh',
    'NSK':'Nashik','VAD':'Vadodara','RJK':'Rajkot','DDN':'Dehradun','KNP':'Kanpur',
    'AGR':'Agra','VAR':'Varanasi','PRY':'Prayagraj','MRT':'Meerut','FDB':'Faridabad',
    'GHZ':'Ghaziabad','JAL':'Jalandhar','AMR':'Amritsar','RNC':'Ranchi','BBS':'Bhubaneswar',
    'SGU':'Siliguri','ASN':'Asansol','GUW':'Guwahati','RAI':'Raipur','MYS':'Mysuru',
    'NVM':'Navi Mumbai','KLN':'Kalyan','AUR':'Aurangabad','MAR':'Margao','SEC':'Secunderabad',
    'DMR':'Dimapur','ITR':'Itanagar'
}

# ── CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 1.2rem; padding-bottom: 0.5rem; max-width: 1400px;}
    [data-testid="stMetric"] {background: #f8f9fa; border-radius: 10px; padding: 12px 16px;
        border-left: 4px solid #FF6B35;}
    [data-testid="stMetric"] label {font-size: 0.72rem !important; color: #666;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.3rem !important; font-weight: 700;}
    .score-card {border-radius: 12px; padding: 18px 22px; margin-bottom: 0.6rem; text-align: center;}
    .score-high {background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%); color: white;}
    .score-med  {background: linear-gradient(135deg, #E65100 0%, #F57C00 100%); color: white;}
    .score-low  {background: linear-gradient(135deg, #B71C1C 0%, #D32F2F 100%); color: white;}
    .score-card h2 {margin: 0; font-size: 2.2rem; font-weight: 800;}
    .score-card p {margin: 4px 0 0 0; font-size: 0.82rem; opacity: 0.9;}
    .insight-box {background: #EDE7F6; border-left: 4px solid #5E35B1; padding: 12px 16px;
        border-radius: 8px; margin: 8px 0; font-size: 0.88rem; line-height: 1.5;}
    .risk-high {background: #FFEBEE; border-left: 4px solid #C62828; padding: 10px 14px;
        border-radius: 8px; margin: 4px 0; font-size: 0.85rem;}
    .risk-low {background: #E8F5E9; border-left: 4px solid #2E7D32; padding: 10px 14px;
        border-radius: 8px; margin: 4px 0; font-size: 0.85rem;}
    .kpi-hero {background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 16px 24px; border-radius: 12px; margin-bottom: 0.8rem;}
    .kpi-hero h3 {margin: 0; font-size: 0.78rem; color: #a0a0b0; font-weight: 400; text-transform: uppercase; letter-spacing: 0.5px;}
    .kpi-hero p {margin: 4px 0 0 0; font-size: 1.7rem; font-weight: 700;}
    .kpi-hero span {font-size: 0.8rem; color: #81C784;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
    div[data-testid="stTabs"] button {font-size: 0.9rem; font-weight: 600;}
    div[data-testid="stTabs"] button[aria-selected="true"] {border-bottom: 3px solid #FF6B35;}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ────────────────────────────────────────────────────────
DATA = "mis_data"
os.makedirs(DATA, exist_ok=True)

# ── Excel → CSV Processing Engine ──────────────────────────────────────
def process_mis_excel(file_bytes):
    """Process Clinic_Location__Monthly_MIS.xlsx → 10 CSVs."""
    import io, datetime
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    
    # 1. clinic_master.csv from 'Goal Sales'
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
    
    # Helper: extract clinic-level monthly data by matching Area name
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
    
    # 2-6. Clinic-level sheets
    for sheet, fname in [('SalesMTD','clinic_sales_mtd'),('1Cx','clinic_1cx'),
                          ('rCx','clinic_rcx'),('CAC','clinic_cac'),('LTV','clinic_ltv')]:
        try:
            df = extract_by_area(sheet)
            df.to_csv(f'{DATA}/{fname}.csv', index=False)
        except: pass
    
    # 7. P&L from 'Ebitda Trend'
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
        # Merge FY26 sales from sales data
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
    
    # 8. Network monthly (from total rows in SalesMTD, 1Cx, rCx)
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
        # Add 1Cx/rCx totals
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
    
    # 9-10. Ramp curves
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
    """Process Clinic_wise_FirstTime_TotalQuantity_by_Pincode.xlsx → pincode_firsttime.csv"""
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.to_csv(f'{DATA}/pincode_firsttime.csv', index=False)
    return True

def process_zipdata_excel(file_bytes):
    """Process ZipData_Clinic_NTB.xlsx → clinic_pincode_demand.csv"""
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    pin_demand = df.groupby(['Clinic Loc','Zip','City','State']).agg(
        qty=('Quantity','sum'), revenue=('Total','sum')
    ).reset_index()
    pin_demand.to_csv(f'{DATA}/clinic_pincode_demand.csv', index=False)
    return True

def process_web_orders_excel(file_bytes):
    """Process 1cx web orders file → web_city_demand.csv + web_pincode_yearly.csv"""
    import io
    df = pd.read_excel(io.BytesIO(file_bytes))
    # City demand
    web_city = df.groupby('City').agg(
        total_orders=('Quantity','sum'), total_revenue=('Total','sum'),
        unique_pincodes=('Zip','nunique')
    ).reset_index().sort_values('total_orders', ascending=False)
    web_city.to_csv(f'{DATA}/web_city_demand.csv', index=False)
    # Yearly pincode
    df['year'] = pd.to_datetime(df['Date']).dt.year
    web_pin = df.groupby(['year','Zip','City','State']).agg(
        orders=('Quantity','sum'), revenue=('Total','sum')
    ).reset_index()
    web_pin.to_csv(f'{DATA}/web_pincode_yearly.csv', index=False)
    return True


# ── Upload UI in Sidebar ──────────────────────────────────────────────
with st.sidebar:
    # Show logged-in user identity
    if _user_email:
        st.markdown(f"👤 **{_user_email}**")
        st.caption("Authenticated via Streamlit Cloud")
        st.divider()
    
    with st.expander("📤 Upload Fresh Data", expanded=False):
        st.markdown("Upload updated Excel files to refresh all metrics instantly.")
        
        up_mis = st.file_uploader("Clinic MIS (Monthly)", type=['xlsx','xls'], 
                                   key='up_mis', help="Clinic_Location__Monthly_MIS.xlsx")
        up_ft = st.file_uploader("First-Time Pincodes", type=['xlsx','xls'], 
                                  key='up_ft', help="Clinic_wise_FirstTime_TotalQuantity_by_Pincode.xlsx")
        up_zip = st.file_uploader("Clinic NTB Zip Data", type=['xlsx','xls'], 
                                   key='up_zip', help="ZipData_Clinic_NTB.xlsx")
        up_web = st.file_uploader("Website Orders", type=['xlsx','xls'], 
                                   key='up_web', help="1cx_order_qty_pincode_of_website.xlsx")
        
        if st.button("🔄 Process & Refresh", type="primary", use_container_width=True):
            processed = []
            errors = []
            
            with st.spinner("Processing uploads..."):
                if up_mis:
                    try:
                        process_mis_excel(up_mis.getvalue())
                        processed.append("✅ Clinic MIS → 10 CSVs")
                    except Exception as e:
                        errors.append(f"❌ MIS: {e}")
                if up_ft:
                    try:
                        process_firsttime_excel(up_ft.getvalue())
                        processed.append("✅ First-Time Pincodes")
                    except Exception as e:
                        errors.append(f"❌ First-Time: {e}")
                if up_zip:
                    try:
                        process_zipdata_excel(up_zip.getvalue())
                        processed.append("✅ Clinic NTB Zip Data")
                    except Exception as e:
                        errors.append(f"❌ Zip Data: {e}")
                if up_web:
                    try:
                        process_web_orders_excel(up_web.getvalue())
                        processed.append("✅ Website Orders → 2 CSVs")
                    except Exception as e:
                        errors.append(f"❌ Web Orders: {e}")
            
            if processed:
                st.success("\n".join(processed))
                st.cache_data.clear()
                st.rerun()
            if errors:
                st.error("\n".join(errors))
            if not processed and not errors:
                st.warning("No files uploaded. Select at least one file above.")
        
        st.caption("Upload any combination — only uploaded files get refreshed. Existing data stays for the rest.")


# ── Load CSVs (from disk — either original or freshly processed) ──
@st.cache_data(ttl=600)
def load_all():
    d = {}
    d['master'] = pd.read_csv(f'{DATA}/clinic_master.csv')
    d['sales'] = pd.read_csv(f'{DATA}/clinic_sales_mtd.csv')
    d['cx1'] = pd.read_csv(f'{DATA}/clinic_1cx.csv')
    d['rcx'] = pd.read_csv(f'{DATA}/clinic_rcx.csv')
    d['cac'] = pd.read_csv(f'{DATA}/clinic_cac.csv')
    d['ltv'] = pd.read_csv(f'{DATA}/clinic_ltv.csv')
    d['pl'] = pd.read_csv(f'{DATA}/clinic_pl.csv')
    d['network'] = pd.read_csv(f'{DATA}/network_monthly.csv')
    d['ramp_sales'] = pd.read_csv(f'{DATA}/sales_ramp_curve.csv')
    d['ramp_1cx'] = pd.read_csv(f'{DATA}/1cx_ramp_curve.csv')
    d['pin_ft'] = pd.read_csv(f'{DATA}/pincode_firsttime.csv')
    d['pin_demand'] = pd.read_csv(f'{DATA}/clinic_pincode_demand.csv')
    d['web_city'] = pd.read_csv(f'{DATA}/web_city_demand.csv')
    d['web_pin'] = pd.read_csv(f'{DATA}/web_pincode_yearly.csv')
    return d

data = load_all()
master = data['master']
sales = data['sales']
cx1 = data['cx1']
rcx = data['rcx']
net = data['network'].copy()
ramp_s = data['ramp_sales']
ramp_c = data['ramp_1cx']
pin_demand = data['pin_demand']
pin_ft = data['pin_ft']
web_city = data['web_city']
web_pin = data['web_pin']

# Derived: active months
s_months = sorted([c for c in sales.columns if c not in ['area','code']])
active_months = [m for m in s_months if (sales[m] > 0).sum() > 0]
latest_month = active_months[-1] if active_months else '2025-12'
l3m = active_months[-3:] if len(active_months) >= 3 else active_months
l6m = active_months[-6:] if len(active_months) >= 6 else active_months

# ── SCORING ENGINE ──────────────────────────────────────────────────────
@st.cache_data
def build_city_scores():
    """
    Build Composite Expansion Index (CEI) for every city.
    Returns two DataFrames: same_city (existing) and new_city (whitespace).
    
    Dimensions (weighted):
    1. Online Demand Density (25%) — web orders per city
    2. Revenue Performance (20%) — existing clinic L3M avg (same-city only)
    3. Customer Growth Trajectory (15%) — 1Cx growth trend
    4. Capacity Utilization (15%) — sales per cabin vs network benchmark
    5. O2O Conversion Potential (10%) — clinic demand vs web demand ratio
    6. Market Whitespace (10%) — pincodes with demand but no nearby clinic
    7. Economic Viability (5%) — EBITDA % of existing clinics in region
    """
    
    # ── Dimension 1: Online Demand ──
    web_demand = web_city.copy()
    web_demand['City_lower'] = web_demand['City'].str.lower().str.strip()
    # Normalize to 0-100
    max_orders = web_demand['total_orders'].max()
    web_demand['demand_score'] = (web_demand['total_orders'] / max_orders * 100).clip(0, 100)
    
    # ── Dimension 2 & 3: Revenue + Growth for existing cities ──
    city_perf = []
    for city_code in master['city'].unique():
        city_clinics = master[master['city'] == city_code]
        city_sales = sales[sales['code'].isin(city_clinics['code'])]
        city_1cx = cx1[cx1['code'].isin(city_clinics['code'])]
        
        # L3M revenue
        l3m_rev = city_sales[l3m].sum(axis=1).mean() if len(city_sales) > 0 and all(m in city_sales.columns for m in l3m) else 0
        
        # Growth: compare L3M vs prior 3M
        if len(active_months) >= 6:
            prior_3m = active_months[-6:-3]
            prior_rev = city_sales[prior_3m].sum(axis=1).mean() if len(city_sales) > 0 and all(m in city_sales.columns for m in prior_3m) else 0
            growth = ((l3m_rev - prior_rev) / prior_rev) if prior_rev > 0 else 0
        else:
            growth = 0
        
        # L3M 1Cx
        cx_months = [c for c in cx1.columns if c not in ['area','code']]
        cx_l3m = cx_months[-3:] if len(cx_months) >= 3 else cx_months
        l3m_1cx = city_1cx[cx_l3m].sum(axis=1).mean() if len(city_1cx) > 0 else 0
        
        # Cabins and capacity
        total_cabins = city_clinics['cabins'].sum()
        sales_per_cabin = (l3m_rev * 100) / total_cabins if total_cabins > 0 else 0  # ₹L per cabin
        
        # Pincode coverage
        city_areas = city_clinics['area'].tolist()
        city_pins = pin_demand[pin_demand['Clinic Loc'].isin(city_areas)]['Zip'].nunique()
        
        city_name = CITY_NAMES.get(city_code, city_code)
        
        # EBITDA
        pl = data['pl']
        city_pl = pl[pl['code'].isin(city_clinics['code'])]
        avg_ebitda = city_pl['fy26_ebitda_pct'].mean() if len(city_pl) > 0 else 0
        
        city_perf.append({
            'city_code': city_code,
            'city_name': city_name,
            'clinics': len(city_clinics),
            'total_cabins': total_cabins,
            'l3m_rev_cr': l3m_rev,
            'l3m_1cx': l3m_1cx,
            'growth_pct': growth,
            'sales_per_cabin_l': sales_per_cabin,
            'pincodes_served': city_pins,
            'avg_ebitda_pct': avg_ebitda
        })
    
    df_city = pd.DataFrame(city_perf)
    
    # ── Match web demand to existing cities ──
    name_to_code = {v.lower(): k for k, v in CITY_NAMES.items()}
    web_demand['matched_code'] = web_demand['City_lower'].map(name_to_code)
    
    # Merge web demand into city perf
    web_agg = web_demand.groupby('matched_code').agg(
        web_orders=('total_orders', 'sum'),
        web_revenue=('total_revenue', 'sum'),
        demand_score=('demand_score', 'max')
    ).reset_index().rename(columns={'matched_code': 'city_code'})
    
    df_city = df_city.merge(web_agg, on='city_code', how='left').fillna(0)
    
    # ── Compute Same-City CEI ──
    # Normalize each dimension to 0-100
    def norm(s):
        mn, mx = s.min(), s.max()
        return ((s - mn) / (mx - mn) * 100).fillna(0) if mx > mn else pd.Series(50, index=s.index)
    
    df_city['d1_demand'] = norm(df_city['web_orders'])
    df_city['d2_revenue'] = norm(df_city['l3m_rev_cr'])
    df_city['d3_growth'] = norm(df_city['growth_pct'].clip(-0.5, 2))
    df_city['d4_capacity'] = norm(df_city['sales_per_cabin_l'])
    
    # O2O: ratio of clinic demand to web demand (higher = better conversion)
    clinic_demand_by_city = pin_demand.merge(
        master[['area','city']].rename(columns={'area':'Clinic Loc'}), on='Clinic Loc', how='left'
    ).groupby('city')['qty'].sum().reset_index().rename(columns={'city':'city_code','qty':'clinic_demand'})
    df_city = df_city.merge(clinic_demand_by_city, on='city_code', how='left').fillna(0)
    df_city['o2o_ratio'] = df_city['clinic_demand'] / df_city['web_orders'].replace(0, 1)
    df_city['d5_o2o'] = norm(df_city['o2o_ratio'].clip(0, 20))
    
    # Whitespace: pincodes with web orders but no clinic coverage
    # (for same-city, this means room for additional clinics)
    df_city['d6_whitespace'] = norm(100 - df_city['pincodes_served'].clip(0, 500) / 5)
    
    # Economic viability
    df_city['d7_ebitda'] = norm(df_city['avg_ebitda_pct'].clip(-0.1, 0.5))
    
    # Weighted CEI
    df_city['cei_same'] = (
        df_city['d1_demand'] * 0.25 +
        df_city['d2_revenue'] * 0.20 +
        df_city['d3_growth'] * 0.15 +
        df_city['d4_capacity'] * 0.15 +
        df_city['d5_o2o'] * 0.10 +
        df_city['d6_whitespace'] * 0.10 +
        df_city['d7_ebitda'] * 0.05
    )
    
    # ── New City Scores (cities without clinics) ──
    existing_codes = set(master['city'].unique())
    new_cities = web_demand[web_demand['matched_code'].isna() | ~web_demand['matched_code'].isin(existing_codes)].copy()
    new_cities = new_cities.groupby('City').agg(
        total_orders=('total_orders', 'sum'),
        total_revenue=('total_revenue', 'sum'),
        unique_pincodes=('City', 'count')  # proxy
    ).reset_index()
    
    # For new cities: demand is the primary signal
    new_cities['d1_demand'] = norm(new_cities['total_orders'])
    new_cities['d2_revenue_potential'] = norm(new_cities['total_revenue'])
    
    # Use web_pin for growth trajectory
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
    
    new_cities['cei_new'] = (
        new_cities['d1_demand'] * 0.40 +
        new_cities['d2_revenue_potential'] * 0.30 +
        new_cities['d3_growth'] * 0.30
    )
    
    return df_city.sort_values('cei_same', ascending=False), new_cities.sort_values('cei_new', ascending=False)


@st.cache_data
def build_cannibalization_matrix():
    """
    For each existing city with 2+ clinics, compute pincode overlap
    between clinics to quantify cannibalization risk.
    """
    multi_clinic_cities = master.groupby('city').filter(lambda x: len(x) >= 2)['city'].unique()
    
    results = []
    for city in multi_clinic_cities:
        city_clinics = master[master['city'] == city]['area'].tolist()
        
        # Get pincodes served by each clinic
        clinic_pins = {}
        for clinic in city_clinics:
            pins = set(pin_demand[pin_demand['Clinic Loc'] == clinic]['Zip'].unique())
            clinic_pins[clinic] = pins
        
        # Pairwise overlap
        for i, c1 in enumerate(city_clinics):
            for c2 in city_clinics[i+1:]:
                overlap = clinic_pins.get(c1, set()) & clinic_pins.get(c2, set())
                union = clinic_pins.get(c1, set()) | clinic_pins.get(c2, set())
                overlap_pct = len(overlap) / len(union) if len(union) > 0 else 0
                
                # Revenue in overlapping pincodes
                overlap_rev_c1 = pin_demand[(pin_demand['Clinic Loc'] == c1) & (pin_demand['Zip'].isin(overlap))]['revenue'].sum()
                overlap_rev_c2 = pin_demand[(pin_demand['Clinic Loc'] == c2) & (pin_demand['Zip'].isin(overlap))]['revenue'].sum()
                
                results.append({
                    'city': CITY_NAMES.get(city, city),
                    'city_code': city,
                    'clinic_1': c1,
                    'clinic_2': c2,
                    'shared_pincodes': len(overlap),
                    'total_pincodes': len(union),
                    'overlap_pct': overlap_pct,
                    'overlap_revenue': overlap_rev_c1 + overlap_rev_c2,
                    'risk_level': 'High' if overlap_pct > 0.3 else 'Medium' if overlap_pct > 0.15 else 'Low'
                })
    
    return pd.DataFrame(results)


same_city_scores, new_city_scores = build_city_scores()
cannibal_matrix = build_cannibalization_matrix()

# ── SIDEBAR ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Expansion Parameters")
    capex_per_clinic = st.number_input("Capex / Clinic (₹L)", value=28.0, step=1.0, format="%.0f")
    monthly_opex = st.number_input("Monthly OpEx (₹L)", value=3.1, step=0.1, format="%.1f")
    rev_per_ntb = st.number_input("Revenue / NTB Patient (₹K)", value=22.0, step=1.0, format="%.0f")
    target_ebitda = st.slider("Target EBITDA %", 10, 50, 25)
    o2o_conversion = st.slider("Online→Offline Conversion %", 1, 15, 5)
    
    st.markdown("---")
    st.markdown("### 📊 Weights")
    w_demand = st.slider("Demand Weight", 0, 50, 25)
    w_revenue = st.slider("Revenue Weight", 0, 50, 20)
    w_growth = st.slider("Growth Weight", 0, 50, 15)
    w_capacity = st.slider("Capacity Weight", 0, 50, 15)
    
    st.markdown("---")
    st.caption(f"Data: {active_months[0]} to {active_months[-1]} · {len(master)} clinics")

# ── HEADER ──────────────────────────────────────────────────────────────
st.markdown("<h2 style='margin-bottom:0.2rem;'>Gynoveda Expansion Intelligence</h2>", unsafe_allow_html=True)

# ── TABS ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Executive Summary",
    "🏙️ Same-City Expansion",
    "🌍 New-City Whitespace",
    "📈 Revenue Forecaster"
])

# ═══════════════════════════════════════════════════════════════════════
# TAB 1: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════
with tab1:
    # Network health snapshot
    net_df = net.copy()
    net_df['month'] = pd.to_datetime(net_df['month'])
    net_df = net_df.sort_values('month')
    net_df = net_df[net_df['clinics_cr'] > 0]
    
    latest_net = net_df.iloc[-1] if len(net_df) > 0 else {}
    prev_net = net_df.iloc[-2] if len(net_df) > 1 else {}
    
    # Clinic counts
    active_clinics = (sales[latest_month] > 0).sum() if latest_month in sales.columns else 61
    
    # Hero KPIs
    st.markdown("### Network Health")
    h1, h2, h3, h4, h5 = st.columns(5)
    
    with h1:
        val = latest_net.get('clinics_cr', 0)
        prev_val = prev_net.get('clinics_cr', 0)
        delta = f"{((val-prev_val)/prev_val*100):+.0f}% MoM" if prev_val > 0 else ""
        st.metric("Monthly Revenue", fmt_inr(val * 1e7), delta)
    with h2:
        st.metric("Active Clinics", f"{int(active_clinics)}", f"of {len(master)} total")
    with h3:
        avg_rev_per_clinic = val / active_clinics if active_clinics > 0 else 0
        st.metric("Avg Revenue/Clinic", fmt_inr(avg_rev_per_clinic * 1e7))
    with h4:
        cx1_val = latest_net.get('clinics_1cx', 0)
        st.metric("Monthly New Patients", fmt_num(cx1_val))
    with h5:
        if 'fy26_ebitda_pct' in data['pl'].columns:
            avg_ebitda = data['pl']['fy26_ebitda_pct'].mean()
            st.metric("Avg EBITDA %", pct(avg_ebitda))
    
    st.markdown("---")
    
    # ── Composite Expansion Readiness ──
    st.markdown("### Expansion Readiness Scorecard")
    
    # Calculate top-level scores
    top_same = same_city_scores.head(5)
    top_new = new_city_scores.head(5)
    avg_same_cei = same_city_scores['cei_same'].mean()
    avg_new_cei = new_city_scores['cei_new'].mean()
    
    # Network momentum (are things trending up?)
    if len(net_df) >= 4:
        recent_3 = net_df.tail(3)['clinics_cr'].mean()
        prior_3 = net_df.iloc[-6:-3]['clinics_cr'].mean() if len(net_df) >= 6 else net_df.head(3)['clinics_cr'].mean()
        momentum = (recent_3 - prior_3) / prior_3 if prior_3 > 0 else 0
    else:
        momentum = 0
    
    sc1, sc2, sc3 = st.columns(3)
    
    with sc1:
        score_class = "score-high" if avg_same_cei > 55 else "score-med" if avg_same_cei > 35 else "score-low"
        st.markdown(f"""<div class="score-card {score_class}">
            <h2>{avg_same_cei:.0f}</h2>
            <p>Same-City Expansion Score</p>
            <p>Top opportunity: <b>{top_same.iloc[0]['city_name']}</b></p>
        </div>""", unsafe_allow_html=True)
    
    with sc2:
        score_class = "score-high" if avg_new_cei > 40 else "score-med" if avg_new_cei > 25 else "score-low"
        st.markdown(f"""<div class="score-card {score_class}">
            <h2>{avg_new_cei:.0f}</h2>
            <p>New-City Expansion Score</p>
            <p>Top opportunity: <b>{top_new.iloc[0]['City'] if len(top_new) > 0 else 'N/A'}</b></p>
        </div>""", unsafe_allow_html=True)
    
    with sc3:
        mom_class = "score-high" if momentum > 0.05 else "score-med" if momentum > -0.05 else "score-low"
        st.markdown(f"""<div class="score-card {mom_class}">
            <h2>{momentum*100:+.0f}%</h2>
            <p>Revenue Momentum (L3M vs Prior)</p>
            <p>{'Accelerating — expand' if momentum > 0.05 else 'Stable — selective expansion' if momentum > -0.05 else 'Decelerating — consolidate first'}</p>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── Revenue & Growth Trend ──
    col_trend1, col_trend2 = st.columns(2)
    
    with col_trend1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=net_df['month'], y=net_df['clinics_cr'],
                             name='Clinic Revenue (₹Cr)', marker_color='#FF6B35', opacity=0.85))
        if 'video_cr' in net_df.columns:
            fig.add_trace(go.Bar(x=net_df['month'], y=net_df['video_cr'],
                                 name='Video Revenue (₹Cr)', marker_color='#4ECDC4', opacity=0.85))
        fig.update_layout(title="Monthly Revenue Trend", height=350, barmode='stack',
                         margin=dict(l=20, r=20, t=40, b=20),
                         legend=dict(orientation='h', y=1.12), yaxis_title="₹ Crores")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_trend2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=net_df['month'], y=net_df['clinics_1cx'], name='New (1Cx)',
                                   mode='lines+markers', line=dict(color='#FF6B35', width=2.5)))
        fig2.add_trace(go.Scatter(x=net_df['month'], y=net_df['clinics_rcx'], name='Repeat (rCx)',
                                   mode='lines+markers', line=dict(color='#4ECDC4', width=2.5)))
        fig2.update_layout(title="Patient Acquisition Trend", height=350,
                          margin=dict(l=20, r=20, t=40, b=20),
                          legend=dict(orientation='h', y=1.12), yaxis_title="Patients")
        st.plotly_chart(fig2, use_container_width=True)
    
    # ── Top Expansion Picks ──
    st.markdown("### 🏆 Top 5 Expansion Opportunities")
    
    col_same, col_new = st.columns(2)
    
    with col_same:
        st.markdown("**Same-City (Add Clinics)**")
        for _, row in top_same.iterrows():
            cei = row['cei_same']
            badge = "🟢" if cei > 60 else "🟡" if cei > 40 else "🔴"
            st.markdown(f"""
            {badge} **{row['city_name']}** — CEI: **{cei:.0f}** · {int(row['clinics'])} clinics · 
            L3M Rev: {fmt_inr(row['l3m_rev_cr'] * 1e7)} · Web Orders: {fmt_num(row['web_orders'])}
            """)
    
    with col_new:
        st.markdown("**New-City (Open First Clinic)**")
        for _, row in top_new.head(5).iterrows():
            cei = row['cei_new']
            badge = "🟢" if cei > 60 else "🟡" if cei > 40 else "🔴"
            st.markdown(f"""
            {badge} **{row['City']}** — CEI: **{cei:.0f}** · 
            Web Orders: {fmt_num(row['total_orders'])} · Revenue: {fmt_inr(row['total_revenue'])}
            """)
    
    # ── Insights ──
    st.markdown("---")
    
    # Auto-generated insights
    high_growth_cities = same_city_scores[same_city_scores['growth_pct'] > 0.2]
    saturated_cities = same_city_scores[same_city_scores['sales_per_cabin_l'] > same_city_scores['sales_per_cabin_l'].quantile(0.75)]
    high_cannibal = cannibal_matrix[cannibal_matrix['overlap_pct'] > 0.3] if len(cannibal_matrix) > 0 else pd.DataFrame()
    
    insights = []
    if len(saturated_cities) > 0:
        top_sat = saturated_cities.iloc[0]
        insights.append(f"🔥 **{top_sat['city_name']}** has the highest capacity utilization ({fmt_inr(top_sat['sales_per_cabin_l'] * 1e5)}/cabin) — strong candidate for an additional clinic.")
    if len(high_cannibal) > 0:
        insights.append(f"⚠️ **{len(high_cannibal)} clinic pairs** show >30% pincode overlap — review catchment boundaries before adding clinics in those cities.")
    if len(high_growth_cities) > 0:
        growth_list = ', '.join(high_growth_cities.head(3)['city_name'].tolist())
        insights.append(f"📈 **{growth_list}** showing >20% revenue growth L3M — momentum cities for expansion.")
    
    top_unserved = new_city_scores.head(1)
    if len(top_unserved) > 0:
        insights.append(f"🌍 **{top_unserved.iloc[0]['City']}** leads new-city whitespace with {fmt_num(top_unserved.iloc[0]['total_orders'])} web orders and no clinic.")
    
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 2: SAME-CITY EXPANSION
# ═══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Same-City Expansion Analysis")
    st.markdown("*Where should we add clinics in cities we already operate in?*")
    
    # ── CEI Ranking Table ──
    st.markdown("#### Composite Expansion Index — Existing Cities")
    
    display_same = same_city_scores.copy()
    display_same['CEI'] = display_same['cei_same'].fillna(0).round(0).astype(int)
    display_same['L3M Rev'] = display_same['l3m_rev_cr'].apply(lambda x: fmt_inr(x * 1e7))
    display_same['Growth'] = display_same['growth_pct'].apply(lambda x: f"{x*100:+.0f}%")
    display_same['Rev/Cabin'] = display_same['sales_per_cabin_l'].apply(lambda x: fmt_inr(x * 1e5))
    display_same['Web Orders'] = display_same['web_orders'].apply(lambda x: fmt_num(x))
    display_same['EBITDA'] = display_same['avg_ebitda_pct'].apply(lambda x: pct(x))
    display_same['Pincodes'] = display_same['pincodes_served'].fillna(0).astype(int)
    
    st.dataframe(
        display_same[['city_name','clinics','total_cabins','CEI','L3M Rev','Growth',
                       'Rev/Cabin','Web Orders','EBITDA','Pincodes']].rename(columns={
            'city_name':'City','clinics':'Clinics','total_cabins':'Cabins'
        }),
        use_container_width=True, height=400,
        column_config={
            'CEI': st.column_config.ProgressColumn("CEI Score", min_value=0, max_value=100, format="%d"),
        }
    )
    
    st.markdown("---")
    
    # ── CEI Dimension Radar for selected city ──
    st.markdown("#### Deep-Dive: City Expansion Profile")
    
    city_options = same_city_scores['city_name'].tolist()
    selected_city = st.selectbox("Select City", city_options, key='same_city_select')
    city_data = same_city_scores[same_city_scores['city_name'] == selected_city].iloc[0]
    
    col_radar, col_metrics = st.columns([1, 1])
    
    with col_radar:
        categories = ['Demand', 'Revenue', 'Growth', 'Capacity', 'O2O Conv.', 'Whitespace', 'EBITDA']
        values = [city_data['d1_demand'], city_data['d2_revenue'], city_data['d3_growth'],
                  city_data['d4_capacity'], city_data['d5_o2o'], city_data['d6_whitespace'], city_data['d7_ebitda']]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill='toself', fillcolor='rgba(255,107,53,0.2)',
            line=dict(color='#FF6B35', width=2.5),
            marker=dict(size=6)
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
            title=f"CEI Profile — {selected_city}", height=380,
            margin=dict(l=60, r=60, t=50, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col_metrics:
        st.markdown(f"""<div class="kpi-hero">
            <h3>Composite Expansion Index</h3>
            <p>{city_data['cei_same']:.0f} / 100</p>
            <span>{'✅ Strong expansion candidate' if city_data['cei_same'] > 55 else '⚠️ Moderate — validate before expanding' if city_data['cei_same'] > 35 else '❌ Weak — consolidate first'}</span>
        </div>""", unsafe_allow_html=True)
        
        m1, m2 = st.columns(2)
        m1.metric("Clinics", int(city_data['clinics']))
        m2.metric("Cabins", int(city_data['total_cabins']))
        m3, m4 = st.columns(2)
        m3.metric("L3M Monthly Rev", fmt_inr(city_data['l3m_rev_cr'] * 1e7))
        m4.metric("Revenue Growth", f"{city_data['growth_pct']*100:+.0f}%")
        m5, m6 = st.columns(2)
        m5.metric("Sales/Cabin", fmt_inr(city_data['sales_per_cabin_l'] * 1e5))
        m6.metric("Web Orders", fmt_num(city_data['web_orders']))
        
        # Recommendation
        if city_data['cei_same'] > 55 and city_data['sales_per_cabin_l'] > same_city_scores['sales_per_cabin_l'].median():
            st.markdown('<div class="risk-low">✅ <b>Expand</b> — high demand + capacity strain suggests a new clinic will capture incremental revenue without cannibalizing existing locations.</div>', unsafe_allow_html=True)
        elif city_data['cei_same'] > 35:
            st.markdown('<div class="insight-box">⚠️ <b>Selective</b> — expand only if cannibalization analysis shows low overlap and there are underserved pincodes.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="risk-high">❌ <b>Hold</b> — current clinics are underperforming. Fix operations before adding capacity.</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── Cannibalization Risk ──
    st.markdown("#### 🔴 Cannibalization Risk Matrix")
    
    if len(cannibal_matrix) > 0:
        city_code = same_city_scores[same_city_scores['city_name'] == selected_city]['city_code'].values[0]
        city_cannibal = cannibal_matrix[cannibal_matrix['city_code'] == city_code]
        
        if len(city_cannibal) > 0:
            for _, row in city_cannibal.iterrows():
                risk_class = "risk-high" if row['risk_level'] == 'High' else "insight-box" if row['risk_level'] == 'Medium' else "risk-low"
                st.markdown(f"""<div class="{risk_class}">
                    <b>{row['clinic_1']}</b> ↔ <b>{row['clinic_2']}</b> · 
                    Overlap: <b>{row['overlap_pct']*100:.0f}%</b> ({row['shared_pincodes']} shared pincodes / {row['total_pincodes']} total) · 
                    Revenue at risk: <b>{fmt_inr(row['overlap_revenue'])}</b> · 
                    Risk: <b>{row['risk_level']}</b>
                </div>""", unsafe_allow_html=True)
        else:
            st.info(f"Only 1 clinic in {selected_city} — no cannibalization pairs to analyze.")
    else:
        st.info("No multi-clinic cities found for cannibalization analysis.")
    
    st.markdown("---")
    
    # ── Pincode Saturation Map ──
    st.markdown("#### Pincode Demand Distribution")
    
    city_code_sel = same_city_scores[same_city_scores['city_name'] == selected_city]['city_code'].values[0]
    city_clinics = master[master['city'] == city_code_sel]['area'].tolist()
    city_pin_data = pin_demand[pin_demand['Clinic Loc'].isin(city_clinics)]
    
    if len(city_pin_data) > 0:
        # Top pincodes by demand
        top_pins = city_pin_data.groupby(['Zip','City','State']).agg(
            total_qty=('qty','sum'), total_rev=('revenue','sum'), clinics_serving=('Clinic Loc','nunique')
        ).reset_index().sort_values('total_qty', ascending=False).head(20)
        
        top_pins['Revenue'] = top_pins['total_rev'].apply(lambda x: fmt_inr(x))
        top_pins['Multi-Clinic'] = top_pins['clinics_serving'].apply(lambda x: '⚠️ Yes' if x > 1 else '✅ No')
        
        st.dataframe(
            top_pins[['Zip','City','total_qty','Revenue','clinics_serving','Multi-Clinic']].rename(columns={
                'Zip':'Pincode','total_qty':'Demand (Qty)','clinics_serving':'Clinics Serving'
            }),
            use_container_width=True, height=400
        )
        
        # Pincodes served by multiple clinics = saturation signal
        multi_served = top_pins[top_pins['clinics_serving'] > 1]
        if len(multi_served) > 0:
            st.markdown(f'<div class="insight-box">⚠️ <b>{len(multi_served)} pincodes</b> are served by multiple clinics in {selected_city} — review if adding another clinic would increase saturation or target an underserved zone.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 3: NEW-CITY WHITESPACE
# ═══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### New-City Whitespace Discovery")
    st.markdown("*Cities with proven online demand but no Gynoveda clinic — your expansion frontier.*")
    
    # ── Whitespace Scoring Table ──
    display_new = new_city_scores.head(30).copy()
    display_new['CEI'] = display_new['cei_new'].fillna(0).round(0).astype(int)
    display_new['Orders'] = display_new['total_orders'].apply(lambda x: fmt_num(x))
    display_new['Revenue'] = display_new['total_revenue'].apply(lambda x: fmt_inr(x))
    display_new['Growth'] = display_new['trend_growth'].apply(lambda x: f"{x*100:+.0f}%")
    
    # O2O projected patients
    display_new['Projected Monthly NTB'] = (display_new['total_orders'] * (o2o_conversion / 100) / 12).fillna(0).astype(int)
    display_new['Projected Monthly Rev'] = display_new['Projected Monthly NTB'] * rev_per_ntb * 1000
    display_new['Proj. Rev (₹L/mo)'] = (display_new['Projected Monthly Rev'] / 1e5).round(1)
    
    # Breakeven check — safe division, replace Inf/NaN before int cast
    _be_raw = np.where(
        display_new['Proj. Rev (₹L/mo)'] > 0,
        np.ceil(monthly_opex / display_new['Proj. Rev (₹L/mo)'].replace(0, np.nan) * 3),
        99
    )
    display_new['Months to OpEx BE'] = pd.Series(_be_raw).fillna(99).clip(upper=99).astype(int).values
    
    st.dataframe(
        display_new[['City','CEI','Orders','Revenue','Growth','Projected Monthly NTB',
                      'Proj. Rev (₹L/mo)','Months to OpEx BE']].rename(columns={'City':'City'}),
        use_container_width=True, height=500,
        column_config={
            'CEI': st.column_config.ProgressColumn("CEI Score", min_value=0, max_value=100, format="%d"),
        }
    )
    
    st.markdown("---")
    
    # ── Demand Heatmap ──
    st.markdown("#### Online Demand Heatmap")
    
    fig_bar = go.Figure(go.Bar(
        y=display_new.head(20)['City'],
        x=display_new.head(20)['total_orders'],
        orientation='h',
        marker=dict(color=display_new.head(20)['cei_new'],
                    colorscale='YlOrRd', showscale=True,
                    colorbar=dict(title="CEI")),
        text=display_new.head(20)['Orders'],
        textposition='outside'
    ))
    fig_bar.update_layout(title="Top 20 Unserved Cities by Web Demand", height=550,
                         margin=dict(l=120, r=60, t=40, b=20),
                         xaxis_title="Total Web Orders", yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # ── O2O Conversion Projection ──
    st.markdown("#### Online-to-Offline Conversion Projections")
    st.markdown(f"*Based on **{o2o_conversion}%** conversion rate from web orders to clinic NTB patients (adjustable in sidebar)*")
    
    # Use actual O2O ratios from existing cities as benchmarks
    existing_o2o = same_city_scores[same_city_scores['web_orders'] > 100].copy()
    existing_o2o['actual_o2o'] = existing_o2o['clinic_demand'] / existing_o2o['web_orders']
    
    if len(existing_o2o) > 0:
        avg_o2o = existing_o2o['actual_o2o'].median()
        
        col_o2o1, col_o2o2 = st.columns(2)
        
        with col_o2o1:
            fig_o2o = go.Figure(go.Bar(
                y=existing_o2o.sort_values('actual_o2o', ascending=True)['city_name'],
                x=existing_o2o.sort_values('actual_o2o', ascending=True)['actual_o2o'],
                orientation='h', marker_color='#4ECDC4',
                text=[f"{x:.1f}x" for x in existing_o2o.sort_values('actual_o2o', ascending=True)['actual_o2o']],
                textposition='outside'
            ))
            fig_o2o.update_layout(title="Actual O2O Multiplier (Clinic Demand / Web Orders)",
                                 height=400, margin=dict(l=100, r=40, t=40, b=20),
                                 xaxis_title="O2O Ratio")
            st.plotly_chart(fig_o2o, use_container_width=True)
        
        with col_o2o2:
            st.markdown(f"""<div class="insight-box">
                <b>Benchmark:</b> Existing cities show a median O2O multiplier of <b>{avg_o2o:.1f}x</b> — 
                meaning for every 1 web order, clinics generate {avg_o2o:.1f} patient transactions on average. 
                This validates the online-to-offline flywheel. New-city projections use a conservative 
                <b>{o2o_conversion}%</b> first-year conversion rate, ramping up as the clinic matures.
            </div>""", unsafe_allow_html=True)
            
            # Top 5 new city projections
            st.markdown("**Top 5 New-City Revenue Projections (Year 1)**")
            for _, row in display_new.head(5).iterrows():
                y1_rev = row['Proj. Rev (₹L/mo)'] * 12
                y1_profit = y1_rev * (target_ebitda / 100) - monthly_opex * 12
                color = "🟢" if y1_profit > 0 else "🔴"
                st.markdown(f"{color} **{row['City']}**: {row['Projected Monthly NTB']} NTB/mo → "
                           f"₹{row['Proj. Rev (₹L/mo)']:.1f}L/mo → Year 1: {fmt_inr(y1_rev * 1e5)} revenue, "
                           f"{fmt_inr(y1_profit * 1e5)} {'profit' if y1_profit > 0 else 'loss'}")
    
    # ── YoY Web Demand Trend ──
    st.markdown("---")
    st.markdown("#### Web Demand Trend (All Cities)")
    
    yoy = web_pin.groupby('year')['orders'].sum().reset_index()
    yoy = yoy[yoy['year'] >= 2020]
    fig_yoy = go.Figure(go.Bar(x=yoy['year'].astype(str), y=yoy['orders'],
                                marker_color='#FF6B35',
                                text=yoy['orders'].apply(lambda x: fmt_num(x)),
                                textposition='outside'))
    fig_yoy.update_layout(title="National Web Orders by Year", height=300,
                         margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Orders")
    st.plotly_chart(fig_yoy, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 4: REVENUE FORECASTER
# ═══════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Revenue Ramp Forecaster")
    st.markdown("*Project revenue for new clinics using actual ramp curves from your 61-clinic network.*")
    
    # ── Actual Ramp Curves ──
    rc1, rc2 = st.columns(2)
    
    with rc1:
        fig_ramp = go.Figure()
        fig_ramp.add_trace(go.Scatter(x=ramp_s['month_num'], y=ramp_s['avg_sales_l'],
                                       mode='lines+markers', name='Avg Sales (₹L/mo)',
                                       line=dict(color='#FF6B35', width=3), marker=dict(size=5)))
        # Add envelope: use clinics count as confidence
        fig_ramp.add_hline(y=monthly_opex, line_dash="dash", line_color="#dc3545",
                          annotation_text=f"OpEx Breakeven (₹{monthly_opex}L)")
        total_monthly = monthly_opex + (capex_per_clinic / 24)  # 24-month amortization
        fig_ramp.add_hline(y=total_monthly, line_dash="dot", line_color="#FFA000",
                          annotation_text=f"Full Breakeven (₹{total_monthly:.1f}L)")
        fig_ramp.update_layout(title="Average Clinic Sales Ramp (M0→M30)", height=380,
                              margin=dict(l=20, r=20, t=40, b=20),
                              xaxis_title="Month Since Launch", yaxis_title="₹ Lakhs/month")
        st.plotly_chart(fig_ramp, use_container_width=True)
    
    with rc2:
        fig_ramp2 = go.Figure()
        fig_ramp2.add_trace(go.Scatter(x=ramp_c['month_num'], y=ramp_c['avg_1cx'],
                                        mode='lines+markers', name='Avg New Patients',
                                        line=dict(color='#4ECDC4', width=3), marker=dict(size=5)))
        fig_ramp2.update_layout(title="Average New Patient Ramp (M0→M30)", height=380,
                               margin=dict(l=20, r=20, t=40, b=20),
                               xaxis_title="Month Since Launch", yaxis_title="New Patients/month")
        st.plotly_chart(fig_ramp2, use_container_width=True)
    
    st.markdown("---")
    
    # ── Scenario Simulator ──
    st.markdown("### Scenario Simulator")
    
    sim1, sim2, sim3 = st.columns(3)
    with sim1:
        n_clinics = st.number_input("New Clinics to Open", value=20, step=5, min_value=1, max_value=200, key='n_sim')
        scenario = st.radio("Scenario", ["Conservative (0.85x)", "Base Case (1.0x)", "Optimistic (1.15x)"], index=1)
    with sim2:
        steady_month = st.number_input("Months to Steady State", value=12, step=1, min_value=3, max_value=36, key='ss_month')
        steady_sales = st.number_input("Steady-State Sales (₹L/clinic/mo)", 
                                        value=round(ramp_s['avg_sales_l'].iloc[-1], 1) if len(ramp_s) > 0 else 20.0,
                                        step=1.0, format="%.1f", key='ss_val')
    with sim3:
        wave_1_pct = st.slider("Wave 1 Launch (%)", 20, 100, 50)
        wave_2_month = st.number_input("Wave 2 Start (Month)", value=6, step=1, min_value=1)
    
    scenario_mult = {'Conservative (0.85x)': 0.85, 'Base Case (1.0x)': 1.0, 'Optimistic (1.15x)': 1.15}[scenario]
    
    # Build 24-month projection
    wave_1_n = int(n_clinics * wave_1_pct / 100)
    wave_2_n = n_clinics - wave_1_n
    
    proj_data = []
    cum_rev = 0
    cum_opex = 0
    cum_ebitda = 0
    
    for m in range(24):
        # Wave 1 clinics (launch at M0)
        w1_rev = 0
        if m < len(ramp_s):
            w1_rev = ramp_s.iloc[m]['avg_sales_l'] * scenario_mult * wave_1_n
        else:
            w1_rev = steady_sales * scenario_mult * wave_1_n
        
        # Wave 2 clinics (launch at wave_2_month)
        w2_rev = 0
        w2_month = m - wave_2_month
        if w2_month >= 0:
            if w2_month < len(ramp_s):
                w2_rev = ramp_s.iloc[w2_month]['avg_sales_l'] * scenario_mult * wave_2_n
            else:
                w2_rev = steady_sales * scenario_mult * wave_2_n
        
        total_rev = w1_rev + w2_rev
        active = wave_1_n + (wave_2_n if m >= wave_2_month else 0)
        total_opex = monthly_opex * active
        monthly_ebitda = total_rev - total_opex
        
        cum_rev += total_rev
        cum_opex += total_opex
        cum_ebitda += monthly_ebitda
        
        proj_data.append({
            'month': m,
            'active_clinics': active,
            'monthly_rev_l': total_rev,
            'monthly_opex_l': total_opex,
            'monthly_ebitda_l': monthly_ebitda,
            'cum_rev_l': cum_rev,
            'cum_opex_l': cum_opex,
            'cum_ebitda_l': cum_ebitda
        })
    
    df_proj = pd.DataFrame(proj_data)
    total_capex = capex_per_clinic * n_clinics
    
    # Results KPIs
    st.markdown("---")
    
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Total Capex", fmt_inr(total_capex * 1e5))
    
    y1_rev = df_proj[df_proj['month'] < 12]['monthly_rev_l'].sum()
    r2.metric("Year 1 Revenue", fmt_inr(y1_rev * 1e5))
    
    # OpEx breakeven month
    opex_be = df_proj[df_proj['monthly_ebitda_l'] > 0]
    opex_be_month = int(opex_be.iloc[0]['month']) if len(opex_be) > 0 else 'N/A'
    r3.metric("OpEx Breakeven", f"M{opex_be_month}" if isinstance(opex_be_month, int) else opex_be_month)
    
    # Capex payback
    capex_payback = df_proj[df_proj['cum_ebitda_l'] >= total_capex]
    payback = int(capex_payback.iloc[0]['month']) if len(capex_payback) > 0 else 'N/A'
    r4.metric("Capex Payback", f"M{payback}" if isinstance(payback, int) else "24+ months")
    
    y2_ebitda = df_proj.iloc[-1]['cum_ebitda_l'] - total_capex
    r5.metric("Net 24M Return", fmt_inr(y2_ebitda * 1e5))
    
    # Projection chart
    fig_proj = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_proj.add_trace(go.Bar(x=df_proj['month'], y=df_proj['monthly_rev_l'],
                              name='Monthly Revenue (₹L)', marker_color='#FF6B35', opacity=0.7),
                      secondary_y=False)
    fig_proj.add_trace(go.Bar(x=df_proj['month'], y=-df_proj['monthly_opex_l'],
                              name='Monthly OpEx (₹L)', marker_color='#dc3545', opacity=0.4),
                      secondary_y=False)
    fig_proj.add_trace(go.Scatter(x=df_proj['month'], y=df_proj['cum_ebitda_l'],
                                  name='Cum. EBITDA (₹L)', mode='lines',
                                  line=dict(color='#28a745', width=3)),
                      secondary_y=True)
    fig_proj.add_hline(y=total_capex, line_dash="dash", line_color="#5E35B1",
                      annotation_text=f"Total Capex (₹{total_capex:.0f}L)", secondary_y=True)
    
    fig_proj.update_layout(
        title=f"24-Month Projection — {n_clinics} Clinics ({scenario})",
        height=450, margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation='h', y=1.15), barmode='relative'
    )
    fig_proj.update_yaxes(title_text="₹ Lakhs/month", secondary_y=False)
    fig_proj.update_yaxes(title_text="Cumulative ₹ Lakhs", secondary_y=True)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # ── Tier-wise Breakdown ──
    with st.expander("📊 Existing Network P&L by Tier"):
        pl_data = data['pl']
        if len(pl_data) > 0:
            pl_m = pl_data.merge(master[['code','tier','zone','city']], on='code', how='left')
            
            tier_summary = pl_m.groupby('tier').agg(
                clinics=('code', 'count'),
                avg_ebitda=('fy26_ebitda_pct', 'mean')
            ).reset_index()
            
            if 'fy26_sales_l' in pl_m.columns:
                tier_sales = pl_m.groupby('tier')['fy26_sales_l'].sum().reset_index()
                tier_summary = tier_summary.merge(tier_sales, on='tier', how='left')
                tier_summary['total_sales'] = tier_summary['fy26_sales_l'].apply(lambda x: fmt_inr(x * 1e5) if pd.notna(x) else '-')
            
            tier_summary['avg_ebitda'] = tier_summary['avg_ebitda'].apply(lambda x: pct(x))
            
            display_cols = ['tier', 'clinics', 'avg_ebitda']
            col_rename = {'tier': 'Tier', 'clinics': 'Clinics', 'avg_ebitda': 'Avg EBITDA%'}
            if 'total_sales' in tier_summary.columns:
                display_cols.append('total_sales')
                col_rename['total_sales'] = 'FY26 Sales'
            
            st.dataframe(tier_summary[display_cols].rename(columns=col_rename), use_container_width=True)


# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Gynoveda Expansion Intelligence · {active_months[0]} to {active_months[-1]} · {len(master)} clinics · CEI Engine v1.0")
