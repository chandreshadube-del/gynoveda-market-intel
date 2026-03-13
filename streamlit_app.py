import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Expansion OS", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS FOR METRICS ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.image("https://gynoveda.com/cdn/shop/files/Gynoveda_logo_300x.png", width=180)
st.sidebar.markdown("### ⚙️ Expansion OS")
app_mode = st.sidebar.radio("Select Module:", 
    ["1. Portfolio Health (CapEx ROI)", 
     "2. Funnel Leakage Analytics", 
     "3. Geospatial Network Map", 
     "4. Site Underwriter (AOP)",
     "5. Market Discovery (Next 30 Cities)"]
)

st.sidebar.markdown("---")
st.sidebar.header("Data Filters")
region_filter = st.sidebar.selectbox("Filter Region", ["All India", "West", "North", "South", "East"])

# --- DATA INGESTION (DIRECT FROM VG MIS) ---
@st.cache_data
def load_core_data():
    try:
        # 1. Base Geo-Data (Your 62 Clinics)
        df_geo = pd.read_csv("Clinic latitude longitude.xlsx - Sheet1.csv")
        df_geo = df_geo.rename(columns={"Area": "Clinic", "Latitude": "Lat", "Longitude": "Lon"})
        df_main = df_geo[["Clinic", "City", "Lat", "Lon"]].dropna(subset=["Clinic"])
        
        # 2. Sales & Age (from SalesMTD)
        df_sales = pd.read_csv("Copy of (Vg) Clinic Location - Monthly MIS.xlsx - SalesMTD.csv", header=0)
        df_sales = df_sales.rename(columns={"Area": "Clinic", "All": "Sales_MTD_Lacs"})
        df_main = df_main.merge(df_sales[["Clinic", "Region", "Age", "Sales_MTD_Lacs"]], on="Clinic", how="left")
        
        # 3. EBITDA Margin (from Ebitda Trend)
        df_ebitda = pd.read_csv("Copy of (Vg) Clinic Location - Monthly MIS.xlsx - Ebitda Trend.csv", header=0)
        df_ebitda = df_ebitda.rename(columns={df_ebitda.columns[0]: "Clinic", "Fy26": "EBITDA_Margin_Pct"})
        df_ebitda["EBITDA_Margin_Pct"] = pd.to_numeric(df_ebitda["EBITDA_Margin_Pct"], errors='coerce') * 100
        df_main = df_main.merge(df_ebitda[["Clinic", "EBITDA_Margin_Pct"]], on="Clinic", how="left")
        
        # 4. NTB Show Rate (from NTBShow%)
        df_show = pd.read_csv("Copy of (Vg) Clinic Location - Monthly MIS.xlsx - NTBShow%.csv", header=1)
        df_show = df_show.rename(columns={"Area": "Clinic"})
        show_col = [c for c in df_show.columns if 'All' in c][-1] 
        df_show["NTB_Show_Rate_Pct"] = pd.to_numeric(df_show[show_col], errors='coerce') * 100
        df_main = df_main.merge(df_show[["Clinic", "NTB_Show_Rate_Pct"]], on="Clinic", how="left")
        
        # 5. 1Cx Conversion % (from 1Conv)
        df_conv = pd.read_csv("Copy of (Vg) Clinic Location - Monthly MIS.xlsx - 1Conv.csv", header=0)
        df_conv = df_conv.rename(columns={"Area": "Clinic", "All": "Conversion_1Cx_Pct"})
        df_conv["Conversion_1Cx_Pct"] = pd.to_numeric(df_conv["Conversion_1Cx_Pct"], errors='coerce') * 100
        df_main = df_main.merge(df_conv[["Clinic", "Conversion_1Cx_Pct"]], on="Clinic", how="left")
        
        # 6. Absolute Appointments (Last 12 Months Avg)
        df_appt = pd.read_csv("Copy of (Vg) Clinic Location - Monthly MIS.xlsx - NTBAppointment.csv", header=1)
        df_appt = df_appt.rename(columns={"Area": "Clinic"})
        date_cols = [c for c in df_appt.columns if '202' in str(c)]
        last_12_dates = date_cols[-12:] if len(date_cols) >= 12 else date_cols
        df_appt[last_12_dates] = df_appt[last_12_dates].apply(pd.to_numeric, errors='coerce')
        df_appt["Avg_Monthly_Appointments"] = df_appt[last_12_dates].mean(axis=1)
        df_main = df_main.merge(df_appt[["Clinic", "Avg_Monthly_Appointments"]], on="Clinic", how="left")
        
        # 7. Absolute 1Cx Conversions (Unique Customer IDs / 12 Months)
        df_1cx = pd.read_csv("First Time customer - Clinic ( 2023 to 2025).csv")
        df_1cx['Date'] = pd.to_datetime(df_1cx['Date'], errors='coerce', dayfirst=True)
        max_date = df_1cx['Date'].max()
        if pd.notnull(max_date):
            cutoff_date = max_date - pd.DateOffset(months=12)
            df_1cx = df_1cx[df_1cx['Date'] >= cutoff_date]
        df_1cx_grp = df_1cx.groupby("Clinic Loc")["Customer ID"].nunique().reset_index()
        df_1cx_grp = df_1cx_grp.rename(columns={"Clinic Loc": "Clinic", "Customer ID": "Avg_Monthly_1Cx"})
        df_1cx_grp["Avg_Monthly_1Cx"] = df_1cx_grp["Avg_Monthly_1Cx"] / 12
        df_main = df_main.merge(df_1cx_grp[["Clinic", "Avg_Monthly_1Cx"]], on="Clinic", how="left")
        
        # 8. Calculate Absolute Shows
        df_main["Avg_Monthly_Shows"] = df_main["Avg_Monthly_Appointments"] * (df_main["NTB_Show_Rate_Pct"] / 100)

        # Format and Clean the Stitched Data
        df_main = df_main.rename(columns={"Age": "Age_Months"})
        df_main = df_main.fillna(0)
        
        numeric_cols = ["Sales_MTD_Lacs", "Age_Months", "NTB_Show_Rate_Pct", "Conversion_1Cx_Pct", 
                        "EBITDA_Margin_Pct", "Avg_Monthly_Appointments", "Avg_Monthly_Shows", "Avg_Monthly_1Cx"]
        for col in numeric_cols:
            df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)
            
        return df_main[df_main["Lat"] != 0]
        
    except Exception as e:
        st.error(f"🚨 Data Pipeline Error: Ensure all CSV files are uploaded exactly as named. Details: {e}")
        return pd.DataFrame()

