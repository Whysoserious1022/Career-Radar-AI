from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

class BaseJobConnector(ABC):
    """
    Abstract base class for verified employer job connectors (Greenhouse, Lever, Ashby, direct feeds).
    """

    def __init__(self, source_name: str, rate_limit_rpm: int = 60):
        self.source_name = source_name
        self.rate_limit_rpm = rate_limit_rpm

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Strips marketing tracking parameters (utm_*, gclid, ref, etc.) to produce a canonical job URL.
        """
        if not url:
            return ""
        parsed = urlparse(url.strip())
        tracked_prefixes = ("utm_", "fbclid", "gclid", "ref", "source", "gh_src")
        clean_query = [
            (k, v) for k, v in parse_qsl(parsed.query)
            if not any(k.lower().startswith(prefix) for prefix in tracked_prefixes)
        ]
        clean_url = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            urlencode(clean_query),
            ""  # Strip fragment
        ))
        return clean_url

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalizes job titles by removing level prefixes/suffixes and brackets for canonical matching.
        """
        cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', title)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
        return cleaned

    @classmethod
    def generate_dedup_hash(cls, canonical_url: str, title: str, company: str) -> str:
        """
        Generates a SHA-256 deduplication fingerprint based on canonical URL and normalized metadata.
        """
        clean_url = cls.normalize_url(canonical_url)
        clean_title = cls.normalize_title(title)
        clean_company = company.strip().lower()
        key = f"{clean_company}:{clean_title}:{clean_url}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @abstractmethod
    async def fetch_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches job postings from the external ATS source and returns normalized job dictionaries.
        """
        pass
