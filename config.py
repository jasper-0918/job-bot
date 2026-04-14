# config.py
# ─────────────────────────────────────────────────────────
#  YOUR PERSONAL PROFILE — Edit everything in USER_PROFILE
#  The bot uses this to evaluate jobs and write cover letters
# ─────────────────────────────────────────────────────────

USER_PROFILE = {
    # ── Personal Info ──────────────────────────────────────
    "name": "Jasper John C. Paitan",
    "email": "jasperjohn.paitan@lsu.edu.ph",   # ← CHANGE to your email
    "phone": "+63 949 407 9802",
    "location": "Ozamiz City, Misamis Occidental, Philippines",
    "linkedin": "linkedin.com/in/jasper-john-paitan-11641337b",
    "github": "",   # ← Add your GitHub URL here when ready

    # ── Education & Background ────────────────────────────
    "education": "Bachelor of Science in Computer Engineering, La Salle University – Ozamiz",
    "experience": [
        "Software Development Intern at Benpos Systems (Feb–Apr 2026): "
        "maintained system software, resolved defects, coordinated client deployments.",
    ],
    "projects": [
        "Automatic Plastic Bottle Segregation System — TensorFlow + Edge Impulse real-time classifier (Thesis)",
        "AI Document Organizer — Python + HuggingFace Transformers + OpenCV",
        "JobBot — Automated job application scraper and email manager",
    ],
    "certifications": [
        "Google Cloud Cybersecurity Certificate (2026)",
        "Cisco Junior Cybersecurity Analyst (2026)",
        "Machining NC II – TESDA",
    ],

    # ── Skills (used for job matching) ────────────────────
    "skills": [
        "python", "automation", "cybersecurity", "machine learning",
        "tensorflow", "edge impulse", "opencv", "sql", "c", "c++",
        "javascript", "data analysis", "git", "linux", "virtual assistant",
        "technical support", "data entry", "ai", "nlp", "fastapi",
    ],

    # ── Job Preferences ───────────────────────────────────
    "preferred_roles": [
        "virtual assistant", "va", "python developer", "automation",
        "technical support", "data analyst", "cybersecurity analyst",
        "it support", "ai automation", "customer service representative",
        "csr", "non voice", "data entry", "software developer",
    ],
    "remote_only": True,
    "min_hourly_usd": 3,       # minimum $3/hr — change as you see fit
    "min_monthly_php": 15000,  # minimum ₱15,000/month

    # ── Writing Style (how your cover letters will sound) ─
    "tone": "professional but personable, confident without being arrogant",
    "writing_style": "concise, direct, highlights technical skills and real project experience",
}

# ─────────────────────────────────────────────────────────
#  DECISION THRESHOLDS — tweak these to change sensitivity
# ─────────────────────────────────────────────────────────
SCORE_AUTO_APPLY  = 78   # score >= this → bot applies automatically
SCORE_ASK_USER    = 50   # score >= this → bot asks you first
SCORE_IGNORE      = 0    # score < ASK_USER → silently ignored

# ─────────────────────────────────────────────────────────
#  SAFETY LIMITS — prevents bans and spam
# ─────────────────────────────────────────────────────────
MAX_AUTO_APPLIES_PER_DAY = 15   # hard cap on auto applications per day
DELAY_BETWEEN_APPLIES_SEC = 45  # seconds to wait between email sends
DELAY_BETWEEN_SCRAPES_SEC = 3   # politeness delay between page requests

# ─────────────────────────────────────────────────────────
#  SCAM DETECTION — red flag keywords
# ─────────────────────────────────────────────────────────
SCAM_KEYWORDS = [
    "pay to apply", "registration fee", "training fee", "deposit",
    "send money", "wire transfer", "western union",
    "telegram only", "whatsapp only", "no company", "no website",
    "earn $500 daily", "earn $1000 daily", "easy $",
    "get rich", "work from anywhere unlimited",
    "mlm", "network marketing", "downline",
    "bitcoin", "crypto investment",
]

SCAM_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"
    # Legitimate companies use their own domain for hiring emails
    # e.g. hiring@cargoboss.ph is OK, cargobosshiring@gmail.com is suspicious
]

# ─────────────────────────────────────────────────────────
#  JOB SEARCH KEYWORDS — what to search for
# ─────────────────────────────────────────────────────────
SEARCH_KEYWORDS = [
    "virtual assistant fresh graduate",
    "VA no experience",
    "non voice CSR",
    "customer service representative WFH",
    "technical support work from home",
    "python developer entry level",
    "data entry no experience",
    "AI automation assistant",
    "IT support fresh graduate",
    "cybersecurity analyst trainee",
]
