import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_recommendations_flow_with_multi_resume(client: AsyncClient, auth_headers: dict):
    # 1. Sync sample jobs
    await client.post("/api/v1/jobs/sync-seeds")

    # 2. Upload SDE Resume
    sde_resume = """
    Alex Rivera
    Email: alex@example.com
    Skills: Python, Go, Docker, Kubernetes, Kafka, PostgreSQL, AWS
    Experience: 6 years building distributed streaming systems.
    """
    files_sde = {'file': ('resume_sde.txt', sde_resume.encode('utf-8'), 'text/plain')}
    sde_res = await client.post("/api/v1/resumes/upload", files=files_sde, data={'category': 'sde'}, headers=auth_headers)
    assert sde_res.status_code == 201

    # 3. Upload AI/ML Resume
    ml_resume = """
    Alex Rivera
    Email: alex@example.com
    Skills: Python, PyTorch, Transformers, LLM, Vector Search, FastAPI
    Experience: 5 years deploying generative AI pipelines.
    """
    files_ml = {'file': ('resume_ml.txt', ml_resume.encode('utf-8'), 'text/plain')}
    ml_res = await client.post("/api/v1/resumes/upload", files=files_ml, data={'category': 'ai_ml'}, headers=auth_headers)
    assert ml_res.status_code == 201

    # 4. Fetch recommendations
    rec_res = await client.get("/api/v1/recommendations", headers=auth_headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert len(recs) >= 3

    # Check that highest scoring job has matched skills and explainability reasons
    top_rec = recs[0]
    assert top_rec["composite_score"] > 60.0
    assert len(top_rec["matched_skills"]) > 0
    assert len(top_rec["reasons"]) >= 2
    assert top_rec["eligibility_status"] in ["eligible", "likely_eligible"]

    # 5. Test Deep-Dive comparison endpoint
    job_id = top_rec["job_id"]
    match_res = await client.post(f"/api/v1/recommendations/match-job/{job_id}", headers=auth_headers)
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert "resume_scores" in match_data
    assert len(match_data["resume_scores"]) == 2  # SDE and AI/ML resumes both evaluated

    # 6. Test recording feedback
    fb_res = await client.post(
        f"/api/v1/recommendations/{top_rec['id']}/feedback",
        json={"feedback_type": "saved", "comments": "Strong alignment with infrastructure background"},
        headers=auth_headers
    )
    assert fb_res.status_code == 201
