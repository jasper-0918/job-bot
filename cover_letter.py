# agents/cover_letter.py
import os
import re
import logging
import anthropic
from config import USER_PROFILE

log = logging.getLogger("cover_letter")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def generate_cover_letter(job: dict) -> str:
    """
    Generate a personalized cover letter for a specific job.
    Sounds like Jasper — professional, confident, concise.
    """
    prompt = f"""Write a professional cover letter email body for this job application.

APPLICANT:
Name: {USER_PROFILE['name']}
Email: {USER_PROFILE['email']}
Phone: {USER_PROFILE['phone']}
Education: {USER_PROFILE['education']}
Experience: {'; '.join(USER_PROFILE['experience'])}
Skills: {', '.join(USER_PROFILE['skills'][:12])}
Projects: {'; '.join(USER_PROFILE['projects'][:2])}
Certifications: {', '.join(USER_PROFILE['certifications'][:2])}

JOB:
Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'the company')}
Description: {job.get('description', '')[:500]}

TONE: {USER_PROFILE['tone']}
STYLE: {USER_PROFILE['writing_style']}

INSTRUCTIONS:
- Write ONLY the email body (no subject line, no HTML)
- Start with "Good day," or "Dear Hiring Team,"
- Keep it under 200 words
- Highlight 2–3 most relevant skills for THIS specific job
- End with your name and contact info
- Do NOT say "I am a fresh graduate with no experience"
- DO lead with what you can do, not what you lack
- Sound genuine, not like a template

Write the email body now:"""

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    except Exception as e:
        log.error(f"Cover letter generation failed: {e}")
        # Fallback to template
        return _fallback_cover_letter(job)


def _fallback_cover_letter(job: dict) -> str:
    """Fallback template if AI is unavailable."""
    return f"""Good day, {job.get('company', 'Hiring Team')},

I am Jasper John C. Paitan, a Computer Engineering graduate from La Salle University – Ozamiz and recent software intern at Benpos Systems, where I handled system software updates and client deployments. I am writing to express my interest in the {job.get('title', 'position')} role.

I bring hands-on experience in Python automation, AI model development (TensorFlow, HuggingFace Transformers), and cybersecurity fundamentals (Google Cloud Certificate, Cisco Jr. Cybersecurity Analyst). I work independently, learn quickly, and take my output seriously.

My CV is attached for your review.

Respectfully,
{USER_PROFILE['name']}
{USER_PROFILE['phone']}
{USER_PROFILE['email']}"""
