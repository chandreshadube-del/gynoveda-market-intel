# Census & CEI Upload Patch

## Files Changed (3 files, 1,113 lines total)

### 1. db.py
Added 7 new table definitions:
- `census_district_demographics` — 640 districts, demographics & workforce
- `census_hh_assets` — Household infrastructure & asset ownership %
- `state_health_spending` — State-level NFHS-5 + HCES MPCE data
- `cei_district_scores` — Pre-computed CEI with 4 sub-indices + overall score
- `cei_methodology` — CEI scoring methodology reference
- `smart_cities` — 100 Smart Cities with selection rounds
- `amrut_cities` — 40+ AMRUT cities with population

### 2. pages/8_Upload_Refresh.py (431 lines)
Added 3 new upload sections:
- **Section 7: Census District Demographics** — Multi-sheet Excel support, auto-detects sheet→table mapping
- **Section 8: CEI Scoring Data** — Uploads pre-computed CEI, auto-detects CEI Score column
- **Section 9: City Classifications** — Smart Cities + AMRUT data upload

### 3. pages/2_Market_Scoring.py (444 lines)
Major upgrade — now supports:
- District-level analysis (640 districts) when CEI data is uploaded
- State vs District toggle
- State/Tier multi-select filters
- Top N district slider (10-100)
- District radar charts (top 5)
- State-aggregated CEI heatmap
- Census Data Explorer tab (demographics + HH infrastructure charts)
- CSV download of filtered rankings
- Backwards compatible — still works with state-only data

## Upload Mapping

| Excel File | Upload Section | Target Tables |
|---|---|---|
| District_Demographics_Census2011.xlsx | Section 7 | census_district_demographics, census_hh_assets, state_health_spending |
| CEI_Scoring_Data.xlsx | Section 8 | cei_district_scores, cei_methodology |
| City_Classifications_India.xlsx | Section 9 | smart_cities, amrut_cities |

## Deployment
Replace these 3 files in your GitHub repo. Streamlit Cloud auto-redeploys.
