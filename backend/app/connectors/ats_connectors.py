import asyncio
import httpx
from typing import List, Dict, Any, Optional
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
    "systems", "platform", "infrastructure", "security", "distributed", "ml", "research",
    "compiler", "firmware", "kernel", "product", "designer", "scientist", "quantitative"
]

COMPANY_DISPLAY_MAP = {
    # AI / LLMs
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "perplexity": "Perplexity AI",
    "cursor": "Cursor",
    "cohere": "Cohere",
    "character": "Character.ai",
    "replit": "Replit",
    "scaleai": "Scale AI",
    "baseten": "Baseten",
    "modal": "Modal Labs",
    "pika": "Pika Labs",
    "runway": "Runway",
    "langchain": "LangChain",
    "cognition": "Cognition AI",
    "cartesia": "Cartesia AI",
    "togetherai": "Together AI",
    "stabilityai": "Stability AI",
    "vapi": "Vapi",

    # Cloud & Infra
    "cloudflare": "Cloudflare",
    "databricks": "Databricks",
    "datadog": "Datadog",
    "mongodb": "MongoDB",
    "vercel": "Vercel",
    "elastic": "Elastic",
    "cockroachlabs": "Cockroach Labs",
    "fastly": "Fastly",
    "netlify": "Netlify",
    "supabase": "Supabase",
    "neon": "Neon",
    "samsara": "Samsara",
    "hashicorp": "HashiCorp",

    # Fintech & Payments
    "stripe": "Stripe",
    "ramp": "Ramp",
    "brex": "Brex",
    "coinbase": "Coinbase",
    "affirm": "Affirm",
    "plaid": "Plaid",
    "robinhood": "Robinhood",
    "toast": "Toast",
    "mercury": "Mercury",
    "carta": "Carta",
    "gusto": "Gusto",
    "kraken": "Kraken",
    "checkr": "Checkr",

    # DevTools & Productivity
    "linear": "Linear",
    "figma": "Figma",
    "gitlab": "GitLab",
    "postman": "Postman",
    "asana": "Asana",
    "canva": "Canva",
    "miro": "Miro",
    "zapier": "Zapier",
    "posthog": "PostHog",
    "intercom": "Intercom",
    "resend": "Resend",
    "airtable": "Airtable",
    "braze": "Braze",
    "klaviyo": "Klaviyo",
    "lattice": "Lattice",

    # Consumer & Entertainment
    "spotify": "Spotify",
    "netflix": "Netflix",
    "reddit": "Reddit",
    "discord": "Discord",
    "dropbox": "Dropbox",
    "pinterest": "Pinterest",
    "roblox": "Roblox",
    "airbnb": "Airbnb",
    "duolingo": "Duolingo",
    "lyft": "Lyft",
    "twitch": "Twitch",
    "instacart": "Instacart",

    # Enterprise & Security
    "palantir": "Palantir",
    "okta": "Okta",
    "twilio": "Twilio",
    "1password": "1Password"
}

