"""
JobFlow Job Match Score Agent
Scores each scraped job against the user's resume using AI.
Filters out low-match jobs before applying — saves time and improves success rate.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobflow.database.db import fetch_all, update_row
from jobflow.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

RESUME_PATH = Path(__file__).parent.parent / "resume" / "base_resume.json"

MATCH_PROMPT = """You are a job match evaluator. Score how well this job matches the candidate's resume.

CANDIDATE RESUME SUMMARY:
Skills: {skills}
Experience: {experience}
Job Titles: {titles}

JOB POSTING:
Title: {job_title}
Company: {company}
Description: {description}

Return ONLY a JSON object with these fields:
{{
  "score": <integer 0-100>,
  "match_reasons": ["reason1", "reason2"],
  "missing_skills": ["skill1", "skill2"],
  "verdict": "strong_match" | "good_match" | "weak_match" | "no_match"
}}

Scoring guide:
- 80-100: Strong match — skills align, title matches, apply immediately
- 60-79: Good match — most skills present, minor gaps
- 40-59: Weak match — some overlap, significant gaps
- 0-39: No match — different domain or level
"""


class JobMatcher:
    """
    Scores job listings against the user's resume using LLM.
    Updates the database with match_score and match_details.
    Recommended minimum score to apply: 60.
    """

    def __init__(self, min_score: int = 60):
        self.min_score = min_score
        self.llm = LLMClient()
        self._resume_cache: Optional[Dict] = None

    def _load_resume(self) -> Dict:
        if self._resume_cache:
            return self._resume_cache
        if not RESUME_PATH.exists():
            logger.warning("base_resume.json not found — using empty resume")
            return {}
        with open(RESUME_PATH) as f:
            self._resume_cache = json.load(f)
        return self._resume_cache

    def _resume_summary(self, resume: Dict) -> Dict[str, str]:
        skills = resume.get("skills", [])
        if isinstance(skills, dict):
            all_skills = []
            for v in skills.values():
                all_skills.extend(v if isinstance(v, list) else [v])
            skills = all_skills

        experience = resume.get("experience", [])
        titles = [e.get("title", "") for e in experience if isinstance(e, dict)]
        companies = [e.get("company", "") for e in experience if isinstance(e, dict)]

        return {
            "skills": ", ".join(str(s) for s in skills[:20]),
            "experience": "; ".join(f"{t} at {c}" for t, c in zip(titles, companies))[:400],
            "titles": ", ".join(set(titles[:5])),
        }

    def score_job(self, job: Dict) -> Dict[str, Any]:
        """Score a single job against the resume. Returns score dict."""
        resume = self._load_resume()
        summary = self._resume_summary(resume)

        prompt = MATCH_PROMPT.format(
            skills=summary["skills"],
            experience=summary["experience"],
            titles=summary["titles"],
            job_title=job.get("job_title", ""),
            company=job.get("company_name", ""),
            description=(job.get("job_description", "") or "")[:500],
        )

        try:
            raw = self.llm.complete(prompt)
            # Extract JSON from response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return {
                    "score": int(result.get("score", 0)),
                    "match_reasons": result.get("match_reasons", []),
                    "missing_skills": result.get("missing_skills", []),
                    "verdict": result.get("verdict", "weak_match"),
                }
        except Exception as e:
            logger.error(f"LLM match score error for {job.get('job_title')}: {e}")

        # Fallback: keyword-based scoring if LLM fails
        return self._keyword_score(job, summary)

    def _keyword_score(self, job: Dict, summary: Dict) -> Dict[str, Any]:
        """Fallback keyword overlap scoring without LLM."""
        resume_skills = set(s.lower() for s in summary["skills"].split(", "))
        desc = (job.get("job_description", "") + " " + job.get("job_title", "")).lower()

        matched = [s for s in resume_skills if s and s in desc]
        score = min(100, int((len(matched) / max(len(resume_skills), 1)) * 100))

        verdict = "strong_match" if score >= 80 else "good_match" if score >= 60 else "weak_match" if score >= 40 else "no_match"
        return {
            "score": score,
            "match_reasons": [f"Keyword match: {s}" for s in matched[:3]],
            "missing_skills": [],
            "verdict": verdict,
        }

    def run(self, country_codes: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Score all unscored jobs in the database.
        Returns summary of scored jobs and those above min_score.
        """
        query = "SELECT * FROM jobs WHERE status = 'new' AND (match_score IS NULL OR match_score = 0)"
        params: tuple = ()

        if country_codes:
            placeholders = ",".join("?" * len(country_codes))
            query += f" AND country IN ({placeholders})"
            params = tuple(c.upper() for c in country_codes)

        query += f" LIMIT {limit}"

        jobs = fetch_all(query, params) if params else fetch_all(query)
        if not jobs:
            logger.info("No unscored jobs found")
            return {"scored": 0, "above_threshold": 0, "threshold": self.min_score}

        scored = 0
        above_threshold = 0

        for job in jobs:
            job_dict = dict(job)
            result = self.score_job(job_dict)
            score = result["score"]

            try:
                update_row(
                    "jobs",
                    {
                        "match_score": score,
                        "match_details": json.dumps({
                            "reasons": result["match_reasons"],
                            "missing": result["missing_skills"],
                            "verdict": result["verdict"],
                        }),
                        "status": "scored" if score >= self.min_score else "low_match",
                    },
                    "id = ?",
                    (job_dict["id"],),
                )
                scored += 1
                if score >= self.min_score:
                    above_threshold += 1
                logger.info(f"Scored '{job_dict.get('job_title')}' at {job_dict.get('company_name')}: {score}/100 ({result['verdict']})")
            except Exception as e:
                logger.error(f"Error saving match score: {e}")

        logger.info(f"Match scoring complete: {scored} scored, {above_threshold} above {self.min_score} threshold")
        return {
            "scored": scored,
            "above_threshold": above_threshold,
            "threshold": self.min_score,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    matcher = JobMatcher(min_score=60)
    results = matcher.run()
    print(f"Results: {results}")
