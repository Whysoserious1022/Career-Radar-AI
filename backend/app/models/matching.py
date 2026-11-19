from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.core.database import Base

class ResumeJobMatch(Base):
    __tablename__ = "resume_job_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    
    overall_match_score = Column(Float, nullable=False)  # 0 to 100
    skill_match_score = Column(Float, nullable=False)
    experience_match_score = Column(Float, nullable=False)
    education_match_score = Column(Float, nullable=False)
    
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    rationales = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    resume = relationship("Resume", back_populates="matches")
    job = relationship("Job", back_populates="matches")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    best_resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    
    composite_score = Column(Float, nullable=False)  # 0 to 100
    eligibility_status = Column(String(50), default="eligible")  # eligible, likely_eligible, unclear, ineligible
    
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    reasons = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="recommendations")
    job = relationship("Job", back_populates="recommendations")
    best_resume = relationship("Resume")
    feedback = relationship("RecommendationFeedback", back_populates="recommendation", uselist=False, cascade="all, delete-orphan")

class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id = Column(String(36), ForeignKey("recommendations.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    feedback_type = Column(String(50), nullable=False)  # saved, dismissed, applied, marked_irrelevant
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    recommendation = relationship("Recommendation", back_populates="feedback")
