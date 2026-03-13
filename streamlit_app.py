"""
Gynoveda Expansion Intelligence OS
FINAL MASTER VERSION - 5-Second Readability & Logical Math
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import math

st.set_page_config(page_title="Gynoveda Expansion OS", layout="wide", page_icon="◉")

DATA_DIR = "mis_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------
# COLUMN AUTO STANDARDIZER
# ---------------------------------------------------

def standardize_columns(df):
    df.columns = df.columns.str.strip()
    rename_map = {}
    for col in df.columns:
        c = str(col).lower()
        if "city" in c and "sub" not in c:
            rename_map[col] = "City"
        elif "sub" in c and "city" in c:
            rename_map[col] = "SubCity"
        elif "zip" in c or "pin" in c:
            rename_map[col] = "Zip"
        elif "lat" in c:
            rename_map[col] = "Latitude"
        elif "lon" in c or "lng" in c or "long" in c:
            rename_map[col] = "Longitude"
        elif "pop" in c:
            rename_map[col] = "Population"
        elif "customer" in c and "id" in c:
            rename_map[col] = "Customer ID"
    
    df = df.rename(columns=rename_map)
    return df

# ---------------------------------------------------
# UTILITIES
# ---------------------------------------------------

def fmt_inr(v):
    if pd.isna(v): return "₹0"
    if v >= 1e7: return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5: return f"₹{v/1e5:.1f} L"
    return f"₹{v:,.0f}"

def normalize_matrix(X):
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std[std == 0] = 1
    return (X - mean) / std

def cosine_similarity_matrix(A, B):
    A = A / np.linalg.norm(A, axis=1, keepdims=True)
    B = B / np.linalg.norm(B, axis=1, keepdims=True)
    return np.dot(A, B.T)

# ---------------------------------------------------
# DATA LOADER
# ---------------------------------------------------

@st.cache_data(show_spinner=False)
def load_all():
    def safe(file):
        path = f"{DATA_DIR}/{file}"
        if os.path.exists(path):
            try:
                return standardize_columns(pd.read_csv(path))
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    return {
        "web": safe("std_demand_web.csv"),
        "clinic": safe("std_demand_clinic.csv"),
        "clinics": safe("std_clinics.csv"),
        "ivf": safe("std_ivf_comp.csv"),
        "pin": safe("std_pin_geo.csv"),
        "population": safe("std_population.csv")
    }

data = load_all()

# ---------------------------------------------------
# SIDEBAR UPLOAD
# ---------------------------------------------------

with st.sidebar:
    st.markdown("### 📂 Upload Data")
    st.caption("Drop raw files here. The engine auto-cleans headers.")
    files = st.file_uploader("Upload CSV/Excel", accept_multiple_files=True)

    if files and st.button("Process Files", type="primary", use_container_width=True):
        for f in files:
            name = f.name.lower()
            if "ivf" in name: target = "std_ivf_comp.csv"
            elif "clinic" in name and "first time" in name: target = "std_demand_clinic.csv"
            elif "web" in name and "first time" in name: target = "std_demand_web.csv"
            elif "pin" in name or "geo" in name: target = "std_pin_geo.csv"
            elif "pop" in name or "demographic" in name: target = "std_population.csv"
            elif "lat" in name or "lon" in name: target = "std_clinics.csv"
            else: target = f"std_{f.name.lower()}.csv"

            try:
                if name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(f)
                else:
                    df = pd.read_csv(f)
                df = standardize_columns(df)
                df.to_csv(f"{DATA_DIR}/{target}", index=False)
            except Exception as e:
                st.error(f"Failed to process {f.name}")
        
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

st.title("Gynoveda Expansion Intelligence OS")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏥 Network Health",
    "📍 Whitespace Expansion",
    "🧠 Site Simulator (O2O)",
    "💰 Phased Capital Planner"
])

# ===================================================
# 1. NETWORK HEALTH
# ===================================================

with tab1:
    web, clinic, ivf, clinics = data["web"], data["clinic"], data["ivf"], data["clinics"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Clinics", len(clinics) if not clinics.empty else 0)
    c2.metric("Clinic Patients", clinic["Customer ID"].nunique() if not clinic.empty and "Customer ID" in clinic else 0)
    c3.metric("Digital Patients", web["Customer ID"].nunique() if not web.empty and "Customer ID" in web else 0)
    c4.metric("IVF Competitors", len(ivf) if not ivf.empty else 0)

    if not web.empty and "City" in web.columns:
        demand = web.groupby("City")["Customer ID"].nunique().reset_index()
        fig = px.bar(
            demand.sort_values("Customer ID", ascending=False).head(10),
            x="City", y="Customer ID", title="Top Digital Demand Cities",
            color_discrete_sequence=['#c0392b']
        )
        st.plotly_chart(fig, use_container_width=True)

# ===================================================
# 2. EXPANSION OPPORTUNITIES
# ===================================================

with tab2:
    if web.empty:
        st.warning("Upload Web Demand data to view expansion whitespace.")
    else:
        # Groupings
        web_city = web.groupby("City").agg(WebPatients=("Customer ID", "nunique")).reset_index() if "City" in web.columns else pd.DataFrame(columns=["City", "WebPatients"])
        clinic_city = clinic.groupby("City").agg(ClinicPatients=("Customer ID", "nunique")).reset_index() if not clinic.empty and "City" in clinic.columns else pd.DataFrame(columns=["City", "ClinicPatients"])
        ivf_city = ivf.groupby("City").size().reset_index(name="IVF") if not ivf.empty and "City" in ivf.columns else pd.DataFrame(columns=["City", "IVF"])

        df = web_city.merge(clinic_city, on="City", how="left").merge(ivf_city, on="City", how="left").fillna(0)
        clinic_cities = set(clinics["City"].dropna()) if not clinics.empty and "City" in clinics.columns else set()

        served = df[df["City"].isin(clinic_cities)].copy()
        unserved = df[~df["City"].isin(clinic_cities)].copy()
        unserved = unserved[unserved["WebPatients"] > 0] # Remove dead cities

        if not served.empty and not unserved.empty:
            # AI Similarity
            served_matrix = normalize_matrix(served[["WebPatients", "IVF"]].fillna(0).values)
            unserved_matrix = normalize_matrix(unserved[["WebPatients", "IVF"]].fillna(0).values)
            similarity = cosine_similarity_matrix(unserved_matrix, served_matrix)
            
            unserved["SimilarCity"] = served.iloc[similarity.argmax(axis=1)]["City"].values
            unserved["MatchScore"] = similarity.max(axis=1) * 100

            st.markdown("### AI Whitespace Candidates")
            st.caption("Cities where we have NO clinics, ranked by digital demand and demographic similarity to successful existing markets.")
            st.dataframe(
                unserved.sort_values("WebPatients", ascending=False)[["City", "WebPatients", "IVF", "SimilarCity", "MatchScore"]].head(15).style.format({"MatchScore": "{:.1f}%", "WebPatients": "{:,.0f}"}),
                hide_index=True, use_container_width=True
            )

            city = st.selectbox("Select Unserved City to Map Hotspots", unserved.sort_values("WebPatients", ascending=False)["City"].head(20))
            city_web = web[web["City"] == city]

            # Map
            if not city_web.empty and not data["pin"].empty and "Zip" in city_web.columns and "Zip" in data["pin"].columns:
                pins = city_web.groupby("Zip")["Customer ID"].nunique().reset_index()
                pins["Zip"] = pd.to_numeric(pins["Zip"], errors='coerce')
                
                pin_geo = data["pin"].copy()
                pin_geo["Zip"] = pd.to_numeric(pin_geo["Zip"], errors='coerce')
                
                mapdf = pins.merge(pin_geo, on="Zip", how="inner")

                if not mapdf.empty:
                    fig = px.scatter_mapbox(
                        mapdf, lat="Latitude", lon="Longitude", size="Customer ID", color="Customer ID",
                        color_continuous_scale="OrRd", zoom=10, title=f"Digital Heatmap: {city}"
                    )
                    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0})
                    st.plotly_chart(fig, use_container_width=True)

# ===================================================
# 3. SITE SIMULATOR (SMOOTHED O2O)
# ===================================================

with tab3:
    if data["web"].empty or data["clinic"].empty:
        st.warning("Upload both Clinic and Web Demand data to unlock the Simulator.")
    else:
        st.markdown("### 🧠 Predictive O2O Revenue Engine")
        
        # 1. Build Reference Multipliers (City Level to ensure data density)
        web_city_ref = data["web"].groupby("City").agg(WebRev=("Total", "sum"), WebPts=("Customer ID", "nunique")).reset_index()
        clin_city_ref = data["clinic"].groupby("City").agg(ClinRev=("Total", "sum")).reset_index()
        
        # Assume 60 months of web data, calculate Monthly averages
        web_city_ref["Mo_WebRev"] = web_city_ref["WebRev"] / 60
        web_city_ref["Mo_WebPts"] = web_city_ref["WebPts"] / 60
        
        # Assume 12 months avg active clinic time for simple modeling
        clin_city_ref["Mo_ClinRev"] = clin_city_ref["ClinRev"] / 12
        
        ref_df = pd.merge(web_city_ref, clin_city_ref, on="City", how="inner")
        ref_df = ref_df[(ref_df["Mo_WebRev"] > 0) & (ref_df["Mo_ClinRev"] > 0)]
        ref_df["Multiplier"] = ref_df["Mo_ClinRev"] / ref_df["Mo_WebRev"]
        
        # MATH LOGIC: Cap outliers safely at 50X
        ref_df = ref_df[ref_df["Multiplier"] <= 50].copy()
        
        # 2. Get Unserved Pincodes
        web_pins = data["web"].groupby("Zip").agg(WebRev=("Total", "sum"), WebPts=("Customer ID", "nunique"), City=("City", "first")).reset_index()
        web_pins["Mo_WebRev"] = web_pins["WebRev"] / 60
        web_pins["Mo_WebPts"] = web_pins["WebPts"] / 60
        
        active_cities = set(ref_df["City"].unique())
        unserved_pins = web_pins[~web_pins["City"].isin(active_cities)].copy()
        unserved_pins = unserved_pins[unserved_pins["Mo_WebPts"] > 0.5].sort_values("Mo_WebPts", ascending=False)
        
        if not unserved_pins.empty and not ref_df.empty:
            pin_sel = st.selectbox("Select Target Pincode", unserved_pins["Zip"].astype(int).astype(str))
            target_pin = unserved_pins[unserved_pins["Zip"] == int(pin_sel)].iloc[0]
            
            # MATH LOGIC: Blended K-Nearest Neighbors
            diffs = np.abs(ref_df["Mo_WebPts"] - target_pin["Mo_WebPts"])
            closest_3 = ref_df.loc[diffs.nsmallest(3).index]
            blended_multiplier = closest_3["Multiplier"].mean()
            matched_cities = ", ".join(closest_3["City"].tolist())
            
            proj_rev = target_pin["Mo_WebRev"] * blended_multiplier

            # Easy 5-second read
            st.info(f"💡 **The Math:** Because this pincode has **{target_pin['Mo_WebPts']:.1f} digital patients/mo**, it mathematically behaves like our clinics in **{matched_cities}**. We applied their blended historical conversion multiplier of **{blended_multiplier:.1f}X**.")

            c1, c2, c3 = st.columns(3)
            c1.metric("Local Web Rev / mo", fmt_inr(target_pin["Mo_WebRev"]))
            c2.metric("Look-Alike Multiplier", f"{blended_multiplier:.1f}X", "Based on 3 closest cities")
            c3.metric("Projected Offline Rev / mo", fmt_inr(proj_rev), "Target TAM")

            fig = go.Figure(go.Waterfall(
                measure=["absolute", "relative", "total"],
                x=["Current Digital Demand", "O2O Physical Trust Uplift", "Mature Clinic Output"],
                y=[target_pin["Mo_WebRev"], proj_rev - target_pin["Mo_WebRev"], proj_rev],
                text=[fmt_inr(target_pin["Mo_WebRev"]), f"+{fmt_inr(proj_rev - target_pin['Mo_WebRev'])}", fmt_inr(proj_rev)],
                textposition="outside",
                connector={"line":{"color":"rgb(63, 63, 63)"}},
                decreasing={"marker":{"color":"#ef4444"}},
                increasing={"marker":{"color":"#3b82f6"}},
                totals={"marker":{"color":"#10b981"}}
            ))
            fig.update_layout(title=f"Revenue Conversion Architecture for {pin_sel}", margin=dict(t=40, b=20), height=350)
            st.plotly_chart(fig, use_container_width=True)

# ===================================================
# 4. CAPITAL PLANNER (PHASED STAGGER)
# ===================================================

with tab4:
    st.markdown("### 💰 Phased Capital Rollout Model")
    st.caption("A mathematically logical J-Curve based on staggered clinic launches. Launching slowly protects cash flow.")

    col_ctrl, col_chart = st.columns([1, 2.5])
    
    with col_ctrl:
        st.markdown("#### Expansion Controls")
        total_clinics = st.slider("Total Clinics to Build", 1, 50, 12)
        rollout_months = st.slider("Rollout Speed (Months)", 1, 12, 6, help="How many months it will take to launch all clinics.")
        
        st.markdown("#### Unit Economics (Lacs)")
        capex = st.number_input("CapEx per Clinic (L)", value=28.0, step=1.0)
        opex = st.number_input("OpEx per Clinic/mo (L)", value=3.0, step=0.5)
        revenue = st.number_input("Mature Rev per Clinic/mo (L)", value=15.0, step=1.0)

    with col_chart:
        # MATH LOGIC: Dynamic Array Staggering
        proj_timeline = 24 # 2-year view
        
        # Calculate how many clinics launch each month
        clinics_per_month = [0] * proj_timeline
        base_rate = total_clinics // rollout_months
        remainder = total_clinics % rollout_months
        
        for i in range(rollout_months):
            clinics_per_month[i] = base_rate + (1 if i < remainder else 0)

        total_rev_arr = np.zeros(proj_timeline)
        total_opex_arr = np.zeros(proj_timeline)
        total_capex_arr = np.zeros(proj_timeline)
        active_clinics_arr = np.zeros(proj_timeline)
        
        ramp_multipliers = np.array([min(1.0, m/6) for m in range(proj_timeline)]) # 6 month ramp to maturity

        for t in range(proj_timeline):
            total_capex_arr[t] = clinics_per_month[t] * capex
            active_clinics_arr[t] = np.sum(clinics_per_month[:t+1])
            total_opex_arr[t] = active_clinics_arr[t] * opex
            
            # Sum revenue for all cohorts that have launched
            for i in range(t+1):
                if clinics_per_month[i] > 0:
                    age = t - i
                    total_rev_arr[t] += clinics_per_month[i] * revenue * ramp_multipliers[age]
                    
        net_cashflow_arr = (total_rev_arr - total_opex_arr) - total_capex_arr
        cum_cashflow_arr = np.cumsum(net_cashflow_arr)
        max_burn = np.min(cum_cashflow_arr)
        
        # KPIs
        rm1, rm2, rm3 = st.columns(3)
        rm1.metric("Total CapEx Required", fmt_inr(np.sum(total_capex_arr) * 1e5))
        rm2.metric("Peak Capital Burn", fmt_inr(abs(max_burn) * 1e5), "Deepest point of J-Curve", delta_color="inverse")
        rm3.metric("Year 2 Run-Rate (Mo)", fmt_inr(total_rev_arr[-1] * 1e5))

        # Chart
        fig_phased = go.Figure()
        months_labels = [f"M{i+1}" for i in range(proj_timeline)]
        
        fig_phased.add_trace(go.Bar(x=months_labels, y=total_rev_arr, name="Revenue", marker_color='#3b82f6', opacity=0.7))
        fig_phased.add_trace(go.Bar(x=months_labels, y=-total_capex_arr, name="CapEx (Hit)", marker_color='#ef4444', opacity=0.8))
        fig_phased.add_trace(go.Scatter(x=months_labels, y=total_opex_arr, name="OpEx", line=dict(color='#f97316', dash='dot')))
        fig_phased.add_trace(go.Scatter(x=months_labels, y=cum_cashflow_arr, name="Cumulative Cashflow", line=dict(color='#10b981', width=4)))
        
        fig_phased.add_hline(y=0, line_color='black', line_width=1)
        fig_phased.update_layout(
            barmode='relative', height=400, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="₹ Lacs"
        )
        st.plotly_chart(fig_phased, use_container_width=True, config=PLOTLY_CFG)
