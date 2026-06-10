"""
JobFlow Email Client
SMTP sending and IMAP reading utilities.
"""

import email
import imaplib
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailClient:
    """
    Email utility for sending via SMTP and reading via IMAP.
    Configured through environment variables.
    """

    def __init__(self):
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            attachments: Optional list of file paths to attach
            html_body: Optional HTML body (if provided, sends multipart)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.gmail_user or not self.gmail_password:
            logger.error("SMTP credentials not configured (GMAIL_USER / GMAIL_APP_PASSWORD)")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.gmail_user
            msg["To"] = to

            # Attach plain text
            msg.attach(MIMEText(body, "plain"))

            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            else:
                # Auto-convert plain text to basic HTML
                html = f"<html><body><p>{body.replace(chr(10), '<br>')}</p></body></html>"
                msg.attach(MIMEText(html, "html"))

            # Add file attachments
            for filepath in (attachments or []):
                path = Path(filepath)
                if not path.exists():
                    logger.warning(f"Attachment not found: {filepath}")
                    continue
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{path.name}"',
                )
                msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.sendmail(self.gmail_user, to, msg.as_string())

            logger.info(f"Email sent to {to}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check credentials.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected email error: {e}")
            return False

    def check_inbox(
        self,
        folder: str = "INBOX",
        since_days: int = 7,
        max_emails: int = 50,
    ) -> List[Dict]:
        """
        Read emails from IMAP inbox.

        Args:
            folder: IMAP folder name (default: INBOX)
            since_days: How many days back to search
            max_emails: Maximum number of emails to return

        Returns:
            List of email dicts with subject, from, date, body, message_id
        """
        if not self.gmail_user or not self.gmail_password:
            logger.error("IMAP credentials not configured")
            return []

        messages = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            mail.select(folder)

            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            _, msg_ids = mail.search(None, f"SINCE {since_date}")

            all_ids = msg_ids[0].split()
            # Process most recent emails first, up to max_emails
            for msg_id in reversed(all_ids[-max_emails:]):
                try:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Decode subject
                    subject_raw = msg.get("Subject", "")
                    subject_parts = decode_header(subject_raw)
                    subject = ""
                    for part, enc in subject_parts:
                        if isinstance(part, bytes):
                            subject += part.decode(enc or "utf-8", errors="replace")
                        else:
                            subject += str(part)

                    # Extract body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            ct = part.get_content_type()
                            cd = str(part.get("Content-Disposition", ""))
                            if ct == "text/plain" and "attachment" not in cd:
                                try:
                                    body = part.get_payload(decode=True).decode(
                                        part.get_content_charset() or "utf-8",
                                        errors="replace"
                                    )
                                    break
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(
                                msg.get_content_charset() or "utf-8",
                                errors="replace"
                            )
                        except Exception:
                            pass

                    messages.append({
                        "message_id": msg_id.decode(),
                        "subject": subject,
                        "from": msg.get("From", ""),
                        "to": msg.get("To", ""),
                        "date": msg.get("Date", ""),
                        "body": body[:5000],
                        "is_unread": True,
                    })

                except Exception as e:
                    logger.debug(f"Error parsing email {msg_id}: {e}")

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error: {e}")
        except Exception as e:
            logger.error(f"Inbox check failed: {e}")

        return messages

    def mark_as_read(self, message_id: str, folder: str = "INBOX") -> bool:
        """
        Mark an email as read (remove \\Unseen flag).

        Args:
            message_id: IMAP message ID (numeric string)
            folder: IMAP folder name

        Returns:
            True if successful
        """
        if not self.gmail_user or not self.gmail_password:
            return False

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            mail.select(folder)
            mail.store(message_id, "+FLAGS", "\\Seen")
            mail.logout()
            return True
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False

    def search_emails(self, query: str, since_days: int = 30) -> List[Dict]:
        """
        Search emails by subject/from query.

        Args:
            query: Search string (searches subject and sender)
            since_days: Search window in days

        Returns:
            List of matching email dicts
        """
        all_emails = self.check_inbox(since_days=since_days, max_emails=100)
        query_lower = query.lower()
        return [
            e for e in all_emails
            if query_lower in e.get("subject", "").lower()
            or query_lower in e.get("from", "").lower()
            or query_lower in e.get("body", "").lower()
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = EmailClient()
    print(f"Email client configured for: {client.gmail_user}")
    print(f"SMTP: {client.smtp_server}:{client.smtp_port}")
    print(f"IMAP: {client.imap_server}")
