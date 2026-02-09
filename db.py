"""
Expansion Intelligence Platform - Database Abstraction Layer
=============================================================
Dual-mode: Neon PostgreSQL (production) or local CSV (development).
Supports multi-vertical data isolation via vertical_key prefix.

Usage:
    from db import load_table, save_table, is_db_mode, get_db_status
    df = load_table("master_state")          # loads for current vertical
    save_table("master_state", df)
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
UPLOAD_LOG = os.path.join(DATA_DIR, "upload_log.json")

# === All table definitions (name -> CSV filename) ====================
TABLE_MAP = {
    # == Universal tables ==
    "master_state":          "master_state.csv",
    "state_orders_summary":  "state_orders_summary.csv",
    "state_clinic_summary":  "state_clinic_summary.csv",
    "city_orders_summary":   "city_orders_summary.csv",
    "city_clinic_summary":   "city_clinic_summary.csv",
    "year_trend":            "year_trend.csv",
    "year_state_orders":     "year_state_orders.csv",
    "pincode_clinic":        "pincode_clinic.csv",
    "product_state":         "product_state.csv",
    # == Location performance ==
    "clinic_performance":    "clinic_performance.csv",
    "clinic_zip_summary":    "clinic_zip_summary.csv",
    "clinic_monthly_trend":  "clinic_monthly_trend.csv",
    # == Health indicators (healthcare vertical) ==
    "nfhs5_state":           "nfhs5_state.csv",
    "nfhs5_district":        "nfhs5_district.csv",
    "infra_city":            "infra_city.csv",
    # == Expansion data ==
    "expansion_scores":      "expansion_scores.csv",
    "competition_map":       "competition_map.csv",
    # == Census 2011 District Data ==
    "census_district_demographics": "census_district_demographics.csv",
    "census_hh_assets":             "census_hh_assets.csv",
    "state_health_spending":        "state_health_spending.csv",
    # == CEI Scoring Engine ==
    "cei_district_scores":          "cei_district_scores.csv",
    "cei_methodology":              "cei_methodology.csv",
    # == City Classifications ==
    "smart_cities":                 "smart_cities.csv",
    "amrut_cities":                 "amrut_cities.csv",
    # == NTB (New-To-Brand) Show Data ==
    "ntb_show_clinic":              "ntb_show_clinic.csv",
    "ntb_show_summary":             "ntb_show_summary.csv",
    # == Clinic NTB ZipData ==
    "ntb_zipdata_clinic":           "ntb_zipdata_clinic.csv",
    "ntb_zipdata_monthly":          "ntb_zipdata_monthly.csv",
    # == 100-Clinic Expansion Strategy ==
    "revenue_projection_175":       "revenue_projection_175.csv",
    "revenue_city_rollup":          "revenue_city_rollup.csv",
    "existing_clinics_61":          "existing_clinics_61.csv",
    "expansion_same_city":          "expansion_same_city.csv",
    "expansion_new_city":           "expansion_new_city.csv",
    "ivf_competitor_map":           "ivf_competitor_map.csv",
    "web_order_demand":             "web_order_demand.csv",
    "implementation_roadmap":       "implementation_roadmap.csv",
    "show_pct_analysis":            "show_pct_analysis.csv",
    "scenario_simulator_clinics":   "scenario_simulator_clinics.csv",
    "expansion_priority_tiers":     "expansion_priority_tiers.csv",
    "show_pct_rank_comparison":     "show_pct_rank_comparison.csv",
    "show_pct_impact_comparison":   "show_pct_impact_comparison.csv",
}


# === Connection detection ============================================

def _get_neon_url():
    """Extract Neon connection URL from Streamlit secrets."""
    try:
        if hasattr(st, 'secrets'):
            if "connections" in st.secrets and "neon" in st.secrets["connections"]:
                return st.secrets["connections"]["neon"].get("url", None)
            if "neon" in st.secrets:
                return st.secrets["neon"].get("url", None)
            if "NEON_DATABASE_URL" in st.secrets:
                return st.secrets["NEON_DATABASE_URL"]
    except Exception:
        pass
    return None


def is_db_mode():
    """Returns True if Neon PostgreSQL is configured."""
    return _get_neon_url() is not None


def get_db_status():
    """Returns connection status info dict."""
    neon_url = _get_neon_url()
    if neon_url:
        import re
        masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', neon_url)
        return {"mode": "Neon PostgreSQL", "connected": True, "url_masked": masked, "icon": "🟢"}
    return {"mode": "Local CSV (dev)", "connected": False, "url_masked": "N/A", "icon": "📁"}


# === Neon engine (cached) ===========================================

@st.cache_resource
def _get_engine():
    """Create and cache a SQLAlchemy engine for Neon."""
    from sqlalchemy import create_engine
    url = _get_neon_url()
    if not url:
        return None
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url += f"{sep}sslmode=require"
    return create_engine(url, pool_size=3, max_overflow=5, pool_pre_ping=True)


def _ensure_neon_table(table_name: str, df: pd.DataFrame):
    """Create a Neon table from a DataFrame if it doesn't exist."""
    engine = _get_engine()
    if engine is None:
        return
    from sqlalchemy import text
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=:t)"),
            {"t": table_name}
        ).scalar()
        if not exists and not df.empty:
            df.to_sql(table_name, engine, if_exists="replace", index=False)


