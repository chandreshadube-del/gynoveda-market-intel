import { useState, useMemo } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, AreaChart, Area, ComposedChart, PieChart, Pie, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from "recharts";

// ═══════════════════════════════════════════════════════════
// DATA
// ═══════════════════════════════════════════════════════════

const MONTHLY_CLINIC_TREND = [
  { month: "Jan 25", qty: 38331, rev: 315, visits: 17077, appt: 7631, showPct: 19.4 },
  { month: "Feb 25", qty: 53109, rev: 394, visits: 20312, appt: 11395, showPct: 16.8 },
  { month: "Mar 25", qty: 61803, rev: 475, visits: 23765, appt: 10700, showPct: 16.6 },
  { month: "Apr 25", qty: 74212, rev: 598, visits: 29262, appt: 13484, showPct: 20.4 },
  { month: "May 25", qty: 93878, rev: 725, visits: 36875, appt: 15948, showPct: 22.8 },
  { month: "Jun 25", qty: 121365, rev: 927, visits: 46918, appt: 19623, showPct: 22.4 },
  { month: "Jul 25", qty: 150308, rev: 1105, visits: 50186, appt: 27030, showPct: 23.3 },
  { month: "Aug 25", qty: 172717, rev: 1221, visits: 51814, appt: 32457, showPct: 22.3 },
  { month: "Sep 25", qty: 166051, rev: 1181, visits: 47794, appt: 28477, showPct: 21.0 },
  { month: "Oct 25", qty: 152121, rev: 1042, visits: 39286, appt: 26807, showPct: 20.0 },
  { month: "Nov 25", qty: 174238, rev: 1278, visits: 42206, appt: 28941, showPct: 19.0 },
  { month: "Dec 25", qty: 168289, rev: 1227, visits: 38101, appt: 24195, showPct: 20.0 },
  { month: "Jan 26", qty: 159511, rev: 1191, visits: 35481, appt: 23641, showPct: 19.0 },
];

const ZONE_DATA = [
  { zone: "West 1", qty: 501783, rev: 4010, appt: 64051, showPct: 24.1, clinics: 15, color: "#FF6B35" },
  { zone: "North 1", qty: 328416, rev: 2318, appt: 56422, showPct: 17.5, clinics: 13, color: "#1E96FC" },
  { zone: "West 2", qty: 283382, rev: 1961, appt: 46699, showPct: 18.5, clinics: 12, color: "#F0C808" },
  { zone: "South", qty: 236559, rev: 1840, appt: 30786, showPct: 26.8, clinics: 8, color: "#2EC4B6" },
  { zone: "East", qty: 229272, rev: 1594, appt: 28761, showPct: 25.7, clinics: 8, color: "#9B5DE5" },
  { zone: "North 2", qty: 159011, rev: 1226, appt: 43610, showPct: 13.8, clinics: 5, color: "#F15BB5" },
];

