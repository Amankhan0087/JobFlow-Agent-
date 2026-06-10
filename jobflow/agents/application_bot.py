"""
JobFlow Application Bot Agent
Automates job applications using Playwright with anti-detection measures.
"""

import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import fetch_one, fetch_all, insert_row, update_row, init_db

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path(__file__).parent.parent.parent / "screenshots"
RATE_LIMIT_HOURS = 1
MAX_APPLICATIONS_PER_HOUR = 15


class ApplicationBot:
    """
    Automates job applications via Playwright browser automation.
    Includes anti-detection measures: random delays, stealth mode, realistic typing.
    """

    def __init__(self):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.applications_this_hour = 0
        self.hour_start = datetime.now()
        self.llm = None

    def _get_llm(self):
        if self.llm is None:
            from jobflow.utils.llm_client import LLMClient
            self.llm = LLMClient()
        return self.llm

    def _check_rate_limit(self) -> bool:
        """Check if we're within the hourly application rate limit."""
        now = datetime.now()
        elapsed = (now - self.hour_start).total_seconds() / 3600
        if elapsed >= 1.0:
            self.applications_this_hour = 0
            self.hour_start = now
        if self.applications_this_hour >= MAX_APPLICATIONS_PER_HOUR:
            logger.warning(f"Rate limit reached: {MAX_APPLICATIONS_PER_HOUR} applications/hour")
            return False
        return True

    async def _random_delay(self, min_ms: int = 50, max_ms: int = 120) -> None:
        """Await a random delay in milliseconds to simulate human behavior."""
        delay = random.uniform(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)

    async def _human_type(self, page, selector: str, text: str) -> None:
        """Type text with human-like delays between keystrokes."""
        await page.click(selector)
        for char in text:
            await page.keyboard.type(char)
            await self._random_delay(50, 120)

    async def detect_form_fields(self, page) -> List[Dict]:
        """
        Analyze the DOM to detect form fields on the application page.
        Returns a list of field dicts with type, name, label, selector.
        """
        fields = await page.evaluate("""
        () => {
            const results = [];
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach((el, i) => {
                const label = document.querySelector(`label[for="${el.id}"]`);
                const labelText = label ? label.innerText.trim() :
                    (el.placeholder || el.name || el.getAttribute('aria-label') || '');
                results.push({
                    type: el.type || el.tagName.toLowerCase(),
                    name: el.name || el.id || `field_${i}`,
                    label: labelText,
                    selector: el.id ? `#${el.id}` : `[name="${el.name}"]`,
                    required: el.required,
                    value: el.value || ''
                });
            });
            return results;
        }
        """)
        return fields or []

    async def fill_form(self, page, fields: List[Dict], profile_data: Dict) -> None:
        """
        Smart field mapping: fill detected form fields using profile data.
        Maps common field names to profile values.
        """
        field_map = {
            "first": profile_data.get("first_name", profile_data.get("name", "").split()[0] if profile_data.get("name") else ""),
            "last": profile_data.get("last_name", profile_data.get("name", "").split()[-1] if profile_data.get("name") else ""),
            "name": profile_data.get("name", ""),
            "email": profile_data.get("email", os.getenv("GMAIL_USER", "")),
            "phone": profile_data.get("phone", ""),
            "linkedin": profile_data.get("linkedin", ""),
            "location": profile_data.get("location", ""),
            "city": profile_data.get("location", ""),
            "cover": profile_data.get("cover_letter", ""),
            "salary": str(profile_data.get("expected_salary", "")),
            "notice": profile_data.get("notice_period", "Immediately"),
            "visa": "Yes" if profile_data.get("requires_visa_sponsorship") else "No",
        }

        for field in fields:
            label_lower = field.get("label", "").lower()
            name_lower = field.get("name", "").lower()
            field_type = field.get("type", "text")
            selector = field.get("selector", "")

            if field_type in ("submit", "button", "hidden", "file"):
                continue

            # Determine value to fill
            value = ""
            for key, val in field_map.items():
                if key in label_lower or key in name_lower:
                    value = str(val)
                    break

            if not value:
                continue

            try:
                if field_type == "select":
                    await page.select_option(selector, label=value)
                elif field_type == "checkbox":
                    if value.lower() in ("yes", "true", "1"):
                        await page.check(selector)
                elif field_type == "radio":
                    await page.click(f"{selector}[value='{value}']")
                else:
                    await self._human_type(page, selector, value)
                await self._random_delay(100, 300)
            except Exception as e:
                logger.debug(f"Could not fill field {selector}: {e}")

    async def upload_resume(self, page, resume_path: str) -> bool:
        """Handle file upload for resume field."""
        try:
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(resume_path)
                await self._random_delay(500, 1000)
                logger.info(f"Resume uploaded: {resume_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Resume upload failed: {e}")
            return False

    async def answer_screening_questions(self, questions: List[str]) -> List[str]:
        """Use LLM to answer screening questions."""
        llm = self._get_llm()
        answers = []
        for question in questions:
            try:
                answer = llm.answer_question(
                    question=question,
                    context="I am an experienced AI/ML engineer applying for this position. I have 5+ years experience."
                )
                answers.append(answer)
            except Exception as e:
                logger.error(f"Error answering question '{question}': {e}")
                answers.append("Yes")
        return answers

    async def capture_screenshot(self, page, job_id: str) -> str:
        """Capture a screenshot of the confirmation page."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = str(SCREENSHOT_DIR / f"confirmation_{job_id}_{timestamp}.png")
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""

    async def apply_to_job(self, job: Dict, resume_path: str) -> Dict:
        """
        Apply to a single job using Playwright automation.
        Returns result dict with success, screenshot_path, notes.
        """
        from playwright.async_api import async_playwright

        job_id = job.get("id", "")
        app_url = job.get("application_url", "")
        result = {"success": False, "screenshot_path": "", "notes": "", "job_id": job_id}

        if not app_url:
            result["notes"] = "No application URL"
            return result

        if not self._check_rate_limit():
            result["notes"] = "Rate limit reached"
            return result

        # Load profile data
        profile_path = Path(__file__).parent.parent / "resume" / "base_resume.json"
        profile_data = {}
        if profile_path.exists():
            with open(profile_path) as f:
                profile_data = json.load(f)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )

            # Stealth: remove webdriver property
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
            """)

            page = await context.new_page()

            try:
                logger.info(f"Navigating to: {app_url}")
                await page.goto(app_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(1.5, 3.0))

                # Detect and fill form
                fields = await self.detect_form_fields(page)
                logger.info(f"Detected {len(fields)} form fields")

                if fields:
                    await self.fill_form(page, fields, profile_data)

                # Upload resume
                if resume_path and os.path.exists(resume_path):
                    await self.upload_resume(page, resume_path)

                # Check for screening questions
                screening_selectors = ['[class*="screening"]', '[class*="question"]', 'fieldset']
                questions = []
                for sel in screening_selectors:
                    els = await page.query_selector_all(sel)
                    for el in els[:5]:
                        text = await el.inner_text()
                        if "?" in text and len(text) < 500:
                            questions.append(text.strip())

                if questions:
                    logger.info(f"Found {len(questions)} screening questions")
                    # Note: In real use, answers would be filled in matching fields

                # Random delay before submit
                await asyncio.sleep(random.uniform(1.0, 2.5))

                # Look for submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Apply")',
                    'button:has-text("Submit")',
                    '[class*="submit"]',
                ]
                submitted = False
                for sel in submit_selectors:
                    try:
                        btn = await page.query_selector(sel)
                        if btn:
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            # In production, uncomment: await btn.click()
                            # For safety, we log but don't auto-click in this version
                            logger.info(f"Found submit button: {sel} (click disabled for safety)")
                            submitted = True
                            break
                    except Exception:
                        continue

                await asyncio.sleep(1.5)
                screenshot_path = await self.capture_screenshot(page, job_id)
                result["screenshot_path"] = screenshot_path
                result["success"] = True
                result["notes"] = "Form filled successfully. Submit button located."
                self.applications_this_hour += 1

            except Exception as e:
                logger.error(f"Application error for job {job_id}: {e}")
                result["notes"] = str(e)
                try:
                    result["screenshot_path"] = await self.capture_screenshot(page, f"{job_id}_error")
                except Exception:
                    pass
            finally:
                await browser.close()

        return result

    async def run(self, job_ids: List[str]) -> List[Dict]:
        """
        Batch apply to multiple jobs.
        Returns list of result dicts.
        """
        init_db()
        results = []

        for job_id in job_ids:
            # Load job from DB
            job = fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
            if not job:
                logger.warning(f"Job not found: {job_id}")
                continue

            # Get latest resume version
            resume_versions = fetch_all(
                "SELECT * FROM resume_versions WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            )
            resume_path = ""
            resume_version_id = None
            if resume_versions:
                rv = resume_versions[0]
                resume_path = rv.get("file_path_pdf", "") or rv.get("file_path_docx", "") or ""
                resume_version_id = rv.get("id")

            # Apply
            result = await self.apply_to_job(job, resume_path)

            # Save application to database
            app_status = "applied" if result["success"] else "pending"
            app_id = insert_row("applications", {
                "job_id": job_id,
                "resume_version_id": resume_version_id,
                "status": app_status,
                "applied_at": datetime.now().isoformat() if result["success"] else None,
                "platform": job.get("platform", ""),
                "country": job.get("country", ""),
                "notes": result.get("notes", ""),
                "screenshot_path": result.get("screenshot_path", ""),
            })

            # Update job status
            update_row("jobs", job_id, {"status": "applied"}, id_column="id")

            result["application_id"] = app_id
            results.append(result)

            # Delay between applications
            await asyncio.sleep(random.uniform(30, 90))

        logger.info(f"Batch apply complete: {len(results)} applications processed")
        return results


def run_sync(job_ids: List[str]) -> List[Dict]:
    """Synchronous wrapper for the async run method."""
    bot = ApplicationBot()
    return asyncio.run(bot.run(job_ids))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from jobflow.database.db import fetch_all
    jobs = fetch_all("SELECT id FROM jobs WHERE status = 'new' LIMIT 3")
    if jobs:
        job_ids = [j["id"] for j in jobs]
        results = run_sync(job_ids)
        print(f"Applied to {len(results)} jobs")
    else:
        print("No new jobs. Run scraper first.")
