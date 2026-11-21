# CareerRadar AI 🚀
### Intelligent Job Discovery, Multi-Resume Intelligence & Career Recommendation Engine

**CareerRadar AI** is a production-grade, end-to-end job discovery and career tracking platform. It ingests authentic, live requisitions directly from tech employer ATS boards (Greenhouse, Lever) and free public job APIs, parses role-tailored resumes (SDE, AI/ML, DevOps), computes explainable match recommendations, and streamlines applications with 1-click apply and automated pipeline tracking.

---

## 🌟 Key Features

### 1. 🏢 Authentic Tech ATS Ingestion & Public Job Scrapers
- **Direct Employer ATS Connectors**: Ingests live requisitions directly from official career boards across **17+ top tech giants** via Greenhouse & Lever APIs:
  - *Cloudflare, Figma, GitLab, Datadog, Reddit, Discord, Dropbox, Elastic, Instacart, Pinterest, Robinhood, Roblox, Twilio, Airbnb, Stripe, Spotify, Palantir*.
  - Every link points directly to authentic, working application forms (e.g. `https://boards.greenhouse.io/cloudflare/jobs/...`, `https://jobs.lever.co/spotify/...`).
- **Free Public Job Board Connectors**: Built-in ingestors for public developer job boards: **Arbeitnow**, **Remotive**, and **Jobicy** (zero API keys required).
- **Canonical URL Normalization & Deduplication**: Cleans tracking queries (`?ref=...`, `?gh_src=...`) and computes SHA-256 canonical fingerprints to prevent duplicate listings.
- **Link Freshness Verifier**: Background HTTP status verifier to detect expired or closed job listings automatically.

### 2. 📄 Multi-Resume Portfolio Intelligence
- **Role-Tailored Resumes**: Manage distinct resumes for different career tracks (e.g., *Frontend*, *Backend SDE*, *AI/ML Engineer*, *DevOps/Cloud*).
- **Native Document Parsers**: Zero-dependency DOCX XML parser, native PDF stream reader, and plain text parser.
- **Automated Structured Extraction**:
  - Boundary-aware skill extractor for 100+ technologies preventing false positives (e.g. `C++`, `Go`, `R`, `Docker`, `PyTorch`).
  - Regex & timeline-based experience duration calculation.
  - Education cohort and degree normalization.
- **Human-in-the-Loop Feedback**: Candidates can edit or add skills and categories to maintain ground-truth accuracy.

### 3. 🎯 AI Recommendation Radar & Explainable Matching
- **Composite Scoring Engine**: Evaluates candidate profile and portfolio against job requirements based on:
  - Skill overlap & density (40%)
  - Experience suitability & role seniority (30%)
  - Work mode & location preference (15%)
  - Education & domain alignment (15%)
- **Optimal Resume Selection**: Automatically identifies which portfolio resume provides the highest competitive match for any specific requisition.
- **Explainable AI Rationales**: Transparent, human-readable bullet points explaining why a role fits the candidate and highlighting key skill overlaps or gaps.
- **Deep Compare Modal**: Evaluates and contrasts all portfolio resumes side-by-side against any job opening.

### 4. ⚡ 1-Click Apply & Kanban Application Pipeline
- **1-Click Apply & Track**: Opens the official employer portal in a new browser tab while simultaneously filing the role into your application tracker.
- **AI Application Pitch Assistant**: Generates role-tailored cover letters / application pitches highlighting matched skills and relevant experience.
- **5-Stage Kanban Tracker**: Seamlessly transition jobs across `Saved` ➔ `Applied` ➔ `Interview` ➔ `Offer` ➔ `Rejected` with automated timestamps.

### 5. 💻 Modern Single-Page Dashboard
- Built with Tailwind CSS and Lucide icons served directly from FastAPI at `/`.
- Responsive layout with 5 primary navigation tabs: **AI Radar**, **Jobs Directory**, **Resumes Portfolio**, **Application Tracker**, and **Candidate Profile**.
- Real-time search, multi-company dropdown filtering (20+ tech giants), experience range filter, and work-mode toggle.
- Clean user-facing design with dev-mode helper available in browser console.

---

## 🏗️ Architecture & Project Structure

```
career-radar-ai/
├── main.py                          # Root entrypoint redirect for uvicorn
├── requirements.txt                 # Python dependencies
├── career_radar.db                  # SQLite database (auto-generated)
├── test_live_app.py                 # 26-step live end-to-end integration test
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application, lifespan handler, routes mount
│   │   ├── api/v1/
│   │   │   ├── auth.py              # JWT authentication & registration
│   │   │   ├── profile.py           # Candidate profile preferences
│   │   │   ├── resumes.py           # Multi-resume upload, parser & corrections
│   │   │   ├── jobs.py              # Job search, ATS sync & freshness checker
│   │   │   ├── recommendations.py   # Recommendation radar & deep resume matcher
│   │   │   └── applications.py      # Kanban application tracker pipeline
│   │   ├── connectors/
│   │   │   ├── base.py              # Base connector, URL canonicalization, dedup hash
│   │   │   ├── ats_connectors.py    # Greenhouse & Lever multi-board scrapers
│   │   │   ├── free_job_apis.py     # Arbeitnow, Remotive & Jobicy connectors
│   │   │   └── seed_data.py         # Seed tech employer requisitions
│   │   ├── core/
│   │   │   ├── config.py            # Application settings & environment
│   │   │   ├── database.py          # SQLAlchemy async session & engine
│   │   │   └── security.py          # BCrypt password hashing & JWT tokens
│   │   ├── models/                  # SQLAlchemy ORM models (User, Profile, Resume, Job, Application)
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── resume_parser.py     # Native PDF, DOCX, TXT document parser
│   │   │   ├── skill_extractor.py   # Canonical skill taxonomy extractor
│   │   │   └── matcher.py           # AI recommendation & multi-resume matcher
│   │   └── workers/
│   │       └── freshness_checker.py # Automated HTTP link verification worker
│   └── tests/                       # Pytest asynchronous unit & component tests
└── frontend/
    └── index.html                   # Modern single-page responsive application
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.10, 3.11, 3.12, 3.14)
- Git

### 2. Clone Repository & Install Dependencies
```bash
git clone https://github.com/your-username/career-radar-ai.git
cd career-radar-ai

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Application Server
You can launch the server using **any** of the following methods from the project root:

