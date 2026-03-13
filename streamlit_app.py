"""
Gynoveda Expansion Intelligence OS
UPDATED FINAL MASTER VERSION
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Gynoveda Expansion OS", layout="wide")

DATA_DIR = "mis_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------
# COLUMN AUTO STANDARDIZER
# ---------------------------------------------------

def standardize_columns(df):

    df.columns = df.columns.str.strip()

    rename_map = {}

    for col in df.columns:

        c = col.lower()

        if "city" in c:
            rename_map[col] = "City"

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

    if pd.isna(v):
        return "₹0"

    if v >= 1e7:
        return f"₹{v/1e7:.1f} Cr"

    if v >= 1e5:
        return f"₹{v/1e5:.1f} L"

    return f"₹{v:,.0f}"


# ---------------------------------------------------
# LIGHTWEIGHT SIMILARITY ENGINE
# ---------------------------------------------------

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

@st.cache_data
def load_all():

    def safe(file):

        path = f"{DATA_DIR}/{file}"

        if os.path.exists(path):

            df = pd.read_csv(path)

            df = standardize_columns(df)

            return df

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

    st.markdown("### Upload Data")

    files = st.file_uploader("Upload CSV files", accept_multiple_files=True)

    if files and st.button("Process Files"):

        for f in files:

            name = f.name.lower()

            if "web" in name:
                target = "std_demand_web.csv"

            elif "clinic" in name:
                target = "std_demand_clinic.csv"

            elif "ivf" in name:
                target = "std_ivf_comp.csv"

            elif "pin" in name:
                target = "std_pin_geo.csv"

            elif "pop" in name:
                target = "std_population.csv"

            else:
                target = f"std_{name}.csv"

            df = pd.read_csv(f)
            df = standardize_columns(df)

            df.to_csv(f"{DATA_DIR}/{target}", index=False)

        st.cache_data.clear()
        st.success("Data Updated")


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

st.title("Gynoveda Expansion Intelligence OS")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏥 Network Health",
    "📍 Expansion Opportunities",
    "🧠 Site Simulator",
    "💰 Capital Planner"
])


# ===================================================
# NETWORK HEALTH
# ===================================================

with tab1:

    web = data["web"]
    clinic = data["clinic"]
    ivf = data["ivf"]
    clinics = data["clinics"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Active Clinics", len(clinics))

    c2.metric(
        "Clinic Patients",
        clinic["Customer ID"].nunique() if "Customer ID" in clinic else 0
    )

    c3.metric(
        "Digital Patients",
        web["Customer ID"].nunique() if "Customer ID" in web else 0
    )

    c4.metric("IVF Competitors", len(ivf))

    if not web.empty and "City" in web:

        demand = web.groupby("City")["Customer ID"].nunique().reset_index()

        fig = px.bar(
            demand.sort_values("Customer ID", ascending=False).head(10),
            x="City",
            y="Customer ID",
            title="Top Digital Demand Cities"
        )

        st.plotly_chart(fig, use_container_width=True)


# ===================================================
# EXPANSION OPPORTUNITIES
# ===================================================

with tab2:

    web = data["web"]
    clinic = data["clinic"]
    clinics = data["clinics"]
    ivf = data["ivf"]
    pop = data["population"]

    if web.empty:

        st.warning("Upload web demand data")

    else:

        web_city = web.groupby("City").agg(
            WebPatients=("Customer ID", "nunique"),
            WebRevenue=("Total", "sum")
        ).reset_index()

        clinic_city = clinic.groupby("City").agg(
            ClinicPatients=("Customer ID", "nunique"),
            ClinicRevenue=("Total", "sum")
        ).reset_index()

        ivf_city = ivf.groupby("City").size().reset_index(name="IVF")

        df = web_city.merge(clinic_city, on="City", how="left")
        df = df.merge(ivf_city, on="City", how="left")

        df.fillna(0, inplace=True)

        # SAFE POPULATION MERGE

        if not pop.empty:

            pop_cols = [c for c in pop.columns if "pop" in c.lower()]

            if "City" in pop.columns and len(pop_cols) > 0:

                pop_col = pop_cols[0]

                pop_city = pop.groupby("City")[pop_col].sum().reset_index()

                pop_city.rename(columns={pop_col: "Population"}, inplace=True)

                df = df.merge(pop_city, on="City", how="left")

        if "Population" in df.columns:

            df["DemandDensity"] = df["WebPatients"] / df["Population"].replace(0, np.nan)

        else:

            df["DemandDensity"] = 0

        clinic_cities = set(clinics["City"].dropna())

        served = df[df["City"].isin(clinic_cities)].copy()
        unserved = df[~df["City"].isin(clinic_cities)].copy()

        served_matrix = served[["WebPatients", "DemandDensity", "IVF"]].fillna(0).values
        unserved_matrix = unserved[["WebPatients", "DemandDensity", "IVF"]].fillna(0).values

        served_matrix = normalize_matrix(served_matrix)
        unserved_matrix = normalize_matrix(unserved_matrix)

        similarity = cosine_similarity_matrix(unserved_matrix, served_matrix)

        best = similarity.argmax(axis=1)

        unserved["SimilarCity"] = served.iloc[best]["City"].values
        unserved["SimilarityScore"] = similarity.max(axis=1)

        st.markdown("### AI Whitespace Expansion Candidates")

        st.dataframe(
            unserved.sort_values("SimilarityScore", ascending=False)[
                ["City", "WebPatients", "DemandDensity", "IVF", "SimilarCity", "SimilarityScore"]
            ].head(20),
            hide_index=True,
            use_container_width=True
        )

        city = st.selectbox("Explore City", unserved["City"])

        city_web = web[web["City"] == city]

        # DEMAND MAP

        with st.expander("Demand Heatmap"):

            if not city_web.empty and not data["pin"].empty:

                pins = city_web.groupby("Zip")["Customer ID"].nunique().reset_index()

                mapdf = pins.merge(
                    data["pin"],
                    left_on="Zip",
                    right_on="Zip",
                    how="left"
                )

                fig = px.scatter_mapbox(
                    mapdf,
                    lat="Latitude",
                    lon="Longitude",
                    size="Customer ID",
                    zoom=10
                )

                fig.update_layout(mapbox_style="carto-positron")

                st.plotly_chart(fig, use_container_width=True)

        # PINCODE WHITESPACE

        st.markdown("### Top Demand Neighborhoods")

        city_pins = city_web.groupby("Zip").agg(
            WebPatients=("Customer ID", "nunique"),
            WebRevenue=("Total", "sum")
        ).reset_index()

        city_pins["PatientsMo"] = city_pins["WebPatients"] / 60

        top_pins = city_pins.sort_values("PatientsMo", ascending=False).head(10)

        st.dataframe(
            top_pins[["Zip", "PatientsMo"]],
            hide_index=True,
            use_container_width=True
        )

        if not top_pins.empty:

            best_pin = top_pins.iloc[0]

            st.success(
f"""
Recommended Clinic Catchment

