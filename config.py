"""
Expansion Intelligence Platform — Industry Configuration
=========================================================
Defines verticals, terminology, modules, KPIs, and scoring dimensions
for each supported industry. Add a new vertical by extending VERTICALS dict.
"""

# ── Industry Vertical Definitions ─────────────────────────────────────

VERTICALS = {
    "healthcare": {
        "name": "Healthcare",
        "icon": "🏥",
        "tagline": "Clinic networks, wellness chains & diagnostic centers",
        "color_primary": "#667eea",
        "color_accent": "#764ba2",
        "terminology": {
            "location": "Clinic",
            "locations": "Clinics",
            "customer": "Patient",
            "customers": "Patients",
            "transaction": "Consultation",
            "transactions": "Consultations",
            "product": "Treatment",
            "products": "Treatments",
            "revenue_unit": "₹",
            "catchment_label": "Patient Catchment",
        },
        "kpi_cards": [
            {"key": "total_orders", "label": "Online Orders", "fmt": "{:,.0f}"},
            {"key": "total_revenue", "label": "Online Revenue", "fmt": "₹{:.1f} Cr", "divisor": 1e7},
            {"key": "clinic_firsttime_qty", "label": "Clinic First-Time Patients", "fmt": "{:,.0f}"},
            {"key": "states_covered", "label": "States with Demand", "fmt": "{:,.0f}"},
        ],
        "modules": [
            "dashboard", "map_explorer", "market_scoring",
            "location_performance", "product_intelligence",
            "expansion_intelligence", "ivf_analysis",
            "data_explorer", "data_upload", "setup_guide"
        ],
        "sub_verticals": ["Gynoveda", "Custom Healthcare"],
        "scoring_dimensions": {
            "D1": {"name": "Online Demand Density", "weight": 0.20, "universal": True},
            "D2": {"name": "Health Indicator Gap", "weight": 0.15, "universal": False},
            "D3": {"name": "Competition Vacuum", "weight": 0.15, "universal": True},
            "D4": {"name": "Infrastructure Readiness", "weight": 0.15, "universal": True},
            "D5": {"name": "Demographic Fit", "weight": 0.15, "universal": True},
            "D6": {"name": "Digital Adoption", "weight": 0.10, "universal": True},
            "D7": {"name": "Retail Ecosystem", "weight": 0.10, "universal": True},
        },
    },

    "fashion_retail": {
        "name": "Fashion & Apparel Retail",
        "icon": "👗",
        "tagline": "Fashion brands, apparel chains & lifestyle stores",
        "color_primary": "#e84393",
        "color_accent": "#fd79a8",
        "terminology": {
            "location": "Store",
            "locations": "Stores",
            "customer": "Shopper",
            "customers": "Shoppers",
            "transaction": "Sale",
            "transactions": "Sales",
            "product": "Category",
            "products": "Categories",
            "revenue_unit": "₹",
            "catchment_label": "Shopper Catchment",
        },
        "kpi_cards": [
            {"key": "total_orders", "label": "Online Transactions", "fmt": "{:,.0f}"},
            {"key": "total_revenue", "label": "Online Revenue", "fmt": "₹{:.1f} Cr", "divisor": 1e7},
            {"key": "store_footfall", "label": "Store Footfall", "fmt": "{:,.0f}"},
            {"key": "cities_covered", "label": "Cities Covered", "fmt": "{:,.0f}"},
        ],
        "modules": [
            "dashboard", "map_explorer", "market_scoring",
            "location_performance", "product_intelligence",
            "expansion_intelligence",
            "data_explorer", "data_upload", "setup_guide"
        ],
        "sub_verticals": ["Custom Fashion Brand"],
        "scoring_dimensions": {
            "D1": {"name": "Online Demand Density", "weight": 0.20, "universal": True},
            "D2": {"name": "Fashion Spend Index", "weight": 0.15, "universal": False},
            "D3": {"name": "Competition Vacuum", "weight": 0.15, "universal": True},
            "D4": {"name": "Mall & Retail Infrastructure", "weight": 0.15, "universal": True},
            "D5": {"name": "Demographic Fit (18-45 income)", "weight": 0.15, "universal": True},
            "D6": {"name": "Digital Adoption", "weight": 0.10, "universal": True},
            "D7": {"name": "Footfall Density", "weight": 0.10, "universal": True},
        },
    },

    "real_estate": {
        "name": "Real Estate & Residential",
        "icon": "🏗️",
        "tagline": "Residential developers, plotted communities & townships",
        "color_primary": "#00b894",
        "color_accent": "#55efc4",
        "terminology": {
            "location": "Project",
            "locations": "Projects",
            "customer": "Buyer",
            "customers": "Buyers",
            "transaction": "Booking",
            "transactions": "Bookings",
            "product": "Property Type",
            "products": "Property Types",
            "revenue_unit": "₹",
            "catchment_label": "Buyer Catchment",
        },
        "kpi_cards": [
            {"key": "total_leads", "label": "Total Leads", "fmt": "{:,.0f}"},
            {"key": "total_revenue", "label": "Booking Value", "fmt": "₹{:.0f} Cr", "divisor": 1e7},
            {"key": "avg_price_sqft", "label": "Avg ₹/sqft", "fmt": "₹{:,.0f}"},
            {"key": "cities_covered", "label": "Markets Covered", "fmt": "{:,.0f}"},
        ],
        "modules": [
            "dashboard", "map_explorer", "market_scoring",
            "location_performance",
            "expansion_intelligence",
            "data_explorer", "data_upload", "setup_guide"
        ],
        "sub_verticals": ["Custom Real Estate Developer"],
        "scoring_dimensions": {
            "D1": {"name": "Demand (Lead Density)", "weight": 0.20, "universal": True},
            "D2": {"name": "Price Appreciation Trend", "weight": 0.15, "universal": False},
            "D3": {"name": "Supply Gap", "weight": 0.15, "universal": True},
            "D4": {"name": "Infra & Connectivity", "weight": 0.20, "universal": True},
            "D5": {"name": "Demographic Fit (HH income)", "weight": 0.15, "universal": True},
            "D6": {"name": "Regulatory Ease", "weight": 0.10, "universal": False},
            "D7": {"name": "Social Infrastructure", "weight": 0.05, "universal": True},
        },
    },

    "mall_development": {
        "name": "Mall Development & Mgmt",
        "icon": "🏬",
        "tagline": "Shopping centres, mixed-use retail & commercial complexes",
        "color_primary": "#6c5ce7",
        "color_accent": "#a29bfe",
        "terminology": {
            "location": "Mall / Centre",
            "locations": "Malls / Centres",
            "customer": "Visitor",
            "customers": "Visitors",
            "transaction": "Tenant Lease",
            "transactions": "Tenant Leases",
            "product": "Retail Category",
            "products": "Retail Categories",
            "revenue_unit": "₹",
            "catchment_label": "Visitor Catchment",
        },
        "kpi_cards": [
            {"key": "total_footfall", "label": "Annual Footfall", "fmt": "{:,.0f}"},
            {"key": "total_revenue", "label": "Rental Revenue", "fmt": "₹{:.1f} Cr", "divisor": 1e7},
            {"key": "occupancy_pct", "label": "Avg Occupancy %", "fmt": "{:.1f}%"},
            {"key": "cities_covered", "label": "Cities Covered", "fmt": "{:,.0f}"},
        ],
        "modules": [
            "dashboard", "map_explorer", "market_scoring",
            "location_performance",
            "expansion_intelligence", "tenant_mix",
            "data_explorer", "data_upload", "setup_guide"
        ],
        "sub_verticals": ["Custom Mall Developer"],
        "scoring_dimensions": {
            "D1": {"name": "Catchment Population", "weight": 0.20, "universal": True},
            "D2": {"name": "Retail Spend Potential", "weight": 0.15, "universal": False},
            "D3": {"name": "Competition Vacuum", "weight": 0.15, "universal": True},
            "D4": {"name": "Transport Accessibility", "weight": 0.20, "universal": True},
            "D5": {"name": "Income & Lifestyle Fit", "weight": 0.15, "universal": True},
            "D6": {"name": "Land Availability", "weight": 0.10, "universal": False},
            "D7": {"name": "Anchor Tenant Pipeline", "weight": 0.05, "universal": False},
        },
    },

    "fnb_qsr": {
        "name": "F&B / QSR Chains",
        "icon": "🍔",
        "tagline": "Restaurants, quick-service chains, cloud kitchens & cafés",
        "color_primary": "#e17055",
        "color_accent": "#fab1a0",
        "terminology": {
            "location": "Outlet",
            "locations": "Outlets",
            "customer": "Diner",
            "customers": "Diners",
            "transaction": "Order",
            "transactions": "Orders",
            "product": "Menu Category",
            "products": "Menu Categories",
            "revenue_unit": "₹",
            "catchment_label": "Delivery Catchment",
        },
        "kpi_cards": [
            {"key": "total_orders", "label": "Total Orders", "fmt": "{:,.0f}"},
            {"key": "total_revenue", "label": "Gross Revenue", "fmt": "₹{:.1f} Cr", "divisor": 1e7},
            {"key": "avg_order_value", "label": "Avg Order Value", "fmt": "₹{:,.0f}"},
            {"key": "cities_covered", "label": "Cities Covered", "fmt": "{:,.0f}"},
        ],
        "modules": [
            "dashboard", "map_explorer", "market_scoring",
            "location_performance", "product_intelligence",
            "expansion_intelligence",
            "data_explorer", "data_upload", "setup_guide"
        ],
        "sub_verticals": ["Custom F&B Brand"],
        "scoring_dimensions": {
            "D1": {"name": "Order Density (Online)", "weight": 0.20, "universal": True},
            "D2": {"name": "Food Delivery Penetration", "weight": 0.15, "universal": False},
            "D3": {"name": "Competition Saturation", "weight": 0.15, "universal": True},
            "D4": {"name": "High-Street / Mall Access", "weight": 0.15, "universal": True},
            "D5": {"name": "Demographic Fit (young urban)", "weight": 0.15, "universal": True},
            "D6": {"name": "Delivery Infra (Swiggy/Zomato)", "weight": 0.10, "universal": False},
            "D7": {"name": "Rent Feasibility", "weight": 0.10, "universal": True},
        },
    },
}


