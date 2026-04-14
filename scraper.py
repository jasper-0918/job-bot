# agents/scraper.py
import time
import logging
import re
from urllib.parse import quote_plus

log = logging.getLogger("scraper")

# ── Try to import Playwright (optional — falls back to requests) ───────────
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    log.warning("Playwright not installed. Using requests-based scraper.")

try:
    from playwright_stealth import stealth_sync
    STEALTH_OK = True
except ImportError:
    STEALTH_OK = False

try:
    from fake_useragent import UserAgent
    UA = UserAgent()
except Exception:
    UA = None

import requests
from bs4 import BeautifulSoup
from config import SEARCH_KEYWORDS, DELAY_BETWEEN_SCRAPES_SEC


def _random_ua() -> str:
    if UA:
        try:
            return UA.random
        except Exception:
            pass
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def _keywords_matched(text: str) -> list:
    text_l = text.lower()
    return [kw for kw in SEARCH_KEYWORDS if kw.lower() in text_l]


# ── Requests-based scrapers (no JS required) ──────────────────────────────

def scrape_indeed_requests(keyword: str) -> list:
    jobs = []
    url = f"https://ph.indeed.com/jobs?q={quote_plus(keyword)}&remotejob=032b3046-06a2-4a6e-9930-bf5c748afa2b"
    headers = {"User-Agent": _random_ua(), "Accept-Language": "en-US,en;q=0.9"}
    try:
        time.sleep(DELAY_BETWEEN_SCRAPES_SEC)
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.job_seen_beacon, [class*='jobsearch-SerpJobCard']")
        for card in cards[:10]:
            try:
                title_el = card.select_one("h2.jobTitle a, a[data-jk]")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                jk = title_el.get("data-jk", "")
                job_url = f"https://ph.indeed.com/viewjob?jk={jk}" if jk else ""
                company_el = card.select_one("[class*='companyName'], [class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                desc_el = card.select_one("[class*='summary'], [class*='snippet']")
                desc = desc_el.get_text(strip=True) if desc_el else ""
                apply_email = _extract_email(desc)
                jobs.append({
                    "title": title, "company": company,
                    "platform": "Indeed PH", "url": job_url,
                    "apply_email": apply_email, "description": desc,
                    "salary_info": "", "keywords_matched": _keywords_matched(title + desc),
                })
            except Exception:
                continue
    except Exception as e:
        log.warning(f"Indeed scrape error: {e}")
    return jobs


def scrape_jobstreet_requests(keyword: str) -> list:
    jobs = []
    url = f"https://ph.jobstreet.com/jobs?q={quote_plus(keyword)}&location=Philippines&worktype=remote"
    headers = {"User-Agent": _random_ua()}
    try:
        time.sleep(DELAY_BETWEEN_SCRAPES_SEC)
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article[data-job-id], [data-automation='job-card']")
        for card in cards[:10]:
            try:
                title_el = card.select_one("[data-automation='job-card-title'] a, h3 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = href if href.startswith("http") else "https://ph.jobstreet.com" + href
                company_el = card.select_one("[data-automation='job-card-company'], [class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                jobs.append({
                    "title": title, "company": company,
                    "platform": "Jobstreet PH", "url": job_url,
                    "apply_email": None, "description": "",
                    "salary_info": "", "keywords_matched": _keywords_matched(title),
                })
            except Exception:
                continue
    except Exception as e:
        log.warning(f"Jobstreet scrape error: {e}")
    return jobs


def scrape_onlinejobs_requests(keyword: str) -> list:
    jobs = []
    url = f"https://www.onlinejobs.ph/jobseekers/jobsearch?q={quote_plus(keyword)}"
    headers = {"User-Agent": _random_ua()}
    try:
        time.sleep(DELAY_BETWEEN_SCRAPES_SEC)
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".job-post, article.post, [class*='jobpost']")
        for card in cards[:10]:
            try:
                title_el = card.select_one("h2 a, h3 a, .job-title a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = href if href.startswith("http") else "https://www.onlinejobs.ph" + href
                company_el = card.select_one("[class*='company'], [class*='employer']")
                company = company_el.get_text(strip=True) if company_el else "Private Employer"
                desc_el = card.select_one("[class*='description'], [class*='summary']")
                desc = desc_el.get_text(strip=True) if desc_el else ""
                apply_email = _extract_email(desc)
                jobs.append({
                    "title": title, "company": company,
                    "platform": "OnlineJobs.ph", "url": job_url,
                    "apply_email": apply_email, "description": desc,
                    "salary_info": "", "keywords_matched": _keywords_matched(title + desc),
                })
            except Exception:
                continue
    except Exception as e:
        log.warning(f"OnlineJobs scrape error: {e}")
    return jobs


# ── Playwright scraper (more powerful, handles JS sites) ──────────────────

def scrape_with_playwright(platform: str, keyword: str) -> list:
    """Stealth Playwright scraper — use for JS-heavy sites."""
    if not PLAYWRIGHT_OK:
        return []

    jobs = []
    urls = {
        "onlinejobs": f"https://www.onlinejobs.ph/jobseekers/jobsearch?q={quote_plus(keyword)}",
        "jobstreet":  f"https://ph.jobstreet.com/jobs?q={quote_plus(keyword)}&worktype=remote",
    }
    url = urls.get(platform)
    if not url:
        return []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=_random_ua(),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = context.new_page()
            if STEALTH_OK:
                stealth_sync(page)

            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)

            # Extract job data via page evaluation
            raw_jobs = page.evaluate("""
                () => {
                    const results = [];
                    const cards = document.querySelectorAll(
                        'article[data-job-id], .job-post, [class*="jobpost"], [data-automation="job-card"]'
                    );
                    cards.forEach(card => {
                        const titleEl = card.querySelector('h2 a, h3 a, [data-automation="job-card-title"] a');
                        const companyEl = card.querySelector('[class*="company"], [class*="employer"]');
                        const descEl = card.querySelector('[class*="description"], [class*="summary"]');
                        if (titleEl) {
                            results.push({
                                title: titleEl.innerText.trim(),
                                url: titleEl.href || '',
                                company: companyEl ? companyEl.innerText.trim() : 'Unknown',
                                description: descEl ? descEl.innerText.trim() : ''
                            });
                        }
                    });
                    return results.slice(0, 15);
                }
            """)

            for j in raw_jobs:
                apply_email = _extract_email(j.get("description", ""))
                jobs.append({
                    "title": j.get("title", ""),
                    "company": j.get("company", "Unknown"),
                    "platform": platform.capitalize(),
                    "url": j.get("url", ""),
                    "apply_email": apply_email,
                    "description": j.get("description", ""),
                    "salary_info": "",
                    "keywords_matched": _keywords_matched(j.get("title", "") + j.get("description", "")),
                })

            browser.close()
    except Exception as e:
        log.error(f"Playwright scrape error ({platform}): {e}")

    return jobs


# ── Main scrape function ───────────────────────────────────────────────────

def scrape_all_platforms(use_playwright: bool = False) -> list:
    """
    Scrape all platforms for all keywords.
    Returns deduplicated list of job dicts.
    """
    all_jobs = []
    seen = set()

    log.info(f"Scraping {len(SEARCH_KEYWORDS)} keywords across 3 platforms...")

    for keyword in SEARCH_KEYWORDS:
        log.info(f"  Searching: '{keyword}'")

        if use_playwright and PLAYWRIGHT_OK:
            batch = scrape_with_playwright("onlinejobs", keyword)
            batch += scrape_with_playwright("jobstreet", keyword)
        else:
            batch = (
                scrape_indeed_requests(keyword) +
                scrape_jobstreet_requests(keyword) +
                scrape_onlinejobs_requests(keyword)
            )

        for job in batch:
            uid = f"{job['title'].lower()}|{job['company'].lower()}"
            if uid not in seen and job["title"].strip():
                seen.add(uid)
                all_jobs.append(job)

    log.info(f"Scrape complete. {len(all_jobs)} unique jobs found.")
    return all_jobs
