# JobFlow Agent

> **Apply to 100 jobs while you sleep.**
> AI-powered agents that scrape jobs, customize your resume, submit applications, schedule interviews, and send follow-ups — across UAE, UK, Saudi Arabia, and Germany — fully automated.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Overview

JobFlow is a modular, agent-based job application automation system built for AI/tech professionals targeting multiple job markets simultaneously. It handles the entire pipeline — from scraping listings to sending post-interview thank-you emails — so you can focus on showing up to interviews.

**Target Markets:** UAE · UK · Saudi Arabia · Germany

---

## Architecture

JobFlow is built around **6 autonomous agents**, each responsible for one stage of the job application pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                        JobFlow Pipeline                         │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │  Scraper │──▶│  Resume  │──▶│   Bot    │──▶│Scheduler │   │
│  │          │   │Customizer│   │          │   │          │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│       │                                              │          │
│       ▼                                              ▼          │
│  ┌──────────┐                              ┌──────────────┐   │
│  │   CRM    │◀─────────────────────────────│  Follow-Up   │   │
│  │ Tracker  │                              │    Agent     │   │
│  └──────────┘                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

| Agent | Responsibility |
|---|---|
| **JobScraper** | Scrapes LinkedIn, Bayt, Reed, StepStone across 4 countries |
| **ResumeCustomizer** | Tailors your resume per job using Groq/Mistral LLM |
| **ApplicationBot** | Fills and submits application forms via Playwright |
| **InterviewScheduler** | Parses interview emails, creates calendar events |
| **CRMTracker** | Central SQLite database and pipeline analytics |
| **FollowUpAgent** | Generates and sends follow-up emails automatically |

---

## Features

- **Multi-country job scraping** — LinkedIn, Bayt.com, Reed.co.uk, StepStone.de
- **AI resume customization** — LLM rewrites your resume for each specific job
- **Automated form filling** — Playwright with anti-detection (random delays, stealth mode)
- **Interview detection** — IMAP email polling + Google Calendar integration
- **Smart follow-ups** — LLM-generated follow-up emails sent automatically
- **Full CRM pipeline** — SQLite database with kanban tracking
- **React dashboard** — Dark-themed UI with charts, kanban board, calendar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Backend API | FastAPI + Uvicorn |
| Browser Automation | Playwright (stealth mode) |
| Web Scraping | httpx + BeautifulSoup4 |
| LLM | Groq API (free) or Mistral API (free) |
| Database | SQLite → upgradeable to PostgreSQL |
| Resume Generation | reportlab (PDF) + python-docx (DOCX) |
| Email | Gmail API / SMTP + IMAP |
| Scheduling | APScheduler |
| Frontend | React 18 + Recharts |
| Styling | Tailwind CSS + inline design tokens |

---

## Project Structure

```
jobflow/
├── agents/
│   ├── job_scraper.py          # Multi-platform job scraping
│   ├── resume_customizer.py    # LLM-powered resume tailoring
│   ├── application_bot.py      # Playwright form automation
│   ├── interview_scheduler.py  # Email parsing + calendar
│   ├── crm_tracker.py          # Pipeline database management
│   └── followup_agent.py       # Automated follow-up emails
├── api/
│   └── main.py                 # FastAPI REST server
├── configs/
│   ├── country_uae.json
│   ├── country_uk.json
│   ├── country_sa.json
│   └── country_germany.json
├── database/
│   ├── schema.sql              # Full SQLite schema
│   ├── db.py                   # Connection manager + helpers
│   └── migrations/
├── resume/
│   ├── base_resume.json        # Your master resume (edit this)
│   └── templates/
├── utils/
│   ├── llm_client.py           # Groq + Mistral API client
│   ├── pdf_generator.py        # reportlab PDF generation
│   └── email_client.py         # SMTP + IMAP utilities
├── ui/
│   └── react-app/              # React dashboard
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/Amankhan0087/JobFlow-Agent-
cd JobFlow-Agent-
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your API key (get a free key at [console.groq.com](https://console.groq.com)):

```env
GROQ_API_KEY=gsk_your_key_here
LLM_PROVIDER=groq
```

### 3. Initialize Database

```bash
python -c "from jobflow.database.db import init_db; init_db()"
```

### 4. Edit Your Resume

Open `jobflow/resume/base_resume.json` and replace the sample data with your actual resume details.

### 5. Start the API

```bash
uvicorn jobflow.api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 6. Start the Dashboard