@st.cache_data
def load_predictive_data():
    try:
        df_web = pd.read_csv("First Time customer - website  (2020 - 2025).csv")
        df_web['Total'] = pd.to_numeric(df_web['Total'], errors='coerce').fillna(0)
        
        df_pred = df_web.groupby(["City", "State"]).agg(
            Online_1Cx_Volume=("Customer ID", "nunique"),
            Est_Online_Revenue_Lacs=("Total", lambda x: x.sum() / 100000)
        ).reset_index()
        
        df_pred = df_pred.sort_values(by="Est_Online_Revenue_Lacs", ascending=False).head(30)
        return df_pred
        
    except Exception as e:
        st.error(f"🚨 Website D2C Data Error: {e}")
        return pd.DataFrame()

df_main = load_core_data()
df_predictive = load_predictive_data()

# Apply Sidebar Filter to Main Data
if not df_main.empty and region_filter != "All India":
    df_main = df_main[df_main["Region"].astype(str).str.contains(region_filter, case=False, na=False)]

# --- MODULE 1: PORTFOLIO HEALTH ---
if app_mode == "1. Portfolio Health (CapEx ROI)":
    st.title("📊 Portfolio Health & Capital Allocation")
    st.markdown("Track which locations are scaling profitably and which are burning cash.")
    
    if df_main.empty:
        st.warning("Data not loaded. Check the MIS files in your repository.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Active Clinics", len(df_main))
        col2.metric("Avg Network EBITDA", f"{df_main['EBITDA_Margin_Pct'].mean():.1f}%")
        col3.metric("Top Performer", df_main.loc[df_main['EBITDA_Margin_Pct'].idxmax()]['Clinic'])
        col4.metric("Bleeding Locations", len(df_main[df_main['EBITDA_Margin_Pct'] < 10]))
        
        st.divider()
        
        st.subheader("The Scale vs. Profitability Matrix")
        fig = px.scatter(
            df_main, 
            x="Age_Months", 
            y="EBITDA_Margin_Pct", 
            size="Sales_MTD_Lacs",
            color="EBITDA_Margin_Pct",
            text="Clinic",
            color_continuous_scale="RdYlGn",
            labels={"Age_Months": "Clinic Age (Months)", "EBITDA_Margin_Pct": "EBITDA Margin (%)"},
            height=600
        )
        fig.add_hline(y=15, line_dash="dash", line_color="gray", annotation_text="Target Margin (15%)")
        fig.add_vline(x=12, line_dash="dash", line_color="gray", annotation_text="1-Year Maturity Line")
        fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: FUNNEL LEAKAGE ---
