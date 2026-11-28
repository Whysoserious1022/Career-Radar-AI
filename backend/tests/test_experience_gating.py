import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_experience_gating_and_quick_diagnosis(client: AsyncClient, auth_headers: dict):
    # Set candidate experience to 2.0 years via profile endpoint
    resp_prof = await client.put(
        "/api/v1/profile/me",
        json={
            "years_of_experience": 2.0,
            "headline": "Junior Python Engineer",
            "preferred_roles": ["Junior Python Developer"]
        },
        headers=auth_headers
    )
    assert resp_prof.status_code == 200

    # Ingest Junior Job (1.0 yr min exp)
    resp_jr = await client.post(
        "/api/v1/jobs",
        json={
            "company_name": "GateCorp Jr",
            "title": "Junior Python Developer",
            "location": "Remote",
            "work_mode": "remote",
            "original_url": "https://careers.gatecorp.com/jr-dev",
            "description": "Seeking Junior Python Developer with 1+ years experience in Python, FastAPI, and Git.",
            "min_experience_years": 1.0,
            "required_skills": ["Python", "FastAPI", "Git"]
        }
    )
    assert resp_jr.status_code == 201
    jr_data = resp_jr.json()
    assert jr_data["min_experience_years"] == 1.0
    assert "what_they_need" in jr_data
    assert len(jr_data["what_they_need"]) > 0

    # Ingest Senior Job (6.0 yrs min exp)
    resp_sr = await client.post(
        "/api/v1/jobs",
        json={
            "company_name": "GateCorp Sr",
            "title": "Principal Distributed Architect",
            "location": "Remote",
            "work_mode": "remote",
            "original_url": "https://careers.gatecorp.com/sr-architect",
            "description": "Requires minimum 6+ years of distributed systems and Kubernetes experience.",
            "min_experience_years": 6.0,
            "required_skills": ["Kubernetes", "Go", "Distributed Systems"]
        }
    )
    assert resp_sr.status_code == 201
    sr_data = resp_sr.json()
    assert sr_data["min_experience_years"] == 6.0
    assert "what_they_need" in sr_data

    # Fetch AI Radar recommendations
    resp_recs = await client.get("/api/v1/recommendations?min_score=10", headers=auth_headers)
    assert resp_recs.status_code == 200
    recs = resp_recs.json()

    sr_match = next((r for r in recs if r["job"]["company_name"] == "GateCorp Sr"), None)
    jr_match = next((r for r in recs if r["job"]["company_name"] == "GateCorp Jr"), None)

    assert sr_match is not None, "Senior job should be evaluated and diagnosed"
    assert sr_match["can_apply"] is False, "Candidate with 2 yrs exp MUST NOT be allowed to apply for 6 yr req"
    assert sr_match["experience_matched"] is False
    assert sr_match["candidate_experience_years"] == 2.0
    assert sr_match["required_experience_years"] == 6.0
    assert sr_match["experience_gap_years"] == 4.0
    assert sr_match["ineligibility_reason"] is not None
    assert "6+ years" in sr_match["ineligibility_reason"] or "6 years" in sr_match["ineligibility_reason"]
    assert "Ineligible to apply" in sr_match["ineligibility_reason"]
    assert len(sr_match["what_they_need"]) > 0

    assert jr_match is not None, "Junior job should be evaluated and diagnosed"
    assert jr_match["can_apply"] is True, "Candidate with 2 yrs exp MUST be eligible for 1 yr req"
    assert jr_match["experience_matched"] is True
    assert jr_match["candidate_experience_years"] == 2.0
    assert jr_match["required_experience_years"] == 1.0
    assert jr_match["experience_gap_years"] == 0.0
