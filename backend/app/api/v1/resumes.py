from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import hashlib
import os
import uuid
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume, ResumeExtractedData
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeDetailResponse,
    ResumeCorrectionUpdate
)
from app.api.deps import get_current_user
from app.services.resume_parser import ResumeParser

router = APIRouter(prefix="/resumes", tags=["Multi-Resume Management"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    category: str = Form(default="sde"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file contents and compute hash
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Save file securely
    storage_path = Path(settings.STORAGE_DIR)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    saved_file_path = storage_path / unique_filename
    
    with open(saved_file_path, "wb") as f:
        f.write(content)
        
    # Check version count for this category
    existing_resumes = await db.execute(
        select(Resume).where(
            Resume.user_id == current_user.id,
            Resume.category == category
        )
    )
    version = len(existing_resumes.scalars().all()) + 1
    
    # Parse resume
    try:
        parsed_data = ResumeParser.parse_resume(str(saved_file_path))
        raw_text = ResumeParser.extract_text_from_file(str(saved_file_path))
    except Exception as e:
        parsed_data = {
            "skills": [],
            "experience_years": 0.0,
            "education": [],
            "projects": [],
            "certifications": [],
            "error": str(e)
        }
        raw_text = ""

    # Create Resume DB record
    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=str(saved_file_path),
        file_hash=file_hash,
        file_size_bytes=len(content),
        mime_type=file.content_type or "application/octet-stream",
        category=category,
        version=version,
        is_active=True
    )
    db.add(resume)
    await db.flush()

    # Create Extracted Data record
    extracted = ResumeExtractedData(
        resume_id=resume.id,
        raw_text=raw_text,
        structured_json=parsed_data,
        parsed_confidence=parsed_data.get("parsed_confidence", 1.0)
    )
    db.add(extracted)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_name=resume.file_name,
        category=resume.category,
        version=resume.version,
        is_active=resume.is_active,
        file_size_bytes=resume.file_size_bytes,
        extracted_summary={
            "skills_count": len(parsed_data.get("skills", [])),
            "top_skills": parsed_data.get("skills", [])[:8],
            "experience_years": parsed_data.get("experience_years", 0.0),
            "education_count": len(parsed_data.get("education", [])),
            "confidence": parsed_data.get("parsed_confidence", 1.0)
        },
        created_at=resume.created_at
    )

@router.get("", response_model=List[ResumeDetailResponse])
async def list_my_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.extracted_data))
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    response = []
    for r in resumes:
        response.append(ResumeDetailResponse(
            id=r.id,
            user_id=r.user_id,
            file_name=r.file_name,
            category=r.category,
            version=r.version,
            is_active=r.is_active,
            created_at=r.created_at,
            extracted_data=r.extracted_data.structured_json if r.extracted_data else None
        ))
    return response

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume_detail(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.extracted_data))
        .where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    
    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_name=resume.file_name,
        category=resume.category,
        version=resume.version,
        is_active=resume.is_active,
        created_at=resume.created_at,
        extracted_data=resume.extracted_data.structured_json if resume.extracted_data else None
    )

@router.put("/{resume_id}/corrections", response_model=ResumeDetailResponse)
async def correct_resume_data(
    resume_id: str,
    corrections: ResumeCorrectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.extracted_data))
        .where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if corrections.category:
        resume.category = corrections.category

    if resume.extracted_data:
        curr_json = dict(resume.extracted_data.structured_json)
        corr_dict = corrections.model_dump(exclude_unset=True)
        for k, v in corr_dict.items():
            if k != "category" and v is not None:
                curr_json[k] = v
        resume.extracted_data.structured_json = curr_json
        resume.extracted_data.is_user_verified = True
        resume.extracted_data.user_corrections = corr_dict

    await db.commit()
    await db.refresh(resume)

    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_name=resume.file_name,
        category=resume.category,
        version=resume.version,
        is_active=resume.is_active,
        created_at=resume.created_at,
        extracted_data=resume.extracted_data.structured_json if resume.extracted_data else None
    )

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    
    # Remove physical file if exists
    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except OSError:
            pass

    await db.delete(resume)
    await db.commit()
    return None
