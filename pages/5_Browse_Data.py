"""
Expansion Intelligence Platform — Data Explorer
==================================================
Browse all loaded datasets with filtering and export.
"""

import streamlit as st
import pandas as pd
from config import get_vertical, get_term
from db import load_table, TABLE_MAP

st.set_page_config(page_title="Data Explorer", page_icon="📂", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]

st.markdown(f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">{vc["icon"]} {vc["name"]}</span>', unsafe_allow_html=True)
st.title("📂 Data Explorer")
st.markdown("Browse, filter, and export all loaded datasets.")

# List available tables
tables_available = []
for tname in TABLE_MAP.keys():
    df = load_table(tname)
    if not df.empty:
        tables_available.append({"table": tname, "rows": len(df), "cols": len(df.columns)})

if not tables_available:
    st.info("No data loaded. Go to **Upload & Refresh** to import data.")
    st.stop()

summary = pd.DataFrame(tables_available)
st.subheader("📊 Loaded Datasets")
st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()

# Table selector
table_names = [t["table"] for t in tables_available]
selected = st.selectbox("Select dataset to explore", table_names)

if selected:
    df = load_table(selected)
    st.subheader(f"📋 {selected} — {len(df):,} rows × {len(df.columns)} columns")

    # Column info
    with st.expander("Column Info"):
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notna().sum().values,
            "Unique": df.nunique().values,
            "Sample": [str(df[c].dropna().iloc[0])[:50] if not df[c].dropna().empty else "—" for c in df.columns]
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)

    # Filters
    with st.expander("🔍 Filters", expanded=False):
        filter_col = st.selectbox("Filter column", ["None"] + list(df.columns))
        if filter_col != "None":
            if df[filter_col].dtype == 'object':
                vals = df[filter_col].dropna().unique().tolist()
                selected_vals = st.multiselect("Select values", vals, default=vals[:10])
                df = df[df[filter_col].isin(selected_vals)]
            else:
                min_v, max_v = float(df[filter_col].min()), float(df[filter_col].max())
                range_v = st.slider("Range", min_v, max_v, (min_v, max_v))
                df = df[(df[filter_col] >= range_v[0]) & (df[filter_col] <= range_v[1])]

    st.dataframe(df, use_container_width=True, height=500, hide_index=True)

    # Download
    csv = df.to_csv(index=False)
    st.download_button(f"⬇️ Download {selected}.csv", csv, f"{selected}.csv", "text/csv")
