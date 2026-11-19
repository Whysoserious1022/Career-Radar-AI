import httpx
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.connectors.base import BaseJobConnector
from app.services.skill_extractor import extract_skills_from_text

class GreenhouseConnector(BaseJobConnector):
    """
    Ingests and normalizes jobs from Greenhouse API (https://boards-api.greenhouse.io/v1/boards/{token}/jobs).
    """

    def __init__(self, board_token: str = "stripe", rate_limit_rpm: int = 60):
        super().__init__(source_name=f"greenhouse:{board_token}", rate_limit_rpm=rate_limit_rpm)
        self.board_token = board_token
        self.endpoint = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        normalized_jobs = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.endpoint)
                if res.status_code != 200:
                    return []
                data = res.json()
                raw_jobs = data.get("jobs", [])[:limit]

                for item in raw_jobs:
                    title = item.get("title", "")
                    clean_title = self.normalize_title(title)
                    orig_url = item.get("absolute_url", "")
                    canonical_url = self.normalize_url(orig_url)
                    raw_html = item.get("content", "")
                    soup = BeautifulSoup(raw_html, "html.parser")
                    text_content = soup.get_text(separator=" ").strip()

                    extracted_skills, _ = extract_skills_from_text(f"{title} {text_content}")
                    location = item.get("location", {}).get("name", "Remote")

                    normalized_jobs.append({
                        "external_id": str(item.get("id")),
                        "company_name": self.board_token.capitalize(),
                        "title": title,
                        "normalized_title": clean_title,
                        "department": item.get("departments", [{}])[0].get("name", "Engineering") if item.get("departments") else None,
                        "description": text_content[:4000],
                        "raw_description": raw_html[:6000],
                        "responsibilities": [],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 3.0 if "senior" in clean_title else 1.0,
                        "location": location,
                        "work_mode": "remote" if "remote" in location.lower() or "remote" in title.lower() else "hybrid",
                        "employment_type": "full_time",
                        "original_url": orig_url,
                        "canonical_url": canonical_url,
                        "dedup_hash": self.generate_dedup_hash(canonical_url, title, self.board_token),
                        "status": "active"
                    })
        except Exception:
            return []
        return normalized_jobs


class LeverConnector(BaseJobConnector):
    """
    Ingests and normalizes jobs from Lever API (https://api.lever.co/v0/postings/{company}).
    """

    def __init__(self, company_id: str = "netflix", rate_limit_rpm: int = 60):
        super().__init__(source_name=f"lever:{company_id}", rate_limit_rpm=rate_limit_rpm)
        self.company_id = company_id
        self.endpoint = f"https://api.lever.co/v0/postings/{company_id}?mode=json"

    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        normalized_jobs = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.endpoint)
                if res.status_code != 200:
                    return []
                raw_jobs = res.json()[:limit]

                for item in raw_jobs:
                    title = item.get("text", "")
                    clean_title = self.normalize_title(title)
                    orig_url = item.get("hostedUrl", "")
                    canonical_url = self.normalize_url(orig_url)
                    raw_desc = item.get("descriptionPlain", "")
                    categories = item.get("categories", {})
                    location = categories.get("location", "Remote")
                    work_type = item.get("workplaceType", "hybrid").lower()

                    extracted_skills, _ = extract_skills_from_text(f"{title} {raw_desc}")

                    normalized_jobs.append({
                        "external_id": str(item.get("id")),
                        "company_name": self.company_id.capitalize(),
                        "title": title,
                        "normalized_title": clean_title,
                        "department": categories.get("department", "Engineering"),
                        "description": raw_desc[:4000],
                        "raw_description": raw_desc[:6000],
                        "responsibilities": [],
                        "required_skills": extracted_skills[:10],
                        "preferred_skills": extracted_skills[10:18],
                        "min_experience_years": 4.0 if "senior" in clean_title or "lead" in clean_title else 2.0,
                        "location": location,
                        "work_mode": "remote" if "remote" in work_type or "remote" in location.lower() else "onsite",
                        "employment_type": "full_time",
                        "original_url": orig_url,
                        "canonical_url": canonical_url,
                        "dedup_hash": self.generate_dedup_hash(canonical_url, title, self.company_id),
                        "status": "active"
                    })
        except Exception:
            return []
        return normalized_jobs
