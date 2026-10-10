import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };

export default async function InterviewsPage() {
  let interviews = [];
  try {
    const data = await api.interviews();
    interviews = data.interviews || [];
  } catch {
    interviews = [
      { id: 1, company_name: "TechCorp Dubai", job_title: "AI Engineer", scheduled_at: "2026-10-15T10:00:00", country: "UAE", platform: "zoom", meeting_link: "https://zoom.us/j/example" },
      { id: 2, company_name: "FinTech London", job_title: "ML Engineer", scheduled_at: "2026-10-17T14:00:00", country: "UK", platform: "teams" },
    ];
  }

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Interviews</h1>
      {interviews.length === 0 ? (
        <div style={{ color: "#6B7280", textAlign: "center", padding: 60 }}>No interviews scheduled</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {interviews.map((iv: typeof interviews[0]) => (
            <div key={iv.id} style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 20, display: "flex", alignItems: "center", gap: 16 }}>
              <span style={{ fontSize: 28 }}>{FLAGS[iv.country] || "🌍"}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#F9FAFB" }}>{iv.company_name}</div>
                <div style={{ fontSize: 13, color: "#9CA3AF", marginTop: 2 }}>{iv.job_title}</div>
                <div style={{ fontSize: 12, color: "#6B7280", marginTop: 4 }}>📍 {iv.platform}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#2DD4BF" }}>
                  {new Date(iv.scheduled_at).toLocaleDateString()}
                </div>
                <div style={{ fontSize: 12, color: "#6B7280", marginTop: 2 }}>
                  {new Date(iv.scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
                {iv.meeting_link && (
                  <a href={iv.meeting_link} target="_blank" rel="noreferrer"
                    style={{ fontSize: 11, color: "#6366F1", fontWeight: 600, marginTop: 6, display: "block" }}>
                    Join Meeting →
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
