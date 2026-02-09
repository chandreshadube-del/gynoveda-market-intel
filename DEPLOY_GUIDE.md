# FY27 Annual Plan — Deployment Guide

## What's Updated

### New Section: State-Wise Standard Show% Benchmark (Section 1B)
- Grouped bar chart: Gynoveda actual Show% vs industry standard per state
- Benchmarks derived from Dantas et al. 2018 meta-analysis, eSanjeevani telemedicine data, Punjab RCT, IHCI studies
- Base standard: 20% for online-to-offline models, adjusted ±5ppt by state infrastructure
- Revenue impact KPIs for outperforming vs underperforming states
- Full detail table with gap analysis + new expansion state benchmarks

### New Section: Unit Economics (Section 5B)
- Actual cost structure per clinic:
  - Rent: ₹1,50,000/month
  - Doctors (2): ₹1,00,000/month
  - Clinic Manager: ₹30,000/month
  - Housekeeping: ₹10,000/month
  - Receptionist: ₹15,000/month
  - Electricity: ₹5,000/month
  - **Total Monthly OpEx: ₹3,10,000 (₹3.1L)**
  - **Capex (construction): ₹28,00,000 (₹28L)**
- Breakeven: **35 NTB shows/month**
- P&L waterfall chart (avg clinic)
- Breakeven sensitivity curve
- 61-clinic profitability scatter map
- Capex payback period distribution
- Loss-making clinic callout

### Updated: New-City Revenue Projections
- Now uses ₹3.1L actual OpEx and ₹28L capex (not rough estimates)
- Accurate payback periods per city

## App Structure (2 pages only)
```
streamlit_app.py          → Homepage (Online vs Offline dashboard)
pages/0_FY27_Annual_Plan.py → CEO Decision Dashboard (10 sections)
db.py                     → Data layer (CSV fallback)
config.py                 → Configuration
data/                     → 25 CSV files + 1 JSON
```

## Deploy to Streamlit Cloud

### Option A: Replace files in existing repo
```bash
cd your-repo

# Copy the 3 updated Python files
cp streamlit_app.py .
cp 0_FY27_Annual_Plan.py pages/
cp db.py .

# Commit and push
git add .
git commit -m "FY27: State-wise Show% benchmarks + Unit Economics (₹3.1L OpEx + ₹28L capex)"
git push
```

### Option B: Full repo replacement
```bash
# Copy entire expansion_intel_app/ folder contents to your repo
git add .
git commit -m "FY27 Annual Plan: Complete rebuild with benchmarks + unit economics"
git push
```

## Dashboard Sections (in order)
1. **The Case for Caution** — 5 KPIs showing decline
2. **State-Wise Show% Benchmark** ← NEW — Gynoveda vs industry standard
3. **Same-City Expansion Qualifier** — ≥150 NTB shows threshold
4. **NTB:Population Ratio Engine** — 3.8 shows/lakh median
5. **New City Expansion** — Ratio-validated projections
6. **Fix Before Expand** — Show% uplift = ₹0 CAC revenue
7. **Unit Economics** ← NEW — ₹3.1L OpEx, ₹28L capex, 35-show breakeven
8. **FY27 Revenue Projection** — Ratio-adjusted, scenario-tested
9. **Scenario Matrix** — Conservative / Base / Optimistic
10. **The Ask** — Proof-gated 4-phase expansion
