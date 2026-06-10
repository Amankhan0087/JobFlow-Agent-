"""
JobFlow Follow-Up Agent
Generates, schedules, and sends follow-up emails for job applications.
"""

import json
import logging
import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import fetch_all, fetch_one, insert_row, update_row, init_db

logger = logging.getLogger(__name__)

FOLLOWUP_DELAYS = {
    "post_application": 5,    # 5 days after applying
    "post_interview": 1,      # 1 day after interview
    "status_check": 10,       # 10 days if no response
    "thank_you": 0,           # Same day
    "withdrawal": 0,          # Same day
}


class FollowUpAgent:
    """
    Generates and sends follow-up emails for job applications.
    Uses LLM for personalized email generation.
    Monitors inbox for replies to update application statuses.
    """

    def __init__(self):
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.llm = None

    def _get_llm(self):
        if self.llm is None:
            from jobflow.utils.llm_client import LLMClient
            self.llm = LLMClient()
        return self.llm

    def generate_followup_email(
        self, application_id: int, followup_type: str
    ) -> Dict[str, str]:
        """
        Generate a personalized follow-up email using LLM.
        Returns dict with 'subject' and 'body'.
        """
        # Load application context
        app = fetch_one("""
            SELECT
                a.*,
                j.job_title,
                j.company_name,
                j.country,
                j.application_url
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.id = ?
        """, (application_id,))

        if not app:
            return {"subject": "Following Up", "body": "I wanted to follow up on my recent application."}

        job_title = app.get("job_title", "the position")
        company = app.get("company_name", "your company")
        applied_at = app.get("applied_at", "recently")
        country = app.get("country", "")

        # Templates per type
        templates = {
            "post_application": {
                "subject": f"Following Up: {job_title} Application",
                "context": f"I applied for the {job_title} role at {company} on {applied_at}. I'd like to follow up and express my continued interest.",
            },
            "post_interview": {
                "subject": f"Thank You – {job_title} Interview",
                "context": f"I recently interviewed for the {job_title} role at {company}. I wanted to thank you for your time and reiterate my strong interest in joining the team.",
            },
            "status_check": {
                "subject": f"Status Update Request: {job_title} Application",
                "context": f"I applied for {job_title} at {company} and haven't heard back. Could you provide a status update?",
            },
            "thank_you": {
                "subject": f"Thank You – {job_title} at {company}",
                "context": f"I want to sincerely thank the team at {company} for considering me for the {job_title} position.",
            },
            "withdrawal": {
                "subject": f"Application Withdrawal: {job_title}",
                "context": f"After careful consideration, I need to withdraw my application for the {job_title} role at {company}.",
            },
        }

        template = templates.get(followup_type, templates["status_check"])

        try:
            llm = self._get_llm()
            prompt = f"""Write a professional, concise follow-up email for a job application.

Context: {template['context']}
Applicant: AI/ML Engineer with 5+ years of experience
Company: {company}
Role: {job_title}
Country: {country}
Type: {followup_type}

Write ONLY the email body (no subject line). Keep it to 3-4 short paragraphs.
Be professional, warm, and specific. End with a clear call to action."""

            body = llm.complete(prompt)
            if not body:
                raise ValueError("Empty LLM response")

            return {"subject": template["subject"], "body": body}

        except Exception as e:
            logger.error(f"LLM email generation failed: {e}")
            # Fallback templates
            fallback_bodies = {
                "post_application": (
                    f"Dear Hiring Team,\n\n"
                    f"I hope this message finds you well. I'm writing to follow up on my application "
                    f"for the {job_title} position at {company}, submitted on {applied_at}.\n\n"
                    "I remain very enthusiastic about this opportunity and believe my experience "
                    "in AI/ML engineering would be a strong fit for your team.\n\n"
                    "Please let me know if you need any additional information. "
                    "I look forward to hearing from you.\n\nBest regards"
                ),
                "post_interview": (
                    f"Dear Hiring Team,\n\n"
                    f"Thank you so much for taking the time to interview me for the {job_title} "
                    f"role at {company}. I really enjoyed our conversation.\n\n"
                    "I'm very excited about the opportunity and confident I can contribute "
                    "meaningfully to the team.\n\nBest regards"
                ),
                "status_check": (
                    f"Dear Hiring Team,\n\n"
                    f"I'm writing to inquire about the status of my application for the {job_title} "
                    f"position at {company}. I applied previously and wanted to check in.\n\n"
                    "I remain very interested in the role. Please let me know if you need "
                    "anything else from me.\n\nBest regards"
                ),
            }
            body = fallback_bodies.get(followup_type, fallback_bodies["status_check"])
            return {"subject": template["subject"], "body": body}

    def schedule_followup(
        self,
        application_id: int,
        followup_type: str,
        send_at: Optional[datetime] = None,
    ) -> int:
        """
        Schedule a follow-up email for an application.
        Returns followup ID.
        """
        if send_at is None:
            delay_days = FOLLOWUP_DELAYS.get(followup_type, 5)
            send_at = datetime.now() + timedelta(days=delay_days)

        # Get recipient email
        app = fetch_one("""
            SELECT a.*, j.company_name FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.id = ?
        """, (application_id,))

        recipient_email = ""
        if app:
            # Try to find interviewer email
            interviews = fetch_all(
                "SELECT interviewer_email FROM interviews WHERE application_id = ? AND interviewer_email != ''",
                (application_id,),
            )
            if interviews:
                recipient_email = interviews[0].get("interviewer_email", "")

        # Generate email content
        email_content = self.generate_followup_email(application_id, followup_type)

        followup_id = insert_row("followups", {
            "application_id": application_id,
            "followup_type": followup_type,
            "scheduled_at": send_at.isoformat(),
            "status": "pending",
            "email_subject": email_content["subject"],
            "email_body": email_content["body"],
            "recipient_email": recipient_email,
        })

        logger.info(f"Follow-up {followup_id} scheduled for {send_at.isoformat()}")
        return followup_id

    def send_followup(self, followup_id: int) -> bool:
        """
        Send a follow-up email via SMTP.
        Returns True if successful.
        """
        followup = fetch_one("SELECT * FROM followups WHERE id = ?", (followup_id,))
        if not followup:
            logger.error(f"Follow-up not found: {followup_id}")
            return False

        recipient = followup.get("recipient_email", "")
        if not recipient:
            logger.warning(f"No recipient email for follow-up {followup_id}")
            # Mark as failed but with explanation
            update_row("followups", followup_id, {
                "status": "failed",
                "error_message": "No recipient email address found",
            })
            return False

        subject = followup.get("email_subject", "Following Up")
        body = followup.get("email_body", "")

        if not self.gmail_user or not self.gmail_password:
            logger.error("SMTP credentials not configured")
            update_row("followups", followup_id, {
                "status": "failed",
                "error_message": "SMTP credentials not configured",
            })
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.gmail_user
            msg["To"] = recipient

            text_part = MIMEText(body, "plain")
            html_part = MIMEText(
                f"<html><body><p>{body.replace(chr(10), '<br>')}</p></body></html>",
                "html"
            )
            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.sendmail(self.gmail_user, recipient, msg.as_string())

            update_row("followups", followup_id, {
                "status": "sent",
                "sent_at": datetime.now().isoformat(),
            })
            logger.info(f"Follow-up {followup_id} sent to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Failed to send follow-up {followup_id}: {e}")
            update_row("followups", followup_id, {
                "status": "failed",
                "error_message": str(e),
            })
            return False

    def check_responses(self) -> List[Dict]:
        """
        Scan inbox for replies to follow-up emails.
        Updates application statuses based on responses found.
        Returns list of responses processed.
        """
        if not self.gmail_user or not self.gmail_password:
            logger.warning("Email credentials not configured")
            return []

        try:
            from jobflow.utils.email_client import EmailClient
            client = EmailClient()
            messages = client.check_inbox(since_days=7)
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []

        responses_processed = []
        positive_keywords = ["offer", "pleased", "selected", "move forward", "next steps", "congratulations"]
        rejection_keywords = ["unfortunately", "not moving forward", "regret", "decided not", "other candidates"]
        interview_keywords = ["interview", "schedule", "call", "meet"]

        for msg in messages:
            subject = msg.get("subject", "").lower()
            body = msg.get("body", "").lower()
            combined = subject + " " + body

            # Determine response type
            if any(kw in combined for kw in positive_keywords):
                status = "offer_received"
            elif any(kw in combined for kw in rejection_keywords):
                status = "rejected"
            elif any(kw in combined for kw in interview_keywords):
                status = "interview_scheduled"
            else:
                continue  # Not a relevant response

            # Try to match to an application
            from_addr = msg.get("from", "").lower()
            apps = fetch_all("""
                SELECT a.id, j.company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.status NOT IN ('rejected', 'offer_accepted', 'withdrawn')
            """)
            for app in apps:
                company = app.get("company_name", "").lower()
                if company and company in from_addr:
                    update_row("applications", app["id"], {"status": status})
                    responses_processed.append({
                        "application_id": app["id"],
                        "new_status": status,
                        "from": from_addr,
                    })
                    logger.info(f"Application {app['id']} updated to {status} based on email reply")
                    break

        return responses_processed

    def auto_schedule_followups(self) -> int:
        """
        Automatically schedule follow-ups for applications that don't have them yet.
        Returns number of follow-ups scheduled.
        """
        # Find applications that have been submitted but have no pending follow-ups
        apps_needing_followup = fetch_all("""
            SELECT a.id, a.applied_at, a.status
            FROM applications a
            WHERE a.status IN ('applied', 'acknowledged')
              AND a.id NOT IN (
                SELECT DISTINCT application_id FROM followups
                WHERE status IN ('pending', 'sent')
              )
              AND a.applied_at IS NOT NULL
              AND DATE(a.applied_at) <= DATE('now', '-5 days')
        """)

        scheduled_count = 0
        for app in apps_needing_followup:
            try:
                self.schedule_followup(
                    application_id=app["id"],
                    followup_type="status_check",
                )
                scheduled_count += 1
            except Exception as e:
                logger.error(f"Error scheduling follow-up for app {app['id']}: {e}")

        return scheduled_count

    def run(self) -> Dict:
        """
        Main run loop:
        1. Check for responses to previous follow-ups
        2. Auto-schedule new follow-ups
        3. Send all due follow-ups
        Returns summary dict.
        """
        init_db()
        summary = {
            "responses_processed": 0,
            "followups_scheduled": 0,
            "followups_sent": 0,
            "followups_failed": 0,
        }

        # Step 1: Check responses
        responses = self.check_responses()
        summary["responses_processed"] = len(responses)

        # Step 2: Auto-schedule
        scheduled = self.auto_schedule_followups()
        summary["followups_scheduled"] = scheduled

        # Step 3: Send due follow-ups
        pending = fetch_all("""
            SELECT id FROM followups
            WHERE status = 'pending'
              AND scheduled_at <= CURRENT_TIMESTAMP
            ORDER BY scheduled_at ASC
            LIMIT 20
        """)

        for row in pending:
            success = self.send_followup(row["id"])
            if success:
                summary["followups_sent"] += 1
            else:
                summary["followups_failed"] += 1

        logger.info(f"FollowUpAgent run complete: {summary}")
        return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = FollowUpAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))
