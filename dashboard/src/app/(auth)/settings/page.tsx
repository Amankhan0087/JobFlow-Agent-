import { api } from "@/lib/api";
import SettingsClient from "./SettingsClient";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let settings = null;
  let agentStatus = {};
  try {
    [settings, { agents: agentStatus }] = await Promise.all([api.settings.get(), api.agents.status()]);
  } catch {}
  return <SettingsClient initialSettings={settings} initialAgentStatus={agentStatus} />;
}
