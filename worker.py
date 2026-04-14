# agents/worker.py
# ─────────────────────────────────────────────────────────
#  Task Worker Agent — Your "Digital Clone"
#
#  You delegate tasks to this agent via the dashboard or CLI.
#  It uses Claude to attempt the task, reports results,
#  and flags anything that needs your attention.
#
#  Example tasks you can delegate:
#    - "Write a reply to this email: [paste email]"
#    - "Summarize this job description and tell me if I should apply"
#    - "Draft a follow-up email to [company] — I applied 1 week ago"
#    - "Review my cover letter and suggest improvements"
#    - "Translate this English job post to Tagalog"
# ─────────────────────────────────────────────────────────

import os
import logging
import anthropic
from config import USER_PROFILE

log = logging.getLogger("worker")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client

WORKER_SYSTEM_PROMPT = f"""You are a highly capable AI assistant acting as the digital clone of {USER_PROFILE['name']}.

About the person you are cloning:
- Name: {USER_PROFILE['name']}
- Background: {USER_PROFILE['education']}
- Skills: {', '.join(USER_PROFILE['skills'][:15])}
- Experience: {'; '.join(USER_PROFILE['experience'])}
- Tone when writing: {USER_PROFILE['tone']}

Your job is to:
1. Complete tasks delegated to you by {USER_PROFILE['name']}
2. Think and communicate like them
3. Flag anything that requires their personal input or decision
4. Always be honest about what you can and cannot do

When completing a task, structure your response as:
- STATUS: DONE / NEEDS_REVIEW / CANNOT_COMPLETE
- RESULT: (your output — email draft, summary, code, etc.)
- FLAGS: (anything the human should check or decide)"""


def execute_task(task_description: str, context: str = "") -> dict:
    """
    Execute a delegated task using Claude.

    Args:
        task_description: What needs to be done
        context: Any additional context (email content, job description, etc.)

    Returns:
        dict: { status, result, flags, raw_response }
    """
    full_prompt = task_description
    if context:
        full_prompt += f"\n\nContext / Reference material:\n{context}"

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=WORKER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": full_prompt}]
        )

        raw = response.content[0].text.strip()

        # Parse structured response
        status = "DONE"
        result = raw
        flags = ""

        if "STATUS:" in raw:
            lines = raw.split("\n")
            result_lines = []
            flag_lines = []
            in_result = False
            in_flags = False

            for line in lines:
                if line.startswith("STATUS:"):
                    status = line.replace("STATUS:", "").strip()
                elif line.startswith("RESULT:"):
                    in_result = True
                    in_flags = False
                    val = line.replace("RESULT:", "").strip()
                    if val:
                        result_lines.append(val)
                elif line.startswith("FLAGS:"):
                    in_result = False
                    in_flags = True
                    val = line.replace("FLAGS:", "").strip()
                    if val:
                        flag_lines.append(val)
                elif in_result:
                    result_lines.append(line)
                elif in_flags:
                    flag_lines.append(line)

            result = "\n".join(result_lines).strip() or raw
            flags = "\n".join(flag_lines).strip()

        return {
            "status": status,
            "result": result,
            "flags": flags,
            "raw_response": raw,
        }

    except Exception as e:
        log.error(f"Task execution failed: {e}")
        return {
            "status": "CANNOT_COMPLETE",
            "result": "",
            "flags": f"Error: {str(e)}",
            "raw_response": "",
        }


def process_task_queue(db) -> list:
    """
    Process all pending tasks from the database.
    Returns list of completed task results.
    """
    pending = db.get_pending_tasks()
    if not pending:
        log.info("No pending tasks in queue.")
        return []

    log.info(f"Processing {len(pending)} pending task(s)...")
    results = []

    for task in pending:
        log.info(f"  Working on task #{task['id']}: {task['description'][:60]}...")
        outcome = execute_task(task["description"])
        db.complete_task(task["id"], outcome["result"])

        results.append({
            "task_id": task["id"],
            "description": task["description"],
            **outcome
        })

        if outcome["flags"]:
            log.warning(f"  ⚠️  Task #{task['id']} needs your attention: {outcome['flags'][:100]}")
        else:
            log.info(f"  ✅ Task #{task['id']} completed: {outcome['status']}")

    return results
