import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };

export default async function ResumesPage() {
  let versions = [];
  try {
    const data = await api.resumeVersions();
    versions = data.versions || [];
  } catch {
    versions = [
      { id: 1, job_title: "Senior AI Engineer", company_name: "Noon.com", country: "UAE", created_at: "2026-10-10", customization_summary: "Tailored for AI/ML role, emphasized LangChain and RAG experience" },
      { id: 2, job_title: "ML Engineer", company_name: "Google", country: "USA", created_at: "2026-10-09", customization_summary: "US format, compensation negotiation language included" },
      { id: 3, job_title: "Data Scientist", company_name: "SAP", country: "Germany", created_at: "2026-10-08", customization_summary: "German market: EU work eligibility, GDPR experience highlighted" },
    ];
  }

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Resume Versions</h1>
      <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1F2937" }}>
              {["Job Title", "Company", "Country", "Date", "Customization", ""].map(h => (
                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {versions.map((v: typeof versions[0], i: number) => (
              <tr key={v.id} style={{ borderBottom: i < versions.length - 1 ? "1px solid #1A2234" : "none" }}>
                <td style={{ padding: "14px 16px", fontSize: 13, color: "#F9FAFB", fontWeight: 500 }}>{v.job_title}</td>
                <td style={{ padding: "14px 16px", fontSize: 13, color: "#9CA3AF" }}>{v.company_name}</td>
                <td style={{ padding: "14px 16px", fontSize: 16 }}>{FLAGS[v.country] || v.country}</td>
                <td style={{ padding: "14px 16px", fontSize: 12, color: "#6B7280" }}>{v.created_at?.slice(0, 10)}</td>
                <td style={{ padding: "14px 16px", fontSize: 12, color: "#6B7280", maxWidth: 260 }}>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.customization_summary}</div>
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <button style={{ padding: "5px 12px", borderRadius: 6, border: "1px solid #2DD4BF", background: "transparent", color: "#2DD4BF", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>PDF</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
