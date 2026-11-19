from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.resume import Resume
from app.models.application import Application
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/applications", tags=["Application Pipeline Tracker"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    app_in: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Tracks a new job application in the candidate's career pipeline.
    """
    # Verify job exists
    job_res = await db.execute(select(Job).where(Job.id == app_in.job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")

    # Verify resume belongs to user if specified
    if app_in.resume_id:
        res_check = await db.execute(
            select(Resume).where(Resume.id == app_in.resume_id, Resume.user_id == current_user.id)
        )
        if not res_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected resume not found for candidate")

    # Check if application already exists for this job
    existing = await db.execute(
        select(Application).where(Application.user_id == current_user.id, Application.job_id == app_in.job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application for this job is already being tracked in your pipeline"
        )

    now = datetime.now(timezone.utc)
    applied_time = now if app_in.status == "applied" else None

    application = Application(
        user_id=current_user.id,
        job_id=app_in.job_id,
        resume_id=app_in.resume_id,
        status=app_in.status,
        notes=app_in.notes,
        recruiter_name=app_in.recruiter_name,
        recruiter_email=app_in.recruiter_email,
        applied_at=applied_time,
        created_at=now,
        updated_at=now
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # Reload with job
    result = await db.execute(
        select(Application).options(selectinload(Application.job)).where(Application.id == application.id)
    )
    return result.scalar_one()

@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all tracked applications in the candidate's career pipeline (Saved, Applied, Interview, Offer).
    """
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == current_user.id)
    )
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)

    stmt = stmt.order_by(Application.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details of a single tracked application.
    """
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == application_id, Application.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found")
    return application

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    app_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates application progress: status stage, interview date, recruiter contact info, or notes.
    """
    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == application_id, Application.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found")

    update_dict = app_update.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(application, field, value)

    # Automatically set applied_at if status transitions to applied and not previously set
    if app_update.status == "applied" and not application.applied_at:
        application.applied_at = datetime.now(timezone.utc)

    application.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(application)
    return application

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes an application from the candidate's tracker.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found")

    await db.delete(application)
    await db.commit()
    return None
