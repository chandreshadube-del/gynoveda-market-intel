"""
Gynoveda Expansion Intelligence — Dashboard Upgrade Code Blocks
================================================================
Drop these into your existing Streamlit dashboard.

Changes covered:
1. Remove "— Last 12 Months" from Network Health header
2. Same-City Expansion: CEO summary cards below heading
3. New-City Whitespace: CEO summary cards below heading
4. Cannibalization chart: Usage guide tooltip/expander

Author: Claude (for Chandresh @ Gynoveda)
"""

import streamlit as st
import pandas as pd
import numpy as np

# ============================================================
# SHARED: Reusable KPI card component (matches your existing style)
# ============================================================

def render_kpi_card(label: str, value: str, subtitle: str = "", delta: str = "", delta_color: str = "normal"):
    """
    Renders a single KPI metric card matching Gynoveda dashboard styling.
    
    Args:
        label: Card header text (e.g., "Total Revenue")
        value: Main metric value (e.g., "₹168.6 Cr")
        subtitle: Small text below value (e.g., "↑ of 61 total")
        delta: Change indicator (e.g., "-65% last MoM")
        delta_color: "normal" (green up/red down), "inverse", or "off"
    """
    # Using st.metric for consistent styling with your existing cards
    st.metric(
        label=label,
        value=value,
        delta=delta if delta else None,
        delta_color=delta_color
    )
    if subtitle:
        st.caption(subtitle)