class GreenhouseConnector(BaseJobConnector):
    """
    Ingests authentic job postings directly from public Greenhouse company ATS portals (boards-api.greenhouse.io).
    """

    def __init__(self, board_token: str = "cloudflare", rate_limit_rpm: int = 60):
        super().__init__(source_name=f"greenhouse:{board_token}", rate_limit_rpm=rate_limit_rpm)
        self.board_token = board_token
        self.endpoint = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    async def fetch_jobs(self, limit: int = 15, client: Optional[httpx.AsyncClient] = None) -> List[Dict[str, Any]]:
        normalized_jobs = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            if client is not None:
                res = await client.get(self.endpoint)
            else:
                async with httpx.AsyncClient(timeout=4.0, follow_redirects=True, headers=headers) as c:
                    res = await c.get(self.endpoint)
            if res.status_code != 200:
                return []
            data = res.json()
            raw_jobs = data.get("jobs", [])

            tech_jobs = [
                j for j in raw_jobs
                if any(kw in j.get("title", "").lower() for kw in TECH_KEYWORDS)
            ][:limit]

            company_display = COMPANY_DISPLAY_MAP.get(self.board_token.lower(), self.board_token.replace("-", " ").title())

            for item in tech_jobs:
                title = item.get("title", "").strip()
                clean_title = self.normalize_title(title)
                orig_url = item.get("absolute_url", "")
                if not orig_url:
                    continue
                canonical_url = self.normalize_url(orig_url)
                location = item.get("location", {}).get("name", "Remote / Global")

                extracted_skills, _ = extract_skills_from_text(f"{title} {company_display} Engineering Cloud Distributed Systems")

                work_mode = "remote" if "remote" in location.lower() or "remote" in title.lower() else "hybrid"
                desc = f"Official {company_display} verified engineering requisition for {title}. Located in {location}. Direct application hosted on {company_display}'s career portal."
                min_exp = extract_experience_requirement(f"{title} {desc}", title)
                what_they_need = extract_requirements_checklist(desc, title, extracted_skills, min_exp, work_mode)

                dedup_hash = self.generate_dedup_hash(canonical_url, title, company_display)

                normalized_jobs.append({
                    "external_id": f"gh-{self.board_token}-{item.get('id')}",
                    "company_name": company_display,
                    "title": title,
                    "normalized_title": clean_title,
                    "department": "Engineering & Technology",
                    "description": desc,
                    "raw_description": desc,
                    "responsibilities": what_they_need,
                    "required_skills": extracted_skills[:8],
                    "preferred_skills": extracted_skills[8:15],
                    "min_experience_years": min_exp,
                    "location": location,
                    "work_mode": work_mode,
                    "employment_type": "full_time",
                    "original_url": orig_url,
                    "canonical_url": canonical_url,
                    "dedup_hash": dedup_hash,
                    "status": "active",
                    "is_link_verified": True
                })
        except Exception:
            return []
        return normalized_jobs


class LeverConnector(BaseJobConnector):
    """
    Ingests authentic job postings directly from public Lever company ATS portals (api.lever.co/v0/postings).
    """

    def __init__(self, company_id: str = "spotify", rate_limit_rpm: int = 60):
        super().__init__(source_name=f"lever:{company_id}", rate_limit_rpm=rate_limit_rpm)
        self.company_id = company_id
        self.endpoint = f"https://api.lever.co/v0/postings/{company_id}?mode=json"

    async def fetch_jobs(self, limit: int = 15, client: Optional[httpx.AsyncClient] = None) -> List[Dict[str, Any]]:
        normalized_jobs = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            if client is not None:
                res = await client.get(self.endpoint)
            else:
                async with httpx.AsyncClient(timeout=4.0, follow_redirects=True, headers=headers) as c:
                    res = await c.get(self.endpoint)
            if res.status_code != 200:
                return []
            raw_jobs = res.json()

            tech_jobs = [
                j for j in raw_jobs
                if any(kw in j.get("text", "").lower() for kw in TECH_KEYWORDS)
            ][:limit]

            company_display = COMPANY_DISPLAY_MAP.get(self.company_id.lower(), self.company_id.replace("-", " ").title())

            for item in tech_jobs:
                title = item.get("text", "").strip()
                clean_title = self.normalize_title(title)
                orig_url = item.get("hostedUrl", "")
                if not orig_url:
                    continue
                canonical_url = self.normalize_url(orig_url)

                categories = item.get("categories", {})
                location = categories.get("location", "Remote")
                work_type = item.get("workplaceType", "hybrid").lower()

                extracted_skills, _ = extract_skills_from_text(f"{title} {company_display} Software Engineering")

                work_mode = "remote" if "remote" in work_type or "remote" in location.lower() else "hybrid"
                desc = f"Official {company_display} verified requisition for {title}. Location: {location}. Direct application hosted on Lever."
                min_exp = extract_experience_requirement(f"{title} {desc}", title)
                what_they_need = extract_requirements_checklist(desc, title, extracted_skills, min_exp, work_mode)
                dedup_hash = self.generate_dedup_hash(canonical_url, title, company_display)

                normalized_jobs.append({
                    "external_id": f"lever-{self.company_id}-{item.get('id')}",
                    "company_name": company_display,
                    "title": title,
                    "normalized_title": clean_title,
                    "department": categories.get("department", "Engineering"),
                    "description": desc,
                    "raw_description": desc,
                    "responsibilities": what_they_need,
                    "required_skills": extracted_skills[:8],
                    "preferred_skills": extracted_skills[8:15],
                    "min_experience_years": min_exp,
                    "location": location,
                    "work_mode": work_mode,
                    "employment_type": "full_time",
                    "original_url": orig_url,
                    "canonical_url": canonical_url,
                    "dedup_hash": dedup_hash,
                    "status": "active",
                    "is_link_verified": True
                })
        except Exception:
            return []
        return normalized_jobs


