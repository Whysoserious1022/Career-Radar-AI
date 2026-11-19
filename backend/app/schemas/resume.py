from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResumeExtractedDataSchema(BaseModel):
    contact: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    categorized_skills: Dict[str, List[str]] = Field(default_factory=dict)
    experience_years: float = 0.0
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    file_name: str
    category: str
    version: int
    is_active: bool
    file_size_bytes: int
    extracted_summary: Dict[str, Any]
    created_at: datetime

class ResumeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    file_name: str
    category: str
    version: int
    is_active: bool
    created_at: datetime
    extracted_data: Optional[Dict[str, Any]] = None

class ResumeCorrectionUpdate(BaseModel):
    skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    education: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    category: Optional[str] = None
