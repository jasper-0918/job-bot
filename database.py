# db/database.py
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("db")


class Database:
    def __init__(self, path: str = "./job_agent.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                company         TEXT DEFAULT 'Unknown',
                platform        TEXT NOT NULL,
                url             TEXT,
                apply_email     TEXT,
                description     TEXT,
                salary_info     TEXT,
                keywords_matched TEXT,
                ai_score        INTEGER DEFAULT 0,
                ai_scam         TEXT DEFAULT 'unknown',
                ai_decision     TEXT DEFAULT 'PENDING',
                ai_reason       TEXT,
                status          TEXT DEFAULT 'pending',
                cover_letter    TEXT,
                applied_at      TEXT,
                found_at        TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                UNIQUE(title, company, platform)
            );

            CREATE TABLE IF NOT EXISTS responses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      INTEGER REFERENCES jobs(id),
                from_email  TEXT,
                from_name   TEXT,
                subject     TEXT,
                category    TEXT,
                snippet     TEXT,
                received_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                result      TEXT,
                created_at  TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS apply_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      INTEGER REFERENCES jobs(id),
                action      TEXT,
                detail      TEXT,
                timestamp   TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # ── Jobs ──────────────────────────────────────────────

    def add_job(self, job: dict) -> int | None:
        """Insert job. Returns row id if new, None if duplicate."""
        now = datetime.utcnow().isoformat()
        try:
            cur = self.conn.execute("""
                INSERT INTO jobs
                    (title, company, platform, url, apply_email, description,
                     salary_info, keywords_matched, found_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                job.get("title", "Untitled"),
                job.get("company", "Unknown"),
                job.get("platform", ""),
                job.get("url", ""),
                job.get("apply_email"),
                job.get("description", ""),
                job.get("salary_info", ""),
                json.dumps(job.get("keywords_matched", [])),
                now, now,
            ))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None  # duplicate

    def update_ai_evaluation(self, job_id: int, ai_data: dict):
        self.conn.execute("""
            UPDATE jobs SET
                ai_score=?, ai_scam=?, ai_decision=?, ai_reason=?,
                status=?, updated_at=?
            WHERE id=?
        """, (
            ai_data.get("score", 0),
            ai_data.get("scam", "unknown"),
            ai_data.get("decision", "IGNORE"),
            ai_data.get("reason", ""),
            "evaluated",
            datetime.utcnow().isoformat(),
            job_id,
        ))
        self.conn.commit()

    def update_status(self, job_id: int, status: str, cover_letter: str = None):
        now = datetime.utcnow().isoformat()
        if status == "applied":
            self.conn.execute(
                "UPDATE jobs SET status=?, applied_at=?, cover_letter=?, updated_at=? WHERE id=?",
                (status, now, cover_letter, now, job_id)
            )
        else:
            self.conn.execute(
                "UPDATE jobs SET status=?, updated_at=? WHERE id=?",
                (status, now, job_id)
            )
        self.conn.commit()

    def get_evaluated_pending(self) -> list:
        """Jobs that have been AI-evaluated but not yet applied to."""
        rows = self.conn.execute("""
            SELECT * FROM jobs
            WHERE status='evaluated' AND ai_scam='no'
            ORDER BY ai_score DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def get_all_jobs(self, limit: int = 100) -> list:
        rows = self.conn.execute(
            "SELECT * FROM jobs ORDER BY found_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_job_by_id(self, job_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    # ── Responses ─────────────────────────────────────────

    def log_response(self, r: dict, job_id: int = None):
        self.conn.execute("""
            INSERT INTO responses
                (job_id, from_email, from_name, subject, category, snippet, received_at)
            VALUES (?,?,?,?,?,?,?)
        """, (
            job_id, r.get("from_email"), r.get("from_name"),
            r.get("subject"), r.get("category"),
            r.get("snippet"), r.get("received_at", datetime.utcnow().isoformat())
        ))
        self.conn.commit()

    def get_responses(self) -> list:
        rows = self.conn.execute(
            "SELECT * FROM responses ORDER BY received_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Tasks ─────────────────────────────────────────────

    def add_task(self, description: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO tasks (description, created_at) VALUES (?,?)",
            (description, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def complete_task(self, task_id: int, result: str):
        self.conn.execute("""
            UPDATE tasks SET status='done', result=?, completed_at=? WHERE id=?
        """, (result, datetime.utcnow().isoformat(), task_id))
        self.conn.commit()

    def get_pending_tasks(self) -> list:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE status='pending' ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Apply Log ─────────────────────────────────────────

    def log_action(self, job_id: int, action: str, detail: str = ""):
        self.conn.execute(
            "INSERT INTO apply_log (job_id, action, detail, timestamp) VALUES (?,?,?,?)",
            (job_id, action, detail, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    # ── Stats ─────────────────────────────────────────────

    def get_stats(self) -> dict:
        row = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END) as applied,
                SUM(CASE WHEN ai_scam='yes' THEN 1 ELSE 0 END) as scams_caught,
                SUM(CASE WHEN ai_decision='AUTO_APPLY' THEN 1 ELSE 0 END) as auto_eligible,
                SUM(CASE WHEN ai_decision='ASK_USER' THEN 1 ELSE 0 END) as needs_review,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending
            FROM jobs
        """).fetchone()
        responses = self.conn.execute("SELECT COUNT(*) as n FROM responses").fetchone()
        interviews = self.conn.execute(
            "SELECT COUNT(*) as n FROM responses WHERE category='interview'"
        ).fetchone()
        return {
            "total_found":     row["total"] or 0,
            "applied":         row["applied"] or 0,
            "scams_caught":    row["scams_caught"] or 0,
            "auto_eligible":   row["auto_eligible"] or 0,
            "needs_review":    row["needs_review"] or 0,
            "pending":         row["pending"] or 0,
            "responses":       responses["n"] or 0,
            "interviews":      interviews["n"] or 0,
        }

    def close(self):
        self.conn.close()
