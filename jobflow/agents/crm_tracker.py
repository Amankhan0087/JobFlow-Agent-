"""
JobFlow CRM Tracker Agent
Manages job application pipeline data: jobs, applications, interviews, follow-ups.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import (
    fetch_all, fetch_one, insert_row, update_row, execute_query, init_db
)

logger = logging.getLogger(__name__)


class CRMTracker:
    """
    Central CRM for tracking all job applications.
    Provides CRUD operations and pipeline analytics.
    """

    def __init__(self):
        init_db()

    # ------------------------------------------------------------------ #
    #  Jobs                                                               #
    # ------------------------------------------------------------------ #
    def add_job(self, job_data: Dict) -> str:
        """Insert a new job record. Returns job ID."""
        import uuid
        if "id" not in job_data:
            job_data["id"] = str(uuid.uuid4())
        insert_row("jobs", job_data)
        logger.info(f"Job added: {job_data.get('job_title')} ({job_data['id']})")
        return job_data["id"]

    def update_job(self, job_id: str, updates: Dict) -> bool:
        """Update job fields. Returns True if successful."""
        rows_affected = update_row("jobs", job_id, updates, id_column="id")
        return rows_affected > 0

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Fetch a single job by ID."""
        return fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))

    def list_jobs(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List jobs with optional filters."""
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
        return fetch_all(
            f"SELECT * FROM jobs {where} ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        )

    # ------------------------------------------------------------------ #
    #  Applications                                                       #
    # ------------------------------------------------------------------ #
    def add_application(self, app_data: Dict) -> int:
        """Insert a new application record. Returns application ID."""
        app_id = insert_row("applications", app_data)
        logger.info(f"Application added: ID {app_id}")
        return app_id

    def update_application(self, app_id: int, status: str, notes: str = "") -> bool:
        """Update application status and optional notes."""
        updates = {"status": status}
        if notes:
            updates["notes"] = notes
        rows = update_row("applications", app_id, updates)
        return rows > 0

    def get_application(self, app_id: int) -> Optional[Dict]:
        """Fetch a single application with job details."""
        return fetch_one("""
            SELECT
                a.*,
                j.job_title,
                j.company_name,
                j.platform,
                j.country,
                j.salary_min,
                j.salary_max,
                j.currency,
                j.application_url,
                j.location_type
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.id = ?
        """, (app_id,))

    def list_applications(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:
        """List applications with job details."""
        conditions = []
        params = []
        if status:
            conditions.append("a.status = ?")
            params.append(status)
        if country:
            conditions.append("a.country = ?")
            params.append(country)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        return fetch_all(f"""
            SELECT
                a.*,
                j.job_title,
                j.company_name,
                j.salary_min,
                j.salary_max,
                j.currency,
                j.application_url
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            {where}
            ORDER BY a.created_at DESC
            LIMIT ?
        """, tuple(params))

    # ------------------------------------------------------------------ #
    #  Interviews                                                         #
    # ------------------------------------------------------------------ #
    def add_interview(self, interview_data: Dict) -> int:
        """Insert a new interview record. Returns interview ID."""
        iid = insert_row("interviews", interview_data)
        # Update linked application status
        if interview_data.get("application_id"):
            update_row("applications", interview_data["application_id"], {"status": "interview_scheduled"})
        logger.info(f"Interview added: ID {iid}")
        return iid

    def update_interview(self, interview_id: int, outcome: str, notes: str = "") -> bool:
        """Update interview outcome and notes."""
        updates = {"outcome": outcome, "status": "completed"}
        if notes:
            updates["notes"] = notes
        rows = update_row("interviews", interview_id, updates)
        return rows > 0

    def list_interviews(self, upcoming_only: bool = False) -> List[Dict]:
        """List interviews with application and job details."""
        where = "WHERE i.scheduled_at > CURRENT_TIMESTAMP" if upcoming_only else ""
        return fetch_all(f"""
            SELECT
                i.*,
                a.status AS application_status,
                j.job_title,
                j.company_name,
                j.country
            FROM interviews i
            LEFT JOIN applications a ON i.application_id = a.id
            LEFT JOIN jobs j ON i.job_id = j.id
            {where}
            ORDER BY i.scheduled_at ASC
        """)

    # ------------------------------------------------------------------ #
    #  Follow-ups                                                         #
    # ------------------------------------------------------------------ #
    def add_followup(self, followup_data: Dict) -> int:
        """Insert a new follow-up record. Returns follow-up ID."""
        fid = insert_row("followups", followup_data)
        logger.info(f"Follow-up added: ID {fid}")
        return fid

    def mark_followup_sent(self, followup_id: int) -> bool:
        """Mark a follow-up as sent."""
        rows = update_row("followups", followup_id, {
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
        })
        return rows > 0

    def get_pending_followups(self) -> List[Dict]:
        """Return follow-ups that are due (scheduled_at <= now)."""
        return fetch_all("""
            SELECT
                f.*,
                a.status AS application_status,
                j.job_title,
                j.company_name,
                j.country
            FROM followups f
            LEFT JOIN applications a ON f.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE f.status = 'pending'
              AND f.scheduled_at <= CURRENT_TIMESTAMP
            ORDER BY f.scheduled_at ASC
        """)

    # ------------------------------------------------------------------ #
    #  Analytics                                                          #
    # ------------------------------------------------------------------ #
    def get_pipeline_stats(self) -> Dict:
        """
        Return counts per status per country plus overall metrics.
        """
        # Total applications by status
        status_counts = fetch_all("""
            SELECT status, COUNT(*) as count
            FROM applications
            GROUP BY status
        """)

        # Applications by country
        country_counts = fetch_all("""
            SELECT country, COUNT(*) as count
            FROM applications
            GROUP BY country
        """)

        # Applications by country + status
        country_status = fetch_all("""
            SELECT country, status, COUNT(*) as count
            FROM applications
            GROUP BY country, status
        """)

        # Success metrics
        total_apps = sum(r["count"] for r in status_counts)
        offers = sum(r["count"] for r in status_counts if r["status"] in ("offer_received", "offer_accepted"))
        interviews = sum(r["count"] for r in status_counts if "interview" in r["status"])
        success_rate = round((offers / total_apps * 100), 1) if total_apps > 0 else 0
        interview_rate = round((interviews / total_apps * 100), 1) if total_apps > 0 else 0

        # Today's applications
        today_count = fetch_one("""
            SELECT COUNT(*) as count FROM applications
            WHERE DATE(applied_at) = DATE('now')
        """) or {"count": 0}

        # This week
        week_count = fetch_one("""
            SELECT COUNT(*) as count FROM applications
            WHERE applied_at >= DATE('now', '-7 days')
        """) or {"count": 0}

        # Total jobs scraped
        total_jobs = fetch_one("SELECT COUNT(*) as count FROM jobs") or {"count": 0}

        # Upcoming interviews count
        upcoming = fetch_one("""
            SELECT COUNT(*) as count FROM interviews
            WHERE scheduled_at > CURRENT_TIMESTAMP AND status = 'scheduled'
        """) or {"count": 0}

        return {
            "total_applications": total_apps,
            "applications_today": today_count["count"],
            "applications_this_week": week_count["count"],
            "total_jobs_scraped": total_jobs["count"],
            "success_rate": success_rate,
            "interview_rate": interview_rate,
            "offers_received": offers,
            "interviews_scheduled": interviews,
            "upcoming_interviews": upcoming["count"],
            "by_status": {r["status"]: r["count"] for r in status_counts},
            "by_country": {r["country"]: r["count"] for r in country_counts},
            "by_country_status": country_status,
        }

    def get_upcoming_interviews(self, days: int = 7) -> List[Dict]:
        """Return interviews scheduled within the next N days."""
        cutoff = (datetime.now() + timedelta(days=days)).isoformat()
        return fetch_all("""
            SELECT
                i.*,
                j.job_title,
                j.company_name,
                j.country
            FROM interviews i
            LEFT JOIN applications a ON i.application_id = a.id
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.scheduled_at BETWEEN CURRENT_TIMESTAMP AND ?
              AND i.status = 'scheduled'
            ORDER BY i.scheduled_at ASC
        """, (cutoff,))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crm = CRMTracker()
    stats = crm.get_pipeline_stats()
    print(json.dumps(stats, indent=2))
