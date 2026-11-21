from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List, Optional

from app.core.database import get_db
from app.models.job import Job, JobSource
from app.schemas.job import JobCreate, JobResponse, JobFilter
from app.connectors.base import BaseJobConnector
from app.connectors.seed_data import get_prepared_seed_jobs
from app.connectors.ats_connectors import AuthenticATSScraper
from app.connectors.free_job_apis import ArbeitnowConnector, RemotiveConnector, JobicyConnector
from app.services.skill_extractor import extract_skills_from_text
from app.workers.freshness_checker import JobFreshnessVerifier

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

    job_data = job_in.model_dump(exclude={"source_name"})
    job_data["canonical_url"] = clean_url
    job_data["normalized_title"] = norm_title
    job_data["dedup_hash"] = dedup_hash
    job_data["required_skills"] = req_skills

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

@router.post("/sync-free-apis")
async def sync_free_job_apis(
    limit_per_source: int = Query(default=20, ge=5, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Scrapes and syncs live, active job postings from freely available public job APIs
    (Arbeitnow, Remotive, Jobicy) with automatic skill extraction and deduplication.
    """
    connectors = [
        ArbeitnowConnector(),
        RemotiveConnector(),
        JobicyConnector()
    ]
    total_ingested = 0
    total_deduplicated = 0
    sources_summary = {}

    for conn in connectors:
        try:
            jobs = await conn.fetch_jobs(limit=limit_per_source)
            ingested_count = 0
            for item in jobs:
                existing = await db.execute(select(Job).where(Job.dedup_hash == item["dedup_hash"]))
                if not existing.scalar_one_or_none():
                    db.add(Job(**item))
                    ingested_count += 1
                else:
                    total_deduplicated += 1
            sources_summary[conn.source_name] = len(jobs)
            total_ingested += ingested_count
        except Exception as e:
            sources_summary[conn.source_name] = f"Error: {str(e)}"

    await db.commit()
    return {
        "status": "success",
        "total_new_jobs_ingested": total_ingested,
        "total_deduplicated": total_deduplicated,
        "sources": sources_summary
    }

@router.post("/sync-authentic-jobs")
async def sync_authentic_employer_jobs(
    limit_per_company: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Scrapes live, verified requisitions directly from 15+ tech employer ATS portals
    (Greenhouse & Lever: Cloudflare, Figma, GitLab, Datadog, Reddit, Discord, Dropbox,
    Elastic, Instacart, Pinterest, Robinhood, Roblox, Twilio, Airbnb, Stripe, Spotify, Palantir).
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
