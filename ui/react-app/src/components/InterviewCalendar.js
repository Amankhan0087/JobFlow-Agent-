import React, { useState, useEffect } from 'react';

const FLAGS = { UAE: '🇦🇪', UK: '🇬🇧', SA: '🇸🇦', Germany: '🇩🇪' };
const PLATFORM_ICON = { zoom: '📹', teams: '💼', google_meet: '📞', phone: '📱' };
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

export default function InterviewCalendar() {
  const [interviews, setInterviews] = useState([]);
  const [selected, setSelected] = useState(null);
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth());
  const [year, setYear] = useState(today.getFullYear());

  useEffect(() => {
    fetch('/api/interviews')
      .then(r => r.json())
      .then(d => setInterviews(d.interviews || []))
      .catch(() => setInterviews([
        { id: 1, company_name: 'TechCorp Dubai', job_title: 'AI Engineer', scheduled_at: `${year}-${String(month+1).padStart(2,'0')}-12T10:00:00`, country: 'UAE', platform: 'zoom', meeting_link: 'https://zoom.us/j/123456', interviewer_name: 'Ahmed Al-Farsi', status: 'scheduled' },
        { id: 2, company_name: 'Deliveroo UK', job_title: 'ML Engineer', scheduled_at: `${year}-${String(month+1).padStart(2,'0')}-18T14:00:00`, country: 'UK', platform: 'teams', interviewer_name: 'Sarah Johnson', status: 'scheduled' },
      ]));
  }, []);

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const interviewsByDay = {};
  interviews.forEach(iv => {
    const d = new Date(iv.scheduled_at);
    if (d.getMonth() === month && d.getFullYear() === year) {
      const day = d.getDate();
      if (!interviewsByDay[day]) interviewsByDay[day] = [];
      interviewsByDay[day].push(iv);
    }
  });

  const selectedInterviews = selected ? (interviewsByDay[selected] || []) : [];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px' }}>
      {/* Calendar */}
      <div style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <button onClick={() => { if (month === 0) { setMonth(11); setYear(y => y-1); } else setMonth(m => m-1); }}
            style={{ background: '#1F2937', border: 'none', color: '#9CA3AF', borderRadius: '6px', padding: '6px 12px', cursor: 'pointer', fontSize: '16px' }}>←</button>
          <span style={{ fontWeight: '600', color: '#F9FAFB', fontSize: '15px' }}>{MONTHS[month]} {year}</span>
          <button onClick={() => { if (month === 11) { setMonth(0); setYear(y => y+1); } else setMonth(m => m+1); }}
            style={{ background: '#1F2937', border: 'none', color: '#9CA3AF', borderRadius: '6px', padding: '6px 12px', cursor: 'pointer', fontSize: '16px' }}>→</button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', marginBottom: '8px' }}>
          {DAYS.map(d => <div key={d} style={{ textAlign: 'center', fontSize: '11px', color: '#4B5563', fontWeight: '600', padding: '4px' }}>{d}</div>)}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px' }}>
          {Array(firstDay).fill(null).map((_, i) => <div key={`e${i}`} />)}
          {Array(daysInMonth).fill(null).map((_, i) => {
            const day = i + 1;
            const hasInterview = !!interviewsByDay[day];
            const isToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear();
            const isSelected = selected === day;
            return (
              <div key={day} onClick={() => setSelected(isSelected ? null : day)} style={{
                textAlign: 'center', padding: '8px 4px', borderRadius: '8px', cursor: hasInterview ? 'pointer' : 'default',
                background: isSelected ? '#2DD4BF' : isToday ? 'rgba(45,212,191,0.15)' : hasInterview ? 'rgba(99,102,241,0.15)' : 'transparent',
                border: `1px solid ${isSelected ? '#2DD4BF' : isToday ? 'rgba(45,212,191,0.4)' : 'transparent'}`,
                color: isSelected ? '#0A0F1E' : '#F9FAFB',
                fontWeight: isToday || hasInterview ? '600' : '400',
                fontSize: '13px', position: 'relative',
                transition: 'all 0.1s',
              }}>
                {day}
                {hasInterview && !isSelected && <div style={{ position: 'absolute', bottom: '3px', left: '50%', transform: 'translateX(-50%)', width: '4px', height: '4px', borderRadius: '50%', background: '#6366F1' }} />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Detail Panel */}
      <div style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: '12px', padding: '20px' }}>
        <div style={{ fontSize: '13px', fontWeight: '600', color: '#F9FAFB', marginBottom: '16px' }}>
          {selected ? `${MONTHS[month]} ${selected}` : 'Select a date'}
        </div>
        {!selected ? (
          <div style={{ color: '#4B5563', fontSize: '12px' }}>Click a date to see interviews</div>
        ) : selectedInterviews.length === 0 ? (
          <div style={{ color: '#4B5563', fontSize: '12px' }}>No interviews on this day</div>
        ) : (
          selectedInterviews.map(iv => (
            <div key={iv.id} style={{ background: '#1A2234', borderRadius: '10px', padding: '14px', marginBottom: '12px', border: '1px solid #1F2937' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '14px', fontWeight: '600', color: '#F9FAFB' }}>{iv.company_name}</span>
                <span style={{ fontSize: '16px' }}>{FLAGS[iv.country] || '🌍'}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '10px' }}>{iv.job_title}</div>
              <div style={{ fontSize: '12px', color: '#2DD4BF', marginBottom: '4px' }}>
                {PLATFORM_ICON[iv.platform] || '💻'} {new Date(iv.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} via {iv.platform}
              </div>
              {iv.interviewer_name && <div style={{ fontSize: '11px', color: '#6B7280' }}>👤 {iv.interviewer_name}</div>}
              {iv.meeting_link && (
                <a href={iv.meeting_link} target="_blank" rel="noreferrer"
                  style={{ display: 'block', marginTop: '10px', padding: '7px', borderRadius: '6px', background: 'rgba(45,212,191,0.1)', border: '1px solid rgba(45,212,191,0.2)', color: '#2DD4BF', fontSize: '11px', textAlign: 'center', fontWeight: '600' }}>
                  Join Meeting
                </a>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
