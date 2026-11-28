# CareerRadar AI 🚀
### Intelligent Job Discovery, Multi-Resume Intelligence & Career Recommendation Engine

**CareerRadar AI** is a production-grade, end-to-end job discovery and career tracking platform. It ingests authentic, live requisitions directly from 73+ tech employer career boards (Ashby, Greenhouse, Lever) and targeted on-demand web scrapers with zero third-party aggregator APIs, parses role-tailored resumes (SDE, AI/ML, DevOps), computes explainable match recommendations, and streamlines applications with 1-click apply and automated pipeline tracking.

---

## 🌟 Key Features

### 1. 🏢 Authentic Tech ATS Ingestion & On-Demand Web Scraper
- **On-Demand Career Page Web Scraper (`POST /api/v1/jobs/scrape-url`)**:
  - Paste **ANY** career portal, ATS board, or company webpage URL (e.g., `https://jobs.ashbyhq.com/openai`, `https://boards.greenhouse.io/cloudflare`, `https://jobs.lever.co/palantir`, `https://careers.google.com/...`, `company.com/careers`).
  - Automatically crawls the page, parses Schema.org `JobPosting` JSON-LD microdata, extracts job postings, maps skills via NLP taxonomy, deduplicates, and commits to the database.
  - When authenticated, **immediately computes real-time candidate fit scores and rationales** for every scraped role!
- **Universal Multi-Source Scraper (`POST /api/v1/jobs/sync-all-sources`)**: Orchestrates parallel real-time scraping across 73+ official employer career portals and ATS boards directly.
- **Direct Employer ATS Connectors (73+ Tech Giants)**: Ingests live requisitions directly from official career boards across **Ashby**, **Greenhouse**, and **Lever**:
  - **Ashby Boards (20)**: *OpenAI, Perplexity AI, Cursor, Cohere, Character.ai, Replit, Baseten, Modal Labs, Pika Labs, Runway, LangChain, Linear, Ramp, Supabase, Resend, PostHog, Cognition AI (Devin), Cartesia AI, Neon, Vapi*.
  - **Greenhouse Boards (45)**: *Anthropic, Cloudflare, Databricks, Stripe, Figma, GitLab, Datadog, MongoDB, Scale AI, Vercel, Coinbase, Affirm, Toast, Samsara, Reddit, Discord, Dropbox, Elastic, Asana, Duolingo, Lyft, Pinterest, Robinhood, Roblox, Twilio, Airbnb, Okta, Brex, Gusto, Miro, Zapier, Canva, Braze, Klaviyo, Intercom, Checkr, Mercury, Carta, Together AI, Fastly, Cockroach Labs, Netlify, Airtable, Stability AI, Lattice*.
  - **Lever Boards (8)**: *Spotify, Palantir, Netflix, Twitch, Kraken, Plaid, Postman, 1Password*.
  - Every link points directly to authentic, working application forms (e.g. `https://jobs.ashbyhq.com/openai/.../application`, `https://boards.greenhouse.io/cloudflare/jobs/...`, `https://jobs.lever.co/spotify/...`).
- **Canonical URL Normalization & Deduplication**: Cleans tracking queries (`?ref=...`, `?gh_src=...`, `?utm_source=...`) and computes SHA-256 canonical fingerprints to prevent duplicate listings.
- **Link Freshness Verifier**: Background HTTP status verifier to detect expired or closed job listings automatically.

### 2. ⚡ Real-Time Scraper ➔ Quick Diagnosis ➔ AI Radar Funnel
- **Unified Scraper ➔ Radar Diagnosis Pipeline**:
  - The Jobs Directory and AI Radar operate in tight synergy: whenever jobs are scraped (from on-demand URLs, quick picks, or the 73-company catalog), the system runs an automatic **Quick Diagnosis** assessing candidate verified skills and experience against every extracted requisition.
  - Displays a persistent **Real-Time Diagnosis Alert Banner** summarizing total diagnosed jobs, count of Best-Suited eligible roles, and count of experience-gated roles, with a 1-click jump into AI Radar.
- **Automated "What They Need" & Experience Requirements Extraction**:
  - The scraper extracts exact minimum years of experience using specialized regex patterns (`5+ years`, `minimum of 3 years`, `3-5 years`) with seniority fallbacks.
  - Automatically synthesizes a structured **"What They Need & Criteria"** checklist for every role covering: Minimum Experience, Core Tech Stack, Work Arrangement, and Domain/Education requirements.
