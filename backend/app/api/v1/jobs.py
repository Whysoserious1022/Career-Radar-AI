from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job, JobSource
from app.schemas.job import JobCreate, JobResponse, JobFilter, ScrapeUrlRequest
from app.connectors.base import BaseJobConnector
from app.connectors.seed_data import get_prepared_seed_jobs
from app.connectors.ats_connectors import AuthenticATSScraper
from app.connectors.web_scraper import DeepWebJobScraper
from app.services.skill_extractor import extract_skills_from_text
from app.services.matcher import RecommendationMatcher
from app.workers.freshness_checker import JobFreshnessVerifier
from app.api.deps import get_current_user_optional

router = APIRouter(prefix="/jobs", tags=["Job Discovery & Ingestion"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_in: JobCreate, db: AsyncSession = Depends(get_db)):
    """
    Ingests a single job posting, calculating canonical URLs, deduplication fingerprints,
    and automatically extracting skills if missing.
    """
    clean_url = BaseJobConnector.normalize_url(job_in.original_url)
    norm_title = BaseJobConnector.normalize_title(job_in.title)
    dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, job_in.title, job_in.company_name)

    # Check for duplicate
    existing = await db.execute(select(Job).where(Job.dedup_hash == dedup_hash))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job posting already exists with identical canonical fingerprint"
        )

    # Auto-extract skills if not supplied
    req_skills = job_in.required_skills
    if not req_skills:
        extracted, _ = extract_skills_from_text(f"{job_in.title} {job_in.description}")
        req_skills = extracted[:10]

    job_data = job_in.model_dump(exclude={"source_name", "what_they_need"})
    job_data["canonical_url"] = clean_url
    job_data["normalized_title"] = norm_title
    job_data["dedup_hash"] = dedup_hash
    job_data["required_skills"] = req_skills
    if not job_data.get("responsibilities") and job_in.what_they_need:
        job_data["responsibilities"] = job_in.what_they_need

    job = Job(**job_data)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.post("/sync-seeds", response_model=List[JobResponse])
async def sync_sample_jobs(db: AsyncSession = Depends(get_db)):
    """
    Idempotently seeds verified high-quality job postings from top tech employers.
    """
    seed_jobs = get_prepared_seed_jobs()
    synced = []

    for item in seed_jobs:
        existing = await db.execute(select(Job).where(Job.dedup_hash == item["dedup_hash"]))
        found = existing.scalar_one_or_none()
        if not found:
            new_job = Job(**item)
            db.add(new_job)
            synced.append(new_job)
        else:
            synced.append(found)

    await db.commit()
    for j in synced:
        await db.refresh(j)
    return synced