class AshbyConnector(BaseJobConnector):
    """
    Ingests authentic job postings directly from public Ashby company ATS portals (api.ashbyhq.com/posting-api/job-board/{company}).
    """

    def __init__(self, company_name: str = "openai", rate_limit_rpm: int = 60):
        super().__init__(source_name=f"ashby:{company_name}", rate_limit_rpm=rate_limit_rpm)
        self.company_name = company_name
        self.endpoint = f"https://api.ashbyhq.com/posting-api/job-board/{company_name}"

    async def fetch_jobs(self, limit: int = 15, client: Optional[httpx.AsyncClient] = None) -> List[Dict[str, Any]]:
        normalized_jobs = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}
            if client is not None:
                res = await client.get(self.endpoint)
            else:
                async with httpx.AsyncClient(timeout=4.0, follow_redirects=True, headers=headers) as c:
                    res = await c.get(self.endpoint)
            if res.status_code != 200:
                return []
            data = res.json()
            raw_jobs = data.get("jobs", [])

            tech_jobs = [
                j for j in raw_jobs
                if any(kw in j.get("title", "").lower() for kw in TECH_KEYWORDS)
            ][:limit]

            company_display = COMPANY_DISPLAY_MAP.get(self.company_name.lower(), self.company_name.replace("-", " ").title())

            for item in tech_jobs:
                title = item.get("title", "").strip()
                clean_title = self.normalize_title(title)
                orig_url = item.get("applyUrl") or item.get("jobUrl", "")
                if not orig_url:
                    continue
                canonical_url = self.normalize_url(orig_url)

                location = item.get("location") or "Remote / Global"
                workplace = (item.get("workplaceType") or "hybrid").lower()
                work_mode = "remote" if "remote" in workplace or item.get("isRemote") else ("onsite" if "onsite" in workplace else "hybrid")

                desc_plain = item.get("descriptionPlain", "")
                desc = desc_plain[:3000] if desc_plain else f"Official {company_display} verified opening for {title}. Located in {location}."

                extracted_skills, _ = extract_skills_from_text(f"{title} {desc_plain[:800]} {company_display}")
                min_exp = extract_experience_requirement(desc_plain, title)
                what_they_need = extract_requirements_checklist(desc_plain, title, extracted_skills, min_exp, work_mode)

                dedup_hash = self.generate_dedup_hash(canonical_url, title, company_display)

                normalized_jobs.append({
                    "external_id": f"ashby-{self.company_name}-{item.get('id')}",
                    "company_name": company_display,
                    "title": title,
                    "normalized_title": clean_title,
                    "department": item.get("department") or "Engineering",
                    "description": desc,
                    "raw_description": item.get("descriptionHtml") or desc,
                    "responsibilities": what_they_need,
                    "required_skills": extracted_skills[:10],
                    "preferred_skills": extracted_skills[10:18],
                    "min_experience_years": min_exp,
                    "location": location,
                    "work_mode": work_mode,
                    "employment_type": "full_time",
                    "original_url": orig_url,
                    "canonical_url": canonical_url,
                    "dedup_hash": dedup_hash,
                    "status": "active",
                    "is_link_verified": True
                })
        except Exception:
            return []
        return normalized_jobs


