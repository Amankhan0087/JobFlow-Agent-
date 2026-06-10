"""
JobFlow LLM Client
Supports Groq and Mistral API backends with retry logic.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Union

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds


class LLMClient:
    """
    Unified LLM client supporting Groq and Mistral API providers.
    Includes automatic retry with exponential backoff.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

    GROQ_DEFAULT_MODEL = "llama3-8b-8192"
    MISTRAL_DEFAULT_MODEL = "mistral-small-latest"

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider: 'groq' or 'mistral'. Defaults to LLM_PROVIDER env var or 'groq'.
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq")
        self.provider = self.provider.lower()

        if self.provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY", "")
            self.api_url = self.GROQ_API_URL
            self.model = os.getenv("GROQ_MODEL", self.GROQ_DEFAULT_MODEL)
        elif self.provider == "mistral":
            self.api_key = os.getenv("MISTRAL_API_KEY", "")
            self.api_url = self.MISTRAL_API_URL
            self.model = os.getenv("MISTRAL_MODEL", self.MISTRAL_DEFAULT_MODEL)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'groq' or 'mistral'.")

        if not self.api_key:
            logger.warning(f"{self.provider.upper()}_API_KEY not set. LLM calls will fail.")

        self.client = httpx.Client(timeout=60)

    def _call_api(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """
        Internal API call with retry logic.
        Returns the assistant message content as string.
        """
        if not self.api_key:
            raise RuntimeError(f"No API key configured for {self.provider}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.client.post(self.api_url, headers=headers, json=payload)

                if resp.status_code == 429:
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"Rate limited. Retrying in {wait}s (attempt {attempt+1})")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text[:200]}")
                last_error = e
                if e.response.status_code in (400, 401, 403):
                    break  # No point retrying auth errors
                wait = RETRY_BACKOFF_BASE ** attempt
                time.sleep(wait)
            except Exception as e:
                logger.error(f"LLM API error (attempt {attempt+1}): {e}")
                last_error = e
                wait = RETRY_BACKOFF_BASE ** attempt
                time.sleep(wait)

        raise RuntimeError(f"LLM API failed after {MAX_RETRIES} retries: {last_error}")

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
    ) -> str:
        """
        Complete a prompt with optional system context.

        Args:
            prompt: User message
            system_prompt: Optional system instruction
            json_mode: If True, requests JSON output format
            temperature: Sampling temperature (0-1)

        Returns:
            String response from LLM
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self._call_api(messages, temperature=temperature, json_mode=json_mode)

    def customize_resume(
        self,
        base_resume: Dict,
        job_description: str,
        country: str,
    ) -> Union[Dict, str]:
        """
        Customize a resume for a specific job using the LLM.

        Args:
            base_resume: Base resume dict
            job_description: Target job description
            country: Target country for cultural nuances

        Returns:
            Customized resume as dict (parsed JSON) or string on failure
        """
        system_prompt = """You are an expert resume writer specializing in ATS-optimized resumes.
Your task is to customize a resume JSON for a specific job posting.
Keep all factual information accurate - only reorder, emphasize, and tailor the language.
Always return valid JSON in the same structure as the input."""

        prompt = f"""Customize this resume for the following job.

BASE RESUME:
{json.dumps(base_resume, indent=2)}

TARGET JOB:
{job_description}

TARGET COUNTRY: {country}

Instructions:
1. Rewrite the summary to directly address the job requirements
2. Reorder experience bullet points to highlight relevant skills first
3. Add/emphasize skills that match the job description
4. Keep all dates and companies exactly as-is
5. Tailor language for {country} job market conventions
6. Return the complete resume as valid JSON with the same structure

Return ONLY the JSON, no explanation."""

        try:
            response = self._call_api(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=3000,
                json_mode=True,
            )
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON resume, returning as string")
            return response
        except Exception as e:
            logger.error(f"Resume customization failed: {e}")
            return base_resume

    def answer_question(self, question: str, context: str = "") -> str:
        """
        Answer a screening question for a job application.

        Args:
            question: The screening question text
            context: Background context about the applicant

        Returns:
            Concise answer string
        """
        system_prompt = (
            "You are answering job application screening questions on behalf of a candidate. "
            "Give honest, professional, concise answers (1-3 sentences). "
            "Be positive and enthusiastic."
        )

        prompt = f"""Answer this job application screening question.

Applicant context: {context}

Question: {question}

Provide a concise, professional answer (1-3 sentences max)."""

        try:
            return self._call_api(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=200,
            )
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return "Yes, I meet this requirement and am very interested in this position."

    def generate_followup_email(self, context: Dict) -> Dict[str, str]:
        """
        Generate a follow-up email for a job application.

        Args:
            context: Dict with job_title, company_name, followup_type, applicant_name

        Returns:
            Dict with 'subject' and 'body'
        """
        prompt = f"""Generate a professional follow-up email for a job application.

Context:
- Applicant: {context.get('applicant_name', 'Job Seeker')}
- Job Title: {context.get('job_title', 'the position')}
- Company: {context.get('company_name', 'the company')}
- Follow-up Type: {context.get('followup_type', 'status_check')}
- Days Since Application: {context.get('days_since', 7)}

Return a JSON object with "subject" and "body" keys.
The email should be professional, concise (3-4 paragraphs), and end with a clear call to action."""

        try:
            response = self._call_api(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                json_mode=True,
            )
            parsed = json.loads(response)
            return {
                "subject": parsed.get("subject", f"Follow-up: {context.get('job_title', '')}"),
                "body": parsed.get("body", "I wanted to follow up on my application."),
            }
        except Exception as e:
            logger.error(f"Follow-up email generation failed: {e}")
            return {
                "subject": f"Following Up: {context.get('job_title', 'Application')}",
                "body": f"Dear Hiring Team,\n\nI wanted to follow up on my application for the {context.get('job_title', 'position')} at {context.get('company_name', 'your company')}.\n\nBest regards,\n{context.get('applicant_name', 'Applicant')}",
            }

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = LLMClient()
    response = client.complete("Say hello in one sentence.")
    print(response)