# ── Helper Functions ──────────────────────────────────────────────────

def get_vertical(key: str) -> dict:
    """Get vertical config by key."""
    return VERTICALS.get(key, VERTICALS["healthcare"])

def get_term(vertical_key: str, term: str) -> str:
    """Get industry-specific term (e.g., 'location' → 'Clinic' for healthcare)."""
    v = get_vertical(vertical_key)
    return v["terminology"].get(term, term)

def get_modules(vertical_key: str) -> list:
    """Get list of enabled module keys for a vertical."""
    return get_vertical(vertical_key).get("modules", [])

def has_module(vertical_key: str, module: str) -> bool:
    """Check if a module is enabled for a vertical."""
    return module in get_modules(vertical_key)

def get_scoring(vertical_key: str) -> dict:
    """Get scoring dimension config for a vertical."""
    return get_vertical(vertical_key).get("scoring_dimensions", {})

def all_vertical_keys() -> list:
    """Return all registered vertical keys."""
    return list(VERTICALS.keys())

def vertical_selector_options() -> list:
    """Return formatted options for sidebar selector."""
    return [
        {"key": k, "label": f"{v['icon']} {v['name']}", "tagline": v["tagline"]}
        for k, v in VERTICALS.items()
    ]


# ── Universal Module Registry ────────────────────────────────────────

