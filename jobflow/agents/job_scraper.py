"""
JobFlow Job Scraper Agent
Scrapes job listings from multiple platforms across multiple countries.
Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import init_db, insert_row, execute_query, fetch_all

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Sleep for a random duration to avoid rate limiting."""
    delay = random.uniform(min_s, max_s)
    logger.debug(f"Rate limiting: sleeping {delay:.2f}s")
    time.sleep(delay)


def _build_job(
    platform: str,
    country: str,
    job_title: str,
    company_name: str,
    job_description: str,
    application_url: str,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    currency: Optional[str] = None,
    location_type: str = "unknown",
    visa_sponsorship: bool = False,
    accommodation_provided: bool = False,
    required_skills: Optional[List[str]] = None,
    posted_date: Optional[str] = None,
    deadline: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standardised job dict."""
    return {
        "id": str(uuid.uuid4()),
        "platform": platform,
        "country": country,
        "job_title": job_title,
        "company_name": company_name,
        "job_description": job_description,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "location_type": location_type,
        "visa_sponsorship": int(visa_sponsorship),
        "accommodation_provided": int(accommodation_provided),
        "required_skills": json.dumps(required_skills or []),
        "application_url": application_url,
        "posted_date": posted_date or date.today().isoformat(),
        "deadline": deadline,
        "status": "new",
    }


class JobScraper:
    """
    Scrapes job listings from LinkedIn, Bayt, Reed, and StepStone.
    Saves results to the SQLite database.
    """

    CONFIG_DIR = Path(__file__).parent.parent / "configs"

    def __init__(self):
        self.client = httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True)
        self.jobs_found: List[Dict] = []

    def _load_country_config(self, country_code: str) -> Dict:
        """Load a country configuration JSON file."""
        path = self.CONFIG_DIR / f"country_{country_code.lower()}.json"
        if not path.exists():
            raise FileNotFoundError(f"Country config not found: {path}")
        with open(path) as f:
            return json.load(f)

    # ------------------------------------------------------------------ #
    #  LinkedIn scraper                                                    #
    # ------------------------------------------------------------------ #
    def scrape_linkedin(self, country_config: Dict) -> List[Dict]:
        """
        Scrape LinkedIn job listings for the given country config.
        Uses the public LinkedIn jobs search endpoint (no auth required for listings).
        """
        country = country_config["country"]
        currency = country_config["currency"]
        keywords = country_config.get("search_keywords", ["software engineer"])
        jobs: List[Dict] = []

        location_map = {
            "UAE": "United Arab Emirates",
            "UK": "United Kingdom",
            "SA": "Saudi Arabia",
            "Germany": "Germany",
        }
        location_str = location_map.get(country, country)

        for keyword in keywords[:3]:  # Limit to 3 keywords to be polite
            try:
                url = (
                    f"https://www.linkedin.com/jobs/search?"
                    f"keywords={keyword.replace(' ', '%20')}"
                    f"&location={location_str.replace(' ', '%20')}"
                    f"&f_TPR=r86400"  # Last 24 hours
                    f"&start=0"
                )
                logger.info(f"LinkedIn scrape: {keyword} in {country}")
                resp = self.client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"LinkedIn returned {resp.status_code} for {keyword}")
                    _random_delay(2, 4)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                job_cards = soup.select("div.base-card")

                for card in job_cards[:10]:  # Max 10 per keyword
                    try:
                        title_el = card.select_one("h3.base-search-card__title")
                        company_el = card.select_one("h4.base-search-card__subtitle")
                        location_el = card.select_one("span.job-search-card__location")
                        link_el = card.select_one("a.base-card__full-link")
                        time_el = card.select_one("time")

                        if not title_el or not company_el:
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True)
                        location_text = location_el.get_text(strip=True) if location_el else ""
                        app_url = link_el["href"] if link_el else ""
                        posted = time_el.get("datetime", "") if time_el else ""

                        loc_type = "remote"
                        if "remote" in location_text.lower():
                            loc_type = "remote"
                        elif "hybrid" in location_text.lower():
                            loc_type = "hybrid"
                        else:
                            loc_type = "onsite"

                        job = _build_job(
                            platform="linkedin",
                            country=country,
                            job_title=title,
                            company_name=company,
                            job_description=f"{keyword} role at {company} in {location_text}",
                            application_url=app_url,
                            currency=currency,
                            location_type=loc_type,
                            posted_date=posted[:10] if posted else None,
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error parsing LinkedIn card: {e}")
                        continue

                _random_delay(
                    country_config.get("scrape_settings", {}).get("delay_min", 1.5),
                    country_config.get("scrape_settings", {}).get("delay_max", 3.5),
                )

            except Exception as e:
                logger.error(f"LinkedIn scrape error for {keyword}: {e}")
                _random_delay(3, 6)

        logger.info(f"LinkedIn: found {len(jobs)} jobs for {country}")
        return jobs

    # ------------------------------------------------------------------ #
    #  Bayt scraper (UAE / SA)                                            #
    # ------------------------------------------------------------------ #
    def scrape_bayt(self, country_config: Dict) -> List[Dict]:
        """Scrape Bayt.com for UAE and Saudi Arabia job listings."""
        country = country_config["country"]
        currency = country_config["currency"]
        keywords = country_config.get("search_keywords", ["engineer"])
        jobs: List[Dict] = []

        country_slug_map = {"UAE": "ae", "SA": "sa"}
        country_slug = country_slug_map.get(country, "ae")

        for keyword in keywords[:2]:
            try:
                kw_slug = keyword.lower().replace(" ", "-")
                url = f"https://www.bayt.com/en/{country_slug}/jobs/{kw_slug}-jobs/"
                logger.info(f"Bayt scrape: {keyword} in {country}")
                resp = self.client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"Bayt returned {resp.status_code}")
                    _random_delay(2, 5)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                job_cards = soup.select("li[data-js-job]") or soup.select("div.col-md-4.col-sm-6.b-card")

                for card in job_cards[:10]:
                    try:
                        title_el = card.select_one("h2.jb-title") or card.select_one("[class*='title']")
                        company_el = card.select_one("[class*='company']") or card.select_one("span[class*='company']")
                        link_el = card.select_one("a[href*='/job']") or card.select_one("a")

                        title = title_el.get_text(strip=True) if title_el else keyword
                        company = company_el.get_text(strip=True) if company_el else "Unknown Company"
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        app_url = f"https://www.bayt.com{href}" if href.startswith("/") else href

                        job = _build_job(
                            platform="bayt",
                            country=country,
                            job_title=title,
                            company_name=company,
                            job_description=f"{keyword} opportunity via Bayt in {country}",
                            application_url=app_url,
                            currency=currency,
                            visa_sponsorship=True,
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Bayt card parse error: {e}")

                _random_delay(2, 4)

            except Exception as e:
                logger.error(f"Bayt scrape error: {e}")
                _random_delay(3, 6)

        logger.info(f"Bayt: found {len(jobs)} jobs for {country}")
        return jobs

    # ------------------------------------------------------------------ #
    #  Reed scraper (UK)                                                  #
    # ------------------------------------------------------------------ #
    def scrape_reed(self, country_config: Dict) -> List[Dict]:
        """Scrape Reed.co.uk for UK job listings."""
        currency = country_config.get("currency", "GBP")
        keywords = country_config.get("search_keywords", ["software engineer"])
        jobs: List[Dict] = []

        for keyword in keywords[:2]:
            try:
                kw_enc = keyword.replace(" ", "%20")
                url = f"https://www.reed.co.uk/jobs/{keyword.lower().replace(' ', '-')}-jobs"
                logger.info(f"Reed scrape: {keyword}")
                resp = self.client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"Reed returned {resp.status_code}")
                    _random_delay(2, 4)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                job_cards = soup.select("article.job-result")

                for card in job_cards[:10]:
                    try:
                        title_el = card.select_one("h3.title") or card.select_one("[class*='title']")
                        company_el = card.select_one("[class*='employer']") or card.select_one("[class*='company']")
                        salary_el = card.select_one("[class*='salary']")
                        link_el = card.select_one("a[href*='/jobs/']")
                        desc_el = card.select_one("[class*='description']")

                        title = title_el.get_text(strip=True) if title_el else keyword
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        desc = desc_el.get_text(strip=True) if desc_el else f"{keyword} role in UK"
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        app_url = f"https://www.reed.co.uk{href}" if href.startswith("/") else href

                        # Parse salary if available
                        sal_min, sal_max = None, None
                        if salary_el:
                            sal_text = salary_el.get_text(strip=True)
                            import re
                            nums = re.findall(r"[\d,]+", sal_text.replace("£", ""))
                            nums = [int(n.replace(",", "")) for n in nums if n.replace(",", "").isdigit()]
                            if len(nums) >= 2:
                                sal_min, sal_max = nums[0], nums[1]
                            elif len(nums) == 1:
                                sal_min = nums[0]

                        job = _build_job(
                            platform="reed",
                            country="UK",
                            job_title=title,
                            company_name=company,
                            job_description=desc,
                            application_url=app_url,
                            salary_min=sal_min,
                            salary_max=sal_max,
                            currency=currency,
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Reed card parse error: {e}")

                _random_delay(1.5, 3.5)

            except Exception as e:
                logger.error(f"Reed scrape error: {e}")
                _random_delay(3, 6)

        logger.info(f"Reed: found {len(jobs)} jobs")
        return jobs

    # ------------------------------------------------------------------ #
    #  StepStone scraper (Germany)                                        #
    # ------------------------------------------------------------------ #
    def scrape_stepstone(self, country_config: Dict) -> List[Dict]:
        """Scrape StepStone.de for Germany job listings."""
        currency = country_config.get("currency", "EUR")
        keywords = country_config.get("search_keywords", ["software engineer"])
        jobs: List[Dict] = []

        for keyword in keywords[:2]:
            try:
                kw_enc = keyword.replace(" ", "%20")
                url = f"https://www.stepstone.de/jobs/{keyword.lower().replace(' ', '-')}"
                logger.info(f"StepStone scrape: {keyword}")
                resp = self.client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"StepStone returned {resp.status_code}")
                    _random_delay(2, 4)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                job_cards = soup.select("article[data-at='job-item']") or soup.select("[class*='ResultItem']")

                for card in job_cards[:10]:
                    try:
                        title_el = card.select_one("[data-at='job-item-title']") or card.select_one("h2")
                        company_el = card.select_one("[data-at='job-item-company-name']") or card.select_one("[class*='company']")
                        link_el = card.select_one("a[href]")
                        location_el = card.select_one("[data-at='job-item-location']") or card.select_one("[class*='location']")

                        title = title_el.get_text(strip=True) if title_el else keyword
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location_text = location_el.get_text(strip=True) if location_el else "Germany"
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        app_url = f"https://www.stepstone.de{href}" if href.startswith("/") else href

                        loc_type = "remote" if "remote" in location_text.lower() else "onsite"

                        job = _build_job(
                            platform="stepstone",
                            country="Germany",
                            job_title=title,
                            company_name=company,
                            job_description=f"{keyword} position in {location_text}",
                            application_url=app_url,
                            currency=currency,
                            location_type=loc_type,
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.debug(f"StepStone card parse error: {e}")

                _random_delay(1.5, 3.5)

            except Exception as e:
                logger.error(f"StepStone scrape error: {e}")
                _random_delay(3, 6)

        logger.info(f"StepStone: found {len(jobs)} jobs")
        return jobs

    # ------------------------------------------------------------------ #
    #  Save jobs to database                                              #
    # ------------------------------------------------------------------ #
    def save_jobs(self, jobs: List[Dict]) -> int:
        """
        Save a list of job dicts to the database.
        Skips duplicates based on application_url.
        Returns number of new jobs saved.
        """
        saved = 0
        for job in jobs:
            try:
                # Check for duplicate by URL
                existing = None
                if job.get("application_url"):
                    rows = fetch_all(
                        "SELECT id FROM jobs WHERE application_url = ?",
                        (job["application_url"],),
                    )
                    existing = rows[0] if rows else None

                if existing:
                    logger.debug(f"Skipping duplicate job: {job['job_title']}")
                    continue

                insert_row("jobs", job)
                saved += 1
                logger.info(f"Saved job: {job['job_title']} at {job['company_name']} ({job['country']})")
            except Exception as e:
                logger.error(f"Error saving job {job.get('job_title')}: {e}")

        return saved

    # ------------------------------------------------------------------ #
    #  Main orchestrator                                                  #
    # ------------------------------------------------------------------ #
    def run(self, country_codes: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Orchestrate scraping for the given country codes.

        Args:
            country_codes: List of country codes e.g. ['uae', 'uk', 'sa', 'germany'].
                           Defaults to all configured countries.

        Returns:
            Dict mapping country -> number of jobs saved.
        """
        if country_codes is None:
            country_codes = ["uae", "uk", "sa", "germany"]

        init_db()
        results: Dict[str, int] = {}
        all_jobs: List[Dict] = []

        for code in country_codes:
            try:
                config = self._load_country_config(code)
                country_jobs: List[Dict] = []

                # Always scrape LinkedIn for all countries
                country_jobs.extend(self.scrape_linkedin(config))

                # Platform-specific scrapers
                if code in ("uae", "sa"):
                    country_jobs.extend(self.scrape_bayt(config))
                if code == "uk":
                    country_jobs.extend(self.scrape_reed(config))
                if code == "germany":
                    country_jobs.extend(self.scrape_stepstone(config))

                saved = self.save_jobs(country_jobs)
                results[code] = saved
                all_jobs.extend(country_jobs)
                logger.info(f"Country {code}: {saved} new jobs saved")

            except Exception as e:
                logger.error(f"Error scraping {code}: {e}")
                results[code] = 0

        self.jobs_found = all_jobs
        total = sum(results.values())
        logger.info(f"Scraping complete. Total new jobs saved: {total}")
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = JobScraper()
    results = scraper.run()
    print(f"Results: {results}")
