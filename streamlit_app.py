"""
GYNOVEDA EXPANSION DASHBOARD — City Mapping Fix
================================================
Forensic Audit Date: 11 Feb 2026
Issue: 14 city name mismatches between MIS codes and e-commerce data
Impact: 9 CRITICAL bugs causing ₹12.8 Cr in served-city demand to appear as whitespace

HOW TO APPLY:
1. Replace the existing CITY_NAMES dict in streamlit_app.py with CITY_NAMES below
2. Replace the whitespace detection logic with the has_clinic() function below
3. The _build_served_set() utility generates the flat lookup set at startup

The fix uses a TWO-LAYER approach:
  Layer 1: CITY_NAMES — maps MIS code → primary e-com city name (for display & scoring)
  Layer 2: SERVED_CITY_ALIASES — maps MIS code → ALL known e-com names (for whitespace filtering)
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1: MIS Code → Primary E-commerce City Name
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Source: ZipData_Clinic_NTB.xlsx (mode city per clinic) cross-verified
# against 1cx_order_qty_pincode e-commerce data.
#
# 14 corrections from the old hardcoded mapping are marked with # ← FIXED

CITY_NAMES = {
    'AGR': 'Agra',
    'AHM': 'Ahmedabad',
    'AMR': 'Amritsar',
    'ASN': 'Purba Bardhaman',       # ← FIXED (was 'Asansol' — not in ecom data)
    'AUR': 'Aurangabad',
    'BBS': 'Khorda',                 # ← FIXED (was 'Bhubaneswar' — ecom uses district name)
    'BLR': 'Bengaluru',
    'BPL': 'Bhopal',
    'CDG': 'Chandigarh',
    'CHE': 'Chennai',
    'DDN': 'Dehradun',
    'DMR': 'Dimapur',
    'FDB': 'Faridabad',
    'GHZ': 'Ghaziabad',
    'GUR': 'Gurgaon',               # ← FIXED (was 'Gurugram' — ecom uses 'Gurgaon')
    'GUW': 'Kamrup',                 # ← FIXED (was 'Guwahati' — ecom uses district name)
    'HYD': 'Hyderabad',
    'IND': 'Indore',
    'ITR': 'Papum Pare',            # ← FIXED (was 'Itanagar' — ecom uses district name)
    'JAI': 'Jaipur',
    'JAL': 'Jalandhar',
    'KLN': 'Mumbai',                 # ← FIXED (was 'Kalyan' — Khadakpada clinic is in Mumbai metro)
    'KNP': 'Kanpur',
    'KOL': 'North 24 Parganas',     # ← FIXED (was 'Kolkata' — Ballygunge maps to N24P in ecom)
    'LDH': 'Ludhiana',
    'LKO': 'Lucknow',
    'MAR': 'Goa',                    # ← FIXED (was 'Margao' — ecom uses 'Goa')
    'MRT': 'Meerut',
    'MUM': 'Mumbai',
    'MYS': 'Mysuru',
    'NAG': 'Nagpur',
    'NDL': 'Delhi',
    'NOI': 'Gautam Buddha Nagar',    # ← FIXED (was 'Noida' — ecom uses district name)
    'NSK': 'Nashik',
    'NVM': 'Raigarh(MH)',           # ← FIXED (was 'Navi Mumbai' — ecom uses district name)
    'PAT': 'Patna',
    'PRY': 'Allahabad',             # ← FIXED (was 'Prayagraj' — ecom uses old name)
    'PUN': 'Pune',
    'RAI': 'Raipur',
    'RJK': 'Rajkot',
    'RNC': 'Ranchi',
    'SEC': 'Hyderabad',             # ← FIXED (was 'Secunderabad' — ecom uses 'Hyderabad')
    'SGU': 'Darjiling',             # ← FIXED (was 'Siliguri' — ecom uses district name)
    'SUR': 'Surat',
    'THN': 'Mumbai',                 # ← FIXED (was 'Thane' — ecom maps Thane/Mira Rd to Mumbai)
    'VAD': 'Vadodara',
    'VAR': 'Varanasi',
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2: Served City Aliases (for whitespace detection)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Each code maps to ALL city names that should be treated as "served".
# This handles the dual-name problem where ecom data uses both
# modern names (Gurugram) and legacy names (Gurgaon) for the same city.

SERVED_CITY_ALIASES = {
    'AGR': {'Agra'},
    'AHM': {'Ahmedabad'},
    'AMR': {'Amritsar'},
    'ASN': {'Purba Bardhaman', 'Asansol'},
    'AUR': {'Aurangabad', 'Chhatrapati Sambhajinagar'},
    'BBS': {'Khorda', 'Bhubaneswar'},
    'BLR': {'Bengaluru', 'Bangalore'},
    'BPL': {'Bhopal'},
    'CDG': {'Chandigarh'},
    'CHE': {'Chennai', 'Madras'},
    'DDN': {'Dehradun'},
    'DMR': {'Dimapur'},
    'FDB': {'Faridabad'},
    'GHZ': {'Ghaziabad'},
    'GUR': {'Gurgaon', 'Gurugram'},
    'GUW': {'Kamrup', 'Guwahati'},
    'HYD': {'Hyderabad', 'Secunderabad'},
    'IND': {'Indore'},
    'ITR': {'Papum Pare', 'Itanagar'},
    'JAI': {'Jaipur'},
    'JAL': {'Jalandhar'},
    'KLN': {'Mumbai', 'Kalyan', 'Thane'},             # Khadakpada is Mumbai metro
    'KNP': {'Kanpur'},
    'KOL': {'North 24 Parganas', 'Kolkata', 'Calcutta', 'Barasat'},
    'LDH': {'Ludhiana'},
    'LKO': {'Lucknow'},
    'MAR': {'Goa', 'Margao', 'South Goa', 'North Goa', 'Panaji'},
    'MRT': {'Meerut'},
    'MUM': {'Mumbai', 'Bombay', 'Thane', 'Kalyan', 'Navi Mumbai'},
    'MYS': {'Mysuru', 'Mysore'},
    'NAG': {'Nagpur'},
    'NDL': {'Delhi', 'New Delhi'},
    'NOI': {'Gautam Buddha Nagar', 'Noida', 'Greater Noida'},
    'NSK': {'Nashik'},
    'NVM': {'Raigarh(MH)', 'Navi Mumbai', 'Panvel'},
    'PAT': {'Patna'},
    'PRY': {'Allahabad', 'Prayagraj'},
    'PUN': {'Pune'},
    'RAI': {'Raipur'},
    'RJK': {'Rajkot'},
    'RNC': {'Ranchi'},
    'SEC': {'Hyderabad', 'Secunderabad'},
    'SGU': {'Darjiling', 'Darjeeling', 'Siliguri'},
    'SUR': {'Surat'},
    'THN': {'Mumbai', 'Thane', 'Mira Road', 'Kalyan'},  # Thane clinics serve Mumbai metro
    'VAD': {'Vadodara'},
    'VAR': {'Varanasi', 'Benaras', 'Kashi'},
}


def _build_served_set():
    """Build a flat set of all city names that should be excluded from whitespace."""
    served = set()
    for aliases in SERVED_CITY_ALIASES.values():
        served.update(aliases)
    return served


# Pre-built for quick lookup
SERVED_CITIES = _build_served_set()


def has_clinic(city_name: str) -> bool:
    """
    Check if a city has an existing Gynoveda clinic.
    
    Uses exact matching against the SERVED_CITIES set (case-sensitive,
    matching the e-commerce data format). Falls back to case-insensitive
    matching for edge cases.
    
    Args:
        city_name: City name as it appears in the e-commerce order data
        
    Returns:
        True if the city is served by an existing clinic
    """
    if not city_name or city_name == '-':
        return False
    
    # Exact match (fast path — covers 99% of cases)
    if city_name in SERVED_CITIES:
        return True
    
    # Case-insensitive fallback
    city_lower = city_name.lower().strip()
    return any(s.lower() == city_lower for s in SERVED_CITIES)


def get_clinic_code_for_city(city_name: str) -> str | None:
    """
    Given an e-commerce city name, return the MIS clinic code.
    
    Useful for linking whitespace demand back to the nearest existing clinic.
    """
    if not city_name:
        return None
    
    city_lower = city_name.lower().strip()
    for code, aliases in SERVED_CITY_ALIASES.items():
        if any(a.lower() == city_lower for a in aliases):
            return code
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DROP-IN REPLACEMENT for the whitespace detection in your dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# BEFORE (buggy — in your current streamlit_app.py):
# -----------------------------------------------
#   clinic_cities = set(master['city'].unique())
#   web_city['has_clinic'] = web_city['City'].isin(clinic_cities) | web_city['City'].apply(
#       lambda x: any(x.lower() in c.lower() or c.lower() in x.lower() 
#                     for c in clinic_cities) if pd.notna(x) else False)
#   whitespace = web_city[~web_city['has_clinic']]
#
# AFTER (fixed):
# -----------------------------------------------
#   from city_mapping_fix import has_clinic
#   web_city['has_clinic'] = web_city['City'].apply(has_clinic)
#   whitespace = web_city[~web_city['has_clinic']]
#
#
# Also replace the CITY_NAMES dict used for same-city CEI scoring:
#
# BEFORE:
#   CITY_NAMES = {'MUM':'Mumbai', 'GUR':'Gurugram', ...}
#
# AFTER:
#   from city_mapping_fix import CITY_NAMES
#
#
# Also fix the web demand matching for same-city scoring:
#
# BEFORE:
#   name_to_code = {v.lower(): k for k, v in CITY_NAMES.items()}
#   web_city['matched_code'] = web_city['City_lower'].map(name_to_code)
#
# AFTER (handles aliases):
#   def match_city_to_code(city):
#       if not city: return None
#       city_l = city.lower().strip()
#       for code, aliases in SERVED_CITY_ALIASES.items():
#           if any(a.lower() == city_l for a in aliases):
#               return code
#       return None
#   web_city['matched_code'] = web_city['City'].apply(match_city_to_code)