MODULE_REGISTRY = {
    "dashboard":                {"label": "Dashboard",              "icon": "🏠", "page": "streamlit_app.py"},
    "map_explorer":             {"label": "Map Explorer",           "icon": "🗺️", "page": "pages/1_Map_Explorer.py"},
    "market_scoring":           {"label": "Market Scoring",         "icon": "📊", "page": "pages/2_Market_Scoring.py"},
    "location_performance":     {"label": "Location Performance",   "icon": "📍", "page": "pages/3_Location_Performance.py"},
    "product_intelligence":     {"label": "Product Intelligence",   "icon": "📦", "page": "pages/4_Product_Intelligence.py"},
    "expansion_intelligence":   {"label": "Expansion Intelligence", "icon": "🚀", "page": "pages/5_Expansion_Planner.py"},
    "ivf_analysis":             {"label": "IVF Market Analysis",    "icon": "🧬", "page": "pages/6_IVF_Analysis.py"},
    "tenant_mix":               {"label": "Tenant Mix Optimizer",   "icon": "🏪", "page": "pages/6_Tenant_Mix.py"},
    "data_explorer":            {"label": "Data Explorer",          "icon": "📂", "page": "pages/7_Browse_Data.py"},
    "data_upload":              {"label": "Upload & Refresh",       "icon": "📤", "page": "pages/8_Upload_Refresh.py"},
    "setup_guide":              {"label": "Setup Guide",            "icon": "⚙️", "page": "pages/9_Configuration.py"},
}
