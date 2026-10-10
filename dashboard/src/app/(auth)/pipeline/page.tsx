import { api } from "@/lib/api";
import PipelineClient from "./PipelineClient";

export const dynamic = "force-dynamic";

export default async function PipelinePage() {
  let kanban: Record<string, import("@/lib/api").Application[]> = {};
  try {
    const data = await api.applications();
    kanban = data.kanban || {};
  } catch {
    kanban = {
      applied: [
        { id: 1, job_title: "Senior AI Engineer", company_name: "Noon.com", country: "UAE", salary_min: 18000, salary_max: 25000, currency: "AED", platform: "linkedin", applied_at: new Date(Date.now() - 86400000 * 2).toISOString(), status: "applied" },
        { id: 2, job_title: "ML Engineer", company_name: "Google", country: "USA", salary_min: 160000, salary_max: 220000, currency: "USD", platform: "glassdoor", applied_at: new Date(Date.now() - 86400000 * 1).toISOString(), status: "applied" },
      ],
      interview_scheduled: [
        { id: 3, job_title: "Data Scientist", company_name: "Deliveroo", country: "UK", salary_min: 65000, salary_max: 85000, currency: "GBP", platform: "reed", applied_at: new Date(Date.now() - 86400000 * 7).toISOString(), status: "interview_scheduled" },
      ],
      offer_received: [
        { id: 4, job_title: "AI Consultant", company_name: "STC", country: "SA", salary_min: 22000, salary_max: 30000, currency: "SAR", platform: "bayt", applied_at: new Date(Date.now() - 86400000 * 14).toISOString(), status: "offer_received" },
      ],
      rejected: [],
    };
  }
  return <PipelineClient kanban={kanban} />;
}
