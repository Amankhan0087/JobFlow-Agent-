"use client";
import { useState } from "react";
import { api, type Settings, type AgentStatus } from "@/lib/api";

const COUNTRIES = ["UAE", "UK", "SA", "Germany", "USA"];
const FLAGS: Record<string, string> = { UAE: "🇦🇪", UK: "🇬🇧", SA: "🇸🇦", Germany: "🇩🇪", USA: "🇺🇸" };
const AGENTS = ["scraper", "matcher", "customizer", "bot", "scheduler", "followup"];

const DEFAULT: Settings = {
  llm_provider: "groq",
  active_countries: ["UAE", "UK", "SA", "Germany", "USA"],
  daily_application_limit: 15,
  auto_apply_enabled: false,
  min_match_score: 60,
};

export default function SettingsClient({
  initialSettings,
  initialAgentStatus,
}: {
  initialSettings: Settings | null;
  initialAgentStatus: Record<string, AgentStatus>;
}) {
  const [settings, setSettings] = useState<Settings>(initialSettings || DEFAULT);
  const [groqKey, setGroqKey] = useState("");
  const [gmailUser, setGmailUser] = useState(initialSettings?.gmail_user || "");
  const [gmailPass, setGmailPass] = useState("");
  const [saved, setSaved] = useState(false);
  const [agentStatus, setAgentStatus] = useState(initialAgentStatus);

  const S = {
    section: { background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 24, marginBottom: 20 } as React.CSSProperties,
    title: { fontSize: 14, fontWeight: 600, color: "#F9FAFB", marginBottom: 4 } as React.CSSProperties,
    desc: { fontSize: 12, color: "#6B7280", marginBottom: 20 } as React.CSSProperties,
    row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 } as React.CSSProperties,
    label: { fontSize: 12, fontWeight: 500, color: "#9CA3AF", marginBottom: 6, display: "block" } as React.CSSProperties,
    input: { width: "100%", padding: "9px 12px", background: "#1A2234", border: "1px solid #1F2937", borderRadius: 8, color: "#F9FAFB", fontSize: 13, outline: "none", boxSizing: "border-box" } as React.CSSProperties,
    select: { width: "100%", padding: "9px 12px", background: "#1A2234", border: "1px solid #1F2937", borderRadius: 8, color: "#F9FAFB", fontSize: 13, outline: "none", boxSizing: "border-box" } as React.CSSProperties,
  };

  const toggle = (on: boolean): React.CSSProperties => ({
    display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer",
    padding: "8px 14px", borderRadius: 8,
    border: `1px solid ${on ? "#2DD4BF" : "#1F2937"}`,
    background: on ? "rgba(45,212,191,0.1)" : "#1A2234",
    color: on ? "#2DD4BF" : "#6B7280",
    fontSize: 13, fontWeight: 500, userSelect: "none",
  });

  const agentBtn = (running: boolean): React.CSSProperties => ({
    padding: "9px 20px", borderRadius: 8, border: "1px solid",
    borderColor: running ? "#F59E0B" : "#6366F1",
    background: running ? "rgba(245,158,11,0.1)" : "rgba(99,102,241,0.1)",
    color: running ? "#F59E0B" : "#6366F1",
    fontSize: 12, fontWeight: 600, cursor: "pointer",
  });

  const save = async () => {
    const payload: Partial<Settings> & Record<string, unknown> = { ...settings };
    if (groqKey) payload.groq_api_key = groqKey;
    if (gmailUser) payload.gmail_user = gmailUser;
    if (gmailPass) payload.gmail_app_password = gmailPass;
    try {
      await api.settings.save(payload);
    } catch {}
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const startAgent = async (agent: string) => {
    try {
      await api.agents.start(agent);
      const { agents } = await api.agents.status();
      setAgentStatus(agents);
    } catch {}
  };

  const toggleCountry = (c: string) => {
    setSettings(s => ({
      ...s,
      active_countries: s.active_countries.includes(c)
        ? s.active_countries.filter(x => x !== c)
        : [...s.active_countries, c],
    }));
  };

  return (
    <div style={{ maxWidth: 760 }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: "#F9FAFB", marginBottom: 20 }}>Settings</h1>

      <div style={S.section}>
        <div style={S.title}>LLM Configuration</div>
        <div style={S.desc}>AI provider for resume customization and email generation</div>
        <div style={S.row}>
          <div>
            <label style={S.label}>Provider</label>
            <select value={settings.llm_provider} onChange={e => setSettings(s => ({ ...s, llm_provider: e.target.value }))} style={S.select}>
              <option value="groq">Groq (Fast, Free tier)</option>
              <option value="mistral">Mistral (Free tier)</option>
            </select>
          </div>
          <div>
            <label style={S.label}>API Key</label>
            <input type="password" placeholder="sk-..." value={groqKey} onChange={e => setGroqKey(e.target.value)} style={S.input} />
          </div>
        </div>
      </div>

      <div style={S.section}>
        <div style={S.title}>Target Markets</div>
        <div style={S.desc}>Select which countries to scrape and apply in</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {COUNTRIES.map(c => (
            <button key={c} onClick={() => toggleCountry(c)} style={toggle(settings.active_countries.includes(c))}>
              {FLAGS[c]} {c}
            </button>
          ))}
        </div>
      </div>

      <div style={S.section}>
        <div style={S.title}>Email Integration</div>
        <div style={S.desc}>Gmail for follow-ups and reading interview invites</div>
        <div style={S.row}>
          <div>
            <label style={S.label}>Gmail Address</label>
            <input type="email" placeholder="you@gmail.com" value={gmailUser} onChange={e => setGmailUser(e.target.value)} style={S.input} />
          </div>
          <div>
            <label style={S.label}>App Password</label>
            <input type="password" placeholder="16-char app password" value={gmailPass} onChange={e => setGmailPass(e.target.value)} style={S.input} />
          </div>
        </div>
      </div>

      <div style={S.section}>
        <div style={S.title}>Application Limits</div>
        <div style={S.desc}>Control how aggressively agents apply</div>
        <div style={S.row}>
          <div>
            <label style={S.label}>Daily Application Limit</label>
            <input type="number" min={1} max={100} value={settings.daily_application_limit}
              onChange={e => setSettings(s => ({ ...s, daily_application_limit: +e.target.value }))} style={S.input} />
          </div>
          <div>
            <label style={S.label}>Min Match Score to Apply (0–100)</label>
            <input type="number" min={0} max={100} value={settings.min_match_score || 60}
              onChange={e => setSettings(s => ({ ...s, min_match_score: +e.target.value }))} style={S.input} />
            <div style={{ fontSize: 11, color: "#4B5563", marginTop: 4 }}>Jobs below this score are skipped</div>
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          <label style={S.label}>Auto-Apply</label>
          <button onClick={() => setSettings(s => ({ ...s, auto_apply_enabled: !s.auto_apply_enabled }))}
            style={{ ...toggle(settings.auto_apply_enabled) }}>
            {settings.auto_apply_enabled ? "✓ Enabled" : "Disabled"}
          </button>
        </div>
      </div>

      <div style={S.section}>
        <div style={S.title}>Run Agents Manually</div>
        <div style={S.desc}>Trigger agents on demand</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {AGENTS.map(agent => {
            const running = agentStatus[agent]?.status === "running";
            const done = agentStatus[agent]?.status === "completed";
            const failed = agentStatus[agent]?.status === "failed";
            return (
              <button key={agent} onClick={() => startAgent(agent)} disabled={running} style={agentBtn(running)}>
                {running ? "⏳" : "▶"} {agent.charAt(0).toUpperCase() + agent.slice(1)}
                {done && " ✓"}{failed && " ✗"}
              </button>
            );
          })}
        </div>
      </div>

      <button onClick={save} style={{ padding: "10px 28px", borderRadius: 8, border: "none", background: "#2DD4BF", color: "#0A0F1E", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
        {saved ? "✓ Saved!" : "Save Settings"}
      </button>
    </div>
  );
}
