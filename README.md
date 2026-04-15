# 🤖 Job AI Agent — Autonomous Job Hunting on Autopilot

> **Stop spending 3 hours a day job hunting. Let the bot do it while you sleep.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Powered by Claude AI](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange)](https://anthropic.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

---

## 😩 The Problem This Solves

Every day, job seekers in the Philippines spend **2–4 hours**:

- Checking 3+ job platforms manually
- Reading through 50+ listings to find 5 relevant ones
- Getting tricked by scam listings that waste their time
- Writing the same cover letter over and over with small tweaks
- Forgetting to follow up on applications
- Losing track of what they applied to and when

**That's a part-time job just to find a job.**

---

## ✅ What This Bot Does For You

This is a **fully automated job hunting assistant** that runs on your computer. You set it up once, and it handles the entire job search pipeline without you lifting a finger.

| What you used to do manually | What the bot does automatically |
|---|---|
| Check Indeed, Jobstreet, OnlineJobs daily | Scrapes all 3 platforms simultaneously |
| Read 50+ listings to find 5 good ones | AI filters and scores every listing 0–100 |
| Spot scam listings manually | Two-layer scam detection catches red flags instantly |
| Write a cover letter for every application | AI writes a unique, personalized letter per job |
| Send applications one by one | Auto-sends email applications with your CV attached |
| Check inbox manually for replies | Scans Gmail and classifies every response automatically |
| Forget what you applied to | Full audit log of every application, response, and outcome |

---

## 📈 Results

- **Saves 2–4 hours per day** — the bot completes in 10 minutes what took hours manually
- **Applies to 10–15 jobs per day** without extra effort from you (vs. 3–5 manually)
- **Catches scam listings** — two-layer detection flags pay-to-apply schemes, MLM traps, and fake listings before you waste time on them
- **Personalized cover letters** for every single application — not copy-paste templates
- **Never misses a follow-up** — inbox scanner tracks every reply automatically

---

## 💼 Who This Is For

This tool is ideal for:

- **Job seekers** applying to multiple remote/online roles and drowning in the process
- **Virtual assistants** who want to manage job applications for their clients at scale
- **Freelancers** who need to keep a pipeline of opportunities without spending hours sourcing them
- **Anyone tired of Philippine online job scams** eating up their time

> **You don't need to be technical to use this.** Setup takes about 15 minutes following the step-by-step guide below.

---

## 🎬 Demo

▶️ **[Watch it in action — full demo video coming soon]**

*(Video will show: scraping → AI scoring → cover letter generation → auto-apply → inbox scan → dashboard overview)*

---

## ⚙️ How It Works — Plain English

```
Every time you run the bot:

1. SCRAPES  →  Finds new job listings on Indeed PH, Jobstreet PH, OnlineJobs.ph
2. FILTERS  →  AI reads every listing and gives it a score from 0–100
3. DETECTS  →  Scam checker flags suspicious listings before any action
4. DECIDES  →
              Score 78–100 → Bot sends the application automatically
              Score 50–77  → Bot asks YOU to approve first
              Score below 50 → Skipped (not relevant)
5. APPLIES  →  Sends personalized email with your CV attached
6. MONITORS →  Scans your inbox for replies, classifies as interview/assessment/rejection
7. LOGS     →  Everything saved in a dashboard you can review anytime
```

---

## 🖥️ Web Dashboard

The bot includes a full browser-based dashboard at `http://localhost:8000`:

| Tab | What you see |
|---|---|
| **Dashboard** | Stats: jobs found, applied, scams caught, interviews received |
| **Job Listings** | All scraped jobs with AI scores and decisions |
| **Auto-Apply Queue** | Jobs that need your approval before sending |
| **Inbox Responses** | Your email replies, auto-classified by type |
| **Worker Agent** | Type any task in plain English — AI completes it |
| **Add Job Manually** | Paste a job post you found — AI evaluates it instantly |

### Worker Agent — Your Digital Clone

Type a task in plain English and the AI handles it for you:

```
"Write a follow-up email to CargoBoss — I applied 5 days ago with no response"
"Summarize this job post and tell me if I'm a good fit: [paste text]"
"Draft a reply to this interview invitation: [paste email]"
"List the top 5 interview questions I should prepare for a VA role"
```

---

## 🛡️ Scam Detection

Two layers protect you from wasting time on fake listings:

**Layer 1 — Instant keyword check (no API cost)**
Catches: "registration fee", "training fee", "earn ₱500 daily", "Telegram only", "no experience ₱50/hr", gmail.com hiring addresses, MLM language

**Layer 2 — AI deep analysis**
Claude reads the full job post and flags vague descriptions, inconsistent salaries, missing company details, and unusual requirements — with a plain-English explanation visible in your dashboard.

---

## 🚀 Quick Setup (15 Minutes)

### What you need before starting:
- A computer with Python installed ([download here](https://python.org/downloads) if needed)
- A Gmail account
- An Anthropic API key ([get one here](https://console.anthropic.com) — pay-as-you-go, ~₱50–₱250/month for daily use)
- Your CV in PDF format

### Step 1 — Download and install

```bash
git clone https://github.com/jasper-0918/job-bot.git
cd job-bot
python setup.py
```

`setup.py` installs everything automatically.

### Step 2 — Fill in your credentials

Open `.env` and add:

```
ANTHROPIC_API_KEY=your_key_here
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
CV_PATH=./assets/YourName_CV.pdf
```

> **Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → Create one for "job-agent". This is different from your regular Gmail password.

### Step 3 — Add your CV

Copy your CV PDF into the `assets/` folder.

### Step 4 — Customize your profile

Open `config.py` and update your name, skills, preferred roles, and salary requirements.

### Step 5 — Run

```bash
python main.py server
```

Open `http://localhost:8000` in your browser. You're live.

---

## 📋 Daily Workflow

**Morning (5 minutes):**
```bash
python main.py run
```
This scrapes, evaluates, applies, and scans your inbox all at once.

Then open the dashboard to approve any jobs flagged for your review.

**When you find a job yourself** (Facebook group, referral, etc.):
→ Dashboard → Add Job Manually → paste the post → AI scores it → apply in one click

---

## ⚠️ Honest Limitations

- **API cost** — Claude AI charges per job evaluation. Daily use costs roughly ₱50–₱250/month. See the free version below if cost is a concern.
- **Email-only auto-apply** — Only works when a job has a direct email address. Jobs on Workday, Greenhouse, or company portals require manual application.
- **Scraping can break** — Job sites occasionally update their layout. When this happens, use "Add Job Manually" while waiting for a fix.
- **Not 100% autonomous by design** — Ambiguous jobs always need your approval. This is intentional.

> **💡 No budget for the API?** Check out [job-ai-agent-free](https://github.com/jasper-0918/job-ai-agent-free) — the same bot rebuilt entirely with free tools.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | Anthropic Claude |
| Web Scraping | BeautifulSoup4, Requests, Playwright |
| Email | Python smtplib (send) + imaplib (read) |
| API Backend | FastAPI + Uvicorn |
| Database | SQLite |
| Dashboard | HTML / CSS / JavaScript |

---

## 📬 Want This Built for Your Business?

If you have **repetitive tasks or workflows that need automation**, I can build a custom solution for you.

I specialize in Python automation for businesses — job pipelines, document processing, inbox management, and more.

👉 **[Connect on LinkedIn](https://www.linkedin.com/in/jasper-john-paitan-11641337b)**
📧 **jasperjohn.paitan@lsu.edu.ph**
🏅 **[View my certifications on Credly](https://www.credly.com/users/jasper-john-paitan)**

---

## 📄 License

MIT — free to use, modify, and distribute.
