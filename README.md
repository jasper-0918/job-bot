# 🤖 Job AI Agent

> An autonomous AI-powered job hunting assistant that finds job listings, evaluates them for scams, writes personalized cover letters, sends applications, and monitors your inbox — all running on your own computer.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Claude AI](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## What Is This?

Job AI Agent is a personal autonomous agent system — a **digital clone** that hunts for jobs on your behalf while you sleep, study, or work another job. It is built around the idea that finding remote work is itself a full-time task, and that task can be largely automated with the right tools.

The system scrapes job listings from multiple platforms, uses Claude AI to evaluate each one (skills match, salary, legitimacy, scam detection), generates a personalized cover letter, sends the email application with your CV attached, and then monitors your Gmail inbox for interview invites and assessment emails — all logged in a local SQLite database and viewable through a web dashboard.

There is also a **Worker Agent** — a task delegation system where you describe a task in plain English ("write a follow-up email to this company", "summarize this job description") and the AI completes it, acting as your digital assistant.

---

## Features

| Feature | Description |
|---|---|
| **Multi-platform scraping** | Scrapes Indeed PH, Jobstreet PH, and OnlineJobs.ph simultaneously |
| **AI job evaluation** | Claude scores each job 0–100 based on your skills, salary, and job quality |
| **Scam detection** | Rule-based + AI detection catches fake listings, pay-to-apply scams, and MLM schemes |
| **Cover letter generation** | AI writes a unique, personalized cover letter per job using your actual background |
| **Auto-apply engine** | Sends email applications with your CV attached for high-scoring jobs automatically |
| **Human approval layer** | Jobs scoring 50–78 are flagged for your manual review — not auto-sent |
| **Gmail inbox scanner** | IMAP-based inbox scanner classifies responses as interview, assessment, rejected, or followup |
| **Worker Agent** | Delegate tasks to an AI clone of yourself via the dashboard |
| **Web dashboard** | Full browser-based UI to review jobs, approve applications, and delegate tasks |
| **SQLite tracker** | Every job, application, response, and task is logged permanently |
| **Daily safety limits** | Hard cap on auto-applies per day to prevent spam and account bans |

---

## Project Structure

```
job-ai-agent/
│
├── main.py                    # CLI entry point — run commands here
├── config.py                  # YOUR profile, skills, preferences, thresholds
├── setup.py                   # One-click setup script
├── requirements.txt           # Python dependencies
├── .env.example               # Template for your API keys
│
├── agents/
│   ├── scraper.py             # Multi-platform job scraper (requests + Playwright)
│   ├── decision.py            # AI job evaluator + scam detector
│   ├── cover_letter.py        # AI personalized cover letter writer
│   ├── apply.py               # SMTP email sender with CV attachment
│   ├── inbox.py               # Gmail IMAP inbox scanner + response classifier
│   └── worker.py              # Task delegation agent (your "digital clone")
│
├── api/
│   └── app.py                 # FastAPI REST API backend
│
├── db/
│   └── database.py            # SQLite database layer
│
├── frontend/
│   └── index.html             # Web dashboard UI
│
├── assets/                    # Place your CV PDF here
└── logs/                      # Application logs
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- A Gmail account
- An Anthropic API key
- Your CV in PDF format

### Step 1 — Clone the repository

```bash
git clone https://github.com/jasper-john-paitan/job-ai-agent.git
cd job-ai-agent
```

### Step 2 — Run the one-click setup

```bash
python setup.py
```

This installs all packages, creates your `.env` file, installs the Playwright browser, and creates all required folders.

### Step 3 — Fill in your `.env` file

Open `.env` and add your credentials:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
CV_PATH=./assets/YourName_CV.pdf
```

**Getting your Anthropic API key:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in → API Keys → Create Key
3. Copy and paste into `.env`

**Getting your Gmail App Password:**
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required)
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Select Mail + Windows Computer → Generate
5. Copy the 16-character code into `.env`

**Enable Gmail IMAP:**
Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP → Save Changes

### Step 4 — Add your CV

Copy your CV PDF into the `assets/` folder and update `CV_PATH` in `.env` to match the filename.

### Step 5 — Customize your profile

