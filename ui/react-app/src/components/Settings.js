import React, { useState, useEffect } from 'react';

const S = {
  section: { background: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px', marginBottom: '20px' },
  sectionTitle: { fontSize: '14px', fontWeight: '600', color: '#F9FAFB', marginBottom: '4px' },
  sectionDesc: { fontSize: '12px', color: '#6B7280', marginBottom: '20px' },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  field: { marginBottom: '16px' },
  label: { fontSize: '12px', fontWeight: '500', color: '#9CA3AF', marginBottom: '6px', display: 'block' },
  input: { width: '100%', padding: '9px 12px', background: '#1A2234', border: '1px solid #1F2937', borderRadius: '8px', color: '#F9FAFB', fontSize: '13px', outline: 'none', boxSizing: 'border-box' },
  select: { width: '100%', padding: '9px 12px', background: '#1A2234', border: '1px solid #1F2937', borderRadius: '8px', color: '#F9FAFB', fontSize: '13px', outline: 'none', boxSizing: 'border-box' },
  toggle: (on) => ({ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '8px 14px', borderRadius: '8px', border: `1px solid ${on ? '#2DD4BF' : '#1F2937'}`, background: on ? 'rgba(45,212,191,0.1)' : '#1A2234', color: on ? '#2DD4BF' : '#6B7280', fontSize: '13px', fontWeight: '500', userSelect: 'none' }),
  saveBtn: { padding: '10px 28px', borderRadius: '8px', border: 'none', background: '#2DD4BF', color: '#0A0F1E', fontSize: '13px', fontWeight: '700', cursor: 'pointer' },
  agentBtn: (running) => ({ padding: '9px 20px', borderRadius: '8px', border: '1px solid', borderColor: running ? '#F59E0B' : '#6366F1', background: running ? 'rgba(245,158,11,0.1)' : 'rgba(99,102,241,0.1)', color: running ? '#F59E0B' : '#6366F1', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }),
};

const COUNTRIES = ['UAE', 'UK', 'SA', 'Germany'];
const FLAGS = { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' };

export default function Settings() {
  const [settings, setSettings] = useState({ llm_provider: 'groq', active_countries: ['UAE', 'UK', 'SA', 'Germany'], daily_application_limit: 15, auto_apply_enabled: false });
  const [groqKey, setGroqKey] = useState('');
  const [gmailUser, setGmailUser] = useState('');
  const [gmailPass, setGmailPass] = useState('');
  const [saved, setSaved] = useState(false);
  const [agentStatus, setAgentStatus] = useState({});

  useEffect(() => {
    fetch('/api/settings').then(r => r.json()).then(d => {
      setSettings(s => ({ ...s, ...d }));
      if (d.gmail_user) setGmailUser(d.gmail_user);
    }).catch(() => {});

    fetch('/api/agents/status').then(r => r.json()).then(d => setAgentStatus(d.agents || {})).catch(() => {});
  }, []);

  const toggleCountry = (c) => {
    setSettings(s => {
      const ac = s.active_countries || [];
      return { ...s, active_countries: ac.includes(c) ? ac.filter(x => x !== c) : [...ac, c] };
    });
  };

  const save = async () => {
    try {
      const payload = { ...settings };
      if (groqKey) payload.groq_api_key = groqKey;
      if (gmailUser) payload.gmail_user = gmailUser;
      if (gmailPass) payload.gmail_app_password = gmailPass;
      await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) { setSaved(true); setTimeout(() => setSaved(false), 2500); }
  };

  const startAgent = async (agent) => {
    try {
      await fetch('/api/agents/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent }) });
      const d = await fetch('/api/agents/status').then(r => r.json());
      setAgentStatus(d.agents || {});
    } catch (e) {}
  };

  return (
    <div style={{ maxWidth: '760px' }}>
      {/* LLM Config */}
      <div style={S.section}>
        <div style={S.sectionTitle}>LLM Configuration</div>
        <div style={S.sectionDesc}>Configure AI provider for resume customization and email generation</div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>Provider</label>
            <select value={settings.llm_provider || 'groq'} onChange={e => setSettings(s => ({ ...s, llm_provider: e.target.value }))} style={S.select}>
              <option value="groq">Groq (Fast, Free tier)</option>
              <option value="mistral">Mistral (Free tier)</option>
            </select>
          </div>
          <div style={S.field}>
            <label style={S.label}>API Key</label>
            <input type="password" placeholder="sk-..." value={groqKey} onChange={e => setGroqKey(e.target.value)} style={S.input} />
          </div>
        </div>
      </div>

      {/* Target Countries */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Target Countries</div>
        <div style={S.sectionDesc}>Select which countries to scrape and apply to</div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {COUNTRIES.map(c => (
            <button key={c} onClick={() => toggleCountry(c)} style={S.toggle((settings.active_countries || []).includes(c))}>
              {FLAGS[c]} {c}
            </button>
          ))}
        </div>
      </div>

      {/* Email Config */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Email Integration</div>
        <div style={S.sectionDesc}>Gmail for sending follow-ups and reading interview invites</div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>Gmail Address</label>
            <input type="email" placeholder="you@gmail.com" value={gmailUser} onChange={e => setGmailUser(e.target.value)} style={S.input} />
          </div>
          <div style={S.field}>
            <label style={S.label}>App Password</label>
            <input type="password" placeholder="16-char app password" value={gmailPass} onChange={e => setGmailPass(e.target.value)} style={S.input} />
          </div>
        </div>
      </div>

      {/* Application Limits */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Application Limits</div>
        <div style={S.sectionDesc}>Control how aggressively agents apply</div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>Daily Application Limit</label>
            <input type="number" min="1" max="100" value={settings.daily_application_limit || 15} onChange={e => setSettings(s => ({ ...s, daily_application_limit: parseInt(e.target.value) }))} style={S.input} />
          </div>
          <div style={S.field}>
            <label style={S.label}>Auto-Apply</label>
            <button onClick={() => setSettings(s => ({ ...s, auto_apply_enabled: !s.auto_apply_enabled }))} style={{ ...S.toggle(settings.auto_apply_enabled), width: '100%', justifyContent: 'center' }}>
              {settings.auto_apply_enabled ? '✓ Enabled' : 'Disabled'}
            </button>
          </div>
        </div>
      </div>

      {/* Agent Control */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Run Agents Manually</div>
        <div style={S.sectionDesc}>Trigger agents on-demand</div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {['scraper', 'customizer', 'bot', 'scheduler', 'followup'].map(agent => {
            const status = agentStatus[agent]?.status;
            const running = status === 'running';
            return (
              <button key={agent} onClick={() => startAgent(agent)} disabled={running} style={S.agentBtn(running)}>
                {running ? '⏳' : '▶'} {agent.charAt(0).toUpperCase() + agent.slice(1)}
                {status === 'completed' && ' ✓'}
                {status === 'failed' && ' ✗'}
              </button>
            );
          })}
        </div>
      </div>

      <button onClick={save} style={S.saveBtn}>
        {saved ? '✓ Saved!' : 'Save Settings'}
      </button>
    </div>
  );
}
