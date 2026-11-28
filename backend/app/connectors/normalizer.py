import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

class JobDataNormalizer:
    """
    Stage 2: Normalization & Deduplication Layer.
    - Standardizes fields into strict schema columns (role_category, salary ranges, work_mode, skills).
    - Generates unique fingerprints (normalized_company + normalized_title + city).
    - Merges multiple incoming postings for the same job and retains the best apply link.
    """

    ROLE_CATEGORIES = {
        "ai_ml": ["ai", "machine learning", "deep learning", "nlp", "llm", "computer vision", "data scientist", "research engineer"],
        "backend": ["backend", "distributed systems", "server", "api", "microservices", "database", "golang", "java", "python", "node"],
        "frontend": ["frontend", "front-end", "ui", "react", "next.js", "vue", "angular", "web developer"],
        "fullstack": ["full stack", "fullstack", "full-stack", "software engineer", "developer"],
        "devops_cloud": ["devops", "sre", "site reliability", "cloud", "infrastructure", "kubernetes", "platform", "terraform", "aws", "azure"],
        "data_engineering": ["data engineer", "data platform", "etl", "spark", "pipeline", "analytics engineer", "big data"],
        "mobile": ["ios", "android", "mobile", "flutter", "react native", "swift", "kotlin"],
        "security": ["security", "cyber", "infosec", "appsec", "cryptography", "penetration"]
    }

    @classmethod
    def classify_role_category(cls, title: str, description: str = "") -> str:
        text = f"{title} {description[:300]}".lower()
        for cat, keywords in cls.ROLE_CATEGORIES.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
                return cat
        return "software_engineering"

    @classmethod
    def evaluate_link_priority(cls, url: str) -> int:
        """
        Determines the priority rank of an application link.
        Higher score = preferred direct apply link.
        """
        if not url:
            return 0
        u = url.lower()
        if "ashbyhq.com" in u and "application" in u:
            return 100
        if "boards.greenhouse.io" in u:
            return 95
        if "jobs.lever.co" in u:
            return 95
        if "smartrecruiters.com" in u:
            return 90
        if "workable.com" in u:
            return 90
        if any(d in u for d in ["careers.", "/careers", "/jobs/", "apply."]):
            return 80
        if any(b in u for b in ["remoteok.com", "himalayas.app", "weworkremotely.com", "arbeitnow.com"]):
            return 60
        return 40

    @classmethod
    def standardize_salary_inr(cls, min_salary: Optional[float], max_salary: Optional[float], currency: str = "USD") -> Tuple[Optional[float], Optional[float]]:
        """
        Normalizes salary into INR figures for standard comparison (1 USD = ~85 INR).
        """
        if not min_salary and not max_salary:
            return None, None
        curr = (currency or "USD").upper()
        rate = 85.0 if curr == "USD" else (90.0 if curr == "EUR" else 1.0)
        min_inr = round(min_salary * rate) if min_salary else None
        max_inr = round(max_salary * rate) if max_salary else None
        return min_inr, max_inr

    @classmethod
    def generate_canonical_fingerprint(cls, company_name: str, title: str, location: str = "") -> str:
        """
        Deduplication fingerprint based on normalized_company_name + normalized_title + city.
        """
        import hashlib
        comp = re.sub(r"[^a-z0-9]", "", company_name.lower().strip())
        tit = re.sub(r"[^a-z0-9]", "", title.lower().strip())
        loc = re.sub(r"[^a-z0-9]", "", (location or "remote").lower().split(",")[0].strip())
        raw_key = f"{comp}::{tit}::{loc}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def merge_job_records(cls, existing_job_dict: Dict[str, Any], incoming_job_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges duplicate incoming job data, selecting the higher-priority application link
        and combining extracted skills.
        """
        existing_priority = cls.evaluate_link_priority(existing_job_dict.get("original_url", ""))
        incoming_priority = cls.evaluate_link_priority(incoming_job_dict.get("original_url", ""))

        merged = dict(existing_job_dict)

        # Prefer the direct ATS link over a third-party job board
        if incoming_priority > existing_priority:
            merged["original_url"] = incoming_job_dict.get("original_url")
            merged["canonical_url"] = incoming_job_dict.get("canonical_url")
            merged["is_link_verified"] = incoming_job_dict.get("is_link_verified", True)

        # Union and deduplicate required skills
        existing_skills = set(existing_job_dict.get("required_skills") or [])
        incoming_skills = set(incoming_job_dict.get("required_skills") or [])
        merged["required_skills"] = list(existing_skills.union(incoming_skills))

        # Preserve longest detailed description
        if len(incoming_job_dict.get("description", "")) > len(existing_job_dict.get("description", "")):
            merged["description"] = incoming_job_dict.get("description")

        return merged
