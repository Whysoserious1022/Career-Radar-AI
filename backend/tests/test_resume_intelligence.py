import pytest
import io
from httpx import AsyncClient
from app.services.skill_extractor import extract_skills_from_text
from app.services.resume_parser import ResumeParser

def test_skill_extractor_taxonomy_and_boundaries():
    text = (
        "Experienced software developer skilled in Python, FastAPI, Docker, and PostgreSQL. "
        "Built deep learning pipelines with PyTorch, Hugging Face, and LangChain. "
        "Also proficient in Go and C++, deploying services with Kubernetes on AWS."
    )
    skills, categorized = extract_skills_from_text(text)
    
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills
    assert "PyTorch" in skills
    assert "Hugging Face" in skills
    assert "LangChain" in skills
    assert "Go" in skills
    assert "C++" in skills
    assert "AWS" in skills
    assert "Kubernetes" in skills
    
    # Check categorization
    assert "Python" in categorized.get("languages", [])
    assert "FastAPI" in categorized.get("frameworks", [])
    assert "Docker" in categorized.get("cloud_devops", [])
    assert "PyTorch" in categorized.get("frameworks", []) or "PyTorch" in categorized.get("ai_ml", [])

def test_resume_parser_structured_extraction(tmp_path):
    sample_resume_content = """
    Jane Doe
    jane.doe@example.com | (555) 123-4567 | github.com/janedoe | linkedin.com/in/janedoe

    Summary:
    Dedicated Machine Learning Engineer with 3+ years building production AI services.

    Experience:
    AI Engineer at TechCorp (2021 - Present)
    - Developed high-throughput recommendation engines using PyTorch and FastAPI.
    - Optimized vector search queries over pgvector and Redis.
    
    Software Engineering Intern at StartUp Labs (2020 - 2021)
    - Automated CI/CD pipelines with GitHub Actions and Docker.

    Education:
    Bachelor of Technology in Computer Science (2017 - 2021)
    National Institute of Technology
    
    Projects:
    Generative RAG Assistant:
    Built an enterprise document retrieval system using LangChain, pgvector, and Docker.
    """
    resume_file = tmp_path / "jane_resume.txt"
    resume_file.write_text(sample_resume_content, encoding="utf-8")

    parsed = ResumeParser.parse_resume(str(resume_file))

    assert parsed["contact"]["email"] == "jane.doe@example.com"
    assert parsed["experience_years"] >= 3.0
    assert len(parsed["skills"]) > 0
    assert "PyTorch" in parsed["skills"]
    assert "FastAPI" in parsed["skills"]
    assert "Docker" in parsed["skills"]
    assert parsed["parsed_confidence"] > 0.8
    assert len(parsed["education"]) >= 1

@pytest.mark.asyncio
async def test_multi_resume_api_lifecycle(client: AsyncClient, auth_headers: dict):
    # 1. Upload SDE Resume
    sde_resume_bytes = (
        "John Developer\njohn@example.com\nExperience:\nBackend Engineer (2022 - Present)\nSkills: Python, FastAPI, PostgreSQL, Redis, Docker, Go\nEducation:\nB.S. Computer Science 2022\n"
    ).encode("utf-8")
    
    files_sde = {
        "file": ("sde_resume.txt", io.BytesIO(sde_resume_bytes), "text/plain")
    }
    data_sde = {"category": "sde"}

    resp_sde = await client.post("/api/v1/resumes/upload", files=files_sde, data=data_sde, headers=auth_headers)
    assert resp_sde.status_code == 201
    sde_json = resp_sde.json()
    assert sde_json["category"] == "sde"
    assert sde_json["version"] == 1
    sde_id = sde_json["id"]

    # 2. Upload AI/ML Resume
    aiml_resume_bytes = (
        "John Developer\njohn@example.com\nExperience:\nResearch Engineer (2021 - Present)\nSkills: PyTorch, Hugging Face, LangChain, Python, Vector Search\nEducation:\nB.S. Computer Science 2021\n"
    ).encode("utf-8")
    
    files_aiml = {
        "file": ("aiml_resume.txt", io.BytesIO(aiml_resume_bytes), "text/plain")
    }
    data_aiml = {"category": "aiml"}

    resp_aiml = await client.post("/api/v1/resumes/upload", files=files_aiml, data=data_aiml, headers=auth_headers)
    assert resp_aiml.status_code == 201
    aiml_json = resp_aiml.json()
    assert aiml_json["category"] == "aiml"
    aiml_id = aiml_json["id"]

    # 3. List all user resumes (should contain both SDE and AI/ML resumes)
    list_resp = await client.get("/api/v1/resumes", headers=auth_headers)
    assert list_resp.status_code == 200
    resumes_list = list_resp.json()
    assert len(resumes_list) == 2
    categories = [r["category"] for r in resumes_list]
    assert "sde" in categories
    assert "aiml" in categories

    # 4. Fetch details of single resume
    detail_resp = await client.get(f"/api/v1/resumes/{sde_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail_json = detail_resp.json()
    assert detail_json["file_name"] == "sde_resume.txt"
    assert "Python" in detail_json["extracted_data"]["skills"]

    # 5. Apply user corrections
    corr_payload = {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Kafka", "Kubernetes"],
        "experience_years": 4.0
    }
    corr_resp = await client.put(f"/api/v1/resumes/{sde_id}/corrections", json=corr_payload, headers=auth_headers)
    assert corr_resp.status_code == 200
    updated_data = corr_resp.json()
    assert "Kafka" in updated_data["extracted_data"]["skills"]
    assert updated_data["extracted_data"]["experience_years"] == 4.0

    # 6. Delete resume
    del_resp = await client.delete(f"/api/v1/resumes/{aiml_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # 7. Verify deletion
    list_after = await client.get("/api/v1/resumes", headers=auth_headers)
    assert len(list_after.json()) == 1
