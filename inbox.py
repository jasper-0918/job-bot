# agents/inbox.py
import imaplib
import email
import re
import logging
from email.header import decode_header
from datetime import datetime, timedelta

log = logging.getLogger("inbox")

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

INTERVIEW_KEYWORDS = [
    "interview", "schedule a call", "zoom meeting", "google meet",
    "teams meeting", "shortlisted", "selected for interview",
    "invite you for", "hr call", "initial interview", "final interview",
    "video call", "please schedule",
]
ASSESSMENT_KEYWORDS = [
    "assessment", "skills test", "exam", "practical exam",
    "typing test", "written exam", "online test", "questionnaire",
]
REJECTION_KEYWORDS = [
    "unfortunately", "not moving forward", "not selected",
    "other candidates", "position has been filled", "we regret",
    "not a match", "not proceed", "not shortlisted",
]
JOB_TRIGGERS = [
    "application", "job", "position", "hiring", "hr",
    "interview", "assessment", "apply", "resume", "cv",
    "cargoboss", "virtual assistant", "customer service",
]


def _decode(raw) -> str:
    parts = decode_header(raw or "")
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            result.append(str(part))
    return " ".join(result)


def _get_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return body.lower()


def _classify(subject: str, body: str) -> str:
    text = (subject + " " + body).lower()
    for kw in INTERVIEW_KEYWORDS:
        if kw in text:
            return "interview"
    for kw in ASSESSMENT_KEYWORDS:
        if kw in text:
            return "assessment"
    for kw in REJECTION_KEYWORDS:
        if kw in text:
            return "rejected"
    if any(t in text for t in ["thank you for apply", "received your application",
                                "re: job application", "re: application"]):
        return "followup"
    return "other"


def _is_job_related(subject: str, body: str) -> bool:
    text = (subject + " " + body).lower()
    return any(t in text for t in JOB_TRIGGERS)


def scan_inbox(lookback_days: int = 30) -> list:
    """
    Connect to Gmail via IMAP, find job-related emails,
    classify each, return list of response dicts.
    """
    import os
    gmail_addr = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_addr or not app_password:
        log.error("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in .env")
        return []

    results = []

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(gmail_addr, app_password)
        log.info("Gmail IMAP connected successfully.")
    except imaplib.IMAP4.error as e:
        log.error(f"IMAP login failed: {e}")
        log.error(
            "Troubleshooting:\n"
            "  1. Make sure IMAP is enabled in Gmail settings\n"
            "  2. Use an App Password, not your real Gmail password\n"
            "  3. Check GMAIL_APP_PASSWORD in .env (no spaces)"
        )
        return []

    since_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%d-%b-%Y")

    try:
        mail.select("INBOX")
        _, uids = mail.search(None, f"SINCE {since_date}")

        for uid in uids[0].split():
            try:
                _, data = mail.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])

                subject = _decode(msg.get("Subject", ""))
                from_raw = _decode(msg.get("From", ""))
                date_str = msg.get("Date", "")
                body = _get_body(msg)

                if not _is_job_related(subject, body):
                    continue

                email_match = re.search(r"<([^>]+)>", from_raw)
                from_email = email_match.group(1) if email_match else from_raw
                from_name = from_raw.split("<")[0].strip() if "<" in from_raw else from_raw

                category = _classify(subject, body)
                results.append({
                    "from_email": from_email,
                    "from_name": from_name,
                    "subject": subject,
                    "category": category,
                    "snippet": body[:400],
                    "received_at": date_str,
                })

            except Exception as e:
                log.debug(f"Email parse error uid {uid}: {e}")

    except Exception as e:
        log.warning(f"Inbox scan error: {e}")
    finally:
        mail.logout()

    log.info(f"Inbox: {len(results)} job-related emails found")
    return results
