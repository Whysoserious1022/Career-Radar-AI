# CareerRadar AI 🚀
### Production-Grade AI Job Discovery, Recommendation & Career Intelligence Platform

CareerRadar AI is an intelligent career discovery and application intelligence platform. It continuously monitors verified employer sources, extracts structured requirements, normalizes candidate profiles across multi-category resumes, executes deterministic eligibility checks alongside hybrid dense/sparse retrieval, and delivers explainable recommendations with optimal resume selection.

---

## 🏗️ Architecture & Features Implemented (Phase 1)

1. **Enterprise Security & Authentication**:
   - Secure BCrypt (12 rounds) password hashing.
   - Standard RFC 7519 JWT Bearer access token generation and validation.
   - Active account enforcement and role-based controls.
2. **Comprehensive Candidate Profile Intelligence**:
   - Dynamic profile modeling (headline, experience, graduation year, degree, target compensation, remote/hybrid preferences, target locations).
   - Multi-role career trajectory tracking.
3. **Multi-Resume Management & Parser Engine**:
   - Support for PDF, DOCX, and TXT resume uploads.
   - SHA-256 content deduplication and integrity check.
   - Dedicated categorization (e.g. SDE, AI/ML, Data Engineering, DevOps).
   - Zero-external-binary DOCX parser (XML traversal) and native PDF stream parser.
   - Structured section extraction (contact info, timeline-based experience duration calculation, education cohort, projects, certifications).
4. **Canonical Skill Extractor & Taxonomy**:
   - Boundary-aware pattern matching preventing false positives (e.g. `C++`, `Go`, `R`).
   - Categorized taxonomies across languages, frameworks, databases, cloud, DevOps, and AI/ML.
   - User correction loop preserving ground-truth candidate edits.

---

## 🧪 Testing & Execution Evidence

The backend test suite runs fully asynchronous tests over an in-memory SQLite database via `aiosqlite`:

```bash
cd backend
python -m pytest tests -v
```

### Execution Results:
```
tests/test_auth_and_profile.py::test_register_and_login_flow PASSED      [ 20%]
tests/test_auth_and_profile.py::test_candidate_profile_management PASSED [ 40%]
tests/test_resume_intelligence.py::test_skill_extractor_taxonomy_and_boundaries PASSED [ 60%]
tests/test_resume_intelligence.py::test_resume_parser_structured_extraction PASSED [ 80%]
tests/test_resume_intelligence.py::test_multi_resume_api_lifecycle PASSED [100%]

============================== 5 passed in 2.25s ==============================
```

---

## 🏃 Local Development Quickstart

1. **Set Up Python Environment**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Backend Server**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```
3. **Inspect Interactive API Docs**:
   - Swagger UI: `http://localhost:8000/docs`
   - OpenAPI Schema: `http://localhost:8000/openapi.json`