```bash
# Standard uvicorn reload command:
uvicorn main:app --reload

# Or directly with Python:
python main.py

# Or pointing to backend package:
uvicorn app.main:app --app-dir backend --reload --port 8000
```

The application will start at:
- 🌐 **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📚 **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🔑 Default Credentials & Developer Console Helper

When the server initializes for the first time, it automatically creates an admin user and verified seed requisitions:

| Role | Email | Password |
|---|---|---|
| **Administrator** | `admin@careerradar.ai` | `AdminPassword2026!` |
| **Demo Candidate** | `demo@careerradar.ai` | `Password123!` |

> **Developer Console Helper**:
> To log in instantly without typing credentials, open the browser DevTools Console (<kbd>F12</kbd>) on the sign-in page and run:
> ```javascript
> window.__devLogin('admin');      // Pre-fills admin credentials
> // or
> window.__devLogin('candidate');  // Pre-fills demo candidate credentials
> ```

---

## 🧪 Testing & Verification Suite

CareerRadar AI includes comprehensive asynchronous test suites covering unit logic, parsers, scoring algorithms, and live end-to-end integration:

### 1. Pytest Unit & Component Suite
Runs 10 asynchronous test suites over in-memory SQLite:
```bash
python -m pytest backend/tests -v
```

**Results:**
```text
backend/tests/test_applications_tracker.py::test_application_lifecycle_and_tracker PASSED  [ 10%]
backend/tests/test_auth_and_profile.py::test_register_and_login_flow PASSED               [ 20%]
backend/tests/test_auth_and_profile.py::test_candidate_profile_management PASSED          [ 30%]
backend/tests/test_jobs_and_connectors.py::test_connector_url_and_hash_normalization PASSED [ 40%]
backend/tests/test_jobs_and_connectors.py::test_job_sync_seeds_and_list PASSED           [ 50%]
backend/tests/test_jobs_and_connectors.py::test_job_creation_and_deduplication PASSED     [ 60%]
backend/tests/test_recommendations_and_matcher.py::test_recommendations_flow_with_multi_resume PASSED [ 70%]
backend/tests/test_resume_intelligence.py::test_skill_extractor_taxonomy_and_boundaries PASSED [ 80%]
backend/tests/test_resume_intelligence.py::test_resume_parser_structured_extraction PASSED [ 90%]
backend/tests/test_resume_intelligence.py::test_multi_resume_api_lifecycle PASSED        [100%]

============================= 10 passed in 2.90s =============================
```

### 2. Live End-to-End Integration Suite
Runs a 26-step automated test against the running live server:
```bash
python test_live_app.py
```

**Verified Capabilities:**
- Full user registration, JWT authentication & profile preference updates.
- Multi-resume upload (SDE & AI/ML), structured parsing, and human-in-the-loop corrections.
- Requisition scraping, canonical URL deduplication (SHA-256 409 rejection), and link verification.
- Recommendation matching, optimal resume selection, and side-by-side deep compare.
- Kanban application tracking lifecycle (`Saved` ➔ `Applied` ➔ `Interview` ➔ `Deleted`).

---

## 📡 Key API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/register` | Register new candidate account |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token |
| **Auth** | `GET` | `/api/v1/auth/me` | Fetch currently authenticated user |
| **Profile** | `GET` / `PUT` | `/api/v1/profile` | Read and update candidate preferences |
| **Resumes** | `POST` | `/api/v1/resumes` | Upload & parse resume (PDF, DOCX, TXT) |
| **Resumes** | `GET` | `/api/v1/resumes` | List candidate's resume portfolio |
| **Resumes** | `PUT` | `/api/v1/resumes/{id}/correct` | Apply human corrections to parsed skills |
| **Jobs** | `GET` | `/api/v1/jobs` | Search & filter jobs by title, company, mode |
| **Jobs** | `POST` | `/api/v1/jobs/sync-authentic-jobs` | Scrape 17+ tech ATS portals (Greenhouse & Lever) |
| **Jobs** | `POST` | `/api/v1/jobs/sync-free-apis` | Scrape Arbeitnow, Remotive & Jobicy APIs |
| **Jobs** | `POST` | `/api/v1/jobs/verify-freshness` | Verify HTTP status of listed job links |
| **Recommendations** | `GET` | `/api/v1/recommendations` | Get personalized recommendations with rationales |
| **Recommendations** | `POST` | `/api/v1/recommendations/match-job/{id}` | Deep-dive compare portfolio resumes for a job |
| **Applications** | `GET` / `POST` | `/api/v1/applications` | List or track jobs in Kanban pipeline |
| **Applications** | `PUT` | `/api/v1/applications/{id}` | Advance stage (`saved`, `applied`, `interview`, etc.) |

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