```bash
cd ui/react-app
npm install
npm start
```

Dashboard at: `http://localhost:3000`

---

## Dashboard Screens

| Screen | Description |
|---|---|
| **Dashboard** | Stats, country chart, application funnel, upcoming interviews |
| **Job Pipeline** | Kanban board — New → Applied → Interview → Offer → Rejected |
| **Resume Versions** | Table of all AI-customized resumes, filterable by country |
| **Interview Calendar** | Monthly calendar with interview details and meeting links |
| **Follow-Up Tracker** | Pending follow-up emails with one-click send |
| **Settings** | API keys, country toggles, application limits, agent control |

---

## Running Agents

Run agents individually from the command line:

```bash
# Scrape jobs across all countries
python -m jobflow.agents.job_scraper

# Customize resumes for new jobs
python -m jobflow.agents.resume_customizer

# Check email for interview invites
python -m jobflow.agents.interview_scheduler

# Send pending follow-ups
python -m jobflow.agents.followup_agent

# View pipeline statistics
python -m jobflow.agents.crm_tracker
```

Or trigger them from the dashboard **Settings** page, or via the API:

```bash
curl -X POST http://localhost:8000/api/agents/start \
  -H "Content-Type: application/json" \
  -d '{"agent": "scraper", "country_codes": ["uae", "uk"]}'
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Stats, charts, recent activity |
| `GET` | `/api/jobs` | Job listings with filters |
| `GET` | `/api/applications` | Applications + kanban grouping |
| `GET` | `/api/applications/{id}` | Full application detail |
| `PATCH` | `/api/applications/{id}` | Update status / notes |
| `GET` | `/api/interviews` | Interview list (filter: `?upcoming=true`) |
| `GET` | `/api/followups` | Pending follow-ups |
| `POST` | `/api/followups/{id}/send` | Send a follow-up immediately |
| `GET` | `/api/resume-versions` | All generated resumes |
| `GET` | `/api/settings` | Get current settings |
| `POST` | `/api/settings` | Save settings |
| `POST` | `/api/agents/start` | Start an agent |
| `GET` | `/api/agents/status` | Agent run statuses |

Full interactive docs: `http://localhost:8000/docs`

---

## Country Configuration

Each country has a JSON config in `jobflow/configs/`:

```json
{
  "country": "UAE",
  "currency": "AED",
  "salary_range": { "min": 8000, "max": 30000 },
  "job_boards": ["linkedin", "bayt", "naukrigulf"],
  "visa_required": true,
  "daily_application_limit": 15,
  "search_keywords": ["AI Engineer", "ML Engineer", "Software Engineer"],
  "timezone": "Asia/Dubai"
}
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for LLM | Yes (or Mistral) |
| `MISTRAL_API_KEY` | Mistral API key for LLM | Alternative to Groq |
| `LLM_PROVIDER` | `groq` or `mistral` | No (default: groq) |
| `GMAIL_USER` | Gmail address for email features | For email features |
| `GMAIL_APP_PASSWORD` | Gmail app password (not your main password) | For email features |
| `DATABASE_PATH` | Path to SQLite database file | No (default: jobflow.db) |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | Path to Google Calendar credentials JSON | For calendar features |

---

## Roadmap

- [x] JobScraper — LinkedIn, Bayt, Reed, StepStone
- [x] ResumeCustomizer — LLM-powered tailoring
- [x] ApplicationBot — Playwright automation
- [x] InterviewScheduler — Email + calendar
- [x] CRMTracker — SQLite pipeline
- [x] FollowUpAgent — Automated emails
- [x] FastAPI backend
- [x] React dashboard
- [ ] Landing page
- [ ] Electron desktop app packaging
- [ ] LinkedIn profile optimizer
- [ ] Salary negotiation agent
- [ ] Skill gap analyzer
- [ ] Multi-user SaaS mode

---

## License

MIT — free to use, modify, and distribute.

---

*Built for personal use. Designed to scale to SaaS.*
*Target markets: UAE · UK · Saudi Arabia · Germany*
