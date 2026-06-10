-- JobFlow Database Schema
-- SQLite

PRAGMA foreign_keys = ON;

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
    id TEXT PRIMARY KEY,  -- UUID
    platform TEXT NOT NULL,
    country TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_description TEXT,
    salary_min REAL,
    salary_max REAL,
    currency TEXT,
    location_type TEXT CHECK(location_type IN ('remote', 'hybrid', 'onsite', 'unknown')) DEFAULT 'unknown',
    visa_sponsorship INTEGER DEFAULT 0,
    accommodation_provided INTEGER DEFAULT 0,
    required_skills TEXT,  -- JSON array stored as text
    application_url TEXT,
    posted_date TEXT,
    deadline TEXT,
    status TEXT CHECK(status IN ('new', 'scraped', 'applied', 'rejected', 'expired')) DEFAULT 'new',
    raw_data TEXT,  -- full JSON blob of original scrape
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
    resume_data TEXT,  -- JSON
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_version_id INTEGER REFERENCES resume_versions(id) ON DELETE SET NULL,
    status TEXT CHECK(status IN (
        'pending', 'applied', 'acknowledged', 'interview_scheduled',
        'interviewed', 'offer_received', 'offer_accepted', 'offer_declined',
        'rejected', 'withdrawn', 'no_response'
    )) DEFAULT 'pending',
    applied_at TIMESTAMP,
    platform TEXT,
    country TEXT,
    notes TEXT,
    screenshot_path TEXT,
    cover_letter TEXT,
    application_data TEXT,  -- JSON of form fields submitted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    interview_type TEXT CHECK(interview_type IN (
        'phone_screen', 'video_call', 'technical', 'hr', 'final', 'onsite', 'other'
    )) DEFAULT 'other',
    scheduled_at TIMESTAMP,
    duration_minutes INTEGER DEFAULT 60,
    platform TEXT,  -- zoom, teams, google_meet, phone, etc.
    meeting_link TEXT,
    interviewer_name TEXT,
    interviewer_email TEXT,
    status TEXT CHECK(status IN ('scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show')) DEFAULT 'scheduled',
    outcome TEXT,
    notes TEXT,
    calendar_event_id TEXT,
    email_source TEXT,  -- raw email that triggered this
    reminder_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Follow-ups table
CREATE TABLE IF NOT EXISTS followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    followup_type TEXT CHECK(followup_type IN (
        'post_application', 'post_interview', 'status_check', 'thank_you', 'withdrawal'
    )) DEFAULT 'status_check',
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'sent', 'failed', 'cancelled')) DEFAULT 'pending',
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

-- Agent runs table (track agent execution history)
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'stopped')) DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    jobs_found INTEGER DEFAULT 0,
    applications_sent INTEGER DEFAULT 0,
    error_message TEXT,
    log_data TEXT  -- JSON log
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_country ON applications(country);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_at ON interviews(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_interviews_application_id ON interviews(application_id);
CREATE INDEX IF NOT EXISTS idx_followups_status ON followups(status);
CREATE INDEX IF NOT EXISTS idx_followups_scheduled_at ON followups(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_followups_application_id ON followups(application_id);