Open `config.py`. Your information should already be filled in. Confirm the settings match what you want:

```python
SCORE_AUTO_APPLY  = 78   # auto-apply if AI score >= this
SCORE_ASK_USER    = 50   # ask you first if score is between 50–77
MAX_AUTO_APPLIES_PER_DAY = 15   # safety cap per day
```

---

## Usage

### Launch the web dashboard (recommended)

```bash
python main.py server
```

Then open **http://localhost:8000** in your browser.

### Run from the terminal

```bash
python main.py run          # Full cycle: scrape → evaluate → apply → inbox → stats
python main.py scrape       # Find and evaluate new jobs only
python main.py apply        # Send pending applications only
python main.py inbox        # Scan Gmail for responses only
python main.py worker       # Process your delegated task queue
python main.py dashboard    # Print stats summary in terminal
```

### Web Dashboard Tabs

| Tab | What it does |
|---|---|
| **Dashboard** | Stats overview — jobs found, applied, scams caught, interviews |
| **Job Listings** | Browse all scraped jobs, filter by decision and status |
| **Auto-Apply Queue** | Review and approve jobs the AI wants to apply to |
| **Inbox Responses** | See email responses classified by category |
| **Worker Agent** | Type a task and the AI completes it for you |
| **Add Job Manually** | Paste a job post you found — AI evaluates it instantly |

---

## How the AI Decision System Works

Every job goes through a three-stage evaluation:

**Stage 1 — Rule-based scam filter**
Instant check for known red flag keywords. No API cost. Clear scams are rejected before the AI even sees them.

**Stage 2 — Claude AI evaluation**
The job description, company, and your profile are sent to Claude. It returns a score and structured decision:

```
Score 78–100  →  AUTO_APPLY   Bot sends the application automatically
Score 50–77   →  ASK_USER     Bot flags it — you approve or skip
Score 20–49   →  IGNORE       Not relevant enough to bother with
Score 0–19    →  REJECT       Poor quality or suspicious
Scam = yes    →  REJECT       Regardless of score
```

**Stage 3 — Human approval layer**
ASK_USER jobs appear in your dashboard with the AI's reasoning. You approve or skip with one click. Nothing ambiguous is sent without your decision.

---

## Scam Detection

Two layers work together:

**Rule-based keywords (instant)**
- Payment to apply: "registration fee", "training fee", "send money"
- Unrealistic promises: "earn $500 daily", "easy money", "no experience $50/hr"
- Suspicious contact: "Telegram only", "WhatsApp only", no company name
- MLM and network marketing language
- Generic hiring emails from gmail.com or yahoo.com instead of company domains

**AI analysis (deep)**
Claude reads the full context and flags vague job descriptions, inconsistent salary claims, missing company details, and unusual requirements — with a plain-English explanation visible in the dashboard.

---

## Worker Agent — Task Delegation

Type a task in plain English in the Worker Agent tab. The AI acts as you and completes it.

**Example tasks:**

```
"Write a follow-up email to CargoBoss — I applied 5 days ago with no response"
"Summarize this job description and tell me if I should apply: [paste text]"
"Draft a reply to this interview invitation: [paste email]"
"Review my cover letter and suggest improvements: [paste it]"
"List the top 5 questions I should prepare for a customer service interview"
"Translate this job post to Tagalog"
```

The agent knows your background, skills, and writing tone — responses sound like you wrote them.

---

## Strengths

**Saves 2–4 hours daily.** Manually checking 3 job platforms, reading 50+ listings, writing cover letters, and tracking applications takes hours. This system does the same work in under 10 minutes.

**Consistent evaluation.** The bot applies identical criteria to every job without fatigue or rushing. It reads the full job description at midnight just as carefully as it does at 9 AM.

**Catches scams reliably.** Two-layer detection catches common Philippine remote job scams that are easy to miss when you're quickly scrolling through listings.

**Personalized cover letters.** Every auto-applied email is written specifically for that job — referencing the actual job description and matching it to your real skills and experience.

**Full audit trail.** Everything is logged. You always know what was sent, when, to whom, with which cover letter, and what response came back.

