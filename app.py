# api/app.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import sys, os

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from db.database import Database
from agents.decision import evaluate_job, final_decision
from agents.cover_letter import generate_cover_letter
from agents.apply import send_application
from agents.worker import execute_task, process_task_queue

app = FastAPI(title="Job AI Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()

# ── Models ────────────────────────────────────────────────

class TaskRequest(BaseModel):
    description: str
    context: str = ""

class ManualApplyRequest(BaseModel):
    job_id: int

class AddJobRequest(BaseModel):
    title: str
    company: str
    platform: str
    url: str = ""
    apply_email: str = ""
    description: str = ""
    salary_info: str = ""

# ── Dashboard Stats ───────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    return db.get_stats()

# ── Jobs ──────────────────────────────────────────────────

@app.get("/api/jobs")
def get_jobs(limit: int = 100, status: str = None):
    jobs = db.get_all_jobs(limit)
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return jobs

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/add")
def add_job_manual(req: AddJobRequest):
    """Manually add a job posting for evaluation."""
    job = req.dict()
    job["keywords_matched"] = []
    job_id = db.add_job(job)
    if not job_id:
        return {"added": False, "message": "Job already exists"}
    return {"added": True, "job_id": job_id}

@app.post("/api/jobs/{job_id}/evaluate")
def evaluate_single_job(job_id: int):
    """Run AI evaluation on a single job."""
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ai_data = evaluate_job(job)
    db.update_ai_evaluation(job_id, ai_data)
    return {"job_id": job_id, "evaluation": ai_data}

@app.post("/api/jobs/{job_id}/apply")
def apply_to_job(job_id: int):
    """
    Apply to a specific job (requires human approval via API).
    Use this for ASK_USER jobs.
    """
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.get("apply_email"):
        raise HTTPException(status_code=400, detail="No apply email for this job — apply manually")
    if job["status"] == "applied":
        return {"sent": False, "message": "Already applied to this job"}

    cover = generate_cover_letter(job)
    result = send_application(job, cover)
    if result["sent"]:
        db.update_status(job_id, "applied", cover)
        db.log_action(job_id, "applied_manual", f"Sent to {job['apply_email']}")
    return result

@app.post("/api/jobs/{job_id}/reject")
def reject_job(job_id: int):
    db.update_status(job_id, "rejected_by_user")
    return {"message": "Job rejected"}

# ── Inbox ─────────────────────────────────────────────────

@app.get("/api/inbox")
def get_responses():
    return db.get_responses()

@app.post("/api/inbox/scan")
def scan_inbox_now():
    """Trigger an inbox scan."""
    from agents.inbox import scan_inbox
    results = scan_inbox(lookback_days=30)
    for r in results:
        db.log_response(r)
    return {"scanned": len(results), "results": results}

# ── Tasks (Worker Agent) ──────────────────────────────────

@app.get("/api/tasks")
def get_tasks():
    return db.get_pending_tasks()

@app.post("/api/tasks/add")
def add_task(req: TaskRequest):
    """Add a task for the worker agent to complete."""
    task_id = db.add_task(req.description)
    return {"task_id": task_id, "message": "Task added to queue"}

@app.post("/api/tasks/{task_id}/run")
def run_task(task_id: int):
    """Execute a specific task immediately."""
    tasks = db.get_pending_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    result = execute_task(task["description"])
    db.complete_task(task_id, result["result"])
    return result

@app.post("/api/tasks/run-all")
def run_all_tasks():
    """Process all pending tasks."""
    results = process_task_queue(db)
    return {"processed": len(results), "results": results}

# ── Scrape + Evaluate (background job) ───────────────────

@app.post("/api/scrape")
def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger a full scrape + evaluate cycle in the background."""
    background_tasks.add_task(_run_scrape_evaluate)
    return {"message": "Scrape started in background. Check /api/stats for progress."}


def _run_scrape_evaluate():
    from agents.scraper import scrape_all_platforms
    jobs = scrape_all_platforms(use_playwright=False)
    new_count = 0
    for job in jobs:
        job_id = db.add_job(job)
        if job_id:
            new_count += 1
            ai_data = evaluate_job(job)
            db.update_ai_evaluation(job_id, ai_data)

# ── Serve Frontend ────────────────────────────────────────

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    @app.get("/")
    def serve_frontend():
        return FileResponse(str(frontend_path / "index.html"))