const TOP_CLINICS = [
  { name: "Malad", zone: "West 1", region: "MMR", rev: 734.7, qty: 92710, pincodes: 485, cabin: 3, appt: 7082, showPct: 30.5, launch: "Oct 2023" },
  { name: "JP Nagar", zone: "South", region: "BMR", rev: 553.0, qty: 69539, pincodes: 467, cabin: 3, appt: 5779, showPct: 33.7, launch: "Dec 2023" },
  { name: "Lajpat", zone: "North 1", region: "NCR", rev: 513.2, qty: 69911, pincodes: 436, cabin: 3, appt: 8613, showPct: 21.1, launch: "Jan 2024" },
  { name: "Dadar", zone: "West 1", region: "MMR", rev: 505.7, qty: 67822, pincodes: 289, cabin: 2, appt: 8298, showPct: 23.3, launch: "Aug 2024" },
  { name: "Viman Nagar", zone: "West 1", region: "PMR", rev: 463.6, qty: 56597, pincodes: 342, cabin: 2, appt: 7108, showPct: 21.8, launch: "Sep 2023" },
  { name: "Rajouri", zone: "North 1", region: "NCR", rev: 450.8, qty: 62270, pincodes: 260, cabin: 3, appt: 6754, showPct: 17.2, launch: "Nov 2023" },
  { name: "Ballygunge", zone: "East", region: "KMR", rev: 437.2, qty: 57874, pincodes: 766, cabin: 2, appt: 6428, showPct: 27.1, launch: "Nov 2023" },
  { name: "Thane", zone: "West 1", region: "MMR", rev: 426.1, qty: 55610, pincodes: 242, cabin: 2, appt: 7207, showPct: 25.3, launch: "Jul 2024" },
  { name: "Badakdev", zone: "West 2", region: "Gujarat", rev: 412.9, qty: 64791, pincodes: 317, cabin: 2, appt: 8956, showPct: 20.9, launch: "Mar 2024" },
  { name: "Madhapur", zone: "South", region: "HMR", rev: 387.3, qty: 51836, pincodes: 355, cabin: 3, appt: 5889, showPct: 31.5, launch: "Mar 2024" },
  { name: "Kharghar", zone: "West 1", region: "MMR", rev: 385.0, qty: 48567, pincodes: 105, cabin: 2, appt: 4453, showPct: 28.6, launch: "Dec 2024" },
  { name: "Dharam", zone: "West 1", region: "ROM", rev: 359.2, qty: 48533, pincodes: 305, cabin: 2, appt: 9403, showPct: 15.6, launch: "Sep 2024" },
  { name: "Virar", zone: "West 1", region: "MMR", rev: 323.5, qty: 46709, pincodes: 95, cabin: 2, appt: 4638, showPct: 28.1, launch: "Oct 2024" },
  { name: "Sec-51", zone: "North 1", region: "NCR", rev: 308.0, qty: 42240, pincodes: 218, cabin: 2, appt: 6017, showPct: 20.3, launch: "May 2024" },
  { name: "Gomati", zone: "North 2", region: "UP", rev: 294.0, qty: 35227, pincodes: 413, cabin: 2, appt: 9485, showPct: 14.7, launch: "Jul 2024" },
];

const ECOM_YEARLY = [
  { year: "2020", orders: 17157, rev: 2.8 },
  { year: "2021", orders: 40701, rev: 7.6 },
  { year: "2022", orders: 140046, rev: 20.8 },
  { year: "2023", orders: 139248, rev: 27.3 },
  { year: "2024", orders: 40939, rev: 10.6 },
  { year: "2025", orders: 12921, rev: 3.3 },
];

const ECOM_TOP_CITIES = [
  { city: "Mumbai", orders: 33884, rev: 5.85, clinicRev: 18.72, hasClinic: true },
  { city: "Delhi", orders: 27248, rev: 4.72, clinicRev: 6.86, hasClinic: true },
  { city: "Bengaluru", orders: 24658, rev: 4.38, clinicRev: 7.20, hasClinic: true },
  { city: "Pune", orders: 14913, rev: 2.75, clinicRev: 5.74, hasClinic: true },
  { city: "Hyderabad", orders: 13653, rev: 2.48, clinicRev: 3.19, hasClinic: true },
  { city: "Gurgaon", orders: 6800, rev: 1.19, clinicRev: 0, hasClinic: false },
  { city: "Noida/GBN", orders: 6032, rev: 1.08, clinicRev: 1.73, hasClinic: true },
  { city: "Ghaziabad", orders: 5750, rev: 1.04, clinicRev: 0, hasClinic: false },
  { city: "Ahmedabad", orders: 5417, rev: 1.01, clinicRev: 2.40, hasClinic: true },
  { city: "Lucknow", orders: 4871, rev: 0.92, clinicRev: 1.65, hasClinic: true },
  { city: "Kolkata", orders: 4651, rev: 0.83, clinicRev: 5.80, hasClinic: true },
  { city: "Goa", orders: 4482, rev: 0.81, clinicRev: 0, hasClinic: true },
  { city: "Guwahati", orders: 4126, rev: 0.74, clinicRev: 0, hasClinic: true },
  { city: "Nagpur", orders: 3364, rev: 0.63, clinicRev: 1.91, hasClinic: true },
];

