"""
Job AI Agent — Main Orchestrator
=================================
Usage:
  python main.py scrape          — Scrape + AI evaluate all platforms
  python main.py apply           — Auto-send eligible applications
  python main.py inbox           — Scan Gmail for responses
  python main.py worker          — Process pending task queue
  python main.py dashboard       — Show stats summary
  python main.py run             — Full cycle: scrape → apply → inbox → dashboard
  python main.py server          — Start API server + dashboard UI
"""

import argparse
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Setup logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("./logs/agent.log", mode="a"),
    ]
)
log = logging.getLogger("main")

from pathlib import Path
Path("./logs").mkdir(exist_ok=True)
Path("./assets").mkdir(exist_ok=True)

from db.database import Database
from agents.scraper import scrape_all_platforms
from agents.decision import evaluate_job, final_decision
from agents.cover_letter import generate_cover_letter
from agents.apply import send_application
from agents.inbox import scan_inbox
from agents.worker import process_task_queue
from config import SCORE_AUTO_APPLY, SCORE_ASK_USER, MAX_AUTO_APPLIES_PER_DAY


def check_env():
    """Check that required environment variables are set."""
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("GMAIL_ADDRESS"):
        missing.append("GMAIL_ADDRESS")
    if not os.getenv("GMAIL_APP_PASSWORD"):
        missing.append("GMAIL_APP_PASSWORD")

    if missing:
        log.error(f"Missing environment variables: {', '.join(missing)}")
        log.error("Create a .env file based on .env.example")
        return False
    return True


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_scrape(db: Database):
    log.info("=" * 55)
    log.info("STEP 1: SCRAPING JOB PLATFORMS")
    log.info("=" * 55)

    jobs = scrape_all_platforms(use_playwright=False)

    new_count = 0
    eval_count = 0

    for job in jobs:
        job_id = db.add_job(job)
        if not job_id:
            continue  # duplicate

        new_count += 1
        log.info(f"  [{new_count}] Evaluating: {job['title']} @ {job['company']}")

        ai_data = evaluate_job(job)
        db.update_ai_evaluation(job_id, ai_data)
        eval_count += 1

        symbol = {"AUTO_APPLY": "✅", "ASK_USER": "⚠️", "REJECT": "❌", "IGNORE": "  "}.get(ai_data["decision"], "  ")
        log.info(f"      {symbol} Score: {ai_data['score']}  |  Scam: {ai_data['scam']}  |  {ai_data['decision']}")
        log.info(f"         → {ai_data['reason'][:80]}")

    log.info(f"\n  Done. {new_count} new jobs found, {eval_count} evaluated.")
    return new_count


def cmd_apply(db: Database, auto_only: bool = True):
    log.info("=" * 55)
    log.info("STEP 2: APPLICATION ENGINE")
    log.info("=" * 55)

    jobs = db.get_evaluated_pending()
    log.info(f"  {len(jobs)} evaluated jobs in queue")

    applied = 0
    manual_needed = []

    for job in jobs:
        decision = job.get("ai_decision", "IGNORE")
        score = job.get("ai_score", 0)

        # No email found — always manual
        if not job.get("apply_email"):
            log.info(f"  [MANUAL] {job['title']} @ {job['company']} — no email found, visit: {job.get('url','')}")
            manual_needed.append(job)
            db.update_status(job["id"], "manual_required")
            continue

        if decision == "AUTO_APPLY" and score >= SCORE_AUTO_APPLY:
            if applied >= MAX_AUTO_APPLIES_PER_DAY:
                log.warning(f"  Daily limit ({MAX_AUTO_APPLIES_PER_DAY}) reached — stopping auto-apply.")
                break

            log.info(f"  [AUTO] Generating cover letter for: {job['title']}")
            cover = generate_cover_letter(job)
            result = send_application(job, cover, max_per_day=MAX_AUTO_APPLIES_PER_DAY)

            if result["sent"]:
                db.update_status(job["id"], "applied", cover)
                db.log_action(job["id"], "auto_applied", f"Sent to {job['apply_email']}")
                applied += 1
                log.info(f"  ✅ Applied: {job['title']} → {job['apply_email']}")
            else:
                log.warning(f"  ❌ Failed: {job['title']} — {result['error']}")
                db.update_status(job["id"], "apply_failed")

        elif decision == "ASK_USER":
            log.info(f"  [REVIEW] {job['title']} @ {job['company']} (score: {score})")
            log.info(f"          → {job['apply_email']}")
            log.info(f"          → {job.get('ai_reason', '')[:70]}")
            manual_needed.append(job)
            db.update_status(job["id"], "awaiting_approval")

    log.info(f"\n  Applied: {applied} | Needs manual review: {len(manual_needed)}")

    if manual_needed:
        log.info("\n  JOBS NEEDING YOUR REVIEW:")
        for j in manual_needed:
            log.info(f"    • [{j['ai_decision']}] {j['title']} @ {j['company']}")
            if j.get("apply_email"):
                log.info(f"      Email: {j['apply_email']}")
            if j.get("url"):
                log.info(f"      URL: {j['url']}")

    return applied


