import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="CEO Office: Expansion OS", layout="wide", initial_sidebar_state="expanded")

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

# --- DATA INGESTION ---
@st.cache_data
def load_core_data():
    # Master Clinic Offline Data
    df = pd.DataFrame({
        "Clinic": ["Malad", "Viman Nagar", "Lajpat Nagar", "Thane", "JP Nagar", "Madhapur", "Dadar"],
        "Region": ["West", "West", "North", "West", "South", "South", "West"],
        "Launch_Date": ["2023-10-23", "2024-04-01", "2024-06-01", "2024-07-06", "2024-07-27", "2024-10-12", "2024-08-31"],
        "Age_Months": [24, 18, 16, 15, 14, 11, 13],
        "Sales_MTD_Lacs": [12.5, 8.5, 4.5, 8.0, 10.0, 7.5, 9.0],
        "NTB_Show_Rate_Pct": [45, 38, 28, 42, 44, 33, 41],
        "Conversion_1Cx_Pct": [82, 75, 65, 78, 81, 78, 79],
        "EBITDA_Margin_Pct": [31, 15, -5, 20, 22, 8, 25],
        "Lat": [19.17485, 18.56257, 28.57172, 19.19119, 12.91218, 17.44127, 19.01716],
        "Lon": [72.84565, 73.91418, 77.23772, 72.96812, 77.62161, 78.39657, 72.83559]
    })
    return df

@st.cache_data
def load_predictive_data():
    # Website D2C Data Aggregated
    df_web = pd.DataFrame({
        "Rank": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "City": ["Lucknow", "Patna", "Surat", "Indore", "Jaipur", "Bhopal", "Ludhiana", "Guwahati", "Kochi", "Nagpur"],
        "State": ["UP", "Bihar", "Gujarat", "MP", "Rajasthan", "MP", "Punjab", "Assam", "Kerala", "Maharashtra"],
        "Online_1Cx_Volume": [4250, 3890, 3400, 3100, 2950, 2600, 2400, 2100, 1950, 1800],
        "Est_Online_Revenue_Lacs": [85.0, 77.8, 68.0, 62.0, 59.0, 52.0, 48.0, 42.0, 39.0, 36.0]
    })
    return df_web

df_main = load_core_data()
df_predictive = load_predictive_data()

# Apply Sidebar Filter to Main Data
if region_filter != "All India":
    df_main = df_main[df_main["Region"] == region_filter]

# --- MODULE 1: PORTFOLIO HEALTH ---
if app_mode == "1. Portfolio Health (CapEx ROI)":
    st.title("📊 Portfolio Health & Capital Allocation")
    st.markdown("Track which locations are scaling profitably and which are burning cash.")
    
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
    st.title("🔻 Patient Acquisition Funnel")
    st.markdown("Identify operational friction from Appointment → Show → Conversion.")
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df_main['Clinic'], y=df_main['NTB_Show_Rate_Pct'], name='Show Rate (%)', marker_color='#1f77b4'))
    fig2.add_trace(go.Bar(x=df_main['Clinic'], y=df_main['Conversion_1Cx_Pct'], name='1Cx Conversion (%)', marker_color='#2ca02c'))
    
    fig2.update_layout(barmode='group', height=500, xaxis_title="Clinic Location", yaxis_title="Percentage (%)")
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("🚨 Priority Action Required")
    low_show = df_main[df_main['NTB_Show_Rate_Pct'] < 35]
    if not low_show.empty:
        st.error("**Pre-Visit Friction:** The following clinics have severe drop-offs before the patient even arrives. Audit parking, visibility, and reminder calls.")
        st.dataframe(low_show[['Clinic', 'Region', 'NTB_Show_Rate_Pct', 'Conversion_1Cx_Pct']], hide_index=True)

# --- MODULE 3: GEOSPATIAL NETWORK MAP ---
elif app_mode == "3. Geospatial Network Map":
    st.title("🗺️ Pan-India Footprint")
    st.markdown("Visualize current clinic locations and performance.")
    
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
    
    st.success(f"**Top Recommendation: {top_city}** \n\n With ₹{top_rev} Lacs in existing online demand, opening a clinic here allows us to immediately retarget these buyers to drive day-one clinic walk-ins, drastically compressing the CapEx payback period.")
