import React, { useState, useEffect } from 'react';

const COLUMNS = [
  { key: 'new', label: 'New', color: '#6B7280' },
  { key: 'applied', label: 'Applied', color: '#6366F1' },
  { key: 'interview_scheduled', label: 'Interview', color: '#F59E0B' },
  { key: 'interviewed', label: 'Interviewed', color: '#8B5CF6' },
  { key: 'offer_received', label: 'Offer', color: '#10B981' },
  { key: 'rejected', label: 'Rejected', color: '#EF4444' },
];

const FLAGS = { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' };

function JobCard({ app }) {
  const daysSince = app.applied_at
    ? Math.floor((Date.now() - new Date(app.applied_at)) / 86400000)
    : null;

  return (
    <div style={{
      background: '#1A2234', border: '1px solid #1F2937', borderRadius: '10px',
      padding: '14px', marginBottom: '10px', cursor: 'pointer',
      transition: 'border-color 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = '#374151'}
      onMouseLeave={e => e.currentTarget.style.borderColor = '#1F2937'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
        <div style={{ fontSize: '13px', fontWeight: '600', color: '#F9FAFB', lineHeight: 1.3 }}>
          {app.job_title || 'Unknown Role'}
        </div>
        <span style={{ fontSize: '16px' }}>{FLAGS[app.country] || '🌍'}</span>
      </div>
      <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '8px' }}>{app.company_name}</div>
      {(app.salary_min || app.salary_max) && (
        <div style={{ fontSize: '11px', color: '#2DD4BF', marginBottom: '6px' }}>
          {app.currency} {app.salary_min?.toLocaleString()} – {app.salary_max?.toLocaleString()}
        </div>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '10px', color: '#4B5563', background: '#111827', padding: '2px 6px', borderRadius: '4px' }}>
          {app.platform || 'direct'}
        </span>
        {daysSince !== null && (
          <span style={{ fontSize: '10px', color: '#6B7280' }}>{daysSince}d ago</span>
        )}
      </div>
    </div>
  );
}

export default function JobPipeline() {
  const [kanban, setKanban] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/applications')
      .then(r => r.json())
      .then(d => { setKanban(d.kanban || {}); setLoading(false); })
      .catch(() => {
        const demo = {
          applied: [
            { id: 1, job_title: 'Senior AI Engineer', company_name: 'Noon.com', country: 'UAE', salary_min: 18000, salary_max: 25000, currency: 'AED', platform: 'linkedin', applied_at: new Date(Date.now() - 86400000 * 2).toISOString() },
            { id: 2, job_title: 'ML Engineer', company_name: 'Careem', country: 'UAE', salary_min: 15000, salary_max: 22000, currency: 'AED', platform: 'bayt', applied_at: new Date(Date.now() - 86400000 * 3).toISOString() },
          ],
          interview_scheduled: [
            { id: 3, job_title: 'Data Scientist', company_name: 'Deliveroo', country: 'UK', salary_min: 65000, salary_max: 85000, currency: 'GBP', platform: 'reed', applied_at: new Date(Date.now() - 86400000 * 7).toISOString() },
          ],
          offer_received: [
            { id: 4, job_title: 'AI Consultant', company_name: 'STC', country: 'SA', salary_min: 22000, salary_max: 30000, currency: 'SAR', platform: 'linkedin', applied_at: new Date(Date.now() - 86400000 * 14).toISOString() },
          ],
          rejected: [
            { id: 5, job_title: 'Python Developer', company_name: 'SAP', country: 'Germany', salary_min: 70000, salary_max: 90000, currency: 'EUR', platform: 'stepstone', applied_at: new Date(Date.now() - 86400000 * 10).toISOString() },
          ],
        };
        setKanban(demo);
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ color: '#6B7280', textAlign: 'center', padding: '60px' }}>Loading pipeline...</div>;

  return (
    <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '16px' }}>
      {COLUMNS.map(col => {
        const cards = kanban[col.key] || [];
        return (
          <div key={col.key} style={{ minWidth: '240px', flex: '0 0 240px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: col.color }} />
              <span style={{ fontSize: '12px', fontWeight: '600', color: '#9CA3AF' }}>{col.label}</span>
              <span style={{ fontSize: '11px', color: '#4B5563', marginLeft: 'auto',
                background: '#1F2937', borderRadius: '10px', padding: '1px 7px' }}>{cards.length}</span>
            </div>
            <div style={{ background: '#0D1526', borderRadius: '10px', padding: '10px', minHeight: '200px' }}>
              {cards.length === 0
                ? <div style={{ color: '#374151', fontSize: '12px', textAlign: 'center', padding: '20px 0' }}>Empty</div>
                : cards.map(app => <JobCard key={app.id} app={app} />)
              }
            </div>
          </div>
        );
      })}
    </div>
  );
}
