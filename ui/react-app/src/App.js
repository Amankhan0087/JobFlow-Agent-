import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import JobPipeline from './components/JobPipeline';
import ResumeVersions from './components/ResumeVersions';
import InterviewCalendar from './components/InterviewCalendar';
import FollowUpTracker from './components/FollowUpTracker';
import Settings from './components/Settings';

const styles = {
  app: {
    display: 'flex',
    minHeight: '100vh',
    background: '#0A0F1E',
    color: '#F9FAFB',
  },
  sidebar: {
    width: '240px',
    minHeight: '100vh',
    background: '#111827',
    borderRight: '1px solid #1F2937',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    zIndex: 100,
  },
  logo: {
    padding: '24px 20px',
    borderBottom: '1px solid #1F2937',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  logoIcon: {
    width: '32px',
    height: '32px',
    background: 'linear-gradient(135deg, #2DD4BF, #6366F1)',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '16px',
    fontWeight: '700',
    color: '#fff',
  },
  logoText: {
    fontSize: '18px',
    fontWeight: '700',
    color: '#F9FAFB',
    letterSpacing: '-0.3px',
  },
  logoSub: {
    fontSize: '11px',
    color: '#6B7280',
    marginTop: '2px',
  },
  nav: {
    padding: '12px 12px',
    flex: 1,
  },
  navSection: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#4B5563',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    padding: '8px 8px 4px',
    marginTop: '8px',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '9px 12px',
    borderRadius: '8px',
    color: '#9CA3AF',
    textDecoration: 'none',
    fontSize: '13.5px',
    fontWeight: '500',
    marginBottom: '2px',
    transition: 'all 0.15s ease',
  },
  navLinkActive: {
    background: 'rgba(45, 212, 191, 0.1)',
    color: '#2DD4BF',
    border: '1px solid rgba(45, 212, 191, 0.2)',
  },
  navIcon: {
    fontSize: '16px',
    width: '20px',
    textAlign: 'center',
  },
  main: {
    marginLeft: '240px',
    flex: 1,
    minHeight: '100vh',
    background: '#0A0F1E',
  },
  header: {
    background: '#111827',
    borderBottom: '1px solid #1F2937',
    padding: '16px 28px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky',
    top: 0,
    zIndex: 50,
  },
  headerTitle: {
    fontSize: '15px',
    fontWeight: '600',
    color: '#F9FAFB',
  },
  statusDot: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    color: '#10B981',
  },
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#10B981',
    animation: 'pulse 2s infinite',
  },
  content: {
    padding: '28px',
  },
  sidebarFooter: {
    padding: '16px',
    borderTop: '1px solid #1F2937',
    fontSize: '11px',
    color: '#4B5563',
    textAlign: 'center',
  },
};

const navItems = [
  { path: '/', label: 'Dashboard', icon: '⊞', exact: true },
  { path: '/pipeline', label: 'Job Pipeline', icon: '◫' },
  { path: '/resumes', label: 'Resume Versions', icon: '📄' },
  { path: '/interviews', label: 'Interview Calendar', icon: '📅' },
  { path: '/followups', label: 'Follow-Ups', icon: '✉️' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

function PageHeader({ title, subtitle }) {
  return (
    <div style={styles.header}>
      <div>
        <div style={styles.headerTitle}>{title}</div>
        {subtitle && <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '2px' }}>{subtitle}</div>}
      </div>
      <div style={styles.statusDot}>
        <div style={styles.dot} />
        <span>API Connected</span>
      </div>
    </div>
  );
}

const pageTitles = {
  '/': { title: 'Dashboard', subtitle: 'Overview of your job search pipeline' },
  '/pipeline': { title: 'Job Pipeline', subtitle: 'Kanban view of all applications' },
  '/resumes': { title: 'Resume Versions', subtitle: 'AI-customized resumes per job' },
  '/interviews': { title: 'Interview Calendar', subtitle: 'Scheduled interviews and prep' },
  '/followups': { title: 'Follow-Up Tracker', subtitle: 'Pending follow-up emails' },
  '/settings': { title: 'Settings', subtitle: 'Configure agents and API keys' },
};

export default function App() {
  return (
    <Router>
      <div style={styles.app}>
        {/* Sidebar */}
        <aside style={styles.sidebar}>
          <div style={styles.logo}>
            <div style={styles.logoIcon}>JF</div>
            <div>
              <div style={styles.logoText}>JobFlow</div>
              <div style={styles.logoSub}>AI Job Agent</div>
            </div>
          </div>

          <nav style={styles.nav}>
            <div style={styles.navSection}>Navigation</div>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div style={styles.sidebarFooter}>
            JobFlow v1.0.0<br />
            Multi-Country AI Agent
          </div>
        </aside>

        {/* Main Content */}
        <main style={styles.main}>
          <Routes>
            {[
              { path: '/', Component: Dashboard },
              { path: '/pipeline', Component: JobPipeline },
              { path: '/resumes', Component: ResumeVersions },
              { path: '/interviews', Component: InterviewCalendar },
              { path: '/followups', Component: FollowUpTracker },
              { path: '/settings', Component: Settings },
            ].map(({ path, Component }) => (
              <Route
                key={path}
                path={path}
                element={
                  <>
                    <PageHeader
                      title={pageTitles[path]?.title}
                      subtitle={pageTitles[path]?.subtitle}
                    />
                    <div style={styles.content}>
                      <Component />
                    </div>
                  </>
                }
              />
            ))}
          </Routes>
        </main>
      </div>
    </Router>
  );
}
