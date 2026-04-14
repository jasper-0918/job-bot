# agents/apply.py
import os
import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from config import USER_PROFILE, DELAY_BETWEEN_APPLIES_SEC

log = logging.getLogger("apply")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# Tracks how many auto-applies sent today
_daily_count = {"date": "", "count": 0}


def _get_daily_count() -> int:
    from datetime import date
    today = str(date.today())
    if _daily_count["date"] != today:
        _daily_count["date"] = today
        _daily_count["count"] = 0
    return _daily_count["count"]


def _increment_daily():
    _daily_count["count"] += 1


def _build_email(job: dict, cover_letter: str, subject_override: str = None) -> MIMEMultipart:
    gmail_addr = os.getenv("GMAIL_ADDRESS")
    subject = subject_override or f"Job Application – {job.get('title', 'Position')} – {USER_PROFILE['name']}"

    msg = MIMEMultipart()
    msg["From"] = f"{USER_PROFILE['name']} <{gmail_addr}>"
    msg["To"] = job["apply_email"]
    msg["Subject"] = subject
    msg.attach(MIMEText(cover_letter, "plain"))

    # Attach CV
    cv_path = Path(os.getenv("CV_PATH", "./assets/Jasper_John_Paitan_CV.pdf"))
    if cv_path.exists():
        with open(cv_path, "rb") as f:
            att = MIMEApplication(f.read(), _subtype="pdf")
            att.add_header("Content-Disposition", "attachment",
                           filename=cv_path.name)
            msg.attach(att)
    else:
        log.warning(f"CV not found at {cv_path} — sending without attachment")

    return msg


def send_application(job: dict, cover_letter: str,
                     max_per_day: int = 15,
                     subject_override: str = None) -> dict:
    """
    Send one email application.
    Returns: {sent: bool, error: str|None}
    """
    if not job.get("apply_email"):
        return {"sent": False, "error": "No apply_email found for this job"}

    if _get_daily_count() >= max_per_day:
        return {"sent": False, "error": f"Daily limit reached ({max_per_day} applications/day)"}

    gmail_addr = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_addr or not app_password:
        return {"sent": False, "error": "GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing from .env"}

    try:
        msg = _build_email(job, cover_letter, subject_override)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_addr, app_password)
            server.send_message(msg)

        _increment_daily()
        log.info(f"  ✅ Sent to {job['apply_email']} — '{job['title']}' @ {job['company']}")
        time.sleep(DELAY_BETWEEN_APPLIES_SEC)
        return {"sent": True, "error": None}

    except smtplib.SMTPAuthenticationError:
        return {"sent": False,
                "error": "Gmail authentication failed. Check GMAIL_APP_PASSWORD in .env"}
    except smtplib.SMTPRecipientsRefused:
        return {"sent": False,
                "error": f"Email address rejected by server: {job['apply_email']}"}
    except Exception as e:
        return {"sent": False, "error": str(e)}
