import React, { useState, useEffect } from 'react';

const FLAGS = { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' };

export default function ResumeVersions() {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetch('/api/resume-versions')
      .then(r => r.json())
      .then(d => { setVersions(d.versions || []); setLoading(false); })
      .catch(() => {
        setVersions([
          { id: 1, job_title: 'Senior AI Engineer', company_name: 'Noon.com', country: 'UAE', created_at: '2026-06-10', customization_summary: 'Tailored for AI/ML role, emphasized LangChain and RAG experience', file_path_pdf: '/resumes/noon_ai_engineer.pdf' },
          { id: 2, job_title: 'ML Engineer', company_name: 'Deliveroo', country: 'UK', created_at: '2026-06-09', customization_summary: 'UK format, emphasized Python and production ML systems', file_path_pdf: '/resumes/deliveroo_ml.pdf' },
          { id: 3, job_title: 'Data Scientist', company_name: 'SAP', country: 'Germany', created_at: '2026-06-08', customization_summary: 'German market: added EU work eligibility, GDPR experience', file_path_pdf: '/resumes/sap_ds.pdf' },
          { id: 4, job_title: 'AI Consultant', company_name: 'STC', country: 'SA', created_at: '2026-06-07', customization_summary: 'Gulf market: highlighted visa sponsorship readiness, Arabic proficiency', file_path_pdf: '/resumes/stc_ai.pdf' },
        ]);
        setLoading(false);
      });
  }, []);

  const filtered = versions.filter(v =>
    !filter || v.country === filter || v.job_title?.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading) return <div style={{ color: '#6B7280', textAlign: 'center', padding: '60px' }}>Loading...</div>;

  return (
    <div>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        {['', 'UAE', 'UK', 'SA', 'Germany'].map(c => (
          <button key={c} onClick={() => setFilter(c)} style={{
            padding: '7px 16px', borderRadius: '8px', border: '1px solid',
            borderColor: filter === c ? '#2DD4BF' : '#1F2937',
            background: filter === c ? 'rgba(45,212,191,0.1)' : '#111827',
            color: filter === c ? '#2DD4BF' : '#6B7280',
            fontSize: '12px', fontWeight: '500', cursor: 'pointer',
          }}>{c || 'All'} {c && FLAGS[c]}</button>
        ))}
      </div>

      <div style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1F2937' }}>
              {['Job Title', 'Company', 'Country', 'Date', 'Customization', 'Download'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '11px', fontWeight: '600', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((v, i) => (
              <tr key={v.id} style={{ borderBottom: i < filtered.length - 1 ? '1px solid #1A2234' : 'none' }}
                onMouseEnter={e => e.currentTarget.style.background = '#1A2234'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '14px 16px', fontSize: '13px', color: '#F9FAFB', fontWeight: '500' }}>{v.job_title}</td>
                <td style={{ padding: '14px 16px', fontSize: '13px', color: '#9CA3AF' }}>{v.company_name}</td>
                <td style={{ padding: '14px 16px', fontSize: '16px' }}>{FLAGS[v.country] || v.country}</td>
                <td style={{ padding: '14px 16px', fontSize: '12px', color: '#6B7280' }}>{v.created_at?.slice(0, 10)}</td>
                <td style={{ padding: '14px 16px', fontSize: '12px', color: '#6B7280', maxWidth: '240px' }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.customization_summary}</div>
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <button style={{ padding: '5px 12px', borderRadius: '6px', border: '1px solid #2DD4BF', background: 'transparent', color: '#2DD4BF', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}>
                    PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#6B7280', fontSize: '13px' }}>No resume versions found.</div>}
      </div>
    </div>
  );
}