# === Public API ======================================================

@st.cache_data(ttl=300)
def load_table(table_name: str) -> pd.DataFrame:
    """Load a table - from Neon if configured, else from local CSV."""
    engine = _get_engine()

    # Try Neon first
    if engine is not None:
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                exists = conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=:t)"),
                    {"t": table_name}
                ).scalar()
            if exists:
                return pd.read_sql_table(table_name, engine)
        except Exception:
            pass

    # Fallback to local CSV
    csv_name = TABLE_MAP.get(table_name, f"{table_name}.csv")
    csv_path = os.path.join(DATA_DIR, csv_name)
    if os.path.exists(csv_path):
        try:
            return pd.read_csv(csv_path)
        except Exception:
            pass

    return pd.DataFrame()


def save_table(table_name: str, df: pd.DataFrame, mode: str = "replace"):
    """Save a DataFrame - to Neon if configured, always save local CSV too."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save local CSV
    csv_name = TABLE_MAP.get(table_name, f"{table_name}.csv")
    csv_path = os.path.join(DATA_DIR, csv_name)
    df.to_csv(csv_path, index=False)

    # Save to Neon if available
    engine = _get_engine()
    if engine is not None:
        try:
            df.to_sql(table_name, engine, if_exists=mode, index=False)
        except Exception as e:
            st.warning(f"Neon write failed for {table_name}: {e}")

    # Clear cache
    load_table.clear()

    # Log upload
    _log_upload(table_name, len(df))


def _log_upload(table_name: str, rows: int):
    """Append entry to upload log."""
    os.makedirs(DATA_DIR, exist_ok=True)
    log = []
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG) as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append({"table": table_name, "rows": rows, "ts": datetime.now().isoformat()})
    with open(UPLOAD_LOG, "w") as f:
        json.dump(log[-50:], f, indent=2)


def load_geojson():
    """Load India states GeoJSON for choropleth maps."""
    geo_path = os.path.join(DATA_DIR, "india_states_simple.geojson")
    if os.path.exists(geo_path):
        with open(geo_path) as f:
            return json.load(f)

    # Try downloading if not present
    try:
        import urllib.request
        url = "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson"
        urllib.request.urlretrieve(url, geo_path)
        with open(geo_path) as f:
            return json.load(f)
    except Exception:
        return None


def get_upload_log() -> list:
    """Return the upload history log."""
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def push_all_to_neon():
    """Bulk push all local CSVs to Neon. Returns count of tables synced."""
    engine = _get_engine()
    if engine is None:
        return 0
    synced = 0
    for table_name, csv_name in TABLE_MAP.items():
        csv_path = os.path.join(DATA_DIR, csv_name)
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if not df.empty:
                    df.to_sql(table_name, engine, if_exists="replace", index=False)
                    synced += 1
            except Exception:
                continue
    load_table.clear()
    return synced
