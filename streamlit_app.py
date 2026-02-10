"""
Gynoveda Clinic Intelligence Dashboard — v2
4 Tabs: Network Overview | Clinic Deep-Dive | Expansion ROI | Pincode Drill-Down
Powered by actual MIS data (Sales, 1Cx, rCx, CAC, LTV, P&L)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Gynoveda Clinic Intelligence", layout="wide", page_icon="🏥")

# ── Formatting helpers ──────────────────────────────────────────────────────
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
    if v >= 1e7: return f"{sign}{v/1e7:.{d+1}f} Cr"
    if v >= 1e5: return f"{sign}{v/1e5:.{d}f}L"
    if v >= 1e3: return f"{sign}{v/1e3:.{d}f}K"
    return f"{sign}{v:.0f}"

MONTH_ORDER = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 0.8rem; padding-bottom: 0.5rem; max-width: 1300px;}
    [data-testid="stMetric"] {background: #f8f9fa; border-radius: 8px; padding: 10px 14px; border-left: 4px solid #FF6B35;}
    [data-testid="stMetric"] label {font-size: 0.72rem !important; color: #666;}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.35rem !important; font-weight: 700;}
    .kpi-box {background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 14px 20px; border-radius: 10px; margin-bottom: 0.8rem;}
    .kpi-box h3 {margin: 0; font-size: 0.8rem; color: #a0a0b0; font-weight: 400;}
    .kpi-box p {margin: 4px 0 0 0; font-size: 1.6rem; font-weight: 700;}
    .tag-green {background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
    .tag-red {background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
    .tag-blue {background: #d1ecf1; color: #0c5460; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
    div[data-testid="stTabs"] button {font-size: 0.95rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ────────────────────────────────────────────────────────────
DATA = "mis_data"

@st.cache_data
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
    # Pincode data
    d['pin_ft'] = pd.read_csv(f'{DATA}/pincode_firsttime.csv')
    d['pin_demand'] = pd.read_csv(f'{DATA}/clinic_pincode_demand.csv')
    d['web_city'] = pd.read_csv(f'{DATA}/web_city_demand.csv')
    d['web_pin'] = pd.read_csv(f'{DATA}/web_pincode_yearly.csv')
    return d

data = load_all()
master = data['master']

# ── Merge master info into sales/cx/cac/ltv for easy filtering ──
def enrich(df):
    """Add city, tier, zone from master by matching on code or area."""
    if 'code' in df.columns and 'code' in master.columns:
        return df.merge(master[['code','area','city','tier','zone','cabins','launch']], on='code', how='left', suffixes=('','_m'))
    return df

# Get month columns (YYYY-MM format) from sales df
sales = data['sales']
# Filter to months with actual data (at least 1 clinic reporting)
all_months = sorted([c for c in sales.columns if c not in ['area','code','city','region','zone']])
month_cols = [m for m in all_months if (sales[m] > 0).sum() > 0]
latest_month = month_cols[-1] if month_cols else '2026-01'
l3m = month_cols[-3:] if len(month_cols) >= 3 else month_cols
l6m = month_cols[-6:] if len(month_cols) >= 6 else month_cols

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("## 🏥 Gynoveda Clinic Intelligence")

# ── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Network Overview", "🔍 Clinic Deep-Dive", "📈 Expansion ROI", "📍 Pincode Drill-Down"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: NETWORK OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    net = data['network'].copy()
    net['month'] = pd.to_datetime(net['month'])
    net = net.sort_values('month')
    # Filter to months with actual data
    net = net[net['clinics_cr'] > 0]
    
    # Current month KPIs
    latest = net.iloc[-1] if len(net) > 0 else {}
    prev = net.iloc[-2] if len(net) > 1 else {}
    
    # Build clinic count by month from sales data
    clinic_counts = []
    for m in month_cols:
        active = (sales[m] > 0).sum()
        clinic_counts.append({'month': m, 'active_clinics': active})
    df_cc = pd.DataFrame(clinic_counts)
    current_clinics = df_cc.iloc[-1]['active_clinics'] if len(df_cc) > 0 else 61
    
    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        val = latest.get('clinics_cr', 0)
        prev_val = prev.get('clinics_cr', 0)
        delta = f"{((val-prev_val)/prev_val*100):.0f}% MoM" if prev_val > 0 else ""
        st.metric("Monthly Sales (Clinics)", fmt_inr(val * 1e7), delta)
    with c2:
        val1cx = latest.get('clinics_1cx', 0)
        prev1cx = prev.get('clinics_1cx', 0)
        delta1cx = f"{((val1cx-prev1cx)/prev1cx*100):.0f}% MoM" if prev1cx > 0 else ""
        st.metric("New Customers (1Cx)", fmt_num(val1cx), delta1cx)
    with c3:
        valrcx = latest.get('clinics_rcx', 0)
        prevrcx = prev.get('clinics_rcx', 0)
        deltarcx = f"{((valrcx-prevrcx)/prevrcx*100):.0f}% MoM" if prevrcx > 0 else ""
        st.metric("Repeat Customers (rCx)", fmt_num(valrcx), deltarcx)
    with c4:
        total_cx = val1cx + valrcx
        repeat_pct = valrcx / total_cx * 100 if total_cx > 0 else 0
        st.metric("Repeat %", f"{repeat_pct:.0f}%", f"{int(current_clinics)} clinics active")
    with c5:
        # Cumulative sales
        cum_sales = net['clinics_cr'].sum()
        st.metric("Cumulative Sales", fmt_inr(cum_sales * 1e7))

    st.markdown("---")
    
    # Charts Row 1: Sales + Customer Trends
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=net['month'], y=net['clinics_cr'], name='Clinic Sales (₹Cr)',
                             marker_color='#FF6B35', opacity=0.85))
        if 'video_cr' in net.columns:
            fig.add_trace(go.Bar(x=net['month'], y=net['video_cr'], name='Video Sales (₹Cr)',
                                 marker_color='#4ECDC4', opacity=0.85))
        fig.update_layout(title="Monthly Revenue Trend", height=350, barmode='stack',
                         margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation='h', y=1.12),
                         yaxis_title="₹ Crores", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        fig2 = go.Figure()
        if 'clinics_1cx' in net.columns:
            fig2.add_trace(go.Scatter(x=net['month'], y=net['clinics_1cx'], name='New (1Cx)',
                                      mode='lines+markers', line=dict(color='#FF6B35', width=2.5)))
        if 'clinics_rcx' in net.columns:
            fig2.add_trace(go.Scatter(x=net['month'], y=net['clinics_rcx'], name='Repeat (rCx)',
                                      mode='lines+markers', line=dict(color='#4ECDC4', width=2.5)))
        fig2.update_layout(title="Customer Acquisition Trend", height=350,
                          margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation='h', y=1.12),
                          yaxis_title="Customers", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    # Charts Row 2: P&L Overview + Clinic count
    col_a, col_b = st.columns(2)
    
    with col_a:
        pl = data['pl'].copy()
        if len(pl) > 0:
            # Aggregate P&L: FY26 EBITDA distribution
            pl_sorted = pl.sort_values('fy26_ebitda_pct', ascending=True)
            colors = ['#dc3545' if x < 0.20 else '#ffc107' if x < 0.30 else '#28a745' for x in pl_sorted['fy26_ebitda_pct']]
            fig3 = go.Figure(go.Bar(
                y=pl_sorted['area'], x=pl_sorted['fy26_ebitda_pct'] * 100,
                orientation='h', marker_color=colors,
                text=[f"{x:.0f}%" for x in pl_sorted['fy26_ebitda_pct'] * 100],
                textposition='outside'
            ))
            fig3.update_layout(title="FY26 EBITDA % by Clinic", height=max(350, len(pl)*18),
                              margin=dict(l=100, r=40, t=40, b=20),
                              xaxis_title="EBITDA %", yaxis_title="",
                              xaxis=dict(range=[-10, 60]))
            st.plotly_chart(fig3, use_container_width=True)
    
    with col_b:
        # Clinic count growth
        df_cc['month'] = pd.to_datetime(df_cc['month'])
        fig4 = go.Figure(go.Scatter(x=df_cc['month'], y=df_cc['active_clinics'],
                                     mode='lines+markers+text', line=dict(color='#FF6B35', width=3),
                                     text=df_cc['active_clinics'].astype(int),
                                     textposition='top center', textfont=dict(size=9)))
        fig4.update_layout(title="Active Clinic Count Over Time", height=350,
                          margin=dict(l=20, r=20, t=40, b=20),
                          yaxis_title="Clinics", xaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: CLINIC DEEP-DIVE
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    # Clinic selector
    enriched_master = master.copy()
    enriched_master['label'] = enriched_master['area'] + ' (' + enriched_master['city'] + ', ' + enriched_master['tier'] + ')'
    
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        zone_filter = st.selectbox("Filter by Zone", ["All"] + sorted(master['zone'].dropna().unique().tolist()), key='zone_f')
    with col_sel2:
        if zone_filter != "All":
            options = enriched_master[enriched_master['zone'] == zone_filter]['label'].tolist()
        else:
            options = enriched_master['label'].tolist()
        selected_clinic = st.selectbox("Select Clinic", options, key='clinic_sel')
    
    if selected_clinic:
        clinic_area = selected_clinic.split(' (')[0]
        clinic_row = master[master['area'] == clinic_area].iloc[0] if len(master[master['area'] == clinic_area]) > 0 else None
        
        if clinic_row is not None:
            clinic_code = clinic_row['code']
            
            # Clinic header
            st.markdown(f"""<div class="kpi-box">
                <h3>{clinic_row['city']} · {clinic_row['tier']} · {clinic_row['zone']} · {clinic_row['cabins']} cabins · Launched {clinic_row['launch']}</h3>
                <p>{clinic_area} (#{int(clinic_code)})</p>
            </div>""", unsafe_allow_html=True)
            
            # Get clinic data from each dataset
            s_row = sales[sales['code'] == clinic_code]
            cx1_row = data['cx1'][data['cx1']['code'] == clinic_code]
            rcx_row = data['rcx'][data['rcx']['code'] == clinic_code]
            cac_row = data['cac'][data['cac']['code'] == clinic_code]
            ltv_row = data['ltv'][data['ltv']['code'] == clinic_code]
            pl_row = data['pl'][data['pl']['code'] == clinic_code]
            
            # KPI cards
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            
            # Latest month sales
            if len(s_row) > 0:
                latest_sales = s_row[latest_month].values[0] if latest_month in s_row.columns else 0
                l3m_sales = s_row[l3m].mean(axis=1).values[0] if all(m in s_row.columns for m in l3m) else 0
                k1.metric("Latest Sales", fmt_inr(latest_sales * 1e7), f"L3M avg: {fmt_inr(l3m_sales * 1e7)}")
            
            if len(cx1_row) > 0:
                cx1_months = [c for c in cx1_row.columns if c not in ['area','code']]
                latest_1cx = cx1_row[cx1_months[-1]].values[0] if cx1_months else 0
                k2.metric("Latest 1Cx", f"{int(latest_1cx)}")
            
            if len(rcx_row) > 0:
                rcx_months = [c for c in rcx_row.columns if c not in ['area','code']]
                latest_rcx = rcx_row[rcx_months[-1]].values[0] if rcx_months else 0
                k3.metric("Latest rCx", f"{int(latest_rcx)}")
            
            if len(cac_row) > 0:
                cac_months = [c for c in cac_row.columns if c not in ['area','code','city','zone','avg_cac']]
                latest_cac = cac_row[cac_months[-1]].values[0] if cac_months else 0
                k4.metric("Latest CAC", fmt_inr(latest_cac))
            
            if len(ltv_row) > 0:
                ltv_months = [c for c in ltv_row.columns if c not in ['area','code','city','cx_base','ltv_k']]
                latest_ltv = ltv_row[ltv_months[-1]].values[0] if ltv_months else 0
                ltv_k = ltv_row['ltv_k'].values[0] if 'ltv_k' in ltv_row.columns else 0
                k5.metric("Latest LTV", fmt_inr(latest_ltv))
            
            if len(pl_row) > 0:
                ebitda = pl_row['fy26_ebitda_pct'].values[0]
                fy_sales = pl_row['fy26_sales_l'].values[0]
                tag = "tag-green" if ebitda >= 0.30 else "tag-red" if ebitda < 0.15 else "tag-blue"
                k6.metric("FY26 EBITDA %", f"{ebitda*100:.0f}%", f"Sales: {fmt_inr(fy_sales * 1e5)}")
            
            st.markdown("---")
            
            # Charts: Sales + Customers over time
            ch1, ch2 = st.columns(2)
            
            with ch1:
                if len(s_row) > 0:
                    s_data = s_row[month_cols].T.reset_index()
                    s_data.columns = ['month', 'sales_cr']
                    s_data['month'] = pd.to_datetime(s_data['month'])
                    s_data = s_data[s_data['sales_cr'] > 0]
                    fig = go.Figure(go.Bar(x=s_data['month'], y=s_data['sales_cr'],
                                          marker_color='#FF6B35', opacity=0.85))
                    fig.update_layout(title=f"Monthly Sales — {clinic_area}", height=300,
                                    margin=dict(l=20, r=20, t=40, b=20), yaxis_title="₹ Crores")
                    st.plotly_chart(fig, use_container_width=True)
            
            with ch2:
                if len(cx1_row) > 0 and len(rcx_row) > 0:
                    cx1_data = cx1_row[cx1_months].T.reset_index()
                    cx1_data.columns = ['month', '1cx']
                    rcx_data = rcx_row[rcx_months].T.reset_index()
                    rcx_data.columns = ['month', 'rcx']
                    merged = cx1_data.merge(rcx_data, on='month', how='outer').fillna(0)
                    merged['month'] = pd.to_datetime(merged['month'])
                    merged = merged[(merged['1cx'] > 0) | (merged['rcx'] > 0)]
                    
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(x=merged['month'], y=merged['1cx'], name='New (1Cx)',
                                         marker_color='#FF6B35'))
                    fig2.add_trace(go.Bar(x=merged['month'], y=merged['rcx'], name='Repeat (rCx)',
                                         marker_color='#4ECDC4'))
                    fig2.update_layout(title=f"Customers — {clinic_area}", height=300, barmode='stack',
                                      margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Customers",
                                      legend=dict(orientation='h', y=1.12))
                    st.plotly_chart(fig2, use_container_width=True)
            
            # CAC vs LTV chart
            ch3, ch4 = st.columns(2)
            with ch3:
                if len(cac_row) > 0 and len(ltv_row) > 0:
                    cac_data = cac_row[cac_months].T.reset_index()
                    cac_data.columns = ['month', 'cac']
                    ltv_data = ltv_row[ltv_months].T.reset_index()
                    ltv_data.columns = ['month', 'ltv']
                    eco = cac_data.merge(ltv_data, on='month', how='inner')
                    eco['month'] = pd.to_datetime(eco['month'])
                    eco = eco[(eco['cac'] > 0) | (eco['ltv'] > 0)]
                    
                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(x=eco['month'], y=eco['cac'], name='CAC',
                                             mode='lines+markers', line=dict(color='#dc3545', width=2)))
                    fig3.add_trace(go.Scatter(x=eco['month'], y=eco['ltv'], name='LTV',
                                             mode='lines+markers', line=dict(color='#28a745', width=2)))
                    fig3.update_layout(title=f"CAC vs LTV — {clinic_area}", height=300,
                                      margin=dict(l=20, r=20, t=40, b=20), yaxis_title="₹",
                                      legend=dict(orientation='h', y=1.12))
                    st.plotly_chart(fig3, use_container_width=True)
            
            with ch4:
                if len(pl_row) > 0:
                    # Monthly P&L trend
                    pl_months = [c.replace('_sales','') for c in pl_row.columns if c.endswith('_sales') and c != 'fy26_sales_l']
                    pl_months = [m for m in pl_months if m != 'Fy26']
                    if pl_months:
                        pl_trend = pd.DataFrame({
                            'month': pl_months,
                            'sales': [pl_row[f'{m}_sales'].values[0] for m in pl_months],
                            'tacos': [pl_row[f'{m}_tacos'].values[0] for m in pl_months],
                            'ebitda': [pl_row[f'{m}_ebitda'].values[0] * 100 for m in pl_months]
                        })
                        fig4 = make_subplots(specs=[[{"secondary_y": True}]])
                        fig4.add_trace(go.Bar(x=pl_trend['month'], y=pl_trend['sales'], name='Sales (₹L)',
                                             marker_color='#FF6B35', opacity=0.7), secondary_y=False)
                        fig4.add_trace(go.Scatter(x=pl_trend['month'], y=pl_trend['ebitda'], name='EBITDA %',
                                                  mode='lines+markers', line=dict(color='#28a745', width=2.5)),
                                      secondary_y=True)
                        fig4.update_layout(title=f"Monthly P&L — {clinic_area}", height=300,
                                          margin=dict(l=20, r=20, t=40, b=20),
                                          legend=dict(orientation='h', y=1.12))
                        fig4.update_yaxes(title_text="₹ Lakhs", secondary_y=False)
                        fig4.update_yaxes(title_text="EBITDA %", secondary_y=True)
                        st.plotly_chart(fig4, use_container_width=True)

    # ── Clinic comparison table ──
    with st.expander("📋 All Clinics — Performance Table", expanded=False):
        # Build comparison table
        comp = master[['area','code','city','tier','zone','cabins','launch']].copy()
        
        # Add latest sales
        for _, row in comp.iterrows():
            code = row['code']
            s = sales[sales['code'] == code]
            if len(s) > 0 and latest_month in s.columns:
                comp.loc[comp['code'] == code, 'latest_sales_cr'] = s[latest_month].values[0]
                comp.loc[comp['code'] == code, 'l3m_avg_cr'] = s[l3m].mean(axis=1).values[0]
            
            c1 = data['cx1'][data['cx1']['code'] == code]
            cx1_mcols = [c for c in data['cx1'].columns if c not in ['area','code']]
            if len(c1) > 0 and cx1_mcols:
                comp.loc[comp['code'] == code, 'latest_1cx'] = c1[cx1_mcols[-1]].values[0]
            
            p = data['pl'][data['pl']['code'] == code]
            if len(p) > 0:
                comp.loc[comp['code'] == code, 'fy26_ebitda'] = p['fy26_ebitda_pct'].values[0] * 100
        
        comp = comp.sort_values('latest_sales_cr', ascending=False, na_position='last')
        comp['latest_sales_cr'] = comp['latest_sales_cr'].apply(lambda x: f"₹{x:.2f} Cr" if pd.notna(x) else "-")
        comp['l3m_avg_cr'] = comp['l3m_avg_cr'].apply(lambda x: f"₹{x:.2f} Cr" if pd.notna(x) else "-")
        comp['fy26_ebitda'] = comp['fy26_ebitda'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else "-")
        
        st.dataframe(comp.rename(columns={
            'area': 'Clinic', 'code': 'Code', 'city': 'City', 'tier': 'Tier',
            'zone': 'Zone', 'cabins': 'Cabins', 'launch': 'Launch',
            'latest_sales_cr': f'Sales ({latest_month})', 'l3m_avg_cr': 'L3M Avg',
            'latest_1cx': 'Latest 1Cx', 'fy26_ebitda': 'FY26 EBITDA%'
        }), use_container_width=True, height=500)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: EXPANSION ROI
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Clinic Ramp-Up Economics (from actual MIS data)")
    
    # Ramp curve charts
    ramp_s = data['ramp_sales']
    ramp_c = data['ramp_1cx']
    
    rc1, rc2 = st.columns(2)
    with rc1:
        fig_ramp = go.Figure()
        fig_ramp.add_trace(go.Scatter(x=ramp_s['month_num'], y=ramp_s['avg_sales_l'],
                                       mode='lines+markers', name='Avg Sales (₹L)',
                                       line=dict(color='#FF6B35', width=3)))
        fig_ramp.update_layout(title="Average Clinic Sales Ramp (M0→M30)", height=350,
                              margin=dict(l=20, r=20, t=40, b=20),
                              xaxis_title="Month Since Launch", yaxis_title="₹ Lakhs/month")
        # Add breakeven lines
        fig_ramp.add_hline(y=0.31, line_dash="dash", line_color="#dc3545",
                          annotation_text="OpEx Breakeven (₹3.1L)")
        fig_ramp.add_hline(y=0.54, line_dash="dash", line_color="#ffc107",
                          annotation_text="Full Breakeven (₹5.4L incl Capex)")
        st.plotly_chart(fig_ramp, use_container_width=True)
    
    with rc2:
        fig_ramp2 = go.Figure()
        fig_ramp2.add_trace(go.Scatter(x=ramp_c['month_num'], y=ramp_c['avg_1cx'],
                                        mode='lines+markers', name='Avg 1Cx',
                                        line=dict(color='#4ECDC4', width=3)))
        fig_ramp2.update_layout(title="Average New Customer Ramp (M0→M30)", height=350,
                               margin=dict(l=20, r=20, t=40, b=20),
                               xaxis_title="Month Since Launch", yaxis_title="New Customers/month")
        st.plotly_chart(fig_ramp2, use_container_width=True)
    
    st.markdown("---")
    
    # ── Unit Economics Calculator ──
    st.markdown("### New Clinic Investment Calculator")
    
    # Get actual network averages for defaults
    pl_data = data['pl']
    avg_ebitda = pl_data['fy26_ebitda_pct'].mean() if len(pl_data) > 0 else 0.30
    
    # Use actual ramp curve: what month does avg clinic hit breakeven?
    opex_be = ramp_s[ramp_s['avg_sales_l'] >= 0.31]
    full_be = ramp_s[ramp_s['avg_sales_l'] >= 0.54]
    opex_be_month = opex_be.iloc[0]['month_num'] if len(opex_be) > 0 else 'Never'
    full_be_month = full_be.iloc[0]['month_num'] if len(full_be) > 0 else 'Never'
    
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        capex = st.number_input("Capex per Clinic (₹L)", value=28.0, step=1.0, key='capex')
        monthly_opex = st.number_input("Monthly OpEx (₹L)", value=3.1, step=0.1, key='opex')
    with ec2:
        n_new_clinics = st.number_input("New Clinics to Open", value=20, step=5, key='n_new')
        ramp_months = st.number_input("Months to Steady State", value=12, step=1, key='ramp_m')
    with ec3:
        steady_sales_l = st.number_input("Steady-State Monthly Sales (₹L/clinic)", value=round(ramp_s['avg_sales_l'].iloc[-1] * 100) / 100 if len(ramp_s) > 0 else 0.35, step=0.05, key='ss_sales')
        target_ebitda = st.number_input("Target EBITDA %", value=int(avg_ebitda * 100), step=5, key='t_ebitda')
    
    # Projections
    total_capex = capex * n_new_clinics
    monthly_opex_total = monthly_opex * n_new_clinics
    steady_revenue_monthly = steady_sales_l * n_new_clinics  # ₹L per month
    steady_ebitda_monthly = steady_revenue_monthly * (target_ebitda / 100)
    
    # Time to payback
    if steady_ebitda_monthly > 0:
        payback_months = total_capex / steady_ebitda_monthly
    else:
        payback_months = float('inf')
    
    # Year 1 projection using actual ramp curve
    y1_revenue = 0
    for m in range(12):
        if m < len(ramp_s):
            y1_revenue += ramp_s.iloc[m]['avg_sales_l'] * n_new_clinics
        else:
            y1_revenue += steady_sales_l * n_new_clinics
    
    y1_opex = monthly_opex * 12 * n_new_clinics
    y1_ebitda = y1_revenue - y1_opex  # simplified
    
    st.markdown("---")
    
    # Results
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Total Capex", fmt_inr(total_capex * 1e5))
    r2.metric("Year 1 Revenue", fmt_inr(y1_revenue * 1e5))
    r3.metric("OpEx Breakeven", f"M{opex_be_month}" if isinstance(opex_be_month, (int, float)) else opex_be_month)
    r4.metric("Full Breakeven", f"M{full_be_month}" if isinstance(full_be_month, (int, float)) else full_be_month)
    r5.metric("Capex Payback", f"{payback_months:.0f} months" if payback_months < 100 else "N/A")
    
    # 24-month projection chart
    proj_months = list(range(24))
    proj_rev = []
    proj_opex_cum = []
    proj_ebitda_cum = []
    cum_rev = 0
    cum_opex = 0
    for m in proj_months:
        if m < len(ramp_s):
            rev = ramp_s.iloc[m]['avg_sales_l'] * n_new_clinics
        else:
            rev = steady_sales_l * n_new_clinics
        cum_rev += rev
        cum_opex += monthly_opex * n_new_clinics
        proj_rev.append(rev)
        proj_opex_cum.append(cum_opex)
        proj_ebitda_cum.append(cum_rev - cum_opex)
    
    df_proj = pd.DataFrame({'Month': proj_months, 'Monthly Revenue (₹L)': proj_rev,
                            'Cumulative EBITDA (₹L)': proj_ebitda_cum})
    
    fig_proj = make_subplots(specs=[[{"secondary_y": True}]])
    fig_proj.add_trace(go.Bar(x=df_proj['Month'], y=df_proj['Monthly Revenue (₹L)'],
                              name='Monthly Revenue', marker_color='#FF6B35', opacity=0.7), secondary_y=False)
    fig_proj.add_trace(go.Scatter(x=df_proj['Month'], y=df_proj['Cumulative EBITDA (₹L)'],
                                  name='Cum. EBITDA', mode='lines', line=dict(color='#28a745', width=3)),
                      secondary_y=True)
    fig_proj.add_hline(y=total_capex, line_dash="dash", line_color="#dc3545",
                      annotation_text=f"Total Capex (₹{total_capex:.0f}L)", secondary_y=True)
    fig_proj.update_layout(title=f"24-Month Projection — {n_new_clinics} New Clinics", height=400,
                          margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation='h', y=1.12))
    fig_proj.update_yaxes(title_text="₹ Lakhs/month", secondary_y=False)
    fig_proj.update_yaxes(title_text="Cumulative ₹ Lakhs", secondary_y=True)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # ── Network P&L summary ──
    with st.expander("📊 FY26 Network P&L Summary"):
        if len(pl_data) > 0:
            total_fy26_sales = pl_data['fy26_sales_l'].sum()
            total_fy26_tacos = pl_data['fy26_tacos_l'].sum()
            total_fy26_ebitda = total_fy26_sales - total_fy26_tacos
            
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("FY26 Network Sales", fmt_inr(total_fy26_sales * 1e5))
            s2.metric("FY26 TACOS", fmt_inr(total_fy26_tacos * 1e5))
            s3.metric("FY26 EBITDA", fmt_inr(total_fy26_ebitda * 1e5))
            s4.metric("Avg EBITDA %", f"{avg_ebitda*100:.0f}%")
            
            # Tier-wise breakdown
            pl_m = pl_data.merge(master[['code','tier','zone']], on='code', how='left')
            tier_summary = pl_m.groupby('tier').agg(
                clinics=('code', 'count'),
                total_sales=('fy26_sales_l', 'sum'),
                avg_ebitda=('fy26_ebitda_pct', 'mean')
            ).reset_index()
            tier_summary['total_sales'] = tier_summary['total_sales'].apply(lambda x: fmt_inr(x * 1e5))
            tier_summary['avg_ebitda'] = tier_summary['avg_ebitda'].apply(lambda x: f"{x*100:.0f}%")
            st.dataframe(tier_summary.rename(columns={
                'tier': 'Tier', 'clinics': 'Clinics', 'total_sales': 'FY26 Sales', 'avg_ebitda': 'Avg EBITDA%'
            }), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: PINCODE DRILL-DOWN
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Online-to-Offline Demand Mapping")
    
    pin_sub1, pin_sub2 = st.tabs(["🌐 Web Demand by City", "🏥 Clinic Catchment Pincodes"])
    
    with pin_sub1:
        web_city = data['web_city'].copy()
        web_city = web_city[web_city['total_orders'] > 0].sort_values('total_orders', ascending=False)
        
        # Top 30 cities
        top_cities = web_city.head(30)
        
        fig_wc = go.Figure(go.Bar(
            y=top_cities['City'], x=top_cities['total_orders'],
            orientation='h', marker_color='#FF6B35',
            text=top_cities['total_orders'].apply(lambda x: fmt_num(x)),
            textposition='outside'
        ))
        fig_wc.update_layout(title="Top 30 Cities by Web Orders (All-Time)", height=700,
                            margin=dict(l=120, r=60, t=40, b=20),
                            xaxis_title="Total Orders", yaxis_title="",
                            yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig_wc, use_container_width=True)
        
        # Cities with high web demand but no clinic
        clinic_cities = set(master['city'].unique())
        web_city['has_clinic'] = web_city['City'].isin(clinic_cities) | web_city['City'].apply(
            lambda x: any(x.lower() in c.lower() or c.lower() in x.lower() for c in clinic_cities) if pd.notna(x) else False)
        
        whitespace = web_city[~web_city['has_clinic']].head(20)
        if len(whitespace) > 0:
            st.markdown("#### 🎯 High-Demand Cities Without Clinics")
            fig_ws = go.Figure(go.Bar(
                y=whitespace['City'], x=whitespace['total_orders'],
                orientation='h', marker_color='#28a745',
                text=whitespace['total_orders'].apply(lambda x: fmt_num(x)),
                textposition='outside'
            ))
            fig_ws.update_layout(title="Top 20 Unserved Cities by Web Demand", height=500,
                                margin=dict(l=120, r=60, t=40, b=20),
                                xaxis_title="Total Web Orders", yaxis_title="",
                                yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig_ws, use_container_width=True)
        
        # Year-over-year trend
        web_pin = data['web_pin']
        yoy = web_pin.groupby('year')['orders'].sum().reset_index()
        yoy = yoy[yoy['year'] >= 2020]
        fig_yoy = go.Figure(go.Bar(x=yoy['year'].astype(str), y=yoy['orders'],
                                    marker_color='#4ECDC4',
                                    text=yoy['orders'].apply(lambda x: fmt_num(x)),
                                    textposition='outside'))
        fig_yoy.update_layout(title="Web Orders by Year", height=300,
                             margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Orders")
        st.plotly_chart(fig_yoy, use_container_width=True)
    
    with pin_sub2:
        # Clinic-wise pincode catchment
        pin_demand = data['pin_demand']
        pin_ft = data['pin_ft']
        
        clinic_options = sorted(pin_demand['Clinic Loc'].dropna().unique().tolist()) if 'Clinic Loc' in pin_demand.columns else []
        
        if clinic_options:
            sel_clinic_pin = st.selectbox("Select Clinic", clinic_options, key='pin_clinic')
            
            clinic_pins = pin_demand[pin_demand['Clinic Loc'] == sel_clinic_pin].sort_values('qty', ascending=False).head(25)
            
            if len(clinic_pins) > 0:
                c_p1, c_p2 = st.columns([2, 1])
                with c_p1:
                    fig_cp = go.Figure(go.Bar(
                        y=clinic_pins['Zip'].astype(str), x=clinic_pins['qty'],
                        orientation='h', marker_color='#FF6B35',
                        text=clinic_pins['qty'].apply(lambda x: fmt_num(x)),
                        textposition='outside'
                    ))
                    fig_cp.update_layout(title=f"Top 25 Pincodes — {sel_clinic_pin}", height=600,
                                        margin=dict(l=80, r=40, t=40, b=20),
                                        xaxis_title="Quantity", yaxis_title="Pincode",
                                        yaxis=dict(autorange='reversed'))
                    st.plotly_chart(fig_cp, use_container_width=True)
                
                with c_p2:
                    st.markdown("**Top Pincodes**")
                    display_pins = clinic_pins[['Zip', 'City', 'State', 'qty', 'revenue']].copy()
                    display_pins['revenue'] = display_pins['revenue'].apply(lambda x: fmt_inr(x) if pd.notna(x) else '-')
                    display_pins.columns = ['Pincode', 'City', 'State', 'Qty', 'Revenue']
                    st.dataframe(display_pins, use_container_width=True, height=550)
        
        # First-time customer pincodes (cross-clinic)
        with st.expander("📍 All First-Time Customer Pincodes (Top 50)"):
            ft_top = pin_ft.sort_values('Total Quantity', ascending=False).head(50)
            ft_top['Total'] = ft_top['Total'].apply(lambda x: fmt_inr(x) if pd.notna(x) else '-')
            st.dataframe(ft_top.rename(columns={
                'Pincode': 'Pincode', 'Total Quantity': 'First-Time Qty',
                'Total': 'Revenue', 'SubCity': 'Area', 'City': 'City', 'State': 'State'
            }), use_container_width=True, height=500)


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Data: Gynoveda MIS ({month_cols[0]} to {month_cols[-1]}) · {len(master)} clinics · Built Feb 2026")
