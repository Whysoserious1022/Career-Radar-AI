from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    category = Column(String(50), default="sde", nullable=False)  # sde, aiml, data_engineering, devops, general
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="resumes")
    extracted_data = relationship("ResumeExtractedData", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    matches = relationship("ResumeJobMatch", back_populates="resume", cascade="all, delete-orphan")

class ResumeExtractedData(Base):
    __tablename__ = "resume_extracted_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    raw_text = Column(Text, nullable=False)
    # Structured JSON: { "skills": [...], "experience_years": float, "education": [...], "projects": [...], "certifications": [...] }
    structured_json = Column(JSON, default=dict, nullable=False)
    parsed_confidence = Column(Float, default=1.0)
    
    # User-verified overrides
    is_user_verified = Column(Boolean, default=False)
    user_corrections = Column(JSON, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    resume = relationship("Resume", back_populates="extracted_data")
