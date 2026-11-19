from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class JobBase(BaseModel):
    company_name: str
    title: str
    normalized_title: Optional[str] = None
    department: Optional[str] = None
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    max_experience_years: Optional[float] = None
    location: str
    work_mode: str = "onsite"  # remote, hybrid, onsite
    employment_type: str = "full_time"
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: str = "USD"
    original_url: str
    status: str = "active"

class JobCreate(JobBase):
    external_id: Optional[str] = None
    source_name: Optional[str] = None

class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    normalized_title: str
    canonical_url: str
    status: str
    is_link_verified: bool
    discovered_at: datetime
    last_verified_at: Optional[datetime] = None

class JobFilter(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    skills: Optional[List[str]] = None
    limit: int = 20
    offset: int = 0
