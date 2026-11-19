from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.job import JobResponse

class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job: JobResponse
    best_resume_id: Optional[str]
    best_resume_name: Optional[str] = None
    composite_score: float
    eligibility_status: str
    matched_skills: List[str]
    missing_skills: List[str]
    reasons: List[str]
    created_at: datetime

class FeedbackRequest(BaseModel):
    feedback_type: str = Field(description="saved, dismissed, applied, marked_irrelevant")
    comments: Optional[str] = None

class ResumeJobComparisonResponse(BaseModel):
    job_id: str
    best_resume_id: Optional[str]
    best_resume_category: Optional[str]
    overall_match: float
    skill_match: float
    experience_match: float
    education_match: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendation_reasons: List[str]
    resume_scores: List[Dict[str, Any]] = Field(default_factory=list)
