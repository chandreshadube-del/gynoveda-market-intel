"""
Gynoveda Expansion Intelligence OS
Final Production Master
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import os

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

st.set_page_config(
    page_title="Gynoveda Expansion OS",
    layout="wide",
    page_icon="◉"
)

DATA_DIR="mis_data"
os.makedirs(DATA_DIR,exist_ok=True)

# ----------------------------------------------------
# UTILITIES
# ----------------------------------------------------

def fmt_inr(v):
    if pd.isna(v):
        return "₹0"
    if v>=1e7:
        return f"₹{v/1e7:.1f} Cr"
    if v>=1e5:
        return f"₹{v/1e5:.1f} L"
    return f"₹{v:,.0f}"

# ----------------------------------------------------
# DATA LOADER
# ----------------------------------------------------

@st.cache_data
def load_all():

    def safe(file):
        path=f"{DATA_DIR}/{file}"
        if os.path.exists(path):
            df=pd.read_csv(path)
            df.columns=df.columns.str.strip()
            return df
        return pd.DataFrame()

    return{
        "web":safe("std_demand_web.csv"),
        "clinic":safe("std_demand_clinic.csv"),
        "clinics":safe("std_clinics.csv"),
        "ivf":safe("std_ivf_comp.csv"),
        "pin":safe("std_pin_geo.csv"),
        "population":safe("std_population.csv")
    }

data=load_all()

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------

with st.sidebar:

    st.markdown("### Upload Data")

    files=st.file_uploader("Upload CSV",accept_multiple_files=True)

    if files and st.button("Process Files"):

        for f in files:

            name=f.name.lower()

            if "web" in name:
                target="std_demand_web.csv"

            elif "clinic" in name:
                target="std_demand_clinic.csv"

            elif "ivf" in name:
                target="std_ivf_comp.csv"

            elif "pin" in name:
                target="std_pin_geo.csv"

            elif "population" in name:
                target="std_population.csv"

            else:
                target=f"std_{name}.csv"

            df=pd.read_csv(f)
            df.to_csv(f"{DATA_DIR}/{target}",index=False)

        st.cache_data.clear()
        st.success("Data Updated")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------

st.title("Gynoveda Expansion Intelligence OS")

# ----------------------------------------------------
# TABS
# ----------------------------------------------------

tab1,tab2,tab3,tab4=st.tabs([
"🏥 Network Health",
"📍 Expansion Opportunities",
"🧠 Site Simulator",
"💰 Capital Planner"
])

# ====================================================
# NETWORK HEALTH
# ====================================================

with tab1:

    web=data["web"]
    clinic=data["clinic"]
    ivf=data["ivf"]
    clinics=data["clinics"]

    c1,c2,c3,c4=st.columns(4)

    c1.metric("Active Clinics",len(clinics))
    c2.metric("Clinic Patients",clinic["Customer ID"].nunique() if "Customer ID" in clinic else 0)
    c3.metric("Digital Patients",web["Customer ID"].nunique() if "Customer ID" in web else 0)
    c4.metric("IVF Competitors",len(ivf))

    if not web.empty:

        demand=web.groupby("City")["Customer ID"].nunique().reset_index()

        fig=px.bar(
            demand.sort_values("Customer ID",ascending=False).head(10),
            x="City",
            y="Customer ID",
            title="Top Digital Demand Cities"
        )

        st.plotly_chart(fig,use_container_width=True)

# ====================================================
# EXPANSION OPPORTUNITIES
# ====================================================

with tab2:

    web=data["web"]
    clinic=data["clinic"]
    clinics=data["clinics"]
    ivf=data["ivf"]
    pop=data["population"]

    if web.empty:
        st.warning("Upload web demand")
    else:

        web_city=web.groupby("City").agg(
            WebPatients=("Customer ID","nunique"),
            WebRevenue=("Total","sum")
        ).reset_index()

        clinic_city=clinic.groupby("City").agg(
            ClinicPatients=("Customer ID","nunique"),
            ClinicRevenue=("Total","sum")
        ).reset_index()

        ivf_city=ivf.groupby("City").size().reset_index(name="IVF")

        df=web_city.merge(clinic_city,on="City",how="left")
        df=df.merge(ivf_city,on="City",how="left")

        df.fillna(0,inplace=True)

        # population merge
        if not pop.empty and "City" in pop:

            pop_city=pop.groupby("City")["Population"].sum().reset_index()

            df=df.merge(pop_city,on="City",how="left")

        df["DemandDensity"]=df["WebPatients"]/df["Population"].replace(0,np.nan)

        clinic_cities=set(clinics["City"].dropna())

        served=df[df["City"].isin(clinic_cities)]
        unserved=df[~df["City"].isin(clinic_cities)]

        features=served[[
            "WebPatients",
            "DemandDensity",
            "IVF"
        ]].fillna(0)

        scaler=StandardScaler()

        X=scaler.fit_transform(features)

        unserved_features=scaler.transform(
            unserved[["WebPatients","DemandDensity","IVF"]].fillna(0)
        )

        similarity=cosine_similarity(unserved_features,X)

        best=similarity.argmax(axis=1)

        unserved["SimilarCity"]=served.iloc[best]["City"].values
        unserved["SimilarityScore"]=similarity.max(axis=1)

        st.markdown("### AI Whitespace Expansion Candidates")

        st.dataframe(
            unserved.sort_values("SimilarityScore",ascending=False)[
                ["City","WebPatients","DemandDensity","IVF","SimilarCity","SimilarityScore"]
            ].head(20),
            hide_index=True,
            use_container_width=True
        )

        city=st.selectbox("Explore City",unserved["City"])

        city_web=web[web["City"]==city]

        with st.expander("Demand Heatmap"):

            if not city_web.empty and not data["pin"].empty:

                pins=city_web.groupby("Zip")["Customer ID"].nunique().reset_index()

                mapdf=pins.merge(
                    data["pin"],
                    left_on="Zip",
                    right_on="pincode"
                )

                fig=px.scatter_mapbox(
                    mapdf,
                    lat="lat",
                    lon="lon",
                    size="Customer ID",
                    zoom=10
                )

                fig.update_layout(mapbox_style="carto-positron")

                st.plotly_chart(fig,use_container_width=True)

# ====================================================
# SITE SIMULATOR
# ====================================================

with tab3:

    web=data["web"]

    if web.empty:

        st.warning("Upload web demand")

    else:

        pins=web.groupby("Zip").agg(
            WebPatients=("Customer ID","nunique"),
            WebRevenue=("Total","sum")
        ).reset_index()

        pins["RevMo"]=pins["WebRevenue"]/60

        pin=st.selectbox("Select Demand Pincode",pins["Zip"])

        row=pins[pins["Zip"]==pin].iloc[0]

        web_pat=row["WebPatients"]/60
        web_rev=row["RevMo"]

        o2o=3.0
        clinic_rev=web_rev*o2o

        c1,c2,c3=st.columns(3)

        c1.metric("Web Patients/mo",round(web_pat,1))
        c2.metric("O2O Multiplier",f"{o2o}X")
        c3.metric("Projected Clinic Revenue",fmt_inr(clinic_rev))

        fig=go.Figure(go.Waterfall(
            measure=["absolute","relative","total"],
            x=["Web Revenue","O2O Uplift","Clinic Revenue"],
            y=[web_rev,clinic_rev-web_rev,clinic_rev]
        ))

        st.plotly_chart(fig,use_container_width=True)

# ====================================================
# CAPITAL PLANNER
# ====================================================

with tab4:

    st.markdown("### Expansion Capital Model")

    clinics=st.slider("Clinics to Open",1,30,10)
    capex=st.slider("Capex per Clinic (L)",10,50,28)
    opex=st.slider("Monthly Opex (L)",1,10,3)
    revenue=st.slider("Monthly Revenue (L)",5,40,15)

    months=12

    total_capex=clinics*capex

    cash=-total_capex

    curve=[]

    for m in range(months):

        cash+=clinics*(revenue-opex)
        curve.append(cash)

    fig=px.line(
        x=list(range(1,months+1)),
        y=curve,
        labels={"x":"Month","y":"Cashflow (L)"}
    )

    st.plotly_chart(fig,use_container_width=True)

    st.metric("Total Capex Needed",fmt_inr(total_capex*100000))
