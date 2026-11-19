import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_application_lifecycle_and_tracker(client: AsyncClient, auth_headers: dict):
    # 1. Sync jobs to have a target job
    seed_res = await client.post("/api/v1/jobs/sync-seeds")
    jobs = seed_res.json()
    target_job = jobs[0]
    job_id = target_job["id"]

    # 2. Track application (status = saved)
    app_payload = {
        "job_id": job_id,
        "status": "saved",
        "notes": "Target company for Q1. Reviewing referral network."
    }
    create_res = await client.post("/api/v1/applications", json=app_payload, headers=auth_headers)
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]
    assert app_data["status"] == "saved"
    assert app_data["job"]["company_name"] == target_job["company_name"]

    # 3. Duplicate application check
    dup_res = await client.post("/api/v1/applications", json=app_payload, headers=auth_headers)
    assert dup_res.status_code == 409

    # 4. List applications
    list_res = await client.get("/api/v1/applications", headers=auth_headers)
    assert list_res.status_code == 200
    apps = list_res.json()
    assert len(apps) == 1

    # 5. Update application stage to applied, add recruiter info
    update_payload = {
        "status": "applied",
        "recruiter_name": "Sarah Connor",
        "recruiter_email": "sarah@stripe.com",
        "notes": "Submitted direct application via CareerRadar recommended SDE resume."
    }
    update_res = await client.put(f"/api/v1/applications/{app_id}", json=update_payload, headers=auth_headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["status"] == "applied"
    assert updated_data["applied_at"] is not None
    assert updated_data["recruiter_name"] == "Sarah Connor"

    # 6. Delete application
    del_res = await client.delete(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deletion
    verify_res = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert verify_res.status_code == 404
