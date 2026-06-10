-- Migration 001: Initial schema
-- Run this to set up the database from scratch

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    location TEXT,
    linkedin TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    country TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_description TEXT,
    salary_min REAL,
    salary_max REAL,
    currency TEXT,
    location_type TEXT DEFAULT 'unknown',
    visa_sponsorship INTEGER DEFAULT 0,
    accommodation_provided INTEGER DEFAULT 0,
    required_skills TEXT,
    application_url TEXT,
    posted_date TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'new',
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resume versions table
CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    version_name TEXT NOT NULL,
    customization_summary TEXT,
    file_path_pdf TEXT,
    file_path_docx TEXT,
    resume_data TEXT,
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_version_id INTEGER REFERENCES resume_versions(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'pending',
    applied_at TIMESTAMP,
    platform TEXT,
    country TEXT,
    notes TEXT,
    screenshot_path TEXT,
    cover_letter TEXT,
    application_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    interview_type TEXT DEFAULT 'other',
    scheduled_at TIMESTAMP,
    duration_minutes INTEGER DEFAULT 60,
    platform TEXT,
    meeting_link TEXT,
    interviewer_name TEXT,
    interviewer_email TEXT,
    status TEXT DEFAULT 'scheduled',
    outcome TEXT,
    notes TEXT,
    calendar_event_id TEXT,
    email_source TEXT,
    reminder_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Follow-ups table
CREATE TABLE IF NOT EXISTS followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    followup_type TEXT DEFAULT 'status_check',
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    email_subject TEXT,
    email_body TEXT,
    recipient_email TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent runs table
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    jobs_found INTEGER DEFAULT 0,
    applications_sent INTEGER DEFAULT 0,
    error_message TEXT,
    log_data TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_country ON applications(country);
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_at ON interviews(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_followups_status ON followups(status);
CREATE INDEX IF NOT EXISTS idx_followups_scheduled_at ON followups(scheduled_at);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('llm_provider', 'groq'),
    ('daily_application_limit', '15'),
    ('active_countries', '["UAE", "UK", "SA", "Germany"]'),
    ('email_check_interval_minutes', '30'),
    ('followup_delay_days', '5'),
    ('auto_apply_enabled', 'false'),
    ('version', '1');