- **Strict Experience Requirement Gating**:
  - **Deterministic Application Guard**: If a candidate's verified experience is less than the employer's minimum requirement (`cand_exp < min_exp`), the candidate **CANNOT APPLY** for that role.
  - In both the Jobs Directory and AI Radar, the Apply button is locked with a prominent `Cannot Apply` indicator and opens a protective **Ineligible Explanation Modal** showing the exact experience gap to protect the candidate's conversion rate.
- **AI Radar Best-Suited vs. All Roles Filtering**:
  - Toggle seamlessly between **✨ Best-Suited (Eligible)** (default high-conversion view) and **📋 All Diagnosed Roles** (allowing candidates to inspect stretch roles and understand missing qualifications).

### 3. 📄 Multi-Resume Portfolio Intelligence
- **Role-Tailored Resumes**: Manage distinct resumes for different career tracks (e.g., *Frontend*, *Backend SDE*, *AI/ML Engineer*, *DevOps/Cloud*).
- **Native Document Parsers**: Zero-dependency DOCX XML parser, native PDF stream reader, and plain text parser.
- **Automated Structured Extraction**:
  - Boundary-aware skill extractor for 100+ technologies preventing false positives (e.g. `C++`, `Go`, `R`, `Docker`, `PyTorch`).
  - Regex & timeline-based experience duration calculation.
  - Education cohort and degree normalization.
- **Human-in-the-Loop Feedback**: Candidates can edit or add skills and categories to maintain ground-truth accuracy.

### 4. 🎯 Authentic, User-Centric Recommendation Engine
- **Multi-Dimensional Career Fit Index**:
  - **Skills Overlap (40%)**: Verifies exact matches against required & preferred skills.
  - **Role Trajectory (25%)**: Semantic alignment between candidate's desired target roles and the job title.
  - **Experience & Seniority Fit (20%)**: Suitability score matching verified years against minimum/maximum experience requirements.
  - **Work Culture & Mode (10%)**: Remote, hybrid, or onsite alignment with candidate's stated preferences.
  - **Compensation Alignment (5%)**: Checks whether job compensation meets or exceeds candidate's target salary.
- **Profile + Resume Fusion**: Generates tailored recommendations immediately from candidate profile intelligence (even before resume upload) and dynamically scales to 95%+ precision when multi-category resumes are provided.
- **Optimal Resume Weapon Selection**: Automatically identifies which portfolio resume provides the highest competitive match for any specific requisition.
- **Actionable AI Career Coaching & Rationales**:
  - Concrete explanations for why a role fits the candidate's declared target trajectory.
  - Actionable interview preparation tips identifying high-value skill bridges to discuss.
- **Deep Compare Modal**: Evaluates and contrasts all portfolio resumes side-by-side against any job opening.

### 5. ⚡ 1-Click Apply & Kanban Application Pipeline
- **1-Click Apply & Track**: Opens the official employer portal in a new browser tab while simultaneously filing the role into your application tracker.
- **AI Application Pitch Assistant**: Generates role-tailored cover letters / application pitches highlighting matched skills and relevant experience.
- **5-Stage Kanban Tracker**: Seamlessly transition jobs across `Saved` ➔ `Applied` ➔ `Interview` ➔ `Offer` ➔ `Rejected` with automated timestamps.

### 6. 💻 Modern Single-Page Dashboard
- Built with Tailwind CSS and Lucide icons served directly from FastAPI at `/`.
- Responsive layout with 5 primary navigation tabs: **AI Radar**, **Jobs Directory**, **Resumes Portfolio**, **Application Tracker**, and **Candidate Profile**.
- Searchable **73+ Company Catalog Explorer** modal with categorized domain pills (AI/LLMs, Cloud, Fintech, DevTools, Consumer, Enterprise) for one-click ATS scraping.
- Real-time search, categorized multi-company dropdown filtering (73+ verified employers), experience range filter, and work-mode toggle.
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
│   │   │   ├── web_scraper.py       # Deep dynamic career web page scraper
│   │   │   ├── normalizer.py        # Canonical role taxonomy & dedup hash normalizer
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

---

## 🏛️ The 4-Stage Production Pipeline Architecture

