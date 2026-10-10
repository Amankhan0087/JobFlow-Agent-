"use client";
import type { Application } from "@/lib/api";

const COLUMNS = [
  { key: "new",                label: "New",        color: "#6B7280" },
  { key: "applied",            label: "Applied",    color: "#6366F1" },
  { key: "interview_scheduled",label: "Interview",  color: "#F59E0B" },
  { key: "interviewed",        label: "Interviewed",color: "#8B5CF6" },
  { key: "offer_received",     label: "Offer",      color: "#10B981" },
  { key: "rejected",           label: "Rejected",   color: "#EF4444" },
];

const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };

function JobCard({ app }: { app: Application }) {
  const days = app.applied_at
    ? Math.floor((Date.now() - new Date(app.applied_at).getTime()) / 86400000)
    : null;

  return (
    <div style={{ background: "#1A2234", border: "1px solid #1F2937", borderRadius: 10, padding: 14, marginBottom: 10, cursor: "pointer" }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = "#374151")}
      onMouseLeave={e => (e.currentTarget.style.borderColor = "#1F2937")}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB", lineHeight: 1.3, flex: 1, paddingRight: 8 }}>{app.job_title || "Unknown Role"}</div>
        <span style={{ fontSize: 16 }}>{FLAGS[app.country] || "🌍"}</span>
      </div>
      <div style={{ fontSize: 12, color: "#6B7280", marginBottom: 8 }}>{app.company_name}</div>
      {(app.salary_min || app.salary_max) && (
        <div style={{ fontSize: 11, color: "#2DD4BF", marginBottom: 6 }}>
          {app.currency} {app.salary_min?.toLocaleString()} – {app.salary_max?.toLocaleString()}
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 10, color: "#4B5563", background: "#111827", padding: "2px 6px", borderRadius: 4 }}>{app.platform || "direct"}</span>
        {days !== null && <span style={{ fontSize: 10, color: "#6B7280" }}>{days}d ago</span>}
      </div>
    </div>
  );
}

export default function PipelineClient({ kanban }: { kanban: Record<string, Application[]> }) {
  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Job Pipeline</h1>
      <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 16 }}>
        {COLUMNS.map(col => {
          const cards = kanban[col.key] || [];
          return (
            <div key={col.key} style={{ minWidth: 240, flex: "0 0 240px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: col.color }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: "#9CA3AF" }}>{col.label}</span>
                <span style={{ fontSize: 11, color: "#4B5563", marginLeft: "auto", background: "#1F2937", borderRadius: 10, padding: "1px 7px" }}>{cards.length}</span>
              </div>
              <div style={{ background: "#0D1526", borderRadius: 10, padding: 10, minHeight: 200 }}>
                {cards.length === 0
                  ? <div style={{ color: "#374151", fontSize: 12, textAlign: "center", padding: "20px 0" }}>Empty</div>
                  : cards.map(app => <JobCard key={app.id} app={app} />)
                }
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
