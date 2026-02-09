"""
Expansion Intelligence Platform — Setup Guide
================================================
Quick-start guide for deploying and configuring the platform
for any industry vertical.
"""

import streamlit as st
import pandas as pd
from config import VERTICALS, MODULE_REGISTRY, get_vertical

st.set_page_config(page_title="Setup Guide", page_icon="⚙️", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title("⚙️ Setup & Configuration Guide")

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Quick Start", "🏗️ Architecture", "🔌 Neon Setup", "📋 Verticals"])

with tab1:
    st.subheader("Quick Start — 3 Steps to Launch")

    st.markdown("""
    **Step 1: Deploy the App**

    Clone the repository and install dependencies:

    ```bash
    git clone <your-repo-url>
    cd expansion_intel
    pip install -r requirements.txt
    streamlit run streamlit_app.py
    ```

    **Step 2: Select Your Industry Vertical**

    Use the sidebar dropdown to switch between Healthcare, Fashion & Apparel, Real Estate, Mall Development, or F&B/QSR. Each vertical adapts terminology, scoring dimensions, and available modules.

    **Step 3: Upload Your Data**

    Navigate to **Upload & Refresh** and import your datasets in sections:
    1. Online transaction/demand data (state + city + pincode levels)
    2. Location/outlet performance data
    3. Product/category breakdown
    4. Pincode-level catchment mapping
    5. Infrastructure and competition data

    The platform auto-detects column structures and builds analytics dashboards from your data.
    """)

with tab2:
    st.subheader("Platform Architecture")

    st.markdown("""
    The Expansion Intelligence Platform uses a modular architecture designed for multi-industry deployment.

    **Core Components:**

    The **config.py** module defines industry vertical configurations including terminology mappings, KPI definitions, scoring dimensions, and module availability. Adding a new vertical requires only extending the VERTICALS dictionary.

    The **db.py** module provides a dual-mode database layer — local CSV files for development and Neon PostgreSQL for production, with automatic sync between modes.

    **Page modules** are conditionally loaded based on the active vertical. Universal pages (Dashboard, Map Explorer, Market Scoring, Data Upload) appear for all verticals. Vertical-specific pages (IVF Analysis for Healthcare, Tenant Mix for Mall Development) appear only when their parent vertical is selected.

    **Data Flow:** Upload → CSV/Neon storage → Analytics pages read via `load_table()` → Visualizations and scoring computed on-the-fly.
    """)

    # Module availability matrix
    st.subheader("Module Availability by Vertical")
    matrix_data = []
    for vk, vv in VERTICALS.items():
        row = {"Vertical": f"{vv['icon']} {vv['name']}"}
        for mk, mv in MODULE_REGISTRY.items():
            row[mv["label"]] = "✅" if mk in vv.get("modules", []) else "—"
        matrix_data.append(row)

    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Neon PostgreSQL Setup")

    st.markdown("""
    For production deployment with persistent storage, configure Neon PostgreSQL:

    **1. Create a Neon account** at [neon.tech](https://neon.tech) and create a new project.

    **2. Get your connection URL** from the Neon dashboard (format: `postgresql://user:pass@host/db`).

    **3. Configure Streamlit secrets.** Create `.streamlit/secrets.toml`:

    ```toml
    [connections.neon]
    url = "postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"
    ```

    **4. Push existing data.** Go to Upload & Refresh → click "Push All to Neon".

    **5. Deploy to Streamlit Cloud.** Add the same secret in Streamlit Cloud's Settings → Secrets.
    """)

    from db import get_db_status
    status = get_db_status()
    st.info(f"{status['icon']} Current mode: **{status['mode']}**")

with tab4:
    st.subheader("Industry Vertical Reference")

    for vk, vv in VERTICALS.items():
        with st.expander(f"{vv['icon']} {vv['name']} — {vv['tagline']}", expanded=(vk == V)):
            st.markdown(f"**Terminology:**")
            term_df = pd.DataFrame([
                {"Generic Term": k.replace("_", " ").title(), "This Vertical": v}
                for k, v in vv["terminology"].items()
            ])
            st.dataframe(term_df, use_container_width=True, hide_index=True)

            st.markdown("**Scoring Dimensions:**")
            score_df = pd.DataFrame([
                {"ID": dk, "Dimension": dv["name"], "Weight": f"{dv['weight']*100:.0f}%",
                 "Type": "Universal" if dv.get("universal") else "Vertical-specific"}
                for dk, dv in vv.get("scoring_dimensions", {}).items()
            ])
            st.dataframe(score_df, use_container_width=True, hide_index=True)
