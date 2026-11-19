from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.core.database import Base

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)  # greenhouse, lever, ashby, custom_rss
    base_url = Column(String(500), nullable=True)
    rate_limit_rpm = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)

    jobs = relationship("Job", back_populates="source")
    sync_runs = relationship("SourceSyncRun", back_populates="source", cascade="all, delete-orphan")

class SourceSyncRun(Base):
    __tablename__ = "source_sync_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="started")  # started, completed, failed
    jobs_discovered = Column(Integer, default=0)
    jobs_ingested = Column(Integer, default=0)
    jobs_deduplicated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)

    source = relationship("JobSource", back_populates="sync_runs")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(255), index=True, nullable=True)
    
    company_name = Column(String(255), index=True, nullable=False)
    title = Column(String(255), index=True, nullable=False)
    normalized_title = Column(String(255), index=True, nullable=False)
    department = Column(String(255), nullable=True)
    
    description = Column(Text, nullable=False)
    raw_description = Column(Text, nullable=True)
    responsibilities = Column(JSON, default=list)
    
    # Requirements
    required_skills = Column(JSON, default=list)  # ["Python", "FastAPI"]
    preferred_skills = Column(JSON, default=list)
    min_experience_years = Column(Float, default=0.0)
    max_experience_years = Column(Float, nullable=True)
    education_requirements = Column(JSON, default=list)
    graduation_years_accepted = Column(JSON, default=list)
    
    # Work Mode & Location
    location = Column(String(255), index=True, nullable=False)
    work_mode = Column(String(50), default="onsite")  # remote, hybrid, onsite
    employment_type = Column(String(50), default="full_time")  # full_time, internship, contract
    
    # Compensation
    min_salary = Column(Float, nullable=True)
    max_salary = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    
    # URLs & Provenance
    original_url = Column(String(1000), nullable=False)
    canonical_url = Column(String(1000), index=True, nullable=False)
    dedup_hash = Column(String(64), index=True, nullable=False)  # SHA-256(canonical_url + normalized_title)
    
    # Status & Freshness
    status = Column(String(50), default="active", index=True)  # active, closed, expired, unverified
    is_link_verified = Column(Boolean, default=True)
    last_verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    source = relationship("JobSource", back_populates="jobs")
    matches = relationship("ResumeJobMatch", back_populates="job", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