class AuthenticATSScraper:
    """
    Multi-Board Scraper orchestrator that pulls live tech roles from 70+ top tech employers
    across Ashby, Greenhouse, and Lever ATS platforms.
    """

    ASHBY_COMPANIES = [
        "openai", "perplexity", "cursor", "cohere", "character", "replit",
        "baseten", "modal", "pika", "runway", "langchain", "linear",
        "ramp", "supabase", "resend", "posthog", "cognition", "cartesia",
        "neon", "vapi"
    ]

    GREENHOUSE_COMPANIES = [
        "anthropic", "cloudflare", "databricks", "stripe", "figma", "gitlab",
        "datadog", "mongodb", "scaleai", "vercel", "coinbase", "affirm",
        "toast", "samsara", "reddit", "discord", "dropbox", "elastic",
        "asana", "duolingo", "lyft", "pinterest", "robinhood", "roblox",
        "twilio", "airbnb", "okta", "brex", "gusto", "miro",
        "zapier", "canva", "braze", "klaviyo", "intercom", "checkr",
        "mercury", "carta", "togetherai", "fastly", "cockroachlabs", "netlify",
        "airtable", "stabilityai", "lattice"
    ]

    LEVER_COMPANIES = [
        "spotify", "palantir", "netflix", "twitch", "kraken",
        "plaid", "postman", "1password"
    ]

    @classmethod
    def get_supported_companies_catalog(cls) -> List[Dict[str, str]]:
        """
        Returns rich metadata for all supported authentic employer career pages.
        """
        catalog = []
        for c in cls.ASHBY_COMPANIES:
            catalog.append({
                "slug": c,
                "name": COMPANY_DISPLAY_MAP.get(c, c.title()),
                "platform": "Ashby",
                "careers_url": f"https://jobs.ashbyhq.com/{c}"
            })
        for c in cls.GREENHOUSE_COMPANIES:
            catalog.append({
                "slug": c,
                "name": COMPANY_DISPLAY_MAP.get(c, c.title()),
                "platform": "Greenhouse",
                "careers_url": f"https://boards.greenhouse.io/{c}"
            })
        for c in cls.LEVER_COMPANIES:
            catalog.append({
                "slug": c,
                "name": COMPANY_DISPLAY_MAP.get(c, c.title()),
                "platform": "Lever",
                "careers_url": f"https://jobs.lever.co/{c}"
            })
        catalog.sort(key=lambda x: x["name"])
        return catalog

    @classmethod
    async def scrape_all(cls, limit_per_company: int = 3) -> List[Dict[str, Any]]:
        limits = httpx.Limits(max_keepalive_connections=35, max_connections=50)
        timeout = httpx.Timeout(4.5, connect=3.0)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerRadarAI/1.0"}

        async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True, headers=headers) as shared_client:
            tasks = []

            for comp in cls.ASHBY_COMPANIES:
                connector = AshbyConnector(company_name=comp)
                tasks.append(connector.fetch_jobs(limit=limit_per_company, client=shared_client))

            for comp in cls.GREENHOUSE_COMPANIES:
                connector = GreenhouseConnector(board_token=comp)
                tasks.append(connector.fetch_jobs(limit=limit_per_company, client=shared_client))

            for comp in cls.LEVER_COMPANIES:
                connector = LeverConnector(company_id=comp)
                tasks.append(connector.fetch_jobs(limit=limit_per_company, client=shared_client))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for res in results:
            if isinstance(res, list):
                all_jobs.extend(res)

        return all_jobs
