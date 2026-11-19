from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.job import JobResponse

class ApplicationCreate(BaseModel):
    job_id: str
    resume_id: Optional[str] = None
    status: str = "saved"
    notes: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None

class ApplicationUpdate(BaseModel):
    resume_id: Optional[str] = None
    status: Optional[str] = None  # saved, resume_selected, ready_to_apply, applied, assessment, interview, offer, rejected, withdrawn
    applied_at: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    job_id: str
    resume_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None
