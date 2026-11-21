import httpx
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.connectors.base import BaseJobConnector
from app.services.skill_extractor import extract_skills_from_text

class ArbeitnowConnector(BaseJobConnector):
    """
    Connects to Arbeitnow's free public job board API (https://www.arbeitnow.com/api/job-board-api).
    Requires no API keys and provides real-time active engineering and tech jobs.
    """

    def __init__(self, rate_limit_rpm: int = 60):
        super().__init__(source_name="arbeitnow", rate_limit_rpm=rate_limit_rpm)
        self.endpoint = "https://www.arbeitnow.com/api/job-board-api"

    async def fetch_jobs(self, limit: int = 25) -> List[Dict[str, Any]]:
        normalized = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                res = await client.get(self.endpoint)
                if res.status_code != 200:
                    return []
                data = res.json().get("data", [])[:limit]

                for item in data:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "Tech Company").strip()
                    orig_url = item.get("url", "")
                    clean_url = self.normalize_url(orig_url)
                    clean_title = self.normalize_title(title)

                    raw_html = item.get("description", "")
                    soup = BeautifulSoup(raw_html, "html.parser")
                    desc_text = soup.get_text(separator=" ").strip()

                    # Extract skills
                    extracted_skills, _ = extract_skills_from_text(f"{title} {desc_text}")
                    tags = item.get("tags", [])
                    for t in tags:
                        if t and t.capitalize() not in extracted_skills:
                            extracted_skills.append(t.capitalize())

                    is_remote = bool(item.get("remote", False))
                    location = item.get("location", "Remote" if is_remote else "Global")

                    dedup_hash = self.generate_dedup_hash(clean_url, title, company)

                    normalized.append({
                        "external_id": f"arbeitnow-{clean_title[:30]}-{company[:20]}",
                        "company_name": company,
                        "title": title,
                        "normalized_title": clean_title,
                        "department": "Engineering",
                        "description": desc_text[:3500] if desc_text else title,
                        "raw_description": raw_html[:5000],
                        "responsibilities": [],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 4.0 if any(w in clean_title for w in ["senior", "lead", "staff", "principal"]) else 2.0,
                        "location": location,
                        "work_mode": "remote" if is_remote else "hybrid",
                        "employment_type": "full_time",
                        "original_url": orig_url,
                        "canonical_url": clean_url,
                        "dedup_hash": dedup_hash,
                        "status": "active",
                        "is_link_verified": True
                    })
        except Exception:
            return []
        return normalized


class RemotiveConnector(BaseJobConnector):
    """
    Connects to Remotive's free public remote jobs API (https://remotive.com/api/remote-jobs).
    Provides real-time worldwide remote software development opportunities.
    """

    def __init__(self, category: str = "software-dev", rate_limit_rpm: int = 60):
        super().__init__(source_name="remotive", rate_limit_rpm=rate_limit_rpm)
        self.endpoint = f"https://remotive.com/api/remote-jobs?category={category}&limit=25"

    async def fetch_jobs(self, limit: int = 25) -> List[Dict[str, Any]]:
        normalized = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                res = await client.get(self.endpoint)
                if res.status_code != 200:
                    return []
                jobs = res.json().get("jobs", [])[:limit]

                for item in jobs:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "Remote Tech").strip()
                    orig_url = item.get("url", "")
                    clean_url = self.normalize_url(orig_url)
                    clean_title = self.normalize_title(title)

                    raw_html = item.get("description", "")
                    soup = BeautifulSoup(raw_html, "html.parser")
                    desc_text = soup.get_text(separator=" ").strip()

                    extracted_skills, _ = extract_skills_from_text(f"{title} {desc_text}")
                    for t in item.get("tags", []):
                        if t and t.capitalize() not in extracted_skills:
                            extracted_skills.append(t.capitalize())

                    location = item.get("candidate_required_location", "Remote (Worldwide)")

                    dedup_hash = self.generate_dedup_hash(clean_url, title, company)

                    normalized.append({
                        "external_id": f"remotive-{item.get('id', clean_title[:20])}",
                        "company_name": company,
                        "title": title,
                        "normalized_title": clean_title,
                        "department": item.get("category", "Software Development"),
                        "description": desc_text[:3500] if desc_text else title,
                        "raw_description": raw_html[:5000],
                        "responsibilities": [],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 4.0 if any(w in clean_title for w in ["senior", "lead", "staff"]) else 2.0,
                        "location": location,
                        "work_mode": "remote",
                        "employment_type": "full_time",
                        "original_url": orig_url,
                        "canonical_url": clean_url,
                        "dedup_hash": dedup_hash,
                        "status": "active",
                        "is_link_verified": True
                    })
        except Exception:
            return []
        return normalized


class JobicyConnector(BaseJobConnector):
    """
    Connects to Jobicy's free public remote jobs API (https://jobicy.com/api/v2/remote-jobs).
    """

    def __init__(self, rate_limit_rpm: int = 60):
        super().__init__(source_name="jobicy", rate_limit_rpm=rate_limit_rpm)
        self.endpoint = "https://jobicy.com/api/v2/remote-jobs?count=20&industry=engineering"

    async def fetch_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        normalized = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                res = await client.get(self.endpoint)
                if res.status_code != 200:
                    return []
                jobs = res.json().get("jobs", [])[:limit]

                for item in jobs:
                    title = item.get("jobTitle", "").strip()
                    company = item.get("companyName", "Tech Employer").strip()
                    orig_url = item.get("url", "")
                    clean_url = self.normalize_url(orig_url)
                    clean_title = self.normalize_title(title)

                    raw_desc = item.get("jobDescription", "")
                    soup = BeautifulSoup(raw_desc, "html.parser")
                    desc_text = soup.get_text(separator=" ").strip()

                    extracted_skills, _ = extract_skills_from_text(f"{title} {desc_text}")
                    location = item.get("jobGeo", "USA / Remote")

                    dedup_hash = self.generate_dedup_hash(clean_url, title, company)

                    min_salary = float(item.get("annualSalaryMin")) if item.get("annualSalaryMin") else None
                    max_salary = float(item.get("annualSalaryMax")) if item.get("annualSalaryMax") else None

                    normalized.append({
                        "external_id": f"jobicy-{item.get('id', clean_title[:20])}",
                        "company_name": company,
                        "title": title,
                        "normalized_title": clean_title,
                        "department": "Engineering",
                        "description": desc_text[:3500] if desc_text else title,
                        "raw_description": raw_desc[:5000],
                        "responsibilities": [],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 4.0 if any(w in clean_title for w in ["senior", "lead", "staff"]) else 2.0,
                        "location": location,
                        "work_mode": "remote",
                        "employment_type": "full_time",
                        "min_salary": min_salary,
                        "max_salary": max_salary,
                        "currency": item.get("salaryCurrency", "USD") or "USD",
                        "original_url": orig_url,
                        "canonical_url": clean_url,
                        "dedup_hash": dedup_hash,
                        "status": "active",
                        "is_link_verified": True
                    })
        except Exception:
            return []
        return normalized
