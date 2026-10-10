import { api, type DashboardData } from "@/lib/api";
import DashboardClient from "./DashboardClient";

export const dynamic = "force-dynamic";

const DEMO: DashboardData = {
  total_applications: 142,
  applications_today: 8,
  applications_this_week: 34,
  jobs_scraped: 380,
  success_rate: 4.2,
  interview_rate: 12.7,
  offers_received: 6,
  by_country: { UAE: 52, UK: 41, SA: 28, Germany: 21, USA: 31 },
  by_status: { applied: 89, interview_scheduled: 18, offer_received: 6, rejected: 29 },
  upcoming_interviews: [
    { id: 1, company_name: "TechCorp Dubai", job_title: "AI Engineer", scheduled_at: "2026-10-15T10:00:00", country: "UAE", platform: "zoom" },
    { id: 2, company_name: "FinTech London", job_title: "ML Engineer", scheduled_at: "2026-10-17T14:00:00", country: "UK", platform: "teams" },
  ],
  recent_activity: [
    { id: 1, company_name: "Noon.com", job_title: "Senior AI Engineer", country: "UAE", status: "applied", applied_at: "2026-10-10", platform: "linkedin" },
    { id: 2, company_name: "Deliveroo", job_title: "Data Scientist", country: "UK", status: "interview_scheduled", applied_at: "2026-10-09", platform: "reed" },
    { id: 3, company_name: "Google", job_title: "ML Engineer", country: "USA", status: "applied", applied_at: "2026-10-09", platform: "glassdoor" },
    { id: 4, company_name: "STC", job_title: "AI Consultant", country: "SA", status: "offer_received", applied_at: "2026-10-08", platform: "bayt" },
  ],
};

export default async function DashboardPage() {
  let data: DashboardData;
  try {
    data = await api.dashboard();
  } catch {
    data = DEMO;
  }
  return <DashboardClient data={data} />;
}