const REGION_APPT_DATA = [
  { name: "MMR", appt: 35021, showPct: 27.1 },
  { name: "PMR", appt: 12219, showPct: 24.5 },
  { name: "Gujarat", appt: 28256, showPct: 18.9 },
  { name: "NCR", appt: 35235, showPct: 17.6 },
  { name: "BMR", appt: 13032, showPct: 31.6 },
  { name: "KMR", appt: 12579, showPct: 23.3 },
  { name: "HMR", appt: 10662, showPct: 26.3 },
  { name: "UP", appt: 43610, showPct: 13.8 },
  { name: "Central", appt: 12165, showPct: 19.9 },
  { name: "Punjab", appt: 18271, showPct: 17.7 },
  { name: "NE", appt: 5520, showPct: 29.8 },
];

const STATE_ECOM = [
  { state: "Maharashtra", ecomRev: 12.18, clinicRev: 31.9, pincodes: 812 },
  { state: "Uttar Pradesh", ecomRev: 7.21, clinicRev: 12.4, pincodes: 747 },
  { state: "Karnataka", ecomRev: 6.20, clinicRev: 9.0, pincodes: 459 },
  { state: "Delhi", ecomRev: 4.72, clinicRev: 6.9, pincodes: 100 },
  { state: "Gujarat", ecomRev: 4.16, clinicRev: 8.7, pincodes: 497 },
  { state: "West Bengal", ecomRev: 3.69, clinicRev: 5.8, pincodes: 785 },
  { state: "Telangana", ecomRev: 3.17, clinicRev: 3.9, pincodes: 206 },
  { state: "Haryana", ecomRev: 3.05, clinicRev: 0, pincodes: 0 },
  { state: "Punjab", ecomRev: 2.88, clinicRev: 3.7, pincodes: 265 },
  { state: "Madhya Pradesh", ecomRev: 2.61, clinicRev: 3.1, pincodes: 232 },
];

// ═══════════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════════