@router.post("/sync-authentic-jobs")
async def sync_authentic_employer_jobs(
    limit_per_company: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Scrapes live, verified requisitions directly from 35+ tech employer career portals
    across Ashby, Greenhouse & Lever:
    (OpenAI, Ramp, Linear, Supabase, Perplexity, Modal, Cognition, Resend, Cartesia,
     Cloudflare, Figma, GitLab, Datadog, Reddit, Discord, Dropbox, Elastic, Instacart,
     Pinterest, Robinhood, Roblox, Twilio, Airbnb, Stripe, Okta, Brex, Gusto, Miro,
     Zapier, Canva, Spotify, Palantir, Netflix, Affirm, Twitch, Kraken, Plaid, Postman).
    """
    scraped_jobs = await AuthenticATSScraper.scrape_all(limit_per_company=limit_per_company)
    total_ingested = 0
    total_deduplicated = 0
    companies_summary = {}

    for item in scraped_jobs:
        comp = item.get("company_name", "Unknown")
        companies_summary[comp] = companies_summary.get(comp, 0) + 1
        existing = await db.execute(select(Job).where(Job.dedup_hash == item["dedup_hash"]))
        if not existing.scalar_one_or_none():
            db.add(Job(**item))
            total_ingested += 1
        else:
            total_deduplicated += 1

    await db.commit()
    return {
        "status": "success",
        "total_scraped": len(scraped_jobs),
        "total_new_jobs_ingested": total_ingested,
        "total_deduplicated": total_deduplicated,
        "companies_represented": companies_summary
    }

@router.post("/sync-all-sources")
async def sync_all_sources_orchestrator(
    limit_ats: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Universal Scraper Engine: orchestrates parallel web scraping across ALL 35+ employer career portals
    (Ashby, Greenhouse, Lever) in a single unified execution without any external third-party job APIs.
    """
    all_jobs = await AuthenticATSScraper.scrape_all(limit_per_company=limit_ats)

    total_ingested = 0
    total_deduplicated = 0
    companies_summary = {}

    for item in all_jobs:
        comp = item.get("company_name", "Unknown")
        companies_summary[comp] = companies_summary.get(comp, 0) + 1
        existing = await db.execute(select(Job).where(Job.dedup_hash == item["dedup_hash"]))
        if not existing.scalar_one_or_none():
            db.add(Job(**item))
            total_ingested += 1
        else:
            total_deduplicated += 1

    await db.commit()
    return {
        "status": "success",
        "total_scraped": len(all_jobs),
        "total_new_jobs_ingested": total_ingested,
        "total_deduplicated": total_deduplicated,
        "total_companies_covered": len(companies_summary),
        "companies_represented": companies_summary
    }

@router.post("/scrape-url")
async def scrape_career_url(
    payload: ScrapeUrlRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    On-Demand Web Scraper:
    Accepts ANY career portal, ATS link, or company webpage URL (Ashby, Greenhouse, Lever,
    Workable, SmartRecruiters, or generic careers page).
    Extracts all open requisitions, normalizes canonical URLs, extracts skills, deduplicates,
    persists new jobs, and computes real-time candidate recommendation fit scores!
    """
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target URL cannot be empty")

    scraped_jobs = await DeepWebJobScraper.scrape_url(payload.url.strip(), limit=payload.limit or 25)
    if not scraped_jobs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract active job opportunities from the provided URL. Ensure it is a valid careers page or job listing link."
        )

    ingested_jobs = []
    total_deduplicated = 0

    for item in scraped_jobs:
        existing = await db.execute(select(Job).where(Job.dedup_hash == item["dedup_hash"]))
        found = existing.scalar_one_or_none()
        if not found:
            new_job = Job(**item)
            db.add(new_job)
            ingested_jobs.append(new_job)
        else:
            total_deduplicated += 1
            ingested_jobs.append(found)

    await db.commit()
    for j in ingested_jobs:
        await db.refresh(j)

    # If candidate is authenticated, calculate real-time match scores for these scraped jobs
    matched_results = []
    if current_user:
        prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
        profile = prof_res.scalar_one_or_none()

        resume_res = await db.execute(
            select(Resume)
            .options(selectinload(Resume.extracted_data))
            .where(Resume.user_id == current_user.id, Resume.is_active == True)
        )
        resumes = resume_res.scalars().all()

        for j in ingested_jobs:
            match_data = RecommendationMatcher.match_candidate_to_job(profile, resumes, j)
            matched_results.append({
                "job": {
                    "id": j.id,
                    "company_name": j.company_name,
                    "title": j.title,
                    "location": j.location,
                    "work_mode": j.work_mode,
                    "original_url": j.original_url,
                    "canonical_url": j.canonical_url,
                    "min_experience_years": j.min_experience_years,
                    "required_skills": j.required_skills,
                    "what_they_need": j.responsibilities or []
                },
                "match": match_data
            })

    eligible_count = sum(1 for m in matched_results if m.get("match", {}).get("can_apply"))
    ineligible_count = len(matched_results) - eligible_count

    return {
        "status": "success",
        "url_scraped": payload.url,
        "total_scraped": len(scraped_jobs),
        "new_jobs_ingested": len(ingested_jobs) - total_deduplicated,
        "total_deduplicated": total_deduplicated,
        "quick_diagnosis": {
            "total_diagnosed": len(matched_results),
            "eligible_roles_count": eligible_count,
            "ineligible_roles_count": ineligible_count
        },
        "jobs": [
            {
                "id": j.id,
                "company_name": j.company_name,
                "title": j.title,
                "location": j.location,
                "work_mode": j.work_mode,
                "original_url": j.original_url,
                "canonical_url": j.canonical_url,
                "min_experience_years": j.min_experience_years,
                "required_skills": j.required_skills,
                "what_they_need": j.responsibilities or []
            }
            for j in ingested_jobs
        ],
        "personalized_recommendations": matched_results
    }

@router.get("/supported-companies")
async def list_supported_companies():
    """
    Returns the comprehensive catalog of 70+ authentic employer career portals
    (OpenAI, Anthropic, Databricks, Stripe, Figma, Cloudflare, Spotify, etc.).
    """
    return AuthenticATSScraper.get_supported_companies_catalog()

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    work_mode: Optional[str] = None,
    min_exp: Optional[float] = None,
    max_exp: Optional[float] = None,
    status_filter: Optional[str] = "active",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Search and filter verified job opportunities.
    """
    stmt = select(Job)
    filters = []

    if status_filter:
        filters.append(Job.status == status_filter)

    if query:
        q_wild = f"%{query.lower()}%"
        filters.append(or_(
            Job.title.ilike(q_wild),
            Job.company_name.ilike(q_wild),
            Job.description.ilike(q_wild)
        ))

    if location:
        filters.append(Job.location.ilike(f"%{location}%"))

    if work_mode:
        filters.append(Job.work_mode == work_mode.lower())

    if min_exp is not None:
        filters.append(Job.min_experience_years <= min_exp)

    if max_exp is not None:
        filters.append(Job.min_experience_years >= max_exp)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(Job.discovered_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch comprehensive job details.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    return job

@router.post("/verify-freshness")
async def trigger_freshness_verification(limit: int = Query(default=20), db: AsyncSession = Depends(get_db)):
    """
    Executes automated URL validation on active jobs.
    """
    results = await JobFreshnessVerifier.verify_jobs_batch(db, limit=limit)
    return {"verified_count": len(results), "jobs": results}

@router.post("/{job_id}/report-dead-link")
async def report_dead_link(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Stage 4 Dead-Link Cleanup: Immediately verifies reported requisition and updates status if expired.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    verified = await JobFreshnessVerifier.verify_url(job.canonical_url or job.original_url)
    job.is_link_verified = verified["is_valid"]
    if not verified["is_valid"]:
        job.status = "expired"
    await db.commit()
    return {
        "status": "success",
        "job_id": job_id,
        "is_active": verified["is_valid"],
        "http_status": verified.get("status_code")
    }

