import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, FunnelChart, Funnel, LabelList } from 'recharts';

const S = {
  grid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' },
  card: { background: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' },
  statVal: { fontSize: '32px', fontWeight: '700', color: '#F9FAFB', lineHeight: 1 },
  statLabel: { fontSize: '12px', color: '#6B7280', marginTop: '6px' },
  statChange: { fontSize: '11px', color: '#10B981', marginTop: '4px' },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' },
  sectionTitle: { fontSize: '13px', fontWeight: '600', color: '#F9FAFB', marginBottom: '16px' },
  activityItem: { display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 0', borderBottom: '1px solid #1F2937' },
  badge: (status) => ({
    fontSize: '10px', fontWeight: '600', padding: '2px 8px', borderRadius: '20px',
    background: status === 'applied' ? 'rgba(99,102,241,0.15)' :
                status === 'interview_scheduled' ? 'rgba(245,158,11,0.15)' :
                status === 'offer_received' ? 'rgba(16,185,129,0.15)' :
                status === 'rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(107,114,128,0.15)',
    color: status === 'applied' ? '#6366F1' :
           status === 'interview_scheduled' ? '#F59E0B' :
           status === 'offer_received' ? '#10B981' :
           status === 'rejected' ? '#EF4444' : '#6B7280',
  }),
  flag: { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' },
};

function StatCard({ label, value, sub, color = '#2DD4BF' }) {
  return (
    <div style={S.card}>
      <div style={{ ...S.statVal, color }}>{value ?? '—'}</div>
      <div style={S.statLabel}>{label}</div>
      {sub && <div style={S.statChange}>{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => {
        // Demo data when API not running
        setData({
          total_applications: 142,
          applications_today: 8,
          applications_this_week: 34,
          applications_this_month: 142,
          jobs_scraped: 380,
          success_rate: 4.2,
          interview_rate: 12.7,
          offers_received: 6,
          by_country: { UAE: 52, UK: 41, SA: 28, Germany: 21 },
          by_status: { applied: 89, interview_scheduled: 18, offer_received: 6, rejected: 29 },
          upcoming_interviews: [
            { id: 1, company_name: 'TechCorp Dubai', job_title: 'AI Engineer', scheduled_at: '2026-06-12T10:00:00', country: 'UAE', platform: 'zoom' },
            { id: 2, company_name: 'FinTech UK', job_title: 'ML Engineer', scheduled_at: '2026-06-14T14:00:00', country: 'UK', platform: 'teams' },
          ],
          recent_activity: [
            { id: 1, company_name: 'Noon.com', job_title: 'Senior AI Engineer', country: 'UAE', status: 'applied', applied_at: '2026-06-10' },
            { id: 2, company_name: 'Deliveroo', job_title: 'Data Scientist', country: 'UK', status: 'interview_scheduled', applied_at: '2026-06-09' },
            { id: 3, company_name: 'SAP', job_title: 'ML Engineer', country: 'Germany', status: 'applied', applied_at: '2026-06-09' },
            { id: 4, company_name: 'STC', job_title: 'AI Consultant', country: 'SA', status: 'offer_received', applied_at: '2026-06-08' },
          ],
        });
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ color: '#6B7280', textAlign: 'center', padding: '60px' }}>Loading dashboard...</div>;

  const countryChartData = Object.entries(data.by_country || {}).map(([k, v]) => ({ name: k, applications: v }));
  const funnelData = [
    { name: 'Scraped', value: data.jobs_scraped || 0, fill: '#374151' },
    { name: 'Applied', value: data.total_applications || 0, fill: '#6366F1' },
    { name: 'Interviews', value: Math.round((data.total_applications || 0) * (data.interview_rate || 0) / 100), fill: '#F59E0B' },
    { name: 'Offers', value: data.offers_received || 0, fill: '#10B981' },
  ];

  return (
    <div>
      {/* Stats Grid */}
      <div style={S.grid}>
        <StatCard label="Total Applications" value={data.total_applications} sub={`${data.applications_today} today`} color="#6366F1" />
        <StatCard label="This Week" value={data.applications_this_week} sub="Applications sent" color="#2DD4BF" />
        <StatCard label="Interview Rate" value={`${data.interview_rate}%`} sub="Applied → Interview" color="#F59E0B" />
        <StatCard label="Offer Rate" value={`${data.success_rate}%`} sub={`${data.offers_received} offers received`} color="#10B981" />
      </div>

      <div style={S.row}>
        {/* Country Chart */}
        <div style={S.card}>
          <div style={S.sectionTitle}>Applications by Country</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={countryChartData} barSize={32}>
              <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '8px', color: '#F9FAFB' }} />
              <Bar dataKey="applications" fill="#6366F1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pipeline Funnel */}
        <div style={S.card}>
          <div style={S.sectionTitle}>Application Funnel</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px' }}>
            {funnelData.map((item, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', color: '#9CA3AF' }}>{item.name}</span>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#F9FAFB' }}>{item.value}</span>
                </div>
                <div style={{ background: '#1F2937', borderRadius: '4px', height: '6px' }}>
                  <div style={{ background: item.fill, height: '6px', borderRadius: '4px', width: `${Math.min(100, (item.value / (funnelData[0].value || 1)) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={S.row}>
        {/* Upcoming Interviews */}
        <div style={S.card}>
          <div style={S.sectionTitle}>Upcoming Interviews</div>
          {(data.upcoming_interviews || []).length === 0 ? (
            <div style={{ color: '#6B7280', fontSize: '13px' }}>No upcoming interviews</div>
          ) : (
            (data.upcoming_interviews || []).map(iv => (
              <div key={iv.id} style={S.activityItem}>
                <div style={{ fontSize: '20px' }}>{S.flag[iv.country] || '🌍'}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#F9FAFB' }}>{iv.company_name}</div>
                  <div style={{ fontSize: '11px', color: '#6B7280' }}>{iv.job_title} · {iv.platform}</div>
                </div>
                <div style={{ fontSize: '11px', color: '#2DD4BF' }}>{new Date(iv.scheduled_at).toLocaleDateString()}</div>
              </div>
            ))
          )}
        </div>

        {/* Recent Activity */}
        <div style={S.card}>
          <div style={S.sectionTitle}>Recent Activity</div>
          {(data.recent_activity || []).map(a => (
            <div key={a.id} style={S.activityItem}>
              <div style={{ fontSize: '20px' }}>{S.flag[a.country] || '🌍'}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: '500', color: '#F9FAFB' }}>{a.company_name}</div>
                <div style={{ fontSize: '11px', color: '#6B7280' }}>{a.job_title}</div>
              </div>
              <span style={S.badge(a.status)}>{a.status?.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
