import requests
import json
import uuid
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def log_step(num, name, detail=""):
    print(f"\n[STEP {num}] {name}")
    if detail:
        print(f"         {detail}")

def assert_true(cond, msg):
    if not cond:
        print(f"  FAILED: {msg}")
        raise AssertionError(msg)
    print(f"  PASSED: {msg}")

def main():
    print("=" * 80)
    print("CareerRadar AI - Complete Platform End-to-End Feature Verification Suite")
    print(f"Target Live Server: {BASE_URL}")
    print("=" * 80)

    session = requests.Session()

    # 1. System Health Check
    log_step(1, "System Health Check")
    r = session.get(f"{BASE_URL}/health")
    assert_true(r.status_code == 200, f"Health endpoint status is 200")
    data = r.json()
    assert_true(data.get("status") == "healthy", f"Service status is 'healthy'")
    print(f"         Service: {data.get('service')} v{data.get('version')} ({data.get('environment')})")

    # 2. Frontend Delivery
    log_step(2, "Frontend Dashboard Delivery")
    r_fe = session.get(f"{BASE_URL}/")
    assert_true(r_fe.status_code == 200, "Frontend index served at root '/'")
    assert_true("CareerRadar AI" in r_fe.text, "Dashboard HTML contains 'CareerRadar AI'")
    assert_true("Personalized Career Radar" in r_fe.text, "Dashboard contains Radar hero section")

    # 3. Candidate Registration
    log_step(3, "Candidate Registration Flow")
    unique_email = f"candidate_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword2026!"
    payload = {
        "email": unique_email,
        "password": password,
        "full_name": "Dr. Alex Rivera"
    }
    r = session.post(f"{BASE_URL}/api/v1/auth/register", json=payload)
    assert_true(r.status_code == 201, f"User registered successfully (Status 201)")
    auth_data = r.json()
    assert_true("access_token" in auth_data, "RFC 7519 JWT Bearer access token received")
    token = auth_data["access_token"]
    user_id = auth_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"         Registered: {unique_email} (ID: {user_id})")

    # 4. Duplicate Registration Guard
    log_step(4, "Security Guard: Duplicate Email Rejection")
    r_dup = session.post(f"{BASE_URL}/api/v1/auth/register", json=payload)
    assert_true(r_dup.status_code == 400, "Duplicate email rejected with 400 Bad Request")

    # 5. Invalid Password Rejection
    log_step(5, "Security Guard: Invalid Password Rejection")
    r_bad = session.post(f"{BASE_URL}/api/v1/auth/login", json={"email": unique_email, "password": "WrongPassword"})
    assert_true(r_bad.status_code == 401, "Invalid password rejected with 401 Unauthorized")

    # 6. Valid Candidate Login
    log_step(6, "Authentication: Login & Token Issuance")
    r_login = session.post(f"{BASE_URL}/api/v1/auth/login", json={"email": unique_email, "password": password})
    assert_true(r_login.status_code == 200, "Successful candidate authentication")
    assert_true(r_login.json()["email"] == unique_email, "Token email matches candidate")

    # 7. Authenticated User Identity (/auth/me)
    log_step(7, "Identity Verification: Current User (/auth/me)")
    r_me = session.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    assert_true(r_me.status_code == 200, "User identity fetched")
    assert_true(r_me.json()["id"] == user_id, "User ID matches issued token")

    # 8. Candidate Profile Intelligence
    log_step(8, "Candidate Profile Intelligence & Career Preferences")
    profile_update = {
        "full_name": "Dr. Alex Rivera",
        "headline": "Staff AI Platform Engineer & Distributed Systems Architect",
        "years_of_experience": 7.5,
        "preferred_roles": ["Staff AI Engineer", "Principal Backend Architect", "MLOps Lead"],
        "preferred_locations": ["San Francisco, CA", "Seattle, WA", "Remote"],
        "preferred_work_modes": ["hybrid", "remote"],
        "min_salary": 220000.0,
        "expected_salary": 280000.0,
        "degree": "Master of Science",
        "university": "University of Washington",
        "graduation_year": 2017
    }
    r_prof = session.put(f"{BASE_URL}/api/v1/profile/me", json=profile_update, headers=headers)
    assert_true(r_prof.status_code == 200, "Candidate profile preferences updated")
    prof_data = r_prof.json()
    assert_true(prof_data["headline"] == profile_update["headline"], "Headline persisted")
    assert_true(prof_data["years_of_experience"] == 7.5, "Years of experience persisted (7.5)")
    assert_true(len(prof_data["preferred_roles"]) == 3, "Preferred roles persisted (3 roles)")
    assert_true(prof_data["min_salary"] == 220000.0, "Salary preferences persisted ($220k)")

    # 9. Upload SDE Resume
    log_step(9, "Multi-Resume Ingestion & Parsing: SDE Profile")
    sde_resume_text = """
    Alex Rivera, Ph.D.
    Email: alex.rivera@example.com | Phone: +1 (555) 349-2041 | LinkedIn: linkedin.com/in/alexrivera
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 7+ years of experience architecting cloud-native distributed microservices,
    high-throughput streaming pipelines, and enterprise APIs using Python, Go, and C++.
    
    TECHNICAL SKILLS
    Languages: Python, Go, C++, SQL, TypeScript, Bash
    Frameworks & Tools: FastAPI, Docker, Kubernetes, Kafka, gRPC, Terraform
    Databases & Cloud: PostgreSQL, Redis, DynamoDB, AWS, Google Cloud Platform
    
    EXPERIENCE
    Staff Platform Engineer | Apex Cloud Networks
    Jan 2021 - Present
    - Designed and scaled Kubernetes-based distributed streaming services handling 250,000 req/sec with Go and Kafka.
    - Built robust RESTful and gRPC APIs using Python and FastAPI, reducing P99 latency by 45%.
    - Managed automated CI/CD and infrastructure-as-code using Terraform and Docker.
    
    Senior Backend Engineer | CloudScale Labs
    June 2017 - Dec 2020
    - Developed fault-tolerant microservices using Python, C++, and PostgreSQL.
    - Mentored 6 junior engineers and improved integration test coverage from 60% to 94%.
    
    EDUCATION
    Master of Science in Computer Science | University of Washington (2015 - 2017)
    Bachelor of Science in Computer Engineering | Georgia Institute of Technology (2011 - 2015)
    
    CERTIFICATIONS
    AWS Certified Solutions Architect - Professional
    Certified Kubernetes Administrator (CKA)
    """
    files_sde = {'file': ('alex_rivera_sde_resume.txt', sde_resume_text.encode('utf-8'), 'text/plain')}
    r_sde = session.post(f"{BASE_URL}/api/v1/resumes/upload", files=files_sde, data={'category': 'sde'}, headers=headers)
    assert_true(r_sde.status_code == 201, "SDE resume uploaded and parsed")
    sde_res = r_sde.json()
    sde_id = sde_res["id"]
    assert_true(sde_res["category"] == "sde", "Category assigned as 'sde'")
    assert_true(sde_res["extracted_summary"]["skills_count"] >= 10, f"Extracted {sde_res['extracted_summary']['skills_count']} skills")
    assert_true(sde_res["extracted_summary"]["experience_years"] >= 7.0, "Experience calculated accurately (~7+ years)")

    # 10. Upload AI/ML Resume
    log_step(10, "Multi-Resume Ingestion & Parsing: AI/ML Profile")
    ml_resume_text = """
    Alex Rivera - AI/ML Specialist
    Email: alex.rivera@example.com
    
    SUMMARY
    Machine learning specialist focused on deep learning, PyTorch, LLM inference, and vector embeddings.
    
    SKILLS
    Machine Learning: PyTorch, TensorFlow, Scikit-Learn, Hugging Face, Transformers
    Data & Vision: Pandas, NumPy, OpenCV
    Cloud & Ops: MLflow, Docker, AWS
    
    EXPERIENCE
    Machine Learning Engineer | Nova AI Systems
    Feb 2022 - Present
    - Trained transformer-based models and deployed inference microservices using PyTorch and FastAPI.
    - Optimized model quantization and vector embeddings pipelines for retrieval-augmented generation.
    
    EDUCATION
    Master of Science in Computer Science | University of Washington (2015 - 2017)
    """
    files_ml = {'file': ('alex_rivera_aiml_resume.txt', ml_resume_text.encode('utf-8'), 'text/plain')}
    r_ml = session.post(f"{BASE_URL}/api/v1/resumes/upload", files=files_ml, data={'category': 'ai_ml'}, headers=headers)
    assert_true(r_ml.status_code == 201, "AI/ML resume uploaded and parsed")
    ml_res = r_ml.json()
    ml_id = ml_res["id"]
    assert_true(ml_res["category"] == "ai_ml", "Category assigned as 'ai_ml'")

    # 11. Multi-Resume Catalog & Detail
    log_step(11, "Multi-Resume Portfolio Inspection")
    r_list = session.get(f"{BASE_URL}/api/v1/resumes", headers=headers)
    assert_true(r_list.status_code == 200, "Resumes list fetched")
    res_list = r_list.json()
    assert_true(len(res_list) == 2, f"Candidate portfolio contains 2 resumes ({[r['category'] for r in res_list]})")

    # 12. Ground-Truth Feedback & Skill Correction Loop
    log_step(12, "Candidate Human Feedback & Correction Loop")
    corr_payload = {
        "category": "cloud_sde",
        "experience_years": 8.5,
        "skills": ["Python", "Go", "Docker", "Kubernetes", "Kafka", "PostgreSQL", "AWS", "Elasticsearch"]
    }
    r_corr = session.put(f"{BASE_URL}/api/v1/resumes/{sde_id}/corrections", json=corr_payload, headers=headers)
    assert_true(r_corr.status_code == 200, "Resume corrections applied")
    corr_data = r_corr.json()
    assert_true(corr_data["category"] == "cloud_sde", "Category updated to 'cloud_sde'")
    assert_true("Elasticsearch" in corr_data["extracted_data"]["skills"], "Added skill 'Elasticsearch' preserved")

    # 13. Sync Verified Employer Jobs
    log_step(13, "Job Ingestion & Employer ATS Feed Sync")
    r_sync = session.post(f"{BASE_URL}/api/v1/jobs/sync-seeds", headers=headers)
    assert_true(r_sync.status_code == 200, "Sample employer jobs synced")
    synced_jobs = r_sync.json()
    assert_true(len(synced_jobs) >= 6, f"Synced {len(synced_jobs)} verified jobs (Stripe, OpenAI, Databricks, Google...)")

    # 14. Job Search & Filtering: Query
    log_step(14, "Job Discovery: Keyword Search")
    r_search = session.get(f"{BASE_URL}/api/v1/jobs?query=Stripe")
    assert_true(r_search.status_code == 200, "Search by query executed")
    stripe_jobs = r_search.json()
    assert_true(len(stripe_jobs) >= 1 and any(j["company_name"] == "Stripe" for j in stripe_jobs), "Found Stripe job listing")

    # 15. Job Search & Filtering: Work Mode
    log_step(15, "Job Discovery: Work Mode Filter (Remote)")
    r_remote = session.get(f"{BASE_URL}/api/v1/jobs?work_mode=remote")
    assert_true(r_remote.status_code == 200, "Remote jobs filtered")
    remote_jobs = r_remote.json()
    assert_true(len(remote_jobs) >= 1 and all(j["work_mode"] == "remote" for j in remote_jobs), "All returned jobs are Remote")

    # 16. Job Creation & Duplicate Fingerprint Guard
    log_step(16, "Job Ingestion: Custom Job & Canonical Deduplication")
    unique_job_suffix = uuid.uuid4().hex[:6]
    new_job = {
        "company_name": f"Vertex AI Labs {unique_job_suffix}",
        "title": "Senior Cloud Infrastructure Engineer",
        "work_mode": "hybrid",
        "location": "San Francisco, CA",
        "original_url": f"https://vertex.ai/careers/cloud-infra-{unique_job_suffix}?ref=linkedin",
        "description": "Looking for an engineer experienced in Python, Kubernetes, Terraform, and AWS."
    }
    r_new_job = session.post(f"{BASE_URL}/api/v1/jobs", json=new_job)
    assert_true(r_new_job.status_code == 201, "Custom job ingested successfully")
    created_job_data = r_new_job.json()
    assert_true(created_job_data["is_link_verified"] == True, "Job link verified")
    
    # Duplicate ingestion attempt
    r_dup_job = session.post(f"{BASE_URL}/api/v1/jobs", json=new_job)
    assert_true(r_dup_job.status_code == 409, "Duplicate job rejected via SHA-256 canonical hash (409 Conflict)")

    # 17. Automated Job Freshness Verifier
    log_step(17, "Worker: Automated URL Freshness Verifier")
    r_fresh = session.post(f"{BASE_URL}/api/v1/jobs/verify-freshness?limit=5")
    assert_true(r_fresh.status_code == 200, "Freshness verification executed")
    assert_true(r_fresh.json()["verified_count"] > 0, "Jobs verified for live HTTP status")

    # 18. AI Career Radar Recommendations
    log_step(18, "AI Recommendation Radar: Composite Scoring & Explainability")
    r_recs = session.get(f"{BASE_URL}/api/v1/recommendations?limit=10&min_score=30", headers=headers)
    assert_true(r_recs.status_code == 200, "Personalized recommendations computed")
    recs = r_recs.json()
    assert_true(len(recs) >= 3, f"Retrieved {len(recs)} personalized recommendations")
    top_rec = recs[0]
    print(f"         Top Match: {top_rec['job']['company_name']} - {top_rec['job']['title']}")
    print(f"         Composite Score: {top_rec['composite_score']}% ({top_rec['eligibility_status']})")
    print(f"         Optimal Resume: {top_rec['best_resume_name']}")
    print(f"         Matched Skills: {top_rec['matched_skills']}")
    print(f"         Explainability Reasons: {len(top_rec['reasons'])} rationales provided")
    assert_true(top_rec["composite_score"] >= 65.0, "Top recommendation has high match score")
    assert_true(len(top_rec["reasons"]) >= 2, "AI explainability rationales generated")

    # 19. Deep-Dive Multi-Resume Comparison
    log_step(19, "Multi-Resume Matcher: Deep-Dive Comparison")
    target_job_id = top_rec["job_id"]
    r_compare = session.post(f"{BASE_URL}/api/v1/recommendations/match-job/{target_job_id}", headers=headers)
    assert_true(r_compare.status_code == 200, "Deep-dive resume comparison completed")
    compare_data = r_compare.json()
    assert_true("resume_scores" in compare_data, "Resume score comparison returned")
    assert_true(len(compare_data["resume_scores"]) == 2, "Both SDE and AI/ML resumes evaluated side-by-side")

    # 20. Recommendation Feedback
    log_step(20, "AI Feedback Loop: Record User Action")
    r_fb = session.post(
        f"{BASE_URL}/api/v1/recommendations/{top_rec['id']}/feedback",
        json={"feedback_type": "saved", "comments": "Strong alignment with infrastructure goals"},
        headers=headers
    )
    assert_true(r_fb.status_code == 201, "Recommendation feedback saved")

    # 21. Application Tracker: Save Application
    log_step(21, "Application Pipeline: Save Job to Pipeline")
    app_payload = {
        "job_id": target_job_id,
        "resume_id": top_rec["best_resume_id"],
        "status": "saved",
        "notes": "Top AI Radar match. Preparing for referral outreach."
    }
    r_app = session.post(f"{BASE_URL}/api/v1/applications", json=app_payload, headers=headers)
    assert_true(r_app.status_code == 201, "Job tracked in application pipeline")
    app_data = r_app.json()
    app_id = app_data["id"]
    assert_true(app_data["status"] == "saved", "Initial status is 'saved'")

    # 22. Duplicate Application Guard
    log_step(22, "Application Pipeline: Duplicate Guard")
    r_dup_app = session.post(f"{BASE_URL}/api/v1/applications", json=app_payload, headers=headers)
    assert_true(r_dup_app.status_code == 409, "Duplicate tracking prevented with 409 Conflict")

    # 23. List Applications in Pipeline
    log_step(23, "Application Pipeline: List Kanban Cards")
    r_apps_list = session.get(f"{BASE_URL}/api/v1/applications", headers=headers)
    assert_true(r_apps_list.status_code == 200, "Applications fetched")
    assert_true(len(r_apps_list.json()) >= 1, "Tracked application present in list")

    # 24. Advance Application: Saved -> Applied -> Interview
    log_step(24, "Application Pipeline: Stage Progression (Applied & Interview)")
    update_stage = {
        "status": "applied",
        "recruiter_name": "Sarah Jenkins",
        "recruiter_email": "sarah@company.com",
        "notes": "Applied directly with optimal resume selected by CareerRadar AI."
    }
    r_up_app = session.put(f"{BASE_URL}/api/v1/applications/{app_id}", json=update_stage, headers=headers)
    assert_true(r_up_app.status_code == 200, "Application stage advanced to 'applied'")
    assert_true(r_up_app.json()["applied_at"] is not None, "Timestamp 'applied_at' automatically generated")
    
    # Progress to interview
    r_interview = session.put(f"{BASE_URL}/api/v1/applications/{app_id}", json={"status": "interview"}, headers=headers)
    assert_true(r_interview.status_code == 200, "Application stage advanced to 'interview'")
    assert_true(r_interview.json()["status"] == "interview", "Current stage is 'interview'")

    # 25. Remove Application from Pipeline
    log_step(25, "Application Pipeline: Delete Tracked Application")
    r_del_app = session.delete(f"{BASE_URL}/api/v1/applications/{app_id}", headers=headers)
    assert_true(r_del_app.status_code == 204, "Application deleted cleanly (204 No Content)")
    r_check_app = session.get(f"{BASE_URL}/api/v1/applications/{app_id}", headers=headers)
    assert_true(r_check_app.status_code == 404, "Deleted application returns 404 Not Found")

    # 26. Multi-Resume Deletion & Cleanup
    log_step(26, "Multi-Resume Lifecycle: Clean Deletion & File Purge")
    r_del_res = session.delete(f"{BASE_URL}/api/v1/resumes/{ml_id}", headers=headers)
    assert_true(r_del_res.status_code == 204, "AI/ML resume deleted cleanly (204 No Content)")
    r_check_res = session.get(f"{BASE_URL}/api/v1/resumes/{ml_id}", headers=headers)
    assert_true(r_check_res.status_code == 404, "Deleted resume returns 404 Not Found")

    print("\n" + "=" * 80)
    print(" ALL 26 END-TO-END FEATURES IMPLEMENTED AND VERIFIED SUCCESSFULLY! ")
    print("=" * 80)

if __name__ == "__main__":
    main()
