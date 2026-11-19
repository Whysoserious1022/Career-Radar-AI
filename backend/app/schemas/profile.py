from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    graduation_year: Optional[int] = None
    degree: Optional[str] = None
    university: Optional[str] = None
    gpa: Optional[float] = None
    years_of_experience: Optional[float] = 0.0
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    notice_period_days: Optional[int] = 0
    preferred_roles: Optional[List[str]] = Field(default_factory=list)
    preferred_locations: Optional[List[str]] = Field(default_factory=list)
    preferred_work_modes: Optional[List[str]] = Field(default_factory=list)
    skills: Optional[List[str]] = Field(default_factory=list)
    min_salary: Optional[float] = None
    expected_salary: Optional[float] = None
    currency: Optional[str] = "USD"

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
