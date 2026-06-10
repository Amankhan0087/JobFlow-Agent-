import React, { useState, useEffect } from 'react';

const TYPE_COLOR = {
  post_application: { bg: 'rgba(99,102,241,0.15)', color: '#6366F1', label: 'Post-Application' },
  post_interview: { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B', label: 'Post-Interview' },
  status_check: { bg: 'rgba(107,114,128,0.15)', color: '#9CA3AF', label: 'Status Check' },
  thank_you: { bg: 'rgba(16,185,129,0.15)', color: '#10B981', label: 'Thank You' },
};

export default function FollowUpTracker() {
  const [followups, setFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(null);

  const load = () => {
    fetch('/api/followups')
      .then(r => r.json())
      .then(d => { setFollowups(d.followups || []); setLoading(false); })
      .catch(() => {
        setFollowups([
          { id: 1, company_name: 'Noon.com', job_title: 'Senior AI Engineer', country: 'UAE', followup_type: 'post_application', scheduled_at: '2026-06-10T09:00:00', status: 'pending', email_subject: 'Following Up: Senior AI Engineer Application' },
          { id: 2, company_name: 'Deliveroo', job_title: 'Data Scientist', country: 'UK', followup_type: 'post_interview', scheduled_at: '2026-06-11T10:00:00', status: 'pending', email_subject: 'Thank You – Data Scientist Interview' },
          { id: 3, company_name: 'SAP', job_title: 'ML Engineer', country: 'Germany', followup_type: 'status_check', scheduled_at: '2026-06-12T09:00:00', status: 'pending', email_subject: 'Status Update Request: ML Engineer Application' },
        ]);
        setLoading(false);
      });
  };

  useEffect(() => { load(); }, []);

  const send = async (id) => {
    setSending(id);
    try {
      const r = await fetch(`/api/followups/${id}/send`, { method: 'POST' });
      if (r.ok) load();
    } catch (e) {}
    setSending(null);
  };

  const FLAGS = { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' };
  const pending = followups.filter(f => f.status === 'pending');
  const sent = followups.filter(f => f.status === 'sent');

  if (loading) return <div style={{ color: '#6B7280', textAlign: 'center', padding: '60px' }}>Loading...</div>;

  const Row = ({ f }) => {
    const tc = TYPE_COLOR[f.followup_type] || TYPE_COLOR.status_check;
    const overdue = new Date(f.scheduled_at) < new Date();
    return (
      <div style={{ background: '#111827', border: `1px solid ${overdue ? 'rgba(239,68,68,0.3)' : '#1F2937'}`, borderRadius: '10px', padding: '16px', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ fontSize: '22px' }}>{FLAGS[f.country] || '🌍'}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: '#F9FAFB' }}>{f.company_name}</span>
            <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '20px', background: tc.bg, color: tc.color, fontWeight: '600' }}>{tc.label}</span>
            {overdue && f.status === 'pending' && <span style={{ fontSize: '10px', color: '#EF4444', fontWeight: '600' }}>OVERDUE</span>}
          </div>
          <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '2px' }}>{f.job_title}</div>
          <div style={{ fontSize: '11px', color: '#4B5563' }}>📧 {f.email_subject}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '11px', color: overdue ? '#EF4444' : '#6B7280', marginBottom: '8px' }}>
            {new Date(f.scheduled_at).toLocaleDateString()}
          </div>
          {f.status === 'pending' ? (
            <button onClick={() => send(f.id)} disabled={sending === f.id} style={{
              padding: '7px 16px', borderRadius: '7px', border: 'none',
              background: sending === f.id ? '#374151' : '#2DD4BF',
              color: sending === f.id ? '#9CA3AF' : '#0A0F1E',
              fontSize: '12px', fontWeight: '600', cursor: sending === f.id ? 'not-allowed' : 'pointer',
            }}>{sending === f.id ? 'Sending...' : 'Send Now'}</button>
          ) : (
            <span style={{ fontSize: '11px', color: '#10B981', fontWeight: '600' }}>✓ Sent</span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <div style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '10px', padding: '14px 20px', flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#F59E0B' }}>{pending.length}</div>
          <div style={{ fontSize: '11px', color: '#6B7280', marginTop: '4px' }}>Pending</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '10px', padding: '14px 20px', flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#10B981' }}>{sent.length}</div>
          <div style={{ fontSize: '11px', color: '#6B7280', marginTop: '4px' }}>Sent</div>
        </div>
      </div>

      {pending.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '12px', fontWeight: '600', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Pending</div>
          {pending.map(f => <Row key={f.id} f={f} />)}
        </div>
      )}

      {sent.length > 0 && (
        <div>
          <div style={{ fontSize: '12px', fontWeight: '600', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Sent</div>
          {sent.map(f => <Row key={f.id} f={f} />)}
        </div>
      )}

      {followups.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: '#4B5563', fontSize: '13px' }}>No follow-ups scheduled yet.</div>
      )}
    </div>
  );
}