def render_kpi_row(metrics: list, columns: int = 5):
    """
    Renders a horizontal row of KPI cards inside a styled container.
    
    Args:
        metrics: List of dicts with keys: label, value, subtitle (optional), delta (optional)
        columns: Number of columns (default 5 to match your Network Health layout)
    """
    # Orange-accent container matching your existing dashboard
    st.markdown("""
    <style>
    .kpi-container {
        background: #fafafa;
        border-radius: 12px;
        padding: 8px 0;
        margin-bottom: 16px;
    }
    .kpi-container [data-testid="stMetric"] {
        background: white;
        border-left: 4px solid #E8601C;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-container [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: #666 !important;
        font-weight: 500 !important;
    }
    .kpi-container [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
        cols = st.columns(columns)
        for i, m in enumerate(metrics):
            with cols[i % columns]:
                render_kpi_card(
                    label=m.get("label", ""),
                    value=m.get("value", ""),
                    subtitle=m.get("subtitle", ""),
                    delta=m.get("delta", ""),
                    delta_color=m.get("delta_color", "normal")
                )
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CHANGE 1: Network Health header — remove "— Last 12 Months"
# ============================================================
# BEFORE (find this in your code):
#   st.header("Network Health — Last 12 Months")
# 
# REPLACE WITH:
#   st.header("Network Health")
#   st.caption("Rolling 12-month view across all active clinics")
#
# That's it — one line change. The caption adds context without cluttering the header.


# ============================================================
# CHANGE 2: Same-City Expansion — CEO Summary Cards
# ============================================================

def render_same_city_summary(city_df: pd.DataFrame):
    """
    Renders a CEO-ready summary row for the Same-City Expansion tab.
    
    Place this immediately AFTER the tab heading:
        st.header("Same-City Expansion Analysis")
        st.caption("Where should we add clinics in cities we already operate in?")
        render_same_city_summary(city_df)   # <-- ADD THIS LINE
    
    Args:
        city_df: Your existing city-level DataFrame with columns:
            - city: City name
            - clinics: Number of clinics
            - cabins: Number of cabins  
            - cei_score: Composite Expansion Index score
            - l3m_rev: Last 3 months revenue (in lakhs)
            - growth: Growth % (decimal, e.g., 0.10 for 10%)
            - rev_per_cabin: Revenue per cabin (in lakhs)
            - web_orders: Web order count
            - ebitda_pct: EBITDA % (decimal)
            - pincodes: Pincode count
    
    Adjust column names below to match YOUR actual DataFrame.
    """
    
    # ---- Compute summary metrics from your city DataFrame ----
    total_cities = len(city_df)
    total_clinics = city_df['clinics'].sum()
    total_cabins = city_df['cabins'].sum()
    
    # Top expansion candidate (highest CEI)
    top_city_row = city_df.loc[city_df['cei_score'].idxmax()]
    top_city = f"{top_city_row['city']} (CEI: {int(top_city_row['cei_score'])})"
    
    # Cities with positive growth
    growing_cities = city_df[city_df['growth'] > 0].shape[0]
    growth_text = f"{growing_cities} of {total_cities}"
    
    # Total untapped pincodes
    total_pincodes = int(city_df['pincodes'].sum())
    
    # Network avg rev/cabin
    avg_rev_cabin = city_df['rev_per_cabin'].mean()
    avg_rev_cabin_text = f"₹{avg_rev_cabin:.1f}L"
    
    # Total web orders (demand signal)
    total_web_orders = city_df['web_orders'].sum()
    web_orders_text = f"{total_web_orders/1000:.0f}K" if total_web_orders >= 1000 else str(int(total_web_orders))
    
    # ---- Render the summary ----
    st.markdown("#### 📊 Network Snapshot — Existing Cities")
    
    metrics = [
        {
            "label": "Cities with Clinics",
            "value": str(total_cities),
            "subtitle": f"{total_clinics} clinics, {total_cabins} cabins"
        },
        {
            "label": "Top Expansion Pick",
            "value": top_city,
            "subtitle": "Highest Composite Score"
        },
        {
            "label": "Avg Rev / Cabin",
            "value": avg_rev_cabin_text,
            "subtitle": "Across all cities"
        },
        {
            "label": "Cities Growing",
            "value": growth_text,
            "subtitle": "Positive L3M growth"
        },
        {
            "label": "Total Web Orders",
            "value": web_orders_text,
            "subtitle": f"{total_pincodes:,} unique pincodes"
        }
    ]
    
    render_kpi_row(metrics, columns=5)
    
    st.divider()


# ---- ALTERNATIVE: If you don't have a pre-built city_df, ----
# ---- here's a self-contained version that builds it from raw data ----

def render_same_city_summary_from_raw(sales_df, cx_df, ebitda_df, web_orders_df, clinic_pincodes_df):
    """
    Self-contained version that computes everything from raw MIS DataFrames.
    Use this if you don't already have a consolidated city_df.
    
    Args:
        sales_df: From 'SalesMTD' sheet — rows are clinics, columns are months
        cx_df: From '1Cx' sheet — new customer counts by clinic/month  
        ebitda_df: From 'Ebitda Trend' sheet
        web_orders_df: From '1cx_order_qty_pincode_of_website' — web orders by pincode
        clinic_pincodes_df: From 'Clinic_wise_FirstTime_TotalQuantity_by_Pincode'
    """
    # You'll need to adapt column names to your actual DataFrames
    # This is a template showing the computation logic
    
    # Group sales by city, sum last 3 months
    # Group clinics by city, count
    # Join with web orders aggregated by city
    # Compute growth = (L3M - prev L3M) / prev L3M
    # Then call render_same_city_summary(city_df)
    pass


# ============================================================
# CHANGE 3: New-City Whitespace — CEO Summary Cards
# ============================================================

def render_new_city_summary(
    dual_signal_pincodes: int,
    ntb_visits_20km: int,
    web_orders_20km: int, 
    ntb_revenue_cr: float,
    new_cities_count: int,
    top_city: str = "",
    top_city_orders: int = 0
):
    """
    Renders a CEO-ready summary row for the New-City Whitespace tab.
    
    Place this immediately AFTER the tab heading:
        st.header("New-City Whitespace Discovery")
        st.caption("Cities where Gynoveda has zero clinics but proven patient demand — "
                   "customers already buying online or traveling 20+ km to visit existing clinics.")
        render_new_city_summary(...)   # <-- ADD THIS LINE
    
    Args:
        dual_signal_pincodes: Count of pincodes with BOTH web orders AND clinic visits
        ntb_visits_20km: NTB patient visits from pincodes 20+ km away
        web_orders_20km: Web orders from pincodes 20+ km from nearest clinic
        ntb_revenue_cr: Revenue from NTB patients in unserved areas (in crores)
        new_cities_count: Number of new cities identified with dual-signal demand
        top_city: Name of the highest-opportunity new city
        top_city_orders: Order count for the top city
    """
    
    st.markdown("#### 🌍 Untapped Market Snapshot")
    
    # Format large numbers
    def fmt_large(n):
        if n >= 100000:
            return f"{n/100000:.1f}L"
        elif n >= 1000:
            return f"{n/1000:.0f}K"
        return str(int(n))
    
    metrics = [
        {
            "label": "Proven Demand Pincodes",
            "value": fmt_large(dual_signal_pincodes),
            "subtitle": "Both web orders + clinic visits"
        },
        {
            "label": "Patients Traveling 20+ km",
            "value": fmt_large(ntb_visits_20km),
            "subtitle": "Underserved by current network"
        },
        {
            "label": "Unserved Web Orders",
            "value": fmt_large(web_orders_20km),
            "subtitle": "From areas with no clinic"
        },
        {
            "label": "Revenue from Unserved Areas",
            "value": f"₹{ntb_revenue_cr:.1f} Cr",
            "subtitle": "NTB revenue at 20+ km"
        },
        {
            "label": "New Cities Ready to Enter",
            "value": str(new_cities_count),
            "subtitle": f"Top: {top_city} ({fmt_large(top_city_orders)} orders)" if top_city else "Dual-signal demand confirmed"
        }
    ]
    
    render_kpi_row(metrics, columns=5)
    
    st.divider()


# ============================================================
# CHANGE 4: Cannibalization Chart — Usage Guide
# ============================================================

def render_cannibalization_guide():
    """
    Renders an interactive usage guide for the Cannibalization & Radius Safeguard chart.
    Place this ABOVE or BELOW your cannibalization scatter plot.
    """
    
    with st.expander("📖 How to Read This Chart", expanded=False):
        st.markdown("""
**What it shows:** Each bubble is a pair of clinics. The chart reveals which clinic pairs 
are competing for the same patients (cannibalization risk).

**Reading the axes:**
- **X-axis (Distance):** How far apart the two clinics are in kilometers
- **Y-axis (Volume Overlap):** What % of patient pincodes are shared between the pair
- **Bubble size:** Combined patient volume of the pair (bigger = more patients affected)
- **Red dashed line (5 km):** Your minimum safe radius — pairs left of this line are dangerously close

**Color guide:**
- 🔴 **Critical** — High overlap AND close together → active revenue cannibalization
- 🟠 **Medium** — Moderate overlap → monitor closely
- 🟢 **Low / Minimal** — Healthy separation → distinct catchments

**What happens when you change the radius:**

| Radius | Effect | Best for |
|--------|--------|----------|
| **Smaller (3-4 km)** | More locations qualify, but higher cannibalization risk | Dense metros like Mumbai where 4 km apart = different demographics |
| **Standard (5 km)** | Balanced protection — current default | Most cities |
| **Larger (8-10 km)** | Maximum protection per clinic, but leaves demand gaps | Tier 2/3 cities with lower population density |

**Action items:** If you see a 🔴 Critical pair, investigate whether one clinic should be 
relocated, or whether the pair should be treated as a single market with shared marketing budget.
        """)


# ============================================================
# FULL INTEGRATION EXAMPLE
# ============================================================

def example_integration():
    """
    Shows how all pieces fit together in your Streamlit app.
    This is NOT meant to run standalone — it's a template showing placement.
    """
    
    st.set_page_config(page_title="Gynoveda Expansion Intelligence", layout="wide")
    st.title("Gynoveda Expansion Intelligence")
    
    # ---- Tab Navigation ----
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Executive Summary",
        "🏙️ Same-City Expansion", 
        "🌍 New-City Whitespace",
        "📈 Revenue Forecaster"
    ])
    
    # ---- TAB 1: Executive Summary ----
    with tab1:
        # CHANGE 1: Removed "— Last 12 Months"
        st.header("Network Health")
        st.caption("Rolling 12-month view across all active clinics")
        
        # ... your existing Network Health KPI cards ...
        # ... your existing charts ...
    
    # ---- TAB 2: Same-City Expansion ----
    with tab2:
        st.header("Same-City Expansion Analysis")
        st.caption("Where should we add clinics in cities we already operate in?")
        
        # CHANGE 2: CEO summary cards — ADD THIS
        # Assuming you have `city_expansion_df` already computed:
        # render_same_city_summary(city_expansion_df)
        
        # Example with hardcoded values (replace with your actual data):
        example_city_df = pd.DataFrame({
            'city': ['Kolkata', 'Bhubaneswar', 'Bhopal', 'Ahmedabad', 'Pune'],
            'clinics': [3, 1, 1, 2, 3],
            'cabins': [6, 2, 2, 4, 6],
            'cei_score': [36, 36, 34, 34, 33],
            'l3m_rev': [110, 100, 86.2, 86.5, 71.7],  # in lakhs
            'growth': [0.01, 0.10, 0.13, -0.19, -0.19],
            'rev_per_cabin': [17.9, 50.8, 43.1, 21.6, 12.0],
            'web_orders': [8000, 3000, 2000, 6000, 15000],
            'ebitda_pct': [0.38, 0.00, -0.06, 0.22, 0.26],
            'pincodes': [861, 380, 159, 330, 410]
        })
        render_same_city_summary(example_city_df)
        
        # ... your existing CEI table ...
        # ... your existing Deep-Dive: City Expansion Profile ...
    
    # ---- TAB 3: New-City Whitespace ----
    with tab3:
        st.header("New-City Whitespace Discovery")
        st.caption(
            "Cities where Gynoveda has zero clinics but proven patient demand — "
            "customers already buying online or traveling 20+ km to visit existing clinics."
        )
        
        # CHANGE 3: CEO summary cards — ADD THIS
        render_new_city_summary(
            dual_signal_pincodes=6000,
            ntb_visits_20km=1010000,    # 10.1L
            web_orders_20km=220000,      # 2.2L
            ntb_revenue_cr=74.9,
            new_cities_count=540,
            top_city="Lucknow",          # Replace with your actual top city
            top_city_orders=4500
        )
        
        # ... your existing whitespace table ...
        # ... your existing maps ...
    
    # ---- Cannibalization section (wherever it lives) ----
    # CHANGE 4: Add the guide
    render_cannibalization_guide()
    # ... your existing cannibalization scatter plot ...


# ============================================================
# QUICK COPY-PASTE: Minimal versions if you just want the cards
# ============================================================

def quick_same_city_cards():
    """
    Absolute minimum code to add Same-City summary cards.
    Copy-paste this into your Same-City tab after the header.
    Replace the values with your computed variables.
    """
    st.markdown("#### 📊 Network Snapshot — Existing Cities")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Cities with Clinics", "25", help="Unique cities in network")
        st.caption("61 clinics, 120 cabins")
    with c2:
        st.metric("Top Expansion Pick", "Kolkata", help="Highest CEI score")
        st.caption("CEI Score: 36")
    with c3:
        st.metric("Avg Rev / Cabin", "₹23.8L", help="Network average revenue per cabin")
    with c4:
        st.metric("Cities Growing", "14 of 25", help="Positive L3M growth")
        st.caption("L3M vs prior period")
    with c5:
        st.metric("Total Web Orders", "78K", help="Online demand in clinic cities")
        st.caption("3,200+ unique pincodes")
    st.divider()


def quick_new_city_cards():
    """
    Absolute minimum code to add New-City summary cards.
    Copy-paste this into your New-City tab after the header.
    Replace the values with your computed variables.
    """
    st.markdown("#### 🌍 Untapped Market Snapshot")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Proven Demand Pincodes", "6K", help="Pincodes with both web + clinic signals")
        st.caption("Both web orders + clinic visits")
    with c2:
        st.metric("Patients Traveling 20+ km", "10.1L", help="NTB visits from distant pincodes")
        st.caption("Underserved by current network")
    with c3:
        st.metric("Unserved Web Orders", "2.2L", help="Orders from areas with no clinic")
        st.caption("From areas with no clinic")
    with c4:
        st.metric("Revenue from Unserved Areas", "₹74.9 Cr", help="NTB revenue beyond 20km")
        st.caption("NTB revenue at 20+ km")
    with c5:
        st.metric("New Cities Ready to Enter", "540", help="Cities with dual-signal demand")
        st.caption("Dual-signal demand confirmed")
    st.divider()


# ============================================================
# CSS STYLING (add to your main app.py at the top)
# ============================================================

DASHBOARD_CSS = """
<style>
/* Orange-accent KPI cards matching Gynoveda brand */
[data-testid="stMetric"] {
    background: white;
    border-left: 4px solid #E8601C;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    color: #666 !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
}

/* Section headers */
h4 {
    color: #333 !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}

/* Divider spacing */
hr {
    margin: 12px 0 20px 0 !important;
}

/* Expander styling for cannibalization guide */
.streamlit-expanderHeader {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #444 !important;
}
</style>
"""

# Add this at the top of your app:
# st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
