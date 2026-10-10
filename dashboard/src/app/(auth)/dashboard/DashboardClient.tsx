"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { DashboardData } from "@/lib/api";

const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };

const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  applied:             { bg: "rgba(99,102,241,0.15)",  color: "#6366F1" },
  interview_scheduled: { bg: "rgba(245,158,11,0.15)",  color: "#F59E0B" },
  offer_received:      { bg: "rgba(16,185,129,0.15)",  color: "#10B981" },
  rejected:            { bg: "rgba(239,68,68,0.15)",   color: "#EF4444" },
};

function Card({ children, style = {} }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 20, ...style }}>
      {children}
    </div>
  );
}

function StatCard({ label, value, sub, color = "#2DD4BF" }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <Card>
      <div style={{ fontSize: 32, fontWeight: 700, color, lineHeight: 1 }}>{value ?? "—"}</div>
      <div style={{ fontSize: 12, color: "#6B7280", marginTop: 6 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: "#10B981", marginTop: 4 }}>{sub}</div>}
    </Card>
  );
}

export default function DashboardClient({ data }: { data: DashboardData }) {
  const countryData = Object.entries(data.by_country || {}).map(([name, applications]) => ({ name, applications }));
  const funnel = [
    { name: "Scraped",    value: data.jobs_scraped || 0,         fill: "#374151" },
    { name: "Applied",    value: data.total_applications || 0,   fill: "#6366F1" },
    { name: "Interviews", value: Math.round((data.total_applications || 0) * (data.interview_rate || 0) / 100), fill: "#F59E0B" },
    { name: "Offers",     value: data.offers_received || 0,      fill: "#10B981" },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Dashboard</h1>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 24 }}>
        <StatCard label="Total Applications" value={data.total_applications} sub={`${data.applications_today} today`} color="#6366F1" />
        <StatCard label="This Week"          value={data.applications_this_week} sub="Applications sent" color="#2DD4BF" />
        <StatCard label="Interview Rate"     value={`${data.interview_rate}%`} sub="Applied → Interview" color="#F59E0B" />
        <StatCard label="Offer Rate"         value={`${data.success_rate}%`} sub={`${data.offers_received} offers`} color="#10B981" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        {/* Bar chart */}
        <Card>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB", marginBottom: 16 }}>Applications by Country</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={countryData} barSize={32}>
              <XAxis dataKey="name" tick={{ fill: "#6B7280", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6B7280", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 8, color: "#F9FAFB" }} />
              <Bar dataKey="applications" fill="#6366F1" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Funnel */}
        <Card>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB", marginBottom: 16 }}>Application Funnel</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {funnel.map(item => (
              <div key={item.name}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: "#9CA3AF" }}>{item.name}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#F9FAFB" }}>{item.value}</span>
                </div>
                <div style={{ background: "#1F2937", borderRadius: 4, height: 6 }}>
                  <div style={{ background: item.fill, height: 6, borderRadius: 4, width: `${Math.min(100, item.value / Math.max(funnel[0].value, 1) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Upcoming Interviews */}
        <Card>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB", marginBottom: 16 }}>Upcoming Interviews</div>
          {(data.upcoming_interviews || []).length === 0 ? (
            <div style={{ color: "#6B7280", fontSize: 13 }}>No upcoming interviews</div>
          ) : (
            (data.upcoming_interviews || []).map(iv => (
              <div key={iv.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid #1F2937" }}>
                <span style={{ fontSize: 20 }}>{FLAGS[iv.country] || "🌍"}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{iv.company_name}</div>
                  <div style={{ fontSize: 11, color: "#6B7280" }}>{iv.job_title} · {iv.platform}</div>
                </div>
                <div style={{ fontSize: 11, color: "#2DD4BF" }}>
                  {new Date(iv.scheduled_at).toLocaleDateString()}
                </div>
              </div>
            ))
          )}
        </Card>

        {/* Recent Activity */}
        <Card>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB", marginBottom: 16 }}>Recent Activity</div>
          {(data.recent_activity || []).map(a => {
            const ss = STATUS_STYLE[a.status] || { bg: "rgba(107,114,128,0.15)", color: "#6B7280" };
            return (
              <div key={a.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid #1F2937" }}>
                <span style={{ fontSize: 20 }}>{FLAGS[a.country] || "🌍"}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{a.company_name}</div>
                  <div style={{ fontSize: 11, color: "#6B7280" }}>{a.job_title}</div>
                </div>
                <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 20, background: ss.bg, color: ss.color }}>
                  {a.status?.replace(/_/g, " ")}
                </span>
              </div>
            );
          })}
        </Card>
      </div>
    </div>
  );
}