def cmd_inbox(db: Database):
    log.info("=" * 55)
    log.info("STEP 3: SCANNING INBOX")
    log.info("=" * 55)

    results = scan_inbox(lookback_days=30)

    for r in results:
        db.log_response(r)
        cat = r["category"]
        emoji = {"interview": "🎉", "assessment": "📝", "rejected": "❌", "followup": "📬"}.get(cat, "📧")
        log.info(f"  {emoji} [{cat.upper()}] {r['subject']}")
        log.info(f"      From: {r['from_name']} <{r['from_email']}>")

    log.info(f"\n  Inbox scan complete. {len(results)} job-related emails found.")
    return results


def cmd_worker(db: Database):
    log.info("=" * 55)
    log.info("STEP 4: WORKER AGENT — PROCESSING TASKS")
    log.info("=" * 55)
    results = process_task_queue(db)
    if not results:
        log.info("  No pending tasks. Add tasks via the dashboard or API.")
    return results


def cmd_dashboard(db: Database):
    stats = db.get_stats()
    print("\n" + "=" * 55)
    print("  JOB AI AGENT — DASHBOARD")
    print("=" * 55)
    print(f"  Total jobs found       : {stats['total_found']}")
    print(f"  Applied                : {stats['applied']}")
    print(f"  Scams caught           : {stats['scams_caught']}")
    print(f"  Auto-apply eligible    : {stats['auto_eligible']}")
    print(f"  Needs your review      : {stats['needs_review']}")
    print(f"  Pending evaluation     : {stats['pending']}")
    print(f"  Email responses        : {stats['responses']}")
    print(f"  Interviews scheduled   : {stats['interviews']} 🎉")
    print("=" * 55)
    print()


def cmd_server():
    """Start FastAPI server + open dashboard."""
    import webbrowser
    import threading
    import uvicorn

    def open_browser():
        import time; time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000")

    log.info("Starting Job AI Agent server at http://127.0.0.1:8000")
    log.info("Dashboard will open in your browser automatically.")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Job AI Agent — Autonomous job hunting assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  scrape       Find and evaluate new job listings
  apply        Send applications to eligible jobs
  inbox        Scan Gmail for interview / assessment emails
  worker       Process your task queue (worker agent)
  dashboard    Show stats summary
  run          Full cycle: scrape → apply → inbox → dashboard
  server       Launch the web dashboard (http://localhost:8000)
        """
    )
    parser.add_argument("command", choices=["scrape", "apply", "inbox", "worker",
                                             "dashboard", "run", "server"])
    args = parser.parse_args()

    if args.command == "server":
        cmd_server()
        return

    if not check_env():
        sys.exit(1)

    db = Database()

    if args.command == "scrape":
        cmd_scrape(db)
    elif args.command == "apply":
        cmd_apply(db)
    elif args.command == "inbox":
        cmd_inbox(db)
    elif args.command == "worker":
        cmd_worker(db)
    elif args.command == "dashboard":
        cmd_dashboard(db)
    elif args.command == "run":
        cmd_scrape(db)
        cmd_apply(db)
        cmd_inbox(db)
        cmd_worker(db)
        cmd_dashboard(db)

    db.close()


if __name__ == "__main__":
    main()