**Scales your applications.** Realistically applying to 3–5 jobs per day manually is already hard to sustain. The bot can handle 15 applications per day without extra effort from you.

**Portfolio value.** The project itself demonstrates Python automation, AI agent design, web scraping, SMTP/IMAP email handling, REST API development, SQLite, and a complete frontend — all in one repository.

---

## Weaknesses and Limitations

**Scraping can break.** Job sites periodically change their HTML structure. When they do, the scrapers stop finding listings until the CSS selectors in `scraper.py` are manually updated.

**Portal-based applications need manual action.** Jobs on Workday, Greenhouse, or any custom application form cannot be auto-filled. The bot flags these for you but cannot submit forms.

**Email-only auto-apply.** Auto-apply only works when a direct email address is found in the job listing. Many posts only have "Apply on website" — those are always flagged for manual action.

**API costs money.** Each job evaluation uses one Claude API call. At roughly ₱0.50–₱2.50 per evaluation, scanning 100 jobs per day costs about ₱50–₱250 per month. Very affordable but not free.

**Requires Gmail App Password.** The email system uses SMTP with an App Password — not OAuth. Users with strict Google Workspace security policies may need additional setup.

**Not 100% autonomous by design.** Ambiguous jobs always require your approval. This is intentional — full automation without oversight would produce bad applications and risk account flags on job platforms.

**Bot detection is imperfect.** Some sites use advanced bot detection. The Playwright stealth mode reduces detection but does not eliminate it. The bot falls back to requests-based scraping automatically when blocked.

---

## Benefits at a Glance

| Without Job AI Agent | With Job AI Agent |
|---|---|
| Manually check 3 sites daily | Automated multi-platform scanning |
| Read 50+ listings to find 5 relevant ones | AI filters to only relevant matches |
| Miss scam signs when tired or rushed | Two-layer scam detection on every listing |
| Write the same cover letter slightly tweaked | AI writes a unique letter per job |
| Forget to follow up on applications | Inbox scanner tracks every response automatically |
| Apply to 3–5 jobs per day realistically | Apply to 10–15 per day without extra effort |
| No record of what you sent | Full audit log of every application and response |
| Spend evenings job hunting | Delegate hunting — focus on skills and interviews |

---

## Security Notes

- **Never upload `.env` to GitHub.** It contains your API key and Gmail App Password. The `.gitignore` excludes it automatically.
- **Never upload `job_agent.db` to GitHub.** It contains your personal application history and email data.
- **`assets/` is gitignored.** Your CV stays off GitHub.
- The Gmail App Password only grants access to Gmail — not your full Google account. You can revoke it anytime at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

---

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
Your `.env` file is missing or in the wrong folder. Run `python setup.py` — it creates the file automatically.

**"Gmail authentication failed"**
Re-generate your App Password at myaccount.google.com/apppasswords. Make sure IMAP is enabled in Gmail settings. The password in `.env` must have no extra spaces.

**"No jobs found after scraping"**
The job site's HTML structure may have changed. You can still add jobs manually via the dashboard → Add Job Manually tab while you wait for a scraper fix.

**AI keeps returning IGNORE for everything**
Lower `SCORE_ASK_USER` in `config.py` to 35, and expand your `preferred_roles` list to include more role types.

**"Daily limit reached"**
The bot hit `MAX_AUTO_APPLIES_PER_DAY`. This resets the next calendar day. You can raise the limit in `config.py`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | Anthropic Claude (claude-sonnet-4) |
| Web Scraping | BeautifulSoup4, Requests, Playwright |
| Email Sending | Python smtplib + SMTP/TLS |
| Email Reading | Python imaplib + IMAP SSL |
| API Backend | FastAPI + Uvicorn |
| Database | SQLite via Python sqlite3 |
| Dashboard | Vanilla HTML / CSS / JavaScript |
| Browser Automation | Playwright + playwright-stealth |

---

## License

MIT — free to use, modify, and distribute.

---

## Author

**Jasper John C. Paitan**
Computer Engineering Graduate — La Salle University Ozamiz
[LinkedIn](https://www.linkedin.com/in/jasper-john-paitan-11641337b) · [Credly](https://www.credly.com/users/jasper-john-paitan)
