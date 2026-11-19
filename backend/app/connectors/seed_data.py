from typing import List, Dict, Any
from app.connectors.base import BaseJobConnector

SAMPLE_JOBS: List[Dict[str, Any]] = [
    {
        "external_id": "stripe-sde-001",
        "company_name": "Stripe",
        "title": "Senior Software Engineer - Payments Infrastructure",
        "department": "Core Infrastructure",
        "description": "Join Stripe to scale our core global payments processing engine. You will build high-throughput, fault-tolerant distributed transaction systems handling hundreds of billions in financial volume with high availability.",
        "responsibilities": [
            "Architect mission-critical payment services handling millions of operations daily",
            "Optimize latency and reliability across distributed multi-region databases",
            "Collaborate with security and risk teams on financial idempotency"
        ],
        "required_skills": ["Python", "Go", "PostgreSQL", "Kafka", "Distributed Systems", "Docker", "AWS"],
        "preferred_skills": ["Kubernetes", "Redis", "gRPC", "Terraform"],
        "min_experience_years": 5.0,
        "max_experience_years": 10.0,
        "location": "San Francisco, CA",
        "work_mode": "hybrid",
        "employment_type": "full_time",
        "min_salary": 185000.0,
        "max_salary": 260000.0,
        "currency": "USD",
        "original_url": "https://stripe.com/jobs/listings/payments-infra-senior-sde?utm_source=linkedin&gh_src=123",
    },
    {
        "external_id": "openai-mle-002",
        "company_name": "OpenAI",
        "title": "Member of Technical Staff - Machine Learning & RAG Platform",
        "department": "Applied AI",
        "description": "Build high-scale inference infra and retrieval augmented generation pipelines for frontier LLMs. You will optimize tensor parallelism, vector similarity search, and model serving systems.",
        "responsibilities": [
            "Scale low-latency LLM serving engines and GPU scheduling clusters",
            "Design vector search indexing using pgvector and Qdrant",
            "Implement fine-tuning and evaluation harnesses for agentic workflows"
        ],
        "required_skills": ["Python", "PyTorch", "Transformers", "LLM", "Vector Search", "Docker", "FastAPI"],
        "preferred_skills": ["C++", "Kubernetes", "Triton", "LangChain"],
        "min_experience_years": 4.0,
        "max_experience_years": 9.0,
        "location": "San Francisco, CA",
        "work_mode": "onsite",
        "employment_type": "full_time",
        "min_salary": 240000.0,
        "max_salary": 380000.0,
        "currency": "USD",
        "original_url": "https://openai.com/careers/applied-mts-rag?ref=twitter_job_alert",
    },
    {
        "external_id": "databricks-de-003",
        "company_name": "Databricks",
        "title": "Data Platform Engineer - Lakehouse Streaming",
        "department": "Data Engineering",
        "description": "Help craft the future of unified data processing and streaming architectures. You will develop real-time ETL pipelines, Apache Spark kernels, and delta lake query optimizers.",
        "responsibilities": [
            "Develop ultra-reliable real-time data pipelines processing terabytes per hour",
            "Enhance data governance and lineage across distributed Lakehouse nodes",
            "Optimize batch query execution plans and storage formats"
        ],
        "required_skills": ["Python", "Scala", "Spark", "Kafka", "Data Pipeline", "SQL", "AWS"],
        "preferred_skills": ["dbt", "Airflow", "GCP", "Kubernetes"],
        "min_experience_years": 3.0,
        "max_experience_years": 8.0,
        "location": "Seattle, WA",
        "work_mode": "hybrid",
        "employment_type": "full_time",
        "min_salary": 170000.0,
        "max_salary": 245000.0,
        "currency": "USD",
        "original_url": "https://databricks.com/company/careers/data-platform-engineer-streaming?src=crawler",
    },
    {
        "external_id": "google-cloud-devops-004",
        "company_name": "Google",
        "title": "Site Reliability Engineer - Cloud Kubernetes Engine",
        "department": "Google Cloud",
        "description": "Keep Google Cloud services available and performant at planet-scale. Work with engineering teams to automate failure recovery, infrastructure-as-code, and container orchestration.",
        "responsibilities": [
            "Maintain 99.999% reliability across planetary Kubernetes clusters",
            "Write production automation in Go and Python",
            "Conduct blameless postmortems and improve self-healing telemetry"
        ],
        "required_skills": ["Go", "Python", "Kubernetes", "Docker", "Linux", "GCP", "Terraform", "CI/CD"],
        "preferred_skills": ["Prometheus", "Grafana", "Ansible", "C++"],
        "min_experience_years": 4.0,
        "max_experience_years": 10.0,
        "location": "Remote",
        "work_mode": "remote",
        "employment_type": "full_time",
        "min_salary": 180000.0,
        "max_salary": 270000.0,
        "currency": "USD",
        "original_url": "https://careers.google.com/jobs/results/sre-kubernetes-cloud/?utm_campaign=google_jobs",
    },
    {
        "external_id": "netflix-backend-005",
        "company_name": "Netflix",
        "title": "Senior Backend Engineer - Edge & Recommendation API",
        "department": "Consumer Engineering",
        "description": "Design and scale the edge routing layer and personalized discovery APIs that serve 260M+ members globally. You will work on reactive streaming microservices and caching.",
        "responsibilities": [
            "Build high-concurrency API gateways in Java and Go",
            "Implement multi-tier distributed caching architectures using Redis",
            "Collaborate with algorithms teams to deliver sub-50ms recommendation responses"
        ],
        "required_skills": ["Java", "Go", "Redis", "Microservices", "REST", "AWS", "Docker"],
        "preferred_skills": ["Kafka", "GraphQL", "Kubernetes"],
        "min_experience_years": 5.0,
        "max_experience_years": 12.0,
        "location": "Los Gatos, CA",
        "work_mode": "hybrid",
        "employment_type": "full_time",
        "min_salary": 220000.0,
        "max_salary": 350000.0,
        "currency": "USD",
        "original_url": "https://jobs.netflix.com/jobs/edge-backend-engineer-rec?gh_src=netflix_careers",
    },
    {
        "external_id": "anthropic-fullstack-006",
        "company_name": "Anthropic",
        "title": "Full Stack Engineer - Claude Platform & DevTools",
        "department": "Product Platform",
        "description": "Create intuitive, ultra-fast interfaces and backend APIs for developers integrating Claude into production workflows. You will craft both customer-facing dashboards and low-latency APIs.",
        "responsibilities": [
            "Build responsive, modern web applications with Next.js, React, and TypeScript",
            "Develop scalable API endpoints using Python, FastAPI, and PostgreSQL",
            "Design real-time token streaming and prompt evaluation workflows"
        ],
        "required_skills": ["TypeScript", "React", "Python", "FastAPI", "PostgreSQL", "Next.js", "Docker"],
        "preferred_skills": ["Tailwind", "Redis", "AWS", "GraphQL"],
        "min_experience_years": 3.0,
        "max_experience_years": 7.0,
        "location": "San Francisco, CA",
        "work_mode": "hybrid",
        "employment_type": "full_time",
        "min_salary": 175000.0,
        "max_salary": 255000.0,
        "currency": "USD",
        "original_url": "https://anthropic.com/careers/full-stack-engineer-claude-platform",
    }
]

def get_prepared_seed_jobs() -> List[Dict[str, Any]]:
    prepared = []
    for job in SAMPLE_JOBS:
        clean_url = BaseJobConnector.normalize_url(job["original_url"])
        norm_title = BaseJobConnector.normalize_title(job["title"])
        dedup_hash = BaseJobConnector.generate_dedup_hash(clean_url, job["title"], job["company_name"])
        
        item = dict(job)
        item["canonical_url"] = clean_url
        item["normalized_title"] = norm_title
        item["dedup_hash"] = dedup_hash
        item["status"] = "active"
        item["is_link_verified"] = True
        prepared.append(item)
    return prepared
