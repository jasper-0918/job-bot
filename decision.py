# agents/decision.py
import os
import json
import logging
import re
import anthropic
from config import (
    USER_PROFILE, SCAM_KEYWORDS, SCAM_DOMAINS,
    SCORE_AUTO_APPLY, SCORE_ASK_USER
)

log = logging.getLogger("decision")

# ── Claude client (lazy-loaded) ───────────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment.\n"
                "Make sure you have a .env file with: ANTHROPIC_API_KEY=your_key"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── Rule-based pre-filter (fast, no API call needed) ─────────────────────

def quick_scam_check(job: dict) -> bool:
    """
    Fast rule-based scam detection before calling AI.
    Returns True if clearly a scam.
    """
    text = (
        job.get("title", "") + " " +
        job.get("description", "") + " " +
        job.get("company", "")
    ).lower()

    for kw in SCAM_KEYWORDS:
        if kw.lower() in text:
            log.info(f"  [SCAM RULE] '{kw}' found in: {job['title']}")
            return True

    # Suspicious apply email domain
    email = job.get("apply_email", "") or ""
    if email:
        domain = email.split("@")[-1].lower()
        if domain in SCAM_DOMAINS:
            # Not automatic scam, but flag it for AI review
            job["_flagged_email_domain"] = True

    return False


# ── AI evaluation ─────────────────────────────────────────────────────────

def evaluate_job(job: dict) -> dict:
    """
    Send job to Claude for evaluation.
    Returns dict: { score, scam, decision, reason }
    """
    # Fast check first — save API calls
    if quick_scam_check(job):
        return {
            "score": 0,
            "scam": "yes",
            "decision": "REJECT",
            "reason": "Matched rule-based scam keyword filter."
        }

    flagged_note = ""
    if job.get("_flagged_email_domain"):
        flagged_note = "\nNote: The apply email uses a generic domain (gmail/yahoo) instead of a company domain — this is a mild scam indicator."

    prompt = f"""You are an expert job evaluator for a job-hunting AI assistant.

CANDIDATE PROFILE:
Name: {USER_PROFILE['name']}
Education: {USER_PROFILE['education']}
Skills: {', '.join(USER_PROFILE['skills'])}
Preferred roles: {', '.join(USER_PROFILE['preferred_roles'])}
Location: {USER_PROFILE['location']}
Remote only: {USER_PROFILE['remote_only']}
Min salary: ${USER_PROFILE['min_hourly_usd']}/hr or ₱{USER_PROFILE['min_monthly_php']}/month
Experience: {'; '.join(USER_PROFILE['experience'])}

JOB POSTING:
Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'Unknown')}
Platform: {job.get('platform', 'N/A')}
Salary info: {job.get('salary_info', 'Not specified')}
Apply email: {job.get('apply_email', 'None found')}
Description:
{job.get('description', 'No description available')[:800]}
{flagged_note}

SCAM RED FLAGS TO CHECK:
- Requests payment to apply
- Unrealistic salary promises
- Only Telegram/WhatsApp contact
- No company name or website
- MLM / network marketing
- Vague job description
- Email from gmail/yahoo instead of company domain

EVALUATION TASKS:
1. Score this job 0–100 for this candidate (skills match, legitimacy, clarity)
2. Is this a scam? yes / no / suspicious
3. Decision: AUTO_APPLY / ASK_USER / REJECT / IGNORE
   - AUTO_APPLY: strong match, legitimate, clear requirements
   - ASK_USER: decent match but needs human judgment
   - REJECT: scam, too many red flags, completely irrelevant
   - IGNORE: not relevant enough to bother with
4. Brief reason (1–2 sentences)

Respond ONLY in valid JSON — no extra text, no markdown:
{{
    "score": 75,
    "scam": "no",
    "decision": "AUTO_APPLY",
    "reason": "Good skills match for Python automation role with clear job description."
}}"""

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        # Clean up if Claude wraps in markdown
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)

        data = json.loads(raw)

        # Validate expected fields
        return {
            "score":    int(data.get("score", 0)),
            "scam":     str(data.get("scam", "unknown")),
            "decision": str(data.get("decision", "IGNORE")),
            "reason":   str(data.get("reason", "")),
        }

    except json.JSONDecodeError as e:
        log.warning(f"JSON parse error for '{job.get('title')}': {e}")
        return {"score": 0, "scam": "unknown", "decision": "IGNORE",
                "reason": "AI response could not be parsed."}
    except Exception as e:
        log.error(f"AI evaluation failed for '{job.get('title')}': {e}")
        return {"score": 0, "scam": "unknown", "decision": "IGNORE",
                "reason": f"Evaluation error: {str(e)[:100]}"}


# ── Final action decision ─────────────────────────────────────────────────

def final_decision(ai_data: dict) -> str:
    """
    Maps AI evaluation result to system action.
    Returns: AUTO_APPLY | ASK_USER | REJECT | IGNORE
    """
    if ai_data["scam"] == "yes":
        return "REJECT"

    score = ai_data.get("score", 0)
    ai_dec = ai_data.get("decision", "IGNORE")

    # AI decision takes priority, but we cross-check with score
    if score >= SCORE_AUTO_APPLY and ai_dec in ("AUTO_APPLY", "ASK_USER"):
        return "AUTO_APPLY"
    elif score >= SCORE_ASK_USER:
        return "ASK_USER"
    elif ai_dec == "REJECT" or score < 20:
        return "REJECT"

    return "IGNORE"
