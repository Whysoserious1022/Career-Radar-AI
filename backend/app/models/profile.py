from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    headline = Column(String(255), nullable=True)
    summary = Column(String(2000), nullable=True)
    
    # Education
    graduation_year = Column(Integer, nullable=True)
    degree = Column(String(100), nullable=True)
    university = Column(String(255), nullable=True)
    gpa = Column(Float, nullable=True)
    
    # Career Details
    years_of_experience = Column(Float, default=0.0)
    current_company = Column(String(255), nullable=True)
    current_title = Column(String(255), nullable=True)
    notice_period_days = Column(Integer, default=0)
    
    # Preferences (JSON structures)
    preferred_roles = Column(JSON, default=list)        # ["AI Engineer", "Backend Engineer"]
    preferred_locations = Column(JSON, default=list)    # ["Bengaluru", "Remote"]
    preferred_work_modes = Column(JSON, default=list)   # ["remote", "hybrid", "onsite"]
    skills = Column(JSON, default=list)                 # ["Python", "PyTorch", "FastAPI"]
    
    min_salary = Column(Float, nullable=True)
    expected_salary = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="profile")
