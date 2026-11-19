import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register new user
    reg_data = {
        "email": "engineer@careerradar.ai",
        "password": "SecurePassword2026!",
        "full_name": "Jane Engineer"
    }
    response = await client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 201
    res_json = response.json()
    assert "access_token" in res_json
    assert res_json["email"] == "engineer@careerradar.ai"

    # 2. Duplicate registration should fail with 400
    dup_resp = await client.post("/api/v1/auth/register", json=reg_data)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 3. Login with correct credentials
    login_data = {
        "email": "engineer@careerradar.ai",
        "password": "SecurePassword2026!"
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_data)
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Login with invalid password fails with 401
    bad_login = {
        "email": "engineer@careerradar.ai",
        "password": "WrongPassword!"
    }
    bad_resp = await client.post("/api/v1/auth/login", json=bad_login)
    assert bad_resp.status_code == 401

@pytest.mark.asyncio
async def test_candidate_profile_management(client: AsyncClient, auth_headers: dict):
    # 1. Fetch default profile
    get_resp = await client.get("/api/v1/profile/me", headers=auth_headers)
    assert get_resp.status_code == 200
    profile = get_resp.json()
    assert profile["full_name"] == "Test Candidate"

    # 2. Update profile with preferences, skills, and graduation year
    update_payload = {
        "headline": "Senior AI Systems Engineer",
        "graduation_year": 2022,
        "degree": "B.Tech Computer Science",
        "university": "IIT Madras",
        "years_of_experience": 4.5,
        "preferred_roles": ["AI Engineer", "Senior Backend Engineer"],
        "preferred_locations": ["Bengaluru", "Remote"],
        "preferred_work_modes": ["remote", "hybrid"],
        "skills": ["Python", "FastAPI", "PyTorch", "Docker", "PostgreSQL"],
        "min_salary": 2500000.0,
        "expected_salary": 3500000.0,
        "currency": "INR"
    }
    put_resp = await client.put("/api/v1/profile/me", json=update_payload, headers=auth_headers)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["headline"] == "Senior AI Systems Engineer"
    assert updated["graduation_year"] == 2022
    assert updated["years_of_experience"] == 4.5
    assert "PyTorch" in updated["skills"]
    assert "Bengaluru" in updated["preferred_locations"]
