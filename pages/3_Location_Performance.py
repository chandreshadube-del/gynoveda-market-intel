"""
Expansion Intelligence Platform -- Location Performance
========================================================
Universal location/outlet/store/clinic performance analytics.
Includes NTB Show Rate analysis when clinic appointment data is available.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import get_vertical, get_term
from db import load_table

st.set_page_config(page_title="Location Performance", page_icon="📍", layout="wide")

V = st.session_state.get("vertical", "healthcare")
vc = get_vertical(V)
pri = vc["color_primary"]
loc = get_term(V, "location")
locs = get_term(V, "locations")
cust = get_term(V, "customer")
custs = get_term(V, "customers")
txn = get_term(V, "transactions")

st.markdown(
    f'<span style="background:linear-gradient(135deg,{pri},{vc["color_accent"]});'
    f'color:white;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600">'
    f'{vc["icon"]} {vc["name"]}</span>',
    unsafe_allow_html=True,
)
st.title(f"📍 {loc} Performance Dashboard")

# Load all available data
perf = load_table("clinic_performance")
monthly = load_table("clinic_monthly_trend")
zip_summary = load_table("clinic_zip_summary")
ntb_show = load_table("ntb_show_clinic")
ntb_summary = load_table("ntb_show_summary")

# Determine what data is available
has_ntb = not ntb_show.empty
has_perf = not perf.empty
has_zip = not zip_summary.empty
has_monthly = not monthly.empty

if not has_ntb and not has_perf:
    st.info(
        f"No {loc.lower()} performance data loaded. "
        "Go to **Upload & Refresh** to import NTB Show or Clinic ZipData files."
    )
    st.stop()

# Data source indicator
sources = []
if has_ntb:
    sources.append(f"NTB Show ({len(ntb_show)} clinics)")
if has_perf and not has_ntb:
    sources.append(f"Clinic Performance ({len(perf)} locations)")
if has_zip:
    sources.append(f"ZipData ({len(zip_summary)} catchments)")
if has_monthly:
    sources.append(f"Monthly Trends ({len(monthly)} records)")
st.caption("Data sources: " + " | ".join(sources))


# Detect NTB Show columns
appt_cols = [c for c in perf.columns if c.startswith('appt_')] if has_perf else []
show_cols = [c for c in perf.columns if c.startswith('show_')] if has_perf else []
months = [c.replace('appt_', '') for c in appt_cols]
has_show_data = len(appt_cols) > 0

# Key column detection
if has_perf:
    clinic_name_col = 'clinic_name' if 'clinic_name' in perf.columns else perf.columns[0]
else:
    clinic_name_col = None


# == KPI Row ==============================================================
if has_perf and has_show_data:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Clinics", f"{len(perf):,}")
    with c2:
        total_appts = perf['total_appts'].sum() if 'total_appts' in perf.columns else 0
        st.metric("Total NTB Appts", f"{total_appts:,.0f}")
    with c3:
        avg_show = perf['total_show_rate'].mean() if 'total_show_rate' in perf.columns else 0
        st.metric("Avg Show Rate", f"{avg_show:.1%}")
    with c4:
        cabins_total = perf['cabins'].sum() if 'cabins' in perf.columns else 0
        st.metric("Total Cabins", f"{int(cabins_total):,}")
    with c5:
        if 'launch_date' in perf.columns:
            perf['launch_date'] = pd.to_datetime(perf['launch_date'], errors='coerce')
            newest = perf['launch_date'].max()
            st.metric("Latest Launch", newest.strftime('%b %Y') if pd.notna(newest) else "--")
        else:
            st.metric("Regions", f"{perf['region'].nunique() if 'region' in perf.columns else '--'}")
elif has_perf:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(f"Total {locs}", f"{perf[clinic_name_col].nunique():,}")
    with c2:
        qty_col = next((c for c in ['total_qty', 'total_orders', 'quantity', 'total_appts'] if c in perf.columns), None)
        if qty_col:
            st.metric(f"Total {txn}", f"{perf[qty_col].sum():,.0f}")
    with c3:
        ft_col = next((c for c in ['firsttime_qty', 'new_customers', 'first_time'] if c in perf.columns), None)
        if ft_col:
            st.metric(f"First-Time {custs}", f"{perf[ft_col].sum():,.0f}")
    with c4:
        if has_zip and 'unique_pincodes' in zip_summary.columns:
            st.metric("Pincodes Served", f"{zip_summary['unique_pincodes'].sum():,.0f}")

st.divider()


# == Main Tabs ============================================================
if has_show_data:
    tab_names = ["NTB Show Rankings", "Monthly Trends", "Show Rate Analysis", "Catchment Analysis"]
else:
    tab_names = ["Performance Table", "Monthly Trends", "Catchment Analysis"]

tabs = st.tabs(tab_names)
tab_idx = 0


# == TAB: NTB Show Rankings / Performance Table ===========================
with tabs[tab_idx]:
    if has_show_data:
        st.subheader("Clinic Rankings -- Appointments & Show Rates")

        filter_c1, filter_c2 = st.columns(2)
        with filter_c1:
            regions = ["All"] + sorted(perf['region'].dropna().unique().tolist()) if 'region' in perf.columns else ["All"]
            sel_region = st.selectbox("Filter by Region", regions, key="perf_region")
        with filter_c2:
            if 'city_code' in perf.columns:
                cities_list = ["All"] + sorted(perf['city_code'].dropna().astype(str).unique().tolist())
                sel_city = st.selectbox("Filter by City", cities_list, key="perf_city")
            else:
                sel_city = "All"

        filtered = perf.copy()
        if sel_region != "All" and 'region' in filtered.columns:
            filtered = filtered[filtered['region'] == sel_region]
        if sel_city != "All" and 'city_code' in filtered.columns:
            filtered = filtered[filtered['city_code'].astype(str) == sel_city]

        if filtered.empty:
            st.info("No clinics match the selected filters.")
        else:
            sort_by = st.radio(
                "Sort by:",
                ["Total Appointments", "Show Rate", "Appointments per Cabin"],
                horizontal=True, key="sort_clinics"
            )

            plot_df = filtered.copy()
            if 'cabins' in plot_df.columns:
                plot_df['appts_per_cabin'] = plot_df['total_appts'] / plot_df['cabins'].replace(0, 1)
            else:
                plot_df['appts_per_cabin'] = plot_df['total_appts']

            if sort_by == "Total Appointments":
                plot_df = plot_df.sort_values('total_appts', ascending=True)
                x_col, color_col = 'total_appts', 'total_show_rate'
            elif sort_by == "Show Rate":
                plot_df = plot_df.sort_values('total_show_rate', ascending=True)
                x_col, color_col = 'total_show_rate', 'total_appts'
            else:
                plot_df = plot_df.sort_values('appts_per_cabin', ascending=True)
                x_col, color_col = 'appts_per_cabin', 'total_show_rate'

            hover_dict = {'total_appts': ':,.0f'}
            if 'city_code' in plot_df.columns:
                hover_dict['city_code'] = True
            if 'region' in plot_df.columns:
                hover_dict['region'] = True
            if 'cabins' in plot_df.columns:
                hover_dict['cabins'] = True

            fig = px.bar(
                plot_df.tail(30), x=x_col, y=clinic_name_col,
                orientation='h', color=color_col,
                color_continuous_scale='RdYlGn',
                hover_data=hover_dict,
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                height=max(400, min(len(plot_df), 30) * 22),
                margin=dict(t=10, l=10), yaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)

            # Detail table
            display_cols = [c for c in [clinic_name_col, 'city_code', 'region', 'cabins',
                                        'total_appts', 'total_show_rate'] if c in filtered.columns]
            tbl = filtered[display_cols].copy().sort_values(
                'total_appts', ascending=False
            )
            st.dataframe(tbl, use_container_width=True, height=400, hide_index=True)
    else:
        st.subheader(f"{loc} Rankings")
        sort_col = next((c for c in ['total_qty', 'total_orders', 'quantity', 'total_appts']
                         if c in perf.columns), None)
        if sort_col:
            display_df = perf.sort_values(sort_col, ascending=False)
        else:
            display_df = perf
        st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)

        if sort_col:
            top20 = perf.nlargest(20, sort_col)
            fig = px.bar(top20, x=clinic_name_col, y=sort_col, color_discrete_sequence=[pri], text=sort_col)
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=400, xaxis_tickangle=-45, xaxis_title="", yaxis_title=sort_col)
            st.plotly_chart(fig, use_container_width=True)

tab_idx += 1


# == TAB: Monthly Trends ==================================================
with tabs[tab_idx]:
    if has_show_data and has_perf:
        st.subheader("Monthly NTB Appointment Trends")

        default_clinics = (
            perf.nlargest(5, 'total_appts')[clinic_name_col].tolist()
            if 'total_appts' in perf.columns
            else perf[clinic_name_col].head(5).tolist()
        )
        sel_clinics = st.multiselect(
            "Select clinics to compare:",
            perf[clinic_name_col].tolist(),
            default=default_clinics, key="trend_clinics"
        )

        if sel_clinics and months:
            trend_data = []
            for _, row in perf[perf[clinic_name_col].isin(sel_clinics)].iterrows():
                for m, ac, sc in zip(months, appt_cols, show_cols):
                    appt_val = row.get(ac, None)
                    show_val = row.get(sc, None)
                    if pd.notna(appt_val):
                        trend_data.append({
                            'Clinic': row[clinic_name_col],
                            'Month': m,
                            'Appointments': appt_val,
                            'Show Rate': show_val if pd.notna(show_val) else None
                        })
            trend_df = pd.DataFrame(trend_data)

            if not trend_df.empty:
                tab_appt, tab_show = st.tabs(["Appointments", "Show Rate"])

                with tab_appt:
                    fig_trend = px.line(
                        trend_df, x='Month', y='Appointments', color='Clinic',
                        markers=True, color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_trend.update_layout(height=400, margin=dict(t=10), xaxis_tickangle=-45)
                    st.plotly_chart(fig_trend, use_container_width=True)

                with tab_show:
                    show_df = trend_df.dropna(subset=['Show Rate'])
                    if not show_df.empty:
                        fig_show = px.line(
                            show_df, x='Month', y='Show Rate', color='Clinic',
                            markers=True, color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig_show.update_layout(
                            height=400, margin=dict(t=10),
                            xaxis_tickangle=-45, yaxis_tickformat='.0%'
                        )
                        st.plotly_chart(fig_show, use_container_width=True)
                    else:
                        st.info("No show rate data available for selected clinics.")
        else:
            st.info("Select at least one clinic to see trends.")

    elif has_monthly:
        st.subheader(f"Monthly {txn} Trends")
        clinic_col_m = next((c for c in ['clinic_loc', 'clinic', monthly.columns[0]]
                             if c in monthly.columns), monthly.columns[0])
        clinics_avail = sorted(monthly[clinic_col_m].unique())
        selected_locs = st.multiselect(
            f"Select {locs}", clinics_avail,
            default=clinics_avail[:5], key="trend_locs"
        )

        if selected_locs:
            filt_m = monthly[monthly[clinic_col_m].isin(selected_locs)]
            date_col = next((c for c in ['month', 'date', 'period'] if c in filt_m.columns), None)
            val_col = next((c for c in ['qty', 'total_qty', 'quantity', 'orders'] if c in filt_m.columns), None)

            if date_col and val_col:
                fig = px.line(filt_m, x=date_col, y=val_col, color=clinic_col_m,
                              markers=True, color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(height=400, xaxis_title="", yaxis_title=val_col)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload NTB Show or monthly trend data to see time-series analysis.")

tab_idx += 1


# == TAB: Show Rate Analysis (NTB only) ===================================
if has_show_data:
    with tabs[tab_idx]:
        st.subheader("Show Rate Deep Dive")

        if 'total_show_rate' in perf.columns and 'total_appts' in perf.columns:
            st.markdown("**Appointment Volume vs Show Rate** -- identify high-volume/high-conversion clinics")

            scatter_kwargs = dict(
                x='total_appts', y='total_show_rate',
                hover_name=clinic_name_col,
                labels={'total_appts': 'Total Appointments', 'total_show_rate': 'Show Rate'},
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            if 'cabins' in perf.columns:
                scatter_kwargs['size'] = 'cabins'
            if 'region' in perf.columns:
                scatter_kwargs['color'] = 'region'

            fig_scatter = px.scatter(perf, **scatter_kwargs)
            fig_scatter.update_layout(height=450, margin=dict(t=10), yaxis_tickformat='.0%')

            avg_appts = perf['total_appts'].mean()
            avg_show = perf['total_show_rate'].mean()
            fig_scatter.add_hline(y=avg_show, line_dash="dash", line_color="gray",
                                  annotation_text=f"Avg Show: {avg_show:.1%}")
            fig_scatter.add_vline(x=avg_appts, line_dash="dash", line_color="gray",
                                  annotation_text=f"Avg Appts: {avg_appts:,.0f}")
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("Top-right quadrant = best performers (high volume + high show rate). "
                       "Bubble size = cabin count.")

            st.divider()

            # Region-level summary
            if 'region' in perf.columns:
                st.markdown("**Region-Level NTB Summary**")
                agg_dict = {
                    'region': 'count',
                    'total_appts': 'sum',
                    'total_show_rate': 'mean',
                }
                if 'cabins' in perf.columns:
                    agg_dict['cabins'] = 'sum'
                region_agg = perf.groupby('region').agg(**{
                    'clinics': ('region', 'count'),
                    'total_appts': ('total_appts', 'sum'),
                    'avg_show_rate': ('total_show_rate', 'mean'),
                }).reset_index().sort_values('total_appts', ascending=False)

                region_agg['avg_show_rate'] = region_agg['avg_show_rate'].apply(lambda x: f"{x:.1%}")
                st.dataframe(region_agg, use_container_width=True, height=300, hide_index=True)

            st.divider()

            # NTB Show Summary (Area-level)
            if not ntb_summary.empty:
                st.markdown("**Area-Level NTB Summary (from NTB Show file)**")
                summ_cols = [c for c in ['Area', 'Region', 'Total_Appts', 'Total_Show_Rate'] if c in ntb_summary.columns]
                display_summ = ntb_summary[summ_cols].copy()
                display_summ = display_summ.dropna(subset=['Area'] if 'Area' in display_summ.columns else [display_summ.columns[0]])
                st.dataframe(display_summ, use_container_width=True, height=300, hide_index=True)

    tab_idx += 1


# == TAB: Catchment Analysis ==============================================
with tabs[tab_idx]:
    if has_zip:
        st.subheader(f"{get_term(V, 'catchment_label')} -- Pincode Distribution")

        clinic_col_z = next((c for c in ['clinic_loc', 'Clinic_Loc', 'clinic', zip_summary.columns[0]]
                             if c in zip_summary.columns), zip_summary.columns[0])

        selected_loc = st.selectbox(
            f"Select {loc}", sorted(zip_summary[clinic_col_z].unique()),
            key="catchment_loc"
        )

        loc_data = zip_summary[zip_summary[clinic_col_z] == selected_loc]
        if not loc_data.empty:
            st.dataframe(loc_data, use_container_width=True, height=400, hide_index=True)

            val_z = next((c for c in ['total_qty', 'quantity', 'orders'] if c in loc_data.columns), None)
            if val_z:
                top_pins = loc_data.nlargest(20, val_z)
                pin_col = next((c for c in ['unique_pincodes', 'zip', 'pincode'] if c in top_pins.columns),
                               top_pins.columns[1])
                fig = px.bar(top_pins, x=pin_col, y=val_z, color_discrete_sequence=[pri])
                fig.update_layout(height=350, xaxis_title="Pincode", xaxis_type='category')
                st.plotly_chart(fig, use_container_width=True)

        # Overall scatter
        if 'unique_pincodes' in zip_summary.columns:
            qty_z = next((c for c in ['total_qty', 'quantity'] if c in zip_summary.columns), None)
            rev_z = next((c for c in ['total_revenue', 'revenue'] if c in zip_summary.columns), None)
            if qty_z:
                st.divider()
                st.markdown(f"**{loc} Coverage Overview** -- pincodes served vs total volume")
                scatter_kw = dict(
                    x='unique_pincodes', y=qty_z,
                    hover_name=clinic_col_z,
                    labels={'unique_pincodes': 'Pincodes Served', qty_z: 'Total Customers'}
                )
                if rev_z:
                    scatter_kw['size'] = rev_z
                color_z = next((c for c in ['zone', 'Zone', 'region', 'Region', 'state', 'State']
                                if c in zip_summary.columns), None)
                if color_z:
                    scatter_kw['color'] = color_z

                fig_cz = px.scatter(zip_summary, **scatter_kw)
                fig_cz.update_layout(height=450, margin=dict(t=10))
                st.plotly_chart(fig_cz, use_container_width=True)
                st.caption("Each dot = one clinic location. Bubble size = revenue. "
                           "Top-right = high reach + high volume.")
    else:
        st.info("Upload Clinic NTB ZipData to see catchment analysis.")
