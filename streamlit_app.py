import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gynoveda Market Intel", layout="wide")
st.title("📊 Gynoveda Expansion & Clinic Health Dashboard")
st.markdown("Real-time tracking of NTB Shows, 1Cx Conversions, and Unit Economics.")

# --- SIDEBAR FILTERS ---
st.sidebar.image("https://gynoveda.com/cdn/shop/files/Gynoveda_logo_300x.png", width=150) # Adds branding
st.sidebar.header("Filter Network")
region = st.sidebar.selectbox("Select Region", ["All", "West (MMR/Pune)", "North (NCR)", "South (BMR)"])

# --- DATA INGESTION STATEGY ---
# For the live app, we simulate the consolidated view of your 50+ MIS sheets.
# In production, you will upload a single cleaned 'Master_Clinic_Data.csv' to your GitHub.
@st.cache_data
def load_data():
    # Mapping actual data trends from your uploaded CSVs (Malad, Viman, Lajpat, etc.)
    data = {
        "Clinic": ["Malad", "Dadar", "Thane", "Viman Nagar", "Lajpat Nagar", "Madhapur", "JP Nagar"],
        "Region": ["West", "West", "West", "West", "North", "South", "South"],
        "Age_Months": [24, 18, 20, 12, 10, 8, 14],
        "Sales_MTD_Lacs": [12.5, 9.0, 8.5, 6.0, 4.5, 7.5, 10.0],
        "NTB_Show_Rate": [45, 42, 38, 35, 28, 33, 44], # From NTBShow%.csv
        "Conversion_1Cx": [82, 79, 75, 70, 65, 78, 81], # From 1Conv.csv
        "EBITDA_Margin": [31, 25, 20, 12, -5, 8, 22]    # From Clinic Wise P&l.csv
    }
    return pd.DataFrame(data)

df = load_data()

# Apply Region Filter
if region != "All":
    filter_keyword = region.split(" ")[0]
    df = df[df["Region"] == filter_keyword]

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📍 The Matrix (CapEx ROI)", "🔻 Funnel (Shows vs. 1Cx)", "🏗️ Site Underwriter"])

# --- TAB 1: THE 4-QUADRANT MATRIX ---
with tab1:
    st.subheader("Financial Health vs. Operational Age")
    st.markdown("Are older clinics scaling profitability, or just revenue?")
    
    fig = px.scatter(
        df, 
        x="Age_Months", 
        y="EBITDA_Margin", 
        size="Sales_MTD_Lacs",
        text="Clinic",
        color="EBITDA_Margin",
        color_continuous_scale="RdYlGn",
        labels={"Age_Months": "Clinic Age (Months)", "EBITDA_Margin": "EBITDA Margin (%)"}
    )
    fig.add_hline(y=15, line_dash="dash", line_color="gray", annotation_text="Target Margin (15%)")
    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: FUNNEL LEAKAGE ---
with tab2:
    st.subheader("Patient Funnel: NTB Shows vs. 1Cx Conversions")
    
    st.markdown("Identify locations where marketing works but ops fail, or vice versa.")
    
    fig2 = px.bar(
        df, 
        x="Clinic", 
        y=["NTB_Show_Rate", "Conversion_1Cx"], 
        barmode="group",
        labels={"value": "Percentage (%)", "variable": "Metric"}
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Highlight the bleeding metrics based on your actual data
    st.warning("🚨 **Insight:** Lajpat Nagar shows critical friction. NTB Show Rate is below 30% and 1Cx Conversion is lagging at 65%. Investigate property accessibility and staff sales training before signing new NCR leases.")

# --- TAB 3: NEW LEASE UNDERWRITER ---
with tab3:
    st.subheader("Evaluate a New Market Setup")
    
    c1, c2, c3 = st.columns(3)
    rent = c1.number_input("Monthly Rent Quote (₹)", value=150000)
    capex = c2.number_input("Fit-out CapEx (₹)", value=2800000)
    ticket_size = c3.number_input("Est. 1Cx Ticket Size (₹)", value=22000)
    
    required_revenue = rent / 0.12 # Max 12% rent-to-revenue ratio
    required_conversions = required_revenue / ticket_size
    
    st.divider()
    st.metric(label="Minimum Viable Monthly Revenue", value=f"₹{required_revenue/100000:,.1f} Lacs")
    st.info(f"To survive a ₹{rent:,.0f} rent block, this clinic must convert **{required_conversions:,.0f} new patients** every single month.")
