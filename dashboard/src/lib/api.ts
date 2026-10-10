const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  dashboard: () => apiFetch<DashboardData>("/api/dashboard"),
  jobs: (params?: Record<string, string | number>) => {
    const q = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
    return apiFetch<{ jobs: Job[]; total: number }>(`/api/jobs${q}`);
  },
  applications: () => apiFetch<{ kanban: Record<string, Application[]> }>("/api/applications"),
  interviews: () => apiFetch<{ interviews: Interview[] }>("/api/interviews"),
  followups: () => apiFetch<{ followups: FollowUp[] }>("/api/followups"),
  sendFollowup: (id: number) => apiFetch(`/api/followups/${id}/send`, { method: "POST" }),
  resumeVersions: () => apiFetch<{ versions: ResumeVersion[] }>("/api/resume-versions"),
  settings: {
    get: () => apiFetch<Settings>("/api/settings"),
    save: (data: Partial<Settings>) => apiFetch("/api/settings", { method: "POST", body: JSON.stringify(data) }),
  },
  agents: {
    start: (agent: string, country_codes?: string[]) =>
      apiFetch("/api/agents/start", { method: "POST", body: JSON.stringify({ agent, country_codes }) }),
    status: () => apiFetch<{ agents: Record<string, AgentStatus> }>("/api/agents/status"),
  },
};

// ── Types ────────────────────────────────────────────────────────────────────

export interface DashboardData {
  total_applications: number;
  applications_today: number;
  applications_this_week: number;
  jobs_scraped: number;
  success_rate: number;
  interview_rate: number;
  offers_received: number;
  by_country: Record<string, number>;
  by_status: Record<string, number>;
  upcoming_interviews: Interview[];
  recent_activity: Application[];
}

export interface Job {
  id: string;
  platform: string;
  country: string;
  job_title: string;
  company_name: string;
  job_description: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  location_type: string;
  match_score?: number;
  match_details?: string;
  status: string;
  application_url: string;
  created_at: string;
}

export interface Application {
  id: number;
  job_title: string;
  company_name: string;
  country: string;
  status: string;
  platform: string;
  applied_at: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
}

export interface Interview {
  id: number;
  company_name: string;
  job_title: string;
  scheduled_at: string;
  country: string;
  platform: string;
  meeting_link?: string;
}

export interface FollowUp {
  id: number;
  company_name: string;
  job_title: string;
  country: string;
  followup_type: string;
  scheduled_at: string;
  status: string;
  email_subject: string;
}

export interface ResumeVersion {
  id: number;
  job_title: string;
  company_name: string;
  country: string;
  created_at: string;
  customization_summary: string;
  file_path_pdf?: string;
}

export interface Settings {
  llm_provider: string;
  active_countries: string[];
  daily_application_limit: number;
  auto_apply_enabled: boolean;
  min_match_score: number;
  gmail_user?: string;
}

export interface AgentStatus {
  status: "running" | "completed" | "failed";
  started_at: string;
  finished_at?: string;
  result?: unknown;
  error?: string;
}
