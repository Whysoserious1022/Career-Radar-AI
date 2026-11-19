import pytest
from httpx import AsyncClient
from app.connectors.base import BaseJobConnector
from app.connectors.seed_data import SAMPLE_JOBS, get_prepared_seed_jobs

@pytest.mark.asyncio
async def test_connector_url_and_hash_normalization():
    dirty_url = "https://careers.google.com/jobs/results/12345/?utm_source=linkedin&gh_src=abc&ref=jobboard"
    clean_url = BaseJobConnector.normalize_url(dirty_url)
    assert "utm_source" not in clean_url
    assert "gh_src" not in clean_url
    assert clean_url == "https://careers.google.com/jobs/results/12345"

    norm_title = BaseJobConnector.normalize_title("Senior Software Engineer (L5) [Remote]")
    assert norm_title == "senior software engineer"

    hash1 = BaseJobConnector.generate_dedup_hash(clean_url, "Senior Software Engineer", "Google")
    hash2 = BaseJobConnector.generate_dedup_hash(clean_url, "Senior Software Engineer (L5)", "Google")
    assert hash1 == hash2

@pytest.mark.asyncio
async def test_job_sync_seeds_and_list(client: AsyncClient):
    # Sync seed jobs
    res = await client.post("/api/v1/jobs/sync-seeds")
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) >= 6

    # Test listing jobs
    list_res = await client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    all_jobs = list_res.json()
    assert len(all_jobs) >= 6

    # Test filter by work_mode
    remote_res = await client.get("/api/v1/jobs?work_mode=remote")
    assert remote_res.status_code == 200
    remote_jobs = remote_res.json()
    assert len(remote_jobs) >= 1
    assert all(j["work_mode"] == "remote" for j in remote_jobs)

    # Test filter by keyword
    search_res = await client.get("/api/v1/jobs?query=Stripe")
    assert search_res.status_code == 200
    stripe_jobs = search_res.json()
    assert len(stripe_jobs) == 1
    assert stripe_jobs[0]["company_name"] == "Stripe"

@pytest.mark.asyncio
async def test_job_creation_and_deduplication(client: AsyncClient):
    payload = {
        "company_name": "Acme Systems",
        "title": "Principal Architect",
        "description": "Looking for an architect experienced with Python, Docker, and Kubernetes.",
        "location": "New York, NY",
        "work_mode": "hybrid",
        "original_url": "https://acme.com/jobs/101?utm_medium=email"
    }

    create_res = await client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 201
    created_job = create_res.json()
    assert created_job["company_name"] == "Acme Systems"
    # Auto skill extraction
    assert "Python" in created_job["required_skills"] or "Docker" in created_job["required_skills"]

    # Duplicate creation should be rejected with 409
    dup_res = await client.post("/api/v1/jobs", json=payload)
    assert dup_res.status_code == 409