Pincode: **{best_pin['Zip']}**

Estimated demand:
**{best_pin['PatientsMo']:.1f} patients/month**
"""
            )


# ===================================================
# SITE SIMULATOR
# ===================================================

with tab3:

    web = data["web"]

    if web.empty:

        st.warning("Upload web demand")

    else:

        pins = web.groupby("Zip").agg(
            WebPatients=("Customer ID", "nunique"),
            WebRevenue=("Total", "sum")
        ).reset_index()

        pins["RevMo"] = pins["WebRevenue"] / 60

        pin = st.selectbox("Select Demand Pincode", pins["Zip"])

        row = pins[pins["Zip"] == pin].iloc[0]

        web_pat = row["WebPatients"] / 60
        web_rev = row["RevMo"]

        o2o = 3.0

        clinic_rev = web_rev * o2o

        c1, c2, c3 = st.columns(3)

        c1.metric("Web Patients/mo", round(web_pat, 1))
        c2.metric("O2O Multiplier", f"{o2o}X")
        c3.metric("Projected Clinic Revenue", fmt_inr(clinic_rev))

        fig = go.Figure(go.Waterfall(
            measure=["absolute", "relative", "total"],
            x=["Web Revenue", "O2O Uplift", "Clinic Revenue"],
            y=[web_rev, clinic_rev - web_rev, clinic_rev]
        ))

        st.plotly_chart(fig, use_container_width=True)


# ===================================================
# CAPITAL PLANNER
# ===================================================

with tab4:

    st.markdown("### Expansion Capital Model")

    clinics = st.slider("Clinics to Open", 1, 30, 10)
    capex = st.slider("Capex per Clinic (L)", 10, 50, 28)
    opex = st.slider("Monthly Opex (L)", 1, 10, 3)
    revenue = st.slider("Monthly Revenue (L)", 5, 40, 15)

    months = 12

    total_capex = clinics * capex

    cash = -total_capex
    curve = []

    for m in range(months):

        cash += clinics * (revenue - opex)
        curve.append(cash)

    fig = px.line(
        x=list(range(1, months + 1)),
        y=curve,
        labels={"x": "Month", "y": "Cashflow (L)"}
    )

    st.plotly_chart(fig, use_container_width=True)

    st.metric("Total Capex Needed", fmt_inr(total_capex * 100000))
