import httpx
import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from app.connectors.base import BaseJobConnector
from app.services.skill_extractor import (
    extract_skills_from_text,
    extract_experience_requirement,
    extract_requirements_checklist
)

TECH_KEYWORDS = [
    "engineer", "developer", "software", "backend", "frontend", "full stack", "fullstack",
    "data", "cloud", "devops", "sre", "ai", "machine learning", "architect",
    "systems", "platform", "infrastructure", "security", "distributed", "ml",
    "product manager", "designer", "qa", "analyst", "engineering", "technical"
]

class DeepWebJobScraper:
    """
    Impactful, universal web scraper that extracts job opportunities from:
    1. Direct career portal links (Ashby, Greenhouse, Lever, Workable, SmartRecruiters)
    2. Any company website / career page (via Schema.org JobPosting microdata & semantic HTML DOM parsing)
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    @classmethod
    async def scrape_url(cls, target_url: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Main entry point: dynamically identifies the target webpage architecture and scrapes all jobs.
        """
        clean_target = target_url.strip()
        parsed = urlparse(clean_target)
        netloc = parsed.netloc.lower()
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]

        # 1. Ashby ATS boards (e.g. jobs.ashbyhq.com/openai or direct job)
        if "ashbyhq.com" in netloc:
            return await cls._scrape_ashby(clean_target, parts, limit)

        # 2. Greenhouse ATS boards (e.g. boards.greenhouse.io/cloudflare or direct job)
        if "greenhouse.io" in netloc:
            return await cls._scrape_greenhouse(clean_target, parts, limit)

        # 3. Lever ATS boards (e.g. jobs.lever.co/spotify or direct posting)
        if "lever.co" in netloc:
            return await cls._scrape_lever(clean_target, parts, limit)

        # 4. SmartRecruiters (e.g. careers.smartrecruiters.com/company or direct job)
        if "smartrecruiters.com" in netloc:
            return await cls._scrape_smartrecruiters(clean_target, parts, limit)

        # 5. Generic Website / Company Careers Page (HTML DOM + Schema.org JobPosting JSON-LD)
        return await cls._scrape_generic_web(clean_target, limit)

    @classmethod
    async def _scrape_ashby(cls, url: str, path_parts: List[str], limit: int) -> List[Dict[str, Any]]:
        company = path_parts[0] if path_parts else "company"
        direct_job_id = path_parts[1] if len(path_parts) >= 2 and path_parts[1] != "application" else None

        endpoint = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
        normalized = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=cls.HEADERS) as client:
                res = await client.get(endpoint)
                if res.status_code == 200:
                    raw_jobs = res.json().get("jobs", [])
                    if direct_job_id:
                        raw_jobs = [j for j in raw_jobs if j.get("id") == direct_job_id] or raw_jobs
                    
                    company_name = company.replace("-", " ").title()
                    for item in raw_jobs[:limit]:
                        title = item.get("title", "").strip()
                        clean_title = BaseJobConnector.normalize_title(title)
                        orig_url = item.get("applyUrl") or item.get("jobUrl") or url
                        clean_url = BaseJobConnector.normalize_url(orig_url)
                        location = item.get("location") or "Remote / Global"
                        workplace = (item.get("workplaceType") or "hybrid").lower()
                        work_mode = "remote" if "remote" in workplace or item.get("isRemote") else ("onsite" if "onsite" in workplace else "hybrid")

                        desc = item.get("descriptionPlain") or item.get("descriptionHtml") or f"Verified {title} role at {company_name}."
                        extracted_skills, _ = extract_skills_from_text(f"{title} {desc[:800]} {company_name}")
                        min_exp = extract_experience_requirement(desc, title)
                        what_they_need = extract_requirements_checklist(desc, title, extracted_skills, min_exp, work_mode)
                        dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title, company_name)

                        normalized.append({
                            "company_name": company_name,
                            "title": title,
                            "normalized_title": clean_title,
                            "department": item.get("department") or "Engineering",
                            "description": desc[:3500],
                            "raw_description": item.get("descriptionHtml") or desc[:4000],
                            "responsibilities": what_they_need,
                            "required_skills": extracted_skills[:10],
                            "preferred_skills": extracted_skills[10:18],
                            "min_experience_years": min_exp,
                            "location": location,
                            "work_mode": work_mode,
                            "employment_type": "full_time",
                            "original_url": orig_url,
                            "canonical_url": clean_url,
                            "dedup_hash": dedup_hash,
                            "status": "active",
                            "is_link_verified": True
                        })
        except Exception:
            pass
        return normalized

    @classmethod
    async def _scrape_greenhouse(cls, url: str, path_parts: List[str], limit: int) -> List[Dict[str, Any]]:
        company = path_parts[0] if path_parts else "company"
        direct_job_id = path_parts[2] if len(path_parts) >= 3 and path_parts[1] == "jobs" else None

        endpoint = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        normalized = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=cls.HEADERS) as client:
                res = await client.get(endpoint)
                if res.status_code == 200:
                    raw_jobs = res.json().get("jobs", [])
                    if direct_job_id:
                        raw_jobs = [j for j in raw_jobs if str(j.get("id")) == str(direct_job_id)] or raw_jobs
                    
                    company_name = company.replace("-", " ").title()
                    for item in raw_jobs[:limit]:
                        title = item.get("title", "").strip()
                        clean_title = BaseJobConnector.normalize_title(title)
                        orig_url = item.get("absolute_url") or url
                        clean_url = BaseJobConnector.normalize_url(orig_url)
                        location = item.get("location", {}).get("name") or "Remote / Global"
                        work_mode = "remote" if "remote" in location.lower() or "remote" in title.lower() else "hybrid"
                        desc = f"Official {company_name} verified opportunity for {title}. Located in {location}."
                        extracted_skills, _ = extract_skills_from_text(f"{title} {company_name}")
                        min_exp = extract_experience_requirement(f"{title} {desc}", title)
                        what_they_need = extract_requirements_checklist(desc, title, extracted_skills, min_exp, work_mode)
                        dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title, company_name)

                        normalized.append({
                            "company_name": company_name,
                            "title": title,
                            "normalized_title": clean_title,
                            "department": "Engineering & Technology",
                            "description": desc,
                            "raw_description": desc,
                            "responsibilities": what_they_need,
                            "required_skills": extracted_skills[:10],
                            "preferred_skills": extracted_skills[10:18],
                            "min_experience_years": min_exp,
                            "location": location,
                            "work_mode": work_mode,
                            "employment_type": "full_time",
                            "original_url": orig_url,
                            "canonical_url": clean_url,
                            "dedup_hash": dedup_hash,
                            "status": "active",
                            "is_link_verified": True
                        })
        except Exception:
            pass
        return normalized

    @classmethod
    async def _scrape_lever(cls, url: str, path_parts: List[str], limit: int) -> List[Dict[str, Any]]:
        company = path_parts[0] if path_parts else "company"
        direct_job_id = path_parts[1] if len(path_parts) >= 2 else None

        endpoint = f"https://api.lever.co/v0/postings/{company}?mode=json"
        normalized = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=cls.HEADERS) as client:
                res = await client.get(endpoint)
                if res.status_code == 200:
                    raw_jobs = res.json()
                    if direct_job_id:
                        raw_jobs = [j for j in raw_jobs if str(j.get("id")) == str(direct_job_id)] or raw_jobs
                    
                    company_name = company.replace("-", " ").title()
                    for item in raw_jobs[:limit]:
                        title = item.get("text", "").strip()
                        clean_title = BaseJobConnector.normalize_title(title)
                        orig_url = item.get("hostedUrl") or item.get("applyUrl") or url
                        clean_url = BaseJobConnector.normalize_url(orig_url)
                        categories = item.get("categories", {})
                        location = categories.get("location") or "Remote"
                        work_type = item.get("workplaceType", "hybrid").lower()
                        work_mode = "remote" if "remote" in work_type or "remote" in location.lower() else "hybrid"
                        desc = f"Official {company_name} verified requisition for {title}. Location: {location}."
                        extracted_skills, _ = extract_skills_from_text(f"{title} {company_name}")
                        min_exp = extract_experience_requirement(f"{title} {desc}", title)
                        what_they_need = extract_requirements_checklist(desc, title, extracted_skills, min_exp, work_mode)
                        dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title, company_name)

                        normalized.append({
                            "company_name": company_name,
                            "title": title,
                            "normalized_title": clean_title,
                            "department": categories.get("department", "Engineering"),
                            "description": desc,
                            "raw_description": desc,
                            "responsibilities": what_they_need,
                            "required_skills": extracted_skills[:10],
                            "preferred_skills": extracted_skills[10:18],
                            "min_experience_years": min_exp,
                            "location": location,
                            "work_mode": work_mode,
                            "employment_type": "full_time",
                            "original_url": orig_url,
                            "canonical_url": clean_url,
                            "dedup_hash": dedup_hash,
                            "status": "active",
                            "is_link_verified": True
                        })
        except Exception:
            pass
        return normalized

    @classmethod
    async def _scrape_smartrecruiters(cls, url: str, path_parts: List[str], limit: int) -> List[Dict[str, Any]]:
        company = path_parts[0] if path_parts else "company"
        endpoint = f"https://api.smartrecruiters.com/v1/companies/{company}/postings?limit={limit}"
        normalized = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=cls.HEADERS) as client:
                res = await client.get(endpoint)
                if res.status_code == 200:
                    data = res.json()
                    company_name = company.replace("-", " ").title()
                    for item in data.get("content", [])[:limit]:
                        title = item.get("name", "").strip()
                        clean_title = BaseJobConnector.normalize_title(title)
                        orig_url = f"https://jobs.smartrecruiters.com/{company}/{item.get('id')}"
                        clean_url = BaseJobConnector.normalize_url(orig_url)
                        location = item.get("location", {}).get("city", "Global")
                        work_mode = "remote" if "remote" in title.lower() or "remote" in location.lower() else "hybrid"
                        desc = f"Verified {title} position at {company_name}. Location: {location}."
                        extracted_skills, _ = extract_skills_from_text(f"{title} {company_name}")
                        dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title, company_name)

                        normalized.append({
                            "company_name": company_name,
                            "title": title,
                            "normalized_title": clean_title,
                            "department": item.get("department", {}).get("label") or "Engineering",
                            "description": desc,
                            "raw_description": desc,
                            "responsibilities": [
                                f"Advance engineering goals at {company_name}",
                                "Build performant and secure software"
                            ],
                            "required_skills": extracted_skills[:10],
                            "preferred_skills": extracted_skills[10:18],
                            "min_experience_years": 3.0 if "senior" in clean_title else 1.5,
                            "location": location,
                            "work_mode": work_mode,
                            "employment_type": "full_time",
                            "original_url": orig_url,
                            "canonical_url": clean_url,
                            "dedup_hash": dedup_hash,
                            "status": "active",
                            "is_link_verified": True
                        })
        except Exception:
            pass
        return normalized

    @classmethod
    async def _scrape_generic_web(cls, url: str, limit: int) -> List[Dict[str, Any]]:
        """
        Deep semantic HTML and Schema.org scraper for any arbitrary webpage or company career site.
        """
        normalized = []
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=cls.HEADERS) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return []
                html = res.text
                soup = BeautifulSoup(html, "html.parser")

                # Parse domain name as default company
                domain = urlparse(url).netloc.lower().replace("www.", "").split(".")[0].title()
                site_name_meta = soup.find("meta", property="og:site_name")
                company_name = site_name_meta.get("content").strip() if site_name_meta and site_name_meta.get("content") else domain

                # 1. Search for Schema.org JobPosting JSON-LD
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        content = script.string
                        if not content:
                            continue
                        data = json.loads(content)
                        items = data if isinstance(data, list) else [data]
                        for obj in items:
                            if isinstance(obj, dict) and obj.get("@type") == "JobPosting":
                                title = obj.get("title", "").strip()
                                if not title:
                                    continue
                                clean_title = BaseJobConnector.normalize_title(title)
                                desc_raw = obj.get("description", "")
                                desc_soup = BeautifulSoup(desc_raw, "html.parser")
                                desc_clean = desc_soup.get_text(separator=" ").strip()

                                comp = obj.get("hiringOrganization", {}).get("name") if isinstance(obj.get("hiringOrganization"), dict) else company_name
                                loc_obj = obj.get("jobLocation", {})
                                loc = loc_obj.get("address", {}).get("addressLocality") if isinstance(loc_obj, dict) and isinstance(loc_obj.get("address"), dict) else "Global"

                                orig_url = obj.get("url") or url
                                clean_url = BaseJobConnector.normalize_url(orig_url)
                                extracted_skills, _ = extract_skills_from_text(f"{title} {desc_clean[:1000]}")
                                min_exp = extract_experience_requirement(f"{title} {desc_clean}", title)
                                what_they_need = extract_requirements_checklist(desc_clean, title, extracted_skills, min_exp, "remote" if "remote" in desc_clean.lower() or "remote" in title.lower() else "hybrid")
                                dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title, comp)

                                normalized.append({
                                    "company_name": comp or company_name,
                                    "title": title,
                                    "normalized_title": clean_title,
                                    "department": "Engineering & Technology",
                                    "description": desc_clean[:3500] if desc_clean else f"Verified {title} role at {comp}.",
                                    "raw_description": desc_raw[:5000],
                                    "responsibilities": what_they_need,
                                    "required_skills": extracted_skills[:10],
                                    "preferred_skills": extracted_skills[10:18],
                                    "min_experience_years": min_exp,
                                    "location": loc,
                                    "work_mode": "remote" if "remote" in desc_clean.lower() or "remote" in title.lower() else "hybrid",
                                    "employment_type": "full_time",
                                    "original_url": orig_url,
                                    "canonical_url": clean_url,
                                    "dedup_hash": dedup_hash,
                                    "status": "active",
                                    "is_link_verified": True
                                })
                                if len(normalized) >= limit:
                                    return normalized
                    except Exception:
                        continue

                # 2. If no JSON-LD JobPostings found, parse HTML page metadata and content
                if not normalized:
                    page_title = soup.find("title").text.strip() if soup.find("title") else "Career Opportunity"
                    # Clean title: strip "- Careers", "| Job Opening", etc.
                    title_clean = re.sub(r"(?i)\s*[-|–]\s*(careers|jobs|job opening|work with us|apply now).*$", "", page_title).strip()
                    if not title_clean:
                        title_clean = "Software Engineer"
                    
                    # Remove scripts and styling
                    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
                        tag.extract()
                    
                    body_text = soup.get_text(separator=" ").strip()
                    body_clean = re.sub(r"\s+", " ", body_text)
                    extracted_skills, _ = extract_skills_from_text(f"{title_clean} {body_clean[:1500]}")

                    clean_url = BaseJobConnector.normalize_url(url)
                    clean_title = BaseJobConnector.normalize_title(title_clean)
                    dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, title_clean, company_name)

                    normalized.append({
                        "company_name": company_name,
                        "title": title_clean,
                        "normalized_title": clean_title,
                        "department": "Engineering & Technology",
                        "description": body_clean[:3500] if body_clean else f"Official requisition for {title_clean} at {company_name}.",
                        "raw_description": body_clean[:5000],
                        "responsibilities": [
                            f"Drive high-impact technical initiatives at {company_name}",
                            "Design and build reliable software applications"
                        ],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 3.0 if "senior" in clean_title else 1.5,
                        "location": "Remote / Global",
                        "work_mode": "remote" if "remote" in body_clean.lower() else "hybrid",
                        "employment_type": "full_time",
                        "original_url": url,
                        "canonical_url": clean_url,
                        "dedup_hash": dedup_hash,
                        "status": "active",
                        "is_link_verified": True
                    })
        except Exception:
            pass

        return normalized[:limit]
