"""
JobFlow Interview Scheduler Agent
Polls email for interview invites, creates calendar events, schedules reminders.
"""

import email
import imaplib
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import fetch_all, fetch_one, insert_row, update_row, init_db

logger = logging.getLogger(__name__)


class InterviewScheduler:
    """
    Monitors email inbox for interview invites.
    Parses interview details, creates Google Calendar events,
    and schedules reminder notifications.
    """

    def __init__(self):
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.scheduler = None
        self.llm = None

    def _get_llm(self):
        if self.llm is None:
            from jobflow.utils.llm_client import LLMClient
            self.llm = LLMClient()
        return self.llm

    def _get_scheduler(self):
        """Lazy-load APScheduler."""
        if self.scheduler is None:
            from apscheduler.schedulers.background import BackgroundScheduler
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
        return self.scheduler

    def check_email_for_invites(self) -> List[Dict]:
        """
        Connect to IMAP inbox and scan for interview invitation emails.
        Returns list of raw email dicts.
        """
        if not self.gmail_user or not self.gmail_password:
            logger.warning("Email credentials not configured. Skipping email check.")
            return []

        emails_found = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            mail.select("INBOX")

            # Search for recent emails with interview-related keywords
            since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            _, msg_ids = mail.search(None, f'(SINCE {since_date} UNSEEN)')

            interview_keywords = ["interview", "schedule", "invitation", "call", "meet", "zoom", "teams"]

            for msg_id in (msg_ids[0].split() or [])[-50:]:  # Process last 50 unread
                try:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject_raw = msg.get("Subject", "")
                    subject = decode_header(subject_raw)[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode("utf-8", errors="replace")

                    # Check if email is interview-related
                    subject_lower = subject.lower()
                    if any(kw in subject_lower for kw in interview_keywords):
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                        emails_found.append({
                            "message_id": msg_id.decode(),
                            "subject": subject,
                            "from": msg.get("From", ""),
                            "date": msg.get("Date", ""),
                            "body": body[:5000],  # Limit body size
                        })
                        logger.info(f"Interview email found: {subject}")
                except Exception as e:
                    logger.debug(f"Error processing email {msg_id}: {e}")

            mail.logout()
        except Exception as e:
            logger.error(f"IMAP error: {e}")

        return emails_found

    def parse_interview_details(self, email_body: str, subject: str = "") -> Optional[Dict]:
        """
        Extract interview details from email body using regex + LLM.
        Returns dict with date, time, platform, link, interviewer_name.
        """
        details = {
            "interview_type": "other",
            "scheduled_at": None,
            "duration_minutes": 60,
            "platform": "unknown",
            "meeting_link": "",
            "interviewer_name": "",
            "interviewer_email": "",
        }

        # Detect platform
        platform_patterns = {
            "zoom": r"zoom\.us/j/[\d]+",
            "teams": r"teams\.microsoft\.com",
            "google_meet": r"meet\.google\.com/[a-z-]+",
            "phone": r"(?:call|phone|dial)",
        }
        for platform, pattern in platform_patterns.items():
            if re.search(pattern, email_body, re.IGNORECASE):
                details["platform"] = platform
                link_match = re.search(pattern, email_body)
                if link_match:
                    # Try to extract full URL
                    url_match = re.search(
                        r'https?://[^\s<>"]+', email_body[max(0, link_match.start()-5):]
                    )
                    if url_match:
                        details["meeting_link"] = url_match.group(0).rstrip(".,;)")
                break

        # Extract date/time patterns
        date_patterns = [
            r"(\w+ \d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\w+ \d{1,2})",
        ]
        time_patterns = [
            r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
            r"(\d{1,2}\s*(?:AM|PM|am|pm))",
            r"at\s+(\d{1,2}:\d{2})",
        ]

        date_str = ""
        time_str = ""
        for pattern in date_patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                break
        for pattern in time_patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                time_str = match.group(1)
                break

        # Try to parse combined date+time
        if date_str:
            combined = f"{date_str} {time_str}".strip()
            formats_to_try = [
                "%B %d, %Y %I:%M %p",
                "%B %d %Y %I:%M %p",
                "%m/%d/%Y %I:%M %p",
                "%Y-%m-%d %H:%M",
                "%B %d, %Y",
                "%m/%d/%Y",
                "%Y-%m-%d",
            ]
            for fmt in formats_to_try:
                try:
                    parsed_dt = datetime.strptime(combined.strip(), fmt)
                    details["scheduled_at"] = parsed_dt.isoformat()
                    break
                except ValueError:
                    continue

        # Extract interviewer email
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z.]+", email_body)
        if email_match:
            found_email = email_match.group(0)
            if found_email != self.gmail_user:
                details["interviewer_email"] = found_email

        # Interview type detection
        type_keywords = {
            "phone_screen": ["phone screen", "phone call", "introductory call"],
            "technical": ["technical", "coding", "assessment", "test"],
            "hr": ["hr", "human resources", "people team"],
            "video_call": ["video", "zoom", "teams", "meet"],
            "final": ["final", "last round"],
        }
        combined_text = (subject + " " + email_body).lower()
        for itype, keywords in type_keywords.items():
            if any(kw in combined_text for kw in keywords):
                details["interview_type"] = itype
                break

        # Use LLM for richer parsing if basic parsing failed
        if not details["scheduled_at"]:
            try:
                llm = self._get_llm()
                prompt = f"""Extract interview details from this email. Return JSON with keys:
scheduled_at (ISO datetime), platform, meeting_link, interviewer_name, duration_minutes.

Email subject: {subject}
Email body: {email_body[:2000]}

Return only valid JSON."""
                response = llm.complete(prompt, json_mode=True)
                if response:
                    parsed = json.loads(response) if isinstance(response, str) else response
                    for key in ("scheduled_at", "platform", "meeting_link", "interviewer_name", "duration_minutes"):
                        if parsed.get(key):
                            details[key] = parsed[key]
            except Exception as e:
                logger.debug(f"LLM parsing failed: {e}")

        return details

    def create_calendar_event(self, interview_data: Dict) -> Optional[str]:
        """
        Create a Google Calendar event for the interview.
        Returns calendar event ID.
        """
        credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "credentials/google_calendar.json")

        if not os.path.exists(credentials_path):
            logger.warning(f"Google Calendar credentials not found at {credentials_path}")
            return None

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/calendar"]
            )
            service = build("calendar", "v3", credentials=creds)

            scheduled_at = interview_data.get("scheduled_at")
            if not scheduled_at:
                return None

            start_dt = datetime.fromisoformat(scheduled_at)
            end_dt = start_dt + timedelta(minutes=interview_data.get("duration_minutes", 60))

            event_body = {
                "summary": f"Interview: {interview_data.get('company_name', 'Job Interview')}",
                "description": (
                    f"Platform: {interview_data.get('platform', 'TBD')}\n"
                    f"Link: {interview_data.get('meeting_link', '')}\n"
                    f"Interviewer: {interview_data.get('interviewer_name', '')}"
                ),
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 60},
                        {"method": "popup", "minutes": 15},
                    ],
                },
            }

            if interview_data.get("meeting_link"):
                event_body["conferenceData"] = {
                    "entryPoints": [{"entryPointType": "video", "uri": interview_data["meeting_link"]}]
                }

            event = service.events().insert(calendarId="primary", body=event_body).execute()
            event_id = event.get("id", "")
            logger.info(f"Calendar event created: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Calendar event creation failed: {e}")
            return None

    def schedule_reminders(self, interview_id: int) -> None:
        """Schedule prep, final, and follow-up reminder jobs via APScheduler."""
        interview = fetch_one("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        if not interview:
            logger.error(f"Interview not found: {interview_id}")
            return

        scheduled_at_str = interview.get("scheduled_at")
        if not scheduled_at_str:
            logger.warning(f"No scheduled_at for interview {interview_id}")
            return

        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            logger.error(f"Invalid datetime: {scheduled_at_str}")
            return

        scheduler = self._get_scheduler()

        # Prep reminder: 24 hours before
        prep_time = scheduled_at - timedelta(hours=24)
        if prep_time > datetime.now():
            scheduler.add_job(
                self.send_reminder,
                "date",
                run_date=prep_time,
                args=[interview_id, "prep"],
                id=f"prep_{interview_id}",
                replace_existing=True,
            )
            logger.info(f"Prep reminder scheduled for interview {interview_id} at {prep_time}")

        # Final reminder: 1 hour before
        final_time = scheduled_at - timedelta(hours=1)
        if final_time > datetime.now():
            scheduler.add_job(
                self.send_reminder,
                "date",
                run_date=final_time,
                args=[interview_id, "final"],
                id=f"final_{interview_id}",
                replace_existing=True,
            )

        # Follow-up reminder: 24 hours after
        followup_time = scheduled_at + timedelta(hours=24)
        scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=followup_time,
            args=[interview_id, "followup"],
            id=f"followup_{interview_id}",
            replace_existing=True,
        )

    def send_reminder(self, interview_id: int, reminder_type: str) -> None:
        """Send a reminder email for an interview."""
        interview = fetch_one("""
            SELECT i.*, j.job_title, j.company_name
            FROM interviews i
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.id = ?
        """, (interview_id,))

        if not interview:
            return

        from jobflow.utils.email_client import EmailClient
        client = EmailClient()

        subject_map = {
            "prep": f"Prep Reminder: Interview at {interview.get('company_name', '')} tomorrow",
            "final": f"1 Hour Until Your Interview at {interview.get('company_name', '')}",
            "followup": f"Follow-up: How did the interview at {interview.get('company_name', '')} go?",
        }

        body_map = {
            "prep": (
                f"You have an interview tomorrow at {interview.get('scheduled_at', '')}.\n"
                f"Company: {interview.get('company_name', '')}\n"
                f"Role: {interview.get('job_title', '')}\n"
                f"Platform: {interview.get('platform', '')}\n"
                f"Link: {interview.get('meeting_link', '')}\n\n"
                "Remember to:\n"
                "- Research the company\n"
                "- Review the job description\n"
                "- Prepare your STAR stories\n"
                "- Test your tech setup\n"
            ),
            "final": (
                f"Your interview starts in 1 hour!\n"
                f"Link: {interview.get('meeting_link', '')}\n"
                "Good luck!"
            ),
            "followup": (
                "Time to send a follow-up thank you email to your interviewer.\n"
                f"Interviewer: {interview.get('interviewer_name', '')}\n"
                f"Email: {interview.get('interviewer_email', '')}"
            ),
        }

        to = self.gmail_user
        subject = subject_map.get(reminder_type, "Interview Reminder")
        body = body_map.get(reminder_type, "Interview reminder")

        try:
            client.send_email(to=to, subject=subject, body=body)
            update_row("interviews", interview_id, {"reminder_sent": 1})
            logger.info(f"Reminder sent ({reminder_type}) for interview {interview_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")

    def run(self) -> int:
        """
        Main polling loop: check email, parse invites, create calendar events,
        schedule reminders.
        Returns number of new interviews found.
        """
        init_db()
        new_interviews = 0

        emails = self.check_email_for_invites()
        logger.info(f"Found {len(emails)} potential interview emails")

        for email_data in emails:
            try:
                details = self.parse_interview_details(
                    email_data.get("body", ""),
                    email_data.get("subject", ""),
                )

                if not details or not details.get("scheduled_at"):
                    logger.debug(f"Could not parse interview from: {email_data.get('subject')}")
                    continue

                # Try to match to an application
                # Look for company name in email
                app_id = None
                applications = fetch_all(
                    "SELECT a.id, j.company_name FROM applications a JOIN jobs j ON a.job_id = j.id",
                )
                from_addr = email_data.get("from", "").lower()
                for app in applications:
                    company = app.get("company_name", "").lower()
                    if company and (company in from_addr or company in email_data.get("body", "").lower()):
                        app_id = app["id"]
                        details["company_name"] = app.get("company_name", "")
                        break

                if not app_id:
                    logger.info(f"No matching application for: {email_data.get('subject')}")
                    continue

                # Insert interview record
                interview_id = insert_row("interviews", {
                    "application_id": app_id,
                    "interview_type": details.get("interview_type", "other"),
                    "scheduled_at": details.get("scheduled_at"),
                    "duration_minutes": details.get("duration_minutes", 60),
                    "platform": details.get("platform", "unknown"),
                    "meeting_link": details.get("meeting_link", ""),
                    "interviewer_name": details.get("interviewer_name", ""),
                    "interviewer_email": details.get("interviewer_email", ""),
                    "status": "scheduled",
                    "email_source": email_data.get("subject", ""),
                })

                # Update application status
                update_row("applications", app_id, {"status": "interview_scheduled"})

                # Create calendar event
                event_id = self.create_calendar_event(details)
                if event_id:
                    update_row("interviews", interview_id, {"calendar_event_id": event_id})

                # Schedule reminders
                self.schedule_reminders(interview_id)

                new_interviews += 1
                logger.info(f"New interview scheduled: ID {interview_id}")

            except Exception as e:
                logger.error(f"Error processing interview email: {e}")

        return new_interviews


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = InterviewScheduler()
    count = scheduler.run()
    print(f"New interviews found: {count}")