elif app_mode == "2. Funnel Leakage Analytics":
    st.title("🔻 Patient Acquisition Funnel (Absolute Numbers)")
    st.markdown("Visualizing the exact patient volume drop-off (Monthly Averages over the Last 12 Months).")
    
    if not df_main.empty:
        # Sort by most appointments to make the chart readable
        df_funnel = df_main.sort_values(by="Avg_Monthly_Appointments", ascending=False)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_funnel['Clinic'], y=df_funnel['Avg_Monthly_Appointments'], name='Appointments', marker_color='#1f77b4'))
        fig2.add_trace(go.Bar(x=df_funnel['Clinic'], y=df_funnel['Avg_Monthly_Shows'], name='Shows (Walk-ins)', marker_color='#ff7f0e'))
        fig2.add_trace(go.Bar(x=df_funnel['Clinic'], y=df_funnel['Avg_Monthly_1Cx'], name='1Cx Conversions', marker_color='#2ca02c'))
        
        fig2.update_layout(barmode='group', height=500, xaxis_title="Clinic Location", yaxis_title="Average Patients / Month")
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("🚨 Priority Action Required")
        # Identify clinics where the drop off from Appointment to Show is massive in absolute numbers (>100 lost patients/month)
        df_main["Lost_Pre_Visit"] = df_main["Avg_Monthly_Appointments"] - df_main["Avg_Monthly_Shows"]
        high_dropoff = df_main[df_main["Lost_Pre_Visit"] > 100].sort_values(by="Lost_Pre_Visit", ascending=False)
        
        if not high_dropoff.empty:
            st.error("**Massive Pre-Visit Friction:** The following clinics are losing over 100 booked patients per month before they even arrive. Fix the physical access or the reminder call process immediately.")
            st.dataframe(high_dropoff[['Clinic', 'Region', 'Avg_Monthly_Appointments', 'Avg_Monthly_Shows', 'Lost_Pre_Visit']].style.format({"Avg_Monthly_Appointments": "{:.0f}", "Avg_Monthly_Shows": "{:.0f}", "Lost_Pre_Visit": "{:.0f}"}), hide_index=True)

# --- MODULE 3: GEOSPATIAL NETWORK MAP ---
elif app_mode == "3. Geospatial Network Map":
    st.title("🗺️ Pan-India Footprint")
    st.markdown("Visualize current clinic locations and performance.")
    
    if not df_main.empty:
        fig3 = px.scatter_mapbox(
            df_main, 
            lat="Lat", 
            lon="Lon", 
            hover_name="Clinic", 
            hover_data=["Sales_MTD_Lacs", "EBITDA_Margin_Pct"],
            color="EBITDA_Margin_Pct",
            color_continuous_scale="RdYlGn",
            size="Sales_MTD_Lacs",
            zoom=3.5, 
            height=600,
            center={"lat": 20.5937, "lon": 78.9629} 
        )
        fig3.update_layout(mapbox_style="carto-positron")
        st.plotly_chart(fig3, use_container_width=True)

# --- MODULE 4: SITE UNDERWRITER ---
elif app_mode == "4. Site Underwriter (AOP)":
    st.title("🏗️ Expansion Site Underwriter")
    st.markdown("Calculate break-even and patient targets before approving a commercial lease.")
    
    st.info("Input the variables negotiated by the real estate team below:")
    
    c1, c2, c3, c4 = st.columns(4)
    rent = c1.number_input("Monthly Rent Quote (₹)", value=150000, step=10000)
    capex = c2.number_input("Fit-out CapEx (₹)", value=2800000, step=100000)
    deposit_months = c3.number_input("Deposit (Months)", value=6)
    ticket_size = c4.number_input("Est. Ticket Size (₹)", value=22000)
    
    day_zero_cash = capex + (rent * deposit_months)
    required_revenue = rent / 0.12 
    required_patients = required_revenue / ticket_size
    
    st.markdown("### 📋 Underwriting Results")
    res1, res2, res3 = st.columns(3)
    res1.metric("Day-Zero Cash Burn", f"₹ {day_zero_cash:,.0f}")
    res2.metric("Target Monthly Revenue", f"₹ {required_revenue/100000:,.1f} Lacs", help="To maintain 12% rent ratio")
    res3.metric("Required New Patients / Month", f"{required_patients:,.0f} Patients")
    
    st.divider()
    st.markdown("#### 🎯 Execution Reality Check")
    st.write(f"To hit **{required_patients:,.0f} patients**, assuming the network average Show Rate of **38%** and Conversion of **75%**:")
    
    req_shows = required_patients / 0.75
    req_appts = req_shows / 0.38
    
    st.warning(f"Marketing must generate **{req_appts:,.0f} Appointments** per month for this specific pin code to survive the ₹{rent:,.0f} rent block.")

# --- MODULE 5: MARKET DISCOVERY ---
elif app_mode == "5. Market Discovery (Next 30 Cities)":
    st.title("🎯 Predictive Expansion Engine")
    st.markdown("Ranking the next high-potential target cities based on historical D2C online demand.")
    
    if not df_predictive.empty:
        st.subheader("Top White-Space Markets (Zero-CAC Potential)")
        
        st.dataframe(
            df_predictive.style.background_gradient(subset=['Est_Online_Revenue_Lacs'], cmap='Greens'),
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        st.markdown("### 🛠️ The Expansion Playbook")
        
        top_city = df_predictive.iloc[0]['City']
        top_rev = df_predictive.iloc[0]['Est_Online_Revenue_Lacs']
        
        st.success(f"**Top Recommendation: {top_city}** \n\n With ₹{top_rev:,.1f} Lacs in existing online demand, opening a clinic here allows us to immediately retarget these buyers to drive day-one clinic walk-ins, drastically compressing the CapEx payback period.")
    else:
        st.warning("Predictive data not loaded. Check the 'First Time customer - website' CSV file.")
