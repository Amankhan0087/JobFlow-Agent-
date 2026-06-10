"""
JobFlow FastAPI Application
REST API serving the React UI and agent orchestration.
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import fetch_all, fetch_one, update_row, init_db, upsert_setting, get_setting

logger = logging.getLogger(__name__)

# Initialize database on startup
init_db()

app = FastAPI(
    title="JobFlow API",
    description="Multi-country automated job application system",
    version="1.0.0",
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track agent run statuses in memory
agent_status: Dict[str, Any] = {}


# ------------------------------------------------------------------ #
#  Pydantic Models                                                    #
# ------------------------------------------------------------------ #

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class SettingsPayload(BaseModel):
    llm_provider: Optional[str] = None
    groq_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    gmail_user: Optional[str] = None
    gmail_app_password: Optional[str] = None
    active_countries: Optional[List[str]] = None
    daily_application_limit: Optional[int] = None
    auto_apply_enabled: Optional[bool] = None
    followup_delay_days: Optional[int] = None
    email_check_interval_minutes: Optional[int] = None


class AgentStartPayload(BaseModel):
    agent: str
    country_codes: Optional[List[str]] = None
    job_ids: Optional[List[str]] = None


# ------------------------------------------------------------------ #
#  Dashboard                                                          #
# ------------------------------------------------------------------ #

@app.get("/api/dashboard")
async def get_dashboard():
    """
    Return dashboard statistics:
    total_applications, by_country, success_rate, upcoming_interviews, recent_activity.
    """
    try:
        # Total applications by status
        status_counts = fetch_all("""
            SELECT status, COUNT(*) as count FROM applications GROUP BY status
        """)
        by_status = {r["status"]: r["count"] for r in status_counts}
        total_apps = sum(by_status.values())

        # By country
        country_counts = fetch_all("""
            SELECT country, COUNT(*) as count FROM applications GROUP BY country
        """)
        by_country = {r["country"] or "Unknown": r["count"] for r in country_counts}

        # Today / week / month
        today = fetch_one("SELECT COUNT(*) as c FROM applications WHERE DATE(applied_at) = DATE('now')") or {"c": 0}
        week = fetch_one("SELECT COUNT(*) as c FROM applications WHERE applied_at >= DATE('now', '-7 days')") or {"c": 0}
        month = fetch_one("SELECT COUNT(*) as c FROM applications WHERE applied_at >= DATE('now', '-30 days')") or {"c": 0}

        # Success metrics
        offers = by_status.get("offer_received", 0) + by_status.get("offer_accepted", 0)
        success_rate = round(offers / total_apps * 100, 1) if total_apps > 0 else 0
        interviews_count = sum(v for k, v in by_status.items() if "interview" in k)

        # Upcoming interviews
        upcoming_interviews = fetch_all("""
            SELECT i.id, i.scheduled_at, i.platform, i.meeting_link,
                   j.job_title, j.company_name, j.country
            FROM interviews i
            LEFT JOIN applications a ON i.application_id = a.id
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.scheduled_at > CURRENT_TIMESTAMP AND i.status = 'scheduled'
            ORDER BY i.scheduled_at ASC
            LIMIT 5
        """)

        # Recent activity (last 10 applications)
        recent_activity = fetch_all("""
            SELECT a.id, a.status, a.applied_at, a.created_at,
                   j.job_title, j.company_name, j.country, j.platform
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            ORDER BY a.created_at DESC
            LIMIT 10
        """)

        # Jobs scraped
        jobs_scraped = fetch_one("SELECT COUNT(*) as c FROM jobs") or {"c": 0}

        return {
            "total_applications": total_apps,
            "applications_today": today["c"],
            "applications_this_week": week["c"],
            "applications_this_month": month["c"],
            "jobs_scraped": jobs_scraped["c"],
            "success_rate": success_rate,
            "interview_rate": round(interviews_count / total_apps * 100, 1) if total_apps > 0 else 0,
            "offers_received": offers,
            "by_status": by_status,
            "by_country": by_country,
            "upcoming_interviews": upcoming_interviews,
            "recent_activity": recent_activity,
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Jobs                                                               #
# ------------------------------------------------------------------ #

@app.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = None,
    country: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(default=100, le=500),
):
    """List jobs with optional filters."""
    try:
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if country:
            conditions.append("country = ?")
            params.append(country)
        if platform:
            conditions.append("platform = ?")
            params.append(platform)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        jobs = fetch_all(
            f"SELECT * FROM jobs {where} ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        )
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Applications                                                       #
# ------------------------------------------------------------------ #

@app.get("/api/applications")
async def list_applications(
    status: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
):
    """
    List applications with job details.
    Returns kanban-grouped structure with columns.
    """
    try:
        conditions = ["1=1"]
        params = []
        if status:
            conditions.append("a.status = ?")
            params.append(status)
        if country:
            conditions.append("a.country = ?")
            params.append(country)

        where = "WHERE " + " AND ".join(conditions)
        params.append(limit)

        apps = fetch_all(f"""
            SELECT
                a.id, a.status, a.applied_at, a.created_at, a.notes,
                a.platform, a.country, a.screenshot_path,
                j.job_title, j.company_name, j.salary_min, j.salary_max,
                j.currency, j.application_url, j.location_type,
                j.visa_sponsorship, j.accommodation_provided
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            {where}
            ORDER BY a.created_at DESC
            LIMIT ?
        """, tuple(params))

        # Group by status for kanban
        kanban_columns = {
            "new": [],
            "applied": [],
            "acknowledged": [],
            "interview_scheduled": [],
            "interviewed": [],
            "offer_received": [],
            "offer_accepted": [],
            "rejected": [],
            "no_response": [],
        }
        for app in apps:
            col = app.get("status", "applied")
            if col in kanban_columns:
                kanban_columns[col].append(app)
            else:
                kanban_columns.setdefault(col, []).append(app)

        return {
            "applications": apps,
            "total": len(apps),
            "kanban": kanban_columns,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{app_id}")
async def get_application(app_id: int):
    """Get full application detail with job info and interviews."""
    try:
        app = fetch_one("""
            SELECT
                a.*,
                j.job_title, j.company_name, j.job_description,
                j.salary_min, j.salary_max, j.currency,
                j.application_url, j.location_type, j.required_skills,
                j.visa_sponsorship, j.accommodation_provided, j.country,
                j.platform, j.posted_date
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.id = ?
        """, (app_id,))

        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Get interviews
        interviews = fetch_all(
            "SELECT * FROM interviews WHERE application_id = ? ORDER BY scheduled_at",
            (app_id,),
        )

        # Get follow-ups
        followups = fetch_all(
            "SELECT * FROM followups WHERE application_id = ? ORDER BY scheduled_at",
            (app_id,),
        )

        # Get resume version
        resume_version = fetch_one(
            "SELECT * FROM resume_versions WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
            (app.get("job_id", ""),),
        )

        return {
            **dict(app),
            "interviews": interviews,
            "followups": followups,
            "resume_version": resume_version,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/applications/{app_id}")
async def update_application(app_id: int, update: ApplicationUpdate):
    """Update application status and/or notes."""
    try:
        updates = {}
        if update.status is not None:
            updates["status"] = update.status
        if update.notes is not None:
            updates["notes"] = update.notes

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        rows = update_row("applications", app_id, updates)
        if rows == 0:
            raise HTTPException(status_code=404, detail="Application not found")

        return {"success": True, "updated": updates}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Interviews                                                         #
# ------------------------------------------------------------------ #

@app.get("/api/interviews")
async def list_interviews(upcoming: bool = False):
    """List interviews with job/application context."""
    try:
        where = "WHERE i.scheduled_at > CURRENT_TIMESTAMP AND i.status = 'scheduled'" if upcoming else ""
        interviews = fetch_all(f"""
            SELECT
                i.*,
                j.job_title, j.company_name, j.country,
                a.status AS application_status
            FROM interviews i
            LEFT JOIN applications a ON i.application_id = a.id
            LEFT JOIN jobs j ON i.job_id = j.id
            {where}
            ORDER BY i.scheduled_at ASC
        """)
        return {"interviews": interviews, "total": len(interviews)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Follow-ups                                                         #
# ------------------------------------------------------------------ #

@app.get("/api/followups")
async def list_followups(pending_only: bool = True):
    """List follow-ups with application context."""
    try:
        where = "WHERE f.status = 'pending'" if pending_only else ""
        followups = fetch_all(f"""
            SELECT
                f.*,
                j.job_title, j.company_name, j.country,
                a.status AS application_status
            FROM followups f
            LEFT JOIN applications a ON f.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            {where}
            ORDER BY f.scheduled_at ASC
        """)
        return {"followups": followups, "total": len(followups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/followups/{followup_id}/send")
async def send_followup(followup_id: int):
    """Trigger immediate send of a follow-up email."""
    try:
        from jobflow.agents.followup_agent import FollowUpAgent
        agent = FollowUpAgent()
        success = agent.send_followup(followup_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send follow-up")
        return {"success": True, "followup_id": followup_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Resume Versions                                                    #
# ------------------------------------------------------------------ #

@app.get("/api/resume-versions")
async def list_resume_versions(
    country: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List resume versions with job context."""
    try:
        conditions = ["1=1"]
        params = []
        if country:
            conditions.append("rv.country = ?")
            params.append(country)
        params.append(limit)

        versions = fetch_all(f"""
            SELECT
                rv.*,
                j.job_title, j.company_name
            FROM resume_versions rv
            LEFT JOIN jobs j ON rv.job_id = j.id
            WHERE {' AND '.join(conditions)}
            ORDER BY rv.created_at DESC
            LIMIT ?
        """, tuple(params))

        return {"versions": versions, "total": len(versions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Settings                                                           #
# ------------------------------------------------------------------ #

@app.get("/api/settings")
async def get_settings():
    """Get all application settings."""
    try:
        rows = fetch_all("SELECT key, value FROM settings")
        settings = {}
        for row in rows:
            try:
                settings[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                settings[row["key"]] = row["value"]

        # Mask sensitive values
        if "groq_api_key" in settings and settings["groq_api_key"]:
            settings["groq_api_key"] = "sk-***" + str(settings["groq_api_key"])[-4:]
        if "mistral_api_key" in settings and settings["mistral_api_key"]:
            settings["mistral_api_key"] = "***" + str(settings["mistral_api_key"])[-4:]
        if "gmail_app_password" in settings and settings["gmail_app_password"]:
            settings["gmail_app_password"] = "***"

        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def save_settings(payload: SettingsPayload):
    """Save application settings."""
    try:
        updates = payload.dict(exclude_none=True)
        for key, value in updates.items():
            upsert_setting(key, value)

        # Update env vars for current process if API keys provided
        if payload.groq_api_key:
            os.environ["GROQ_API_KEY"] = payload.groq_api_key
        if payload.mistral_api_key:
            os.environ["MISTRAL_API_KEY"] = payload.mistral_api_key
        if payload.gmail_user:
            os.environ["GMAIL_USER"] = payload.gmail_user
        if payload.gmail_app_password:
            os.environ["GMAIL_APP_PASSWORD"] = payload.gmail_app_password
        if payload.llm_provider:
            os.environ["LLM_PROVIDER"] = payload.llm_provider

        return {"success": True, "saved_keys": list(updates.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------ #
#  Agent Control                                                      #
# ------------------------------------------------------------------ #

@app.post("/api/agents/start")
async def start_agent(payload: AgentStartPayload):
    """
    Start an agent in a background thread.
    agent: 'scraper' | 'customizer' | 'bot' | 'scheduler' | 'followup'
    """
    agent_name = payload.agent.lower()
    if agent_name in agent_status and agent_status[agent_name].get("status") == "running":
        return {"success": False, "message": f"Agent '{agent_name}' is already running"}

    agent_status[agent_name] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "result": None,
        "error": None,
    }

    def run_agent():
        try:
            if agent_name == "scraper":
                from jobflow.agents.job_scraper import JobScraper
                scraper = JobScraper()
                result = scraper.run(payload.country_codes)
                agent_status[agent_name]["result"] = result

            elif agent_name == "customizer":
                from jobflow.agents.resume_customizer import ResumeCustomizer
                customizer = ResumeCustomizer()
                job_ids = payload.job_ids or []
                if not job_ids:
                    jobs = fetch_all("SELECT id FROM jobs WHERE status = 'new' LIMIT 10")
                    job_ids = [j["id"] for j in jobs]
                results = [customizer.run(jid) for jid in job_ids]
                agent_status[agent_name]["result"] = {"customized": len([r for r in results if r])}

            elif agent_name == "bot":
                import asyncio
                from jobflow.agents.application_bot import ApplicationBot
                job_ids = payload.job_ids or []
                if not job_ids:
                    jobs = fetch_all("SELECT id FROM jobs WHERE status = 'new' LIMIT 5")
                    job_ids = [j["id"] for j in jobs]
                bot = ApplicationBot()
                results = asyncio.run(bot.run(job_ids))
                agent_status[agent_name]["result"] = {"applied": len(results)}

            elif agent_name == "scheduler":
                from jobflow.agents.interview_scheduler import InterviewScheduler
                scheduler = InterviewScheduler()
                count = scheduler.run()
                agent_status[agent_name]["result"] = {"new_interviews": count}

            elif agent_name == "followup":
                from jobflow.agents.followup_agent import FollowUpAgent
                fa = FollowUpAgent()
                result = fa.run()
                agent_status[agent_name]["result"] = result

            else:
                raise ValueError(f"Unknown agent: {agent_name}")

            agent_status[agent_name]["status"] = "completed"

        except Exception as e:
            logger.error(f"Agent {agent_name} error: {e}")
            agent_status[agent_name]["status"] = "failed"
            agent_status[agent_name]["error"] = str(e)
        finally:
            agent_status[agent_name]["finished_at"] = datetime.now().isoformat()

    thread = threading.Thread(target=run_agent, daemon=True, name=f"agent-{agent_name}")
    thread.start()

    return {
        "success": True,
        "agent": agent_name,
        "message": f"Agent '{agent_name}' started",
    }


@app.get("/api/agents/status")
async def get_agent_status():
    """Get current status of all agent runs."""
    return {"agents": agent_status}


# ------------------------------------------------------------------ #
#  Health check                                                       #
# ------------------------------------------------------------------ #

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {"message": "JobFlow API v1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
