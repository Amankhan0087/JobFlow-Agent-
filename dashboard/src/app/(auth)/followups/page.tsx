"use client";
import { useState, useEffect } from "react";
import { api, type FollowUp } from "@/lib/api";

const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };
const TYPE_COLOR: Record<string, { bg: string; color: string; label: string }> = {
  post_application: { bg: "rgba(99,102,241,0.15)", color: "#6366F1", label: "Post-Application" },
  post_interview:   { bg: "rgba(245,158,11,0.15)",  color: "#F59E0B", label: "Post-Interview" },
  status_check:     { bg: "rgba(107,114,128,0.15)", color: "#9CA3AF", label: "Status Check" },
  thank_you:        { bg: "rgba(16,185,129,0.15)",  color: "#10B981", label: "Thank You" },
};

const DEMO: FollowUp[] = [
  { id: 1, company_name: "Noon.com",    job_title: "Senior AI Engineer", country: "UAE", followup_type: "post_application", scheduled_at: "2026-10-12T09:00:00", status: "pending", email_subject: "Following Up: Senior AI Engineer Application" },
  { id: 2, company_name: "Deliveroo",   job_title: "Data Scientist",      country: "UK",  followup_type: "post_interview",   scheduled_at: "2026-10-11T10:00:00", status: "pending", email_subject: "Thank You – Data Scientist Interview" },
  { id: 3, company_name: "Google",      job_title: "ML Engineer",         country: "USA", followup_type: "status_check",     scheduled_at: "2026-10-13T09:00:00", status: "sent",    email_subject: "Status Update Request: ML Engineer" },
];

export default function FollowUpsPage() {
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [sending, setSending] = useState<number | null>(null);

  const load = async () => {
    try {
      const d = await api.followups();
      setFollowups(d.followups || []);
    } catch {
      setFollowups(DEMO);
    }
  };

  useEffect(() => { load(); }, []);

  const send = async (id: number) => {
    setSending(id);
    try {
      await api.sendFollowup(id);
      await load();
    } catch {}
    setSending(null);
  };

  const pending = followups.filter(f => f.status === "pending");
  const sent = followups.filter(f => f.status === "sent");

  const Row = ({ f }: { f: FollowUp }) => {
    const tc = TYPE_COLOR[f.followup_type] || TYPE_COLOR.status_check;
    const overdue = new Date(f.scheduled_at) < new Date();
    return (
      <div style={{ background: "#111827", border: `1px solid ${overdue && f.status === "pending" ? "rgba(239,68,68,0.3)" : "#1F2937"}`, borderRadius: 10, padding: 16, marginBottom: 10, display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ fontSize: 22 }}>{FLAGS[f.country] || "🌍"}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: "#F9FAFB" }}>{f.company_name}</span>
            <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 20, background: tc.bg, color: tc.color, fontWeight: 600 }}>{tc.label}</span>
            {overdue && f.status === "pending" && <span style={{ fontSize: 10, color: "#EF4444", fontWeight: 600 }}>OVERDUE</span>}
          </div>
          <div style={{ fontSize: 12, color: "#6B7280" }}>{f.job_title}</div>
          <div style={{ fontSize: 11, color: "#4B5563", marginTop: 2 }}>📧 {f.email_subject}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: overdue ? "#EF4444" : "#6B7280", marginBottom: 8 }}>
            {new Date(f.scheduled_at).toLocaleDateString()}
          </div>
          {f.status === "pending" ? (
            <button onClick={() => send(f.id)} disabled={sending === f.id} style={{ padding: "7px 16px", borderRadius: 7, border: "none", background: sending === f.id ? "#374151" : "#2DD4BF", color: sending === f.id ? "#9CA3AF" : "#0A0F1E", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
              {sending === f.id ? "Sending..." : "Send Now"}
            </button>
          ) : (
            <span style={{ fontSize: 11, color: "#10B981", fontWeight: 600 }}>✓ Sent</span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Follow-Up Tracker</h1>

      <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
        {[{ label: "Pending", val: pending.length, color: "#F59E0B" }, { label: "Sent", val: sent.length, color: "#10B981" }].map(s => (
          <div key={s.label} style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: "14px 20px", flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.val}</div>
            <div style={{ fontSize: 11, color: "#6B7280", marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {pending.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Pending</div>
          {pending.map(f => <Row key={f.id} f={f} />)}
        </div>
      )}
      {sent.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Sent</div>
          {sent.map(f => <Row key={f.id} f={f} />)}
        </div>
      )}
    </div>
  );
}