const fmt = (n) => {
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(0)}L`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n?.toLocaleString("en-IN") ?? "—";
};

const fmtCompact = (n) => {
  if (n >= 100000) return `${(n / 1000).toFixed(0)}K`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n?.toLocaleString("en-IN") ?? "—";
};

const ZONE_COLORS = {
  "West 1": "#FF6B35",
  "North 1": "#1E96FC",
  "West 2": "#F0C808",
  "South": "#2EC4B6",
  "East": "#9B5DE5",
  "North 2": "#F15BB5",
};

// ═══════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "rgba(15,15,20,0.95)",
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: 8,
      padding: "10px 14px",
      fontSize: 12,
      color: "#E0E0E0",
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)"
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: "#fff" }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: p.color }} />
          <span style={{ color: "#999" }}>{p.name}:</span>
          <span style={{ fontWeight: 600 }}>{typeof p.value === "number" && p.value < 1 ? `${(p.value * 100).toFixed(1)}%` : p.value?.toLocaleString("en-IN")}</span>
        </div>
      ))}
    </div>
  );
};

function KPICard({ label, value, sub, accent, icon }) {
  return (
    <div style={{
      background: "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 16,
      padding: "20px 24px",
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: -20, right: -20, width: 80, height: 80,
        borderRadius: "50%", background: accent, opacity: 0.06, filter: "blur(20px)"
      }} />
      <div style={{ fontSize: 11, fontWeight: 500, color: "#888", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
        {icon && <span style={{ marginRight: 6 }}>{icon}</span>}{label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: "#fff", letterSpacing: "-0.02em", lineHeight: 1.1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: accent, marginTop: 6, fontWeight: 500 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0, letterSpacing: "-0.01em" }}>{title}</h2>
      {subtitle && <p style={{ fontSize: 12, color: "#666", margin: "4px 0 0", fontWeight: 400 }}>{subtitle}</p>}
    </div>
  );
}

function ZoneTag({ zone }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 600,
      background: `${ZONE_COLORS[zone] || "#666"}22`,
      color: ZONE_COLORS[zone] || "#666",
      letterSpacing: "0.03em",
    }}>{zone}</span>
  );
}

// ═══════════════════════════════════════════════════════════
// TABS
// ═══════════════════════════════════════════════════════════

const TABS = ["Command Center", "Clinic Deep Dive", "Online→Offline Flywheel", "Zone Intelligence"];

export default function NorthStarDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  const [sortClinic, setSortClinic] = useState("rev");
  const [selectedZone, setSelectedZone] = useState(null);

  const filteredClinics = useMemo(() => {
    let clinics = [...TOP_CLINICS];
    if (selectedZone) clinics = clinics.filter(c => c.zone === selectedZone);
    return clinics.sort((a, b) => b[sortClinic] - a[sortClinic]);
  }, [sortClinic, selectedZone]);

  const totalClinicRev = MONTHLY_CLINIC_TREND.reduce((s, m) => s + m.rev, 0);
  const latestMonth = MONTHLY_CLINIC_TREND[MONTHLY_CLINIC_TREND.length - 1];
  const prevMonth = MONTHLY_CLINIC_TREND[MONTHLY_CLINIC_TREND.length - 2];
  const momGrowth = ((latestMonth.rev - prevMonth.rev) / prevMonth.rev * 100).toFixed(1);

  return (
    <div style={{
      fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif",
      background: "#0A0A0F",
      color: "#E0E0E0",
      minHeight: "100vh",
      padding: 0,
    }}>
      {/* GOOGLE FONT */}
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />

      {/* HEADER */}
      <div style={{
        background: "linear-gradient(180deg, rgba(255,107,53,0.08) 0%, transparent 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        padding: "24px 32px 16px",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
              <div style={{
                width: 10, height: 10, borderRadius: "50%",
                background: "#2EC4B6", boxShadow: "0 0 12px #2EC4B6",
                animation: "pulse 2s infinite",
              }} />
              <span style={{ fontSize: 11, color: "#2EC4B6", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                Live • North Star
              </span>
            </div>
            <h1 style={{
              fontSize: 32, fontWeight: 800, color: "#fff",
              margin: 0, letterSpacing: "-0.03em",
              background: "linear-gradient(135deg, #fff 40%, #FF6B35 100%)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>
              Gynoveda Expansion Command
            </h1>
            <p style={{ fontSize: 13, color: "#555", margin: "6px 0 0", fontWeight: 400 }}>
              61 Clinics · 7,415 Pincodes · 6 Zones · Jan 2025 → Jan 2026
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "#555", marginBottom: 4 }}>Latest Period</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>Jan 2026</div>
            <div style={{ fontSize: 12, color: momGrowth > 0 ? "#F15BB5" : "#2EC4B6", fontWeight: 600 }}>
              {momGrowth > 0 ? "↓" : "↑"} {Math.abs(momGrowth)}% MoM
            </div>
          </div>
        </div>

        {/* TAB NAV */}
        <div style={{ display: "flex", gap: 4 }}>
          {TABS.map((tab, i) => (
            <button key={i} onClick={() => setActiveTab(i)} style={{
              padding: "8px 18px",
              borderRadius: 8,
              border: "none",
              background: activeTab === i ? "rgba(255,107,53,0.15)" : "transparent",
              color: activeTab === i ? "#FF6B35" : "#666",
              fontSize: 12,
              fontWeight: activeTab === i ? 700 : 500,
              cursor: "pointer",
              transition: "all 0.2s",
              fontFamily: "inherit",
            }}>{tab}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "24px 32px" }}>

        {/* ════════════════ TAB 0: COMMAND CENTER ════════════════ */}
        {activeTab === 0 && (
          <div>
            {/* KPI ROW */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 16, marginBottom: 32 }}>
              <KPICard label="Total NTB Appointments" value="2.70L" sub="Jan 25 – Jan 26" accent="#FF6B35" icon="📅" />
              <KPICard label="Avg Show Rate" value="20.6%" sub="National Average" accent="#2EC4B6" icon="✓" />
              <KPICard label="Clinic Revenue (NTB)" value={`₹${(totalClinicRev / 100).toFixed(0)}Cr`} sub="Cumulative 13 months" accent="#F0C808" icon="💰" />
              <KPICard label="Active Clinics" value="61" sub="Across 6 Zones" accent="#9B5DE5" icon="🏥" />
              <KPICard label="Pincode Reach" value="7,415" sub="Clinic Customers" accent="#1E96FC" icon="📍" />
              <KPICard label="E-Com 1CX Orders" value="3.91L" sub="₹72.3Cr Lifetime" accent="#F15BB5" icon="🛒" />
            </div>

            {/* REVENUE TREND */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24, marginBottom: 24,
            }}>
              <SectionHeader title="NTB Revenue Trajectory" subtitle="Monthly Clinic Revenue (₹ Lakhs) & Show Rate %" />
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={MONTHLY_CLINIC_TREND} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#FF6B35" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#FF6B35" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} domain={[10, 30]} unit="%" />
                  <Tooltip content={<CustomTooltip />} />
                  <Area yAxisId="left" type="monotone" dataKey="rev" name="Revenue (₹L)" fill="url(#revGrad)" stroke="#FF6B35" strokeWidth={2.5} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="showPct" name="Show Rate %" stroke="#2EC4B6" strokeWidth={2} dot={{ r: 3, fill: "#2EC4B6" }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* ZONE PERFORMANCE GRID */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24,
            }}>
              <SectionHeader title="Zone Performance Matrix" subtitle="Revenue, Appointments & Show Rate by Zone" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                {ZONE_DATA.map((z) => (
                  <div key={z.zone} style={{
                    background: `linear-gradient(135deg, ${z.color}08, transparent)`,
                    border: `1px solid ${z.color}20`,
                    borderRadius: 12, padding: 18,
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = `${z.color}50`}
                  onMouseLeave={e => e.currentTarget.style.borderColor = `${z.color}20`}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: z.color }}>{z.zone}</span>
                      <span style={{ fontSize: 11, color: "#666" }}>{z.clinics} clinics</span>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                      <div>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 2 }}>Revenue</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>₹{(z.rev / 100).toFixed(1)}Cr</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 2 }}>NTB Appts</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>{fmtCompact(z.appt)}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 2 }}>Show %</div>
                        <div style={{
                          fontSize: 16, fontWeight: 700,
                          color: z.showPct >= 25 ? "#2EC4B6" : z.showPct >= 20 ? "#F0C808" : "#F15BB5"
                        }}>{z.showPct}%</div>
                      </div>
                    </div>
                    {/* Revenue share bar */}
                    <div style={{ marginTop: 10, background: "rgba(255,255,255,0.04)", borderRadius: 4, height: 4, overflow: "hidden" }}>
                      <div style={{
                        width: `${(z.rev / 4010) * 100}%`,
                        height: "100%", background: z.color, borderRadius: 4,
                        transition: "width 0.5s",
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ════════════════ TAB 1: CLINIC DEEP DIVE ════════════════ */}
        {activeTab === 1 && (
          <div>
            {/* FILTERS */}
            <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center" }}>
              <span style={{ fontSize: 12, color: "#666" }}>Sort by:</span>
              {[
                { key: "rev", label: "Revenue" },
                { key: "qty", label: "Quantity" },
                { key: "showPct", label: "Show %" },
                { key: "pincodes", label: "Reach" },
              ].map(s => (
                <button key={s.key} onClick={() => setSortClinic(s.key)} style={{
                  padding: "6px 14px", borderRadius: 6, border: "1px solid",
                  borderColor: sortClinic === s.key ? "#FF6B35" : "rgba(255,255,255,0.08)",
                  background: sortClinic === s.key ? "rgba(255,107,53,0.12)" : "transparent",
                  color: sortClinic === s.key ? "#FF6B35" : "#888",
                  fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
                }}>{s.label}</button>
              ))}
              <div style={{ flex: 1 }} />
              <span style={{ fontSize: 12, color: "#666" }}>Zone:</span>
              <button onClick={() => setSelectedZone(null)} style={{
                padding: "6px 12px", borderRadius: 6, border: "1px solid",
                borderColor: !selectedZone ? "#9B5DE5" : "rgba(255,255,255,0.08)",
                background: !selectedZone ? "rgba(155,93,229,0.12)" : "transparent",
                color: !selectedZone ? "#9B5DE5" : "#888",
                fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
              }}>All</button>
              {Object.keys(ZONE_COLORS).map(z => (
                <button key={z} onClick={() => setSelectedZone(z)} style={{
                  padding: "6px 12px", borderRadius: 6, border: "1px solid",
                  borderColor: selectedZone === z ? ZONE_COLORS[z] : "rgba(255,255,255,0.08)",
                  background: selectedZone === z ? `${ZONE_COLORS[z]}20` : "transparent",
                  color: selectedZone === z ? ZONE_COLORS[z] : "#888",
                  fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
                }}>{z}</button>
              ))}
            </div>

            {/* CLINIC TABLE */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, overflow: "hidden",
            }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ background: "rgba(255,255,255,0.03)" }}>
                    {["#", "Clinic", "Zone", "Region", "Cabin", "Launch", "Revenue (₹L)", "Qty", "NTB Appts", "Show %", "Pincodes"].map(h => (
                      <th key={h} style={{
                        padding: "12px 14px", textAlign: "left", fontWeight: 600,
                        color: "#666", fontSize: 10, letterSpacing: "0.06em", textTransform: "uppercase",
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredClinics.map((c, i) => (
                    <tr key={c.name} style={{
                      borderBottom: "1px solid rgba(255,255,255,0.03)",
                      transition: "background 0.15s",
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                    >
                      <td style={{ padding: "10px 14px", color: "#444", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{i + 1}</td>
                      <td style={{ padding: "10px 14px", fontWeight: 700, color: "#fff" }}>{c.name}</td>
                      <td style={{ padding: "10px 14px" }}><ZoneTag zone={c.zone} /></td>
                      <td style={{ padding: "10px 14px", color: "#888" }}>{c.region}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{
                          display: "inline-block", padding: "2px 8px", borderRadius: 4,
                          background: c.cabin === 3 ? "rgba(46,196,182,0.12)" : "rgba(240,200,8,0.12)",
                          color: c.cabin === 3 ? "#2EC4B6" : "#F0C808",
                          fontSize: 11, fontWeight: 600,
                        }}>{c.cabin}C</span>
                      </td>
                      <td style={{ padding: "10px 14px", color: "#888", fontSize: 11 }}>{c.launch}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ fontWeight: 700, color: "#fff", fontFamily: "'JetBrains Mono', monospace" }}>
                            {c.rev.toFixed(0)}
                          </span>
                          <div style={{ flex: 1, background: "rgba(255,255,255,0.04)", borderRadius: 2, height: 4, maxWidth: 80 }}>
                            <div style={{ width: `${(c.rev / 735) * 100}%`, height: "100%", background: "#FF6B35", borderRadius: 2 }} />
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#ccc" }}>
                        {fmtCompact(c.qty)}
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#ccc" }}>
                        {fmtCompact(c.appt)}
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{
                          fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
                          color: c.showPct >= 28 ? "#2EC4B6" : c.showPct >= 22 ? "#F0C808" : "#F15BB5",
                        }}>{c.showPct}%</span>
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#ccc" }}>
                        {c.pincodes}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* CLINIC CHARTS */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 24 }}>
              <div style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                borderRadius: 16, padding: 24,
              }}>
                <SectionHeader title="Revenue vs Show Rate" subtitle="Bubble = Pincode Reach" />
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={filteredClinics.slice(0, 10)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#666" }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 10, fill: "#666" }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="rev" name="Revenue (₹L)" radius={[6, 6, 0, 0]}>
                      {filteredClinics.slice(0, 10).map((c, i) => (
                        <Cell key={i} fill={ZONE_COLORS[c.zone] || "#666"} fillOpacity={0.8} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                borderRadius: 16, padding: 24,
              }}>
                <SectionHeader title="Regional Show Rate Radar" subtitle="NTB Show % across metro regions" />
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={REGION_APPT_DATA}>
                    <PolarGrid stroke="rgba(255,255,255,0.08)" />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: "#999" }} />
                    <PolarRadiusAxis tick={{ fontSize: 9, fill: "#555" }} domain={[0, 35]} />
                    <Radar name="Show %" dataKey="showPct" stroke="#FF6B35" fill="#FF6B35" fillOpacity={0.15} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════ TAB 2: ONLINE→OFFLINE FLYWHEEL ════════════════ */}
        {activeTab === 2 && (
          <div>
            {/* FLYWHEEL KPIs */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 28 }}>
              <KPICard label="E-Com Lifetime Orders" value="3.91L" sub="₹72.3Cr Revenue" accent="#F15BB5" icon="🌐" />
              <KPICard label="Curative Share" value="91%" sub="₹66.4Cr of ₹72.3Cr" accent="#2EC4B6" icon="💊" />
              <KPICard label="Clinic NTB Revenue" value="₹105Cr" sub="14.1L Qty · 7,415 Pincodes" accent="#FF6B35" icon="🏥" />
              <KPICard label="Conversion Multiplier" value="1.45x" sub="Clinic Rev / E-Com Rev per city" accent="#F0C808" icon="🔄" />
            </div>

            {/* ECOM YEARLY TREND */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24, marginBottom: 24,
            }}>
              <SectionHeader title="E-Commerce 1CX Revenue Journey" subtitle="First-time customer orders by year (₹ Crores)" />
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={ECOM_YEARLY} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="year" tick={{ fontSize: 12, fill: "#888" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} unit="Cr" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="rev" name="Revenue (₹Cr)" radius={[8, 8, 0, 0]}>
                    {ECOM_YEARLY.map((_, i) => (
                      <Cell key={i} fill={i === 2 ? "#FF6B35" : i === 3 ? "#FF6B35" : "#FF6B3566"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* CITY FLYWHEEL MAP */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24,
            }}>
              <SectionHeader title="City-Level Online → Offline Flywheel" subtitle="E-commerce demand vs Clinic revenue by city. Blue bars = E-Com, Orange = Clinic" />
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={ECOM_TOP_CITIES} layout="vertical" margin={{ top: 5, right: 30, left: 70, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} unit="Cr" />
                  <YAxis type="category" dataKey="city" tick={{ fontSize: 11, fill: "#ccc" }} axisLine={false} tickLine={false} width={65} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="rev" name="E-Com Rev (₹Cr)" radius={[0, 4, 4, 0]} fill="#1E96FC" fillOpacity={0.7} barSize={12} />
                  <Bar dataKey="clinicRev" name="Clinic Rev (₹Cr)" radius={[0, 4, 4, 0]} fill="#FF6B35" fillOpacity={0.85} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 16, display: "flex", gap: 24 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 12, height: 12, borderRadius: 3, background: "#F15BB5" }} />
                  <span style={{ fontSize: 11, color: "#888" }}>🚩 Gurgaon & Ghaziabad: High e-com demand, no dedicated clinic</span>
                </div>
              </div>
            </div>

            {/* STATE COMPARISON */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24, marginTop: 24,
            }}>
              <SectionHeader title="State Demand → Clinic Revenue Conversion" subtitle="How well are we converting online demand into clinic revenue?" />
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: "rgba(255,255,255,0.03)" }}>
                      {["State", "E-Com Rev (₹Cr)", "Clinic Rev (₹Cr)", "Multiplier", "Pincodes", "Signal"].map(h => (
                        <th key={h} style={{
                          padding: "10px 14px", textAlign: "left", fontWeight: 600,
                          color: "#666", fontSize: 10, letterSpacing: "0.06em", textTransform: "uppercase",
                          borderBottom: "1px solid rgba(255,255,255,0.04)",
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {STATE_ECOM.map((s) => {
                      const mult = s.clinicRev > 0 ? (s.clinicRev / s.ecomRev).toFixed(1) : "—";
                      const signal = s.clinicRev === 0 ? "🔴 No clinic presence" :
                        parseFloat(mult) >= 2.0 ? "🟢 Strong conversion" :
                          parseFloat(mult) >= 1.0 ? "🟡 Moderate" : "🟠 Under-penetrated";
                      return (
                        <tr key={s.state} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                          <td style={{ padding: "10px 14px", fontWeight: 600, color: "#fff" }}>{s.state}</td>
                          <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", color: "#1E96FC" }}>₹{s.ecomRev.toFixed(2)}</td>
                          <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", color: "#FF6B35" }}>
                            {s.clinicRev > 0 ? `₹${s.clinicRev.toFixed(1)}` : "—"}
                          </td>
                          <td style={{ padding: "10px 14px", fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", color: "#fff" }}>{mult}x</td>
                          <td style={{ padding: "10px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#888" }}>{s.pincodes || "—"}</td>
                          <td style={{ padding: "10px 14px", fontSize: 11 }}>{signal}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════ TAB 3: ZONE INTELLIGENCE ════════════════ */}
        {activeTab === 3 && (
          <div>
            {/* ZONE COMPARISON */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24, marginBottom: 24,
            }}>
              <SectionHeader title="Zone Revenue & Efficiency" subtitle="Revenue share, appointments, and show rate conversion" />
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={ZONE_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="zone" tick={{ fontSize: 12, fill: "#ccc" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} label={{ value: "Revenue (₹L)", angle: -90, position: "insideLeft", fill: "#555", fontSize: 10 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} domain={[10, 30]} label={{ value: "Show %", angle: 90, position: "insideRight", fill: "#555", fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar yAxisId="left" dataKey="rev" name="Revenue (₹L)" radius={[8, 8, 0, 0]} barSize={48}>
                    {ZONE_DATA.map((z, i) => (
                      <Cell key={i} fill={z.color} fillOpacity={0.7} />
                    ))}
                  </Bar>
                  <Line yAxisId="right" type="monotone" dataKey="showPct" name="Show %" stroke="#fff" strokeWidth={2.5} dot={{ r: 5, fill: "#fff", stroke: "#0A0A0F", strokeWidth: 2 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* ZONE DETAIL CARDS */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              {ZONE_DATA.map((z) => {
                const zoneClinics = TOP_CLINICS.filter(c => c.zone === z.zone);
                const topClinic = zoneClinics[0];
                return (
                  <div key={z.zone} style={{
                    background: `linear-gradient(135deg, ${z.color}06, transparent)`,
                    border: `1px solid ${z.color}18`,
                    borderRadius: 16, padding: 24,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                      <div>
                        <h3 style={{ fontSize: 20, fontWeight: 800, color: z.color, margin: 0 }}>{z.zone}</h3>
                        <span style={{ fontSize: 11, color: "#555" }}>{z.clinics} clinics</span>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 22, fontWeight: 700, color: "#fff" }}>₹{(z.rev / 100).toFixed(1)}Cr</div>
                        <div style={{ fontSize: 11, color: "#666" }}>
                          {((z.rev / ZONE_DATA.reduce((s, zz) => s + zz.rev, 0)) * 100).toFixed(0)}% share
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
                      <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: 10, textAlign: "center" }}>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 4 }}>NTB Qty</div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#fff" }}>{fmtCompact(z.qty)}</div>
                      </div>
                      <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: 10, textAlign: "center" }}>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 4 }}>Appointments</div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#fff" }}>{fmtCompact(z.appt)}</div>
                      </div>
                      <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: 10, textAlign: "center" }}>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 4 }}>Show Rate</div>
                        <div style={{
                          fontSize: 14, fontWeight: 700,
                          color: z.showPct >= 25 ? "#2EC4B6" : z.showPct >= 20 ? "#F0C808" : "#F15BB5",
                        }}>{z.showPct}%</div>
                      </div>
                    </div>

                    {topClinic && (
                      <div style={{
                        background: "rgba(255,255,255,0.02)", borderRadius: 8, padding: 10,
                        border: "1px solid rgba(255,255,255,0.04)",
                      }}>
                        <div style={{ fontSize: 10, color: "#555", marginBottom: 4 }}>🏆 Top Clinic</div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>{topClinic.name}</span>
                          <span style={{ fontSize: 12, color: z.color, fontWeight: 600 }}>₹{topClinic.rev.toFixed(0)}L</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* MONTHLY BY ZONE */}
            <div style={{
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 16, padding: 24, marginTop: 24,
            }}>
              <SectionHeader title="Monthly Visits Trajectory" subtitle="Total clinic visits per month — tracking the growth flywheel" />
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={MONTHLY_CLINIC_TREND} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="visitGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#9B5DE5" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#9B5DE5" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="visits" name="Clinic Visits" fill="url(#visitGrad)" stroke="#9B5DE5" strokeWidth={2.5} dot={{ r: 3, fill: "#9B5DE5" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* FOOTER */}
      <div style={{
        padding: "16px 32px",
        borderTop: "1px solid rgba(255,255,255,0.04)",
        display: "flex", justifyContent: "space-between",
        fontSize: 11, color: "#333",
      }}>
        <span>Gynoveda Expansion Intelligence · Data: Jan 2025 – Jan 2026</span>
        <span>61 Clinics · 7,415 Pincodes · ₹105.2Cr Clinic NTB · ₹72.3Cr E-Com 1CX</span>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
      `}</style>
    </div>
  );
}