CareerRadar AI operates on a robust, multi-stage pipeline designed for high-throughput ingestion, zero duplicate clutter, sub-second hybrid retrieval, and continuous feedback learning:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: INGESTION                              │
│  • Structured ATS Feeds: Ashby, Greenhouse, Lever (73+ Tech Giants)    │
│  • Targeted / On-Demand Web Scraper: Schema.org JSON-LD & DOM parsing   │
│  • 100% Direct Scrapers: Zero reliance on third-party aggregator APIs   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Raw Requisitions
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               STAGE 2: NORMALIZATION & DEDUPLICATION                   │
│  • Canonical Normalization: Strip tracking parameters (ref, utm, gh)   │
│  • Role Categorization: Classify into ai_ml, backend, frontend, etc.   │
│  • SHA-256 Deduplication Fingerprint: (company + title + city)         │
│  • Link Priority Engine: Prefer direct ATS apply URLs > aggregators    │
│  • Stale Link Verifier: Auto-expire closed requisitions (404 / 410)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Normalized Jobs Database
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│         STAGE 3: THE RECOMMENDATION ENGINE (3-LAYER FUNNEL)            │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Hard Metadata Filtering (Eliminate Dealbreakers)        │  │
│  │ • Work mode preferences (Remote / Hybrid / Onsite)               │  │
│  │ • Experience bracket check (Fused profile + parsed resume years) │  │
│  │ • Minimum compensation thresholds                                │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ Filtered Requisitions            │
│  ┌──────────────────────────────────▼───────────────────────────────┐  │
│  │ Layer 2: Hybrid Search (Semantic + Lexical BM25)                 │  │
│  │ • Semantic Vector Embeddings: Cosine similarity for title/domain  │  │
│  │ • Lexical BM25 Search: Tech stack overlap for must-have skills   │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ Top Candidate Matches            │
│  ┌──────────────────────────────────▼───────────────────────────────┐  │
│  │ Layer 3: Behavioral Re-Ranking & Cross-Encoder Fit               │  │
│  │ • Freshness Decay Boost: +15% (<24h), +8% (<48h) early advantage │  │
│  │ • Implicit Signal Adjustment: Up-rank saved/applied, down-rank   │  │
│  │   dismissed companies, tech stacks, and categories                │  │
│  │ • Cross-Encoder Fit: Match explanation & optimal weapon selection│  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Tailored Matches (> 75%)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               STAGE 4: DELIVERY & THE FEEDBACK LOOP                    │
│  • Multi-Channel Delivery: In-app feed + Instant High-Match Alerts     │
│  • Action Tracking: Log viewed, saved, applied, dismissed with reasons │
│  • Continuous Profile Refinement: Positive vector shift & negative cut │
│  • Dead-Link Cleanup: Immediate re-verifier on user report             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 Key API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/register` | Register new candidate account |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token |
| **Auth** | `GET` | `/api/v1/auth/me` | Fetch currently authenticated user |
| **Profile** | `GET` / `PUT` | `/api/v1/profile` | Read and update candidate preferences |
| **Resumes** | `POST` | `/api/v1/resumes/upload` | Upload & parse resume (PDF, DOCX, TXT) |
| **Resumes** | `GET` | `/api/v1/resumes` | List candidate's resume portfolio |
| **Resumes** | `PUT` | `/api/v1/resumes/{id}/corrections` | Apply human corrections to parsed skills |
| **Resumes** | `DELETE` | `/api/v1/resumes/{id}` | Remove resume and purge extracted data |
| **Jobs** | `GET` | `/api/v1/jobs` | Search & filter jobs by title, company, mode |
| **Jobs** | `POST` | `/api/v1/jobs/scrape-url` | On-demand web scraper for ANY career URL + instant match |
| **Jobs** | `POST` | `/api/v1/jobs/sync-all-sources` | Universal scrape across 73+ tech employer career portals |
| **Jobs** | `POST` | `/api/v1/jobs/sync-authentic-jobs` | Scrape 73+ tech ATS portals (Ashby, Greenhouse, Lever) |
| **Jobs** | `GET` | `/api/v1/jobs/supported-companies` | List all 73+ verified employer career portal catalog |
| **Jobs** | `POST` | `/api/v1/jobs/verify-freshness` | Verify HTTP status of listed job links |
| **Jobs** | `POST` | `/api/v1/jobs/{id}/report-dead-link` | Stage 4 dead-link reporting & immediate URL re-check |
| **Recommendations** | `GET` | `/api/v1/recommendations` | Get personalized recommendations with 4-bar fit index |
| **Recommendations** | `GET` | `/api/v1/recommendations/alerts` | Stage 4 delivery: Instant high-match alerts (>= 75% fit) |
| **Recommendations** | `POST` | `/api/v1/recommendations/match-job/{id}` | Deep-dive compare portfolio resumes for a job |
| **Recommendations** | `POST` | `/api/v1/recommendations/{id}/feedback` | Record candidate signal (`saved`, `dismissed` with reasons) |
| **Applications** | `GET` / `POST` | `/api/v1/applications` | List or track jobs in Kanban pipeline |
| **Applications** | `PUT` | `/api/v1/applications/{id}` | Advance stage (`saved`, `applied`, `interview`, etc.) |
| **Applications** | `DELETE` | `/api/v1/applications/{id}` | Remove job from application tracker |

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
