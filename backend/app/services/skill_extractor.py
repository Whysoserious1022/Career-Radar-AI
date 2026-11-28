import re
from typing import List, Dict, Set, Tuple

# Comprehensive taxonomy categorized by domain
TAXONOMY: Dict[str, List[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "golang", "go",
        "rust", "ruby", "scala", "kotlin", "swift", "php", "sql", "r", "bash", "shell", "dart"
    ],
    "frameworks": [
        "fastapi", "django", "flask", "react", "next.js", "nextjs", "vue", "angular",
        "node.js", "nodejs", "express", "spring boot", "spring", "asp.net", "pytorch",
        "tensorflow", "scikit-learn", "keras", "hugging face", "huggingface", "transformers", "langchain",
        "llamaindex", "tailwind", "redux", "celery", "graphql", "rest"
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "dynamodb",
        "cassandra", "elasticsearch", "pgvector", "pinecone", "chromadb", "weaviate",
        "qdrant", "milvus", "neo4j", "oracle", "snowflake", "bigquery"
    ],
    "cloud_devops": [
        "aws", "amazon web services", "azure", "gcp", "google cloud", "docker",
        "kubernetes", "terraform", "helm", "ci/cd", "github actions", "gitlab ci",
        "jenkins", "prometheus", "grafana", "ansible", "linux", "nginx", "kafka", "rabbitmq"
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "llm", "large language models", "generative ai", "genai",
        "rag", "retrieval augmented generation", "vector search", "fine-tuning",
        "embeddings", "cross-encoder", "reinforcement learning"
    ],
    "data_engineering": [
        "apache spark", "spark", "apache kafka", "airflow", "dbt", "databricks",
        "pandas", "numpy", "etl", "data pipeline", "data warehousing"
    ],
    "practices": [
        "microservices", "system design", "distributed systems", "agile", "scrum",
        "unit testing", "tdd", "integration testing", "oop", "clean architecture"
    ]
}

# Synonyms and alias mappings to canonical names
CANONICAL_SKILL_MAP: Dict[str, str] = {
    "golang": "Go",
    "go": "Go",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "rust": "Rust",
    "sql": "SQL",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "react": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "spring boot": "Spring Boot",
    "spring": "Spring Boot",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "pgvector": "pgvector",
    "pinecone": "Pinecone",
    "chromadb": "ChromaDB",
    "qdrant": "Qdrant",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "linux": "Linux",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "airflow": "Apache Airflow",
    "dbt": "dbt",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "large language models": "LLMs",
    "llm": "LLMs",
    "generative ai": "Generative AI",
    "genai": "Generative AI",
    "rag": "RAG",
    "vector search": "Vector Search",
    "microservices": "Microservices",
    "system design": "System Design",
    "distributed systems": "Distributed Systems"
}

def extract_skills_from_text(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Extracts canonical skills from raw text using boundary matching.
    Returns:
        (unique_canonical_skills_list, categorized_skills_dict)
    """
    if not text:
        return [], {}
    
    text_lower = text.lower()
    found_canonical: Set[str] = set()
    categorized: Dict[str, List[str]] = {}

    for category, skill_terms in TAXONOMY.items():
        matched_in_cat: Set[str] = set()
        for term in skill_terms:
            # Special regex handling for terms with punctuation like c++, c#, .net, next.js
            escaped = re.escape(term)
            if term in ["c++", "c#", "r"]:
                # Custom boundary for short/special symbols
                pattern = rf"(?:^|[\s,;/()\[\]]){escaped}(?:[\s,;/()\[\].]|$)"
            elif term == "go":
                # Ensure Go doesn't match 'good', 'going', etc.
                pattern = r"(?:^|[\s,;/()\[\]])(?:golang|go)(?:[\s,;/()\[\].]|$)"
            else:
                pattern = rf"\b{escaped}\b"

            if re.search(pattern, text_lower):
                canonical = CANONICAL_SKILL_MAP.get(term, term.capitalize())
                found_canonical.add(canonical)
                matched_in_cat.add(canonical)

        if matched_in_cat:
            categorized[category] = sorted(list(matched_in_cat))

    return sorted(list(found_canonical)), categorized

def extract_experience_requirement(text: str, title: str = "") -> float:
    """
    Extracts the minimum years of experience required from job description text or title.
    Supports patterns such as:
      - "5+ years of experience", "5+ yrs experience"
      - "minimum of 3 years", "min 4 yrs"
      - "at least 6 years", "3-5 years" (takes 3.0)
      - "7+ years hands-on experience"
    Falls back to intelligent title seniority heuristics if not explicitly specified.
    """
    if not text and not title:
        return 1.5

    clean_text = text.lower() if text else ""
    clean_title = title.lower() if title else ""

    # Pattern 1: Minimum / at least X years
    m = re.search(r'(?:at\s+least|minimum\s+of|min\.?\s+of|minimum|min\.?)\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs)', clean_text)
    if m:
        try:
            val = float(m.group(1))
            if 0.5 <= val <= 25.0:
                return val
        except ValueError:
            pass

    # Pattern 2: Range "X-Y years" or "X to Y years" -> take lower bound
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)\s+(?:of\s+)?(?:experience|exp|industry|software|engineering|hands-on)', clean_text)
    if m:
        try:
            val = float(m.group(1))
            if 0.5 <= val <= 25.0:
                return val
        except ValueError:
            pass

    # Pattern 3: "X+ years of experience" or "X+ yrs"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:\+)\s*(?:years|yrs)(?:\s+of)?(?:\s+(?:professional|work|industry|software|engineering|hands-on|relevant))?\s+experience', clean_text)
    if m:
        try:
            val = float(m.group(1))
            if 0.5 <= val <= 25.0:
                return val
        except ValueError:
            pass

    # Pattern 4: Generic "X years experience"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:years|yrs)\s+(?:of\s+)?experience', clean_text)
    if m:
        try:
            val = float(m.group(1))
            if 0.5 <= val <= 25.0:
                return val
        except ValueError:
            pass

    # Fallback heuristics based on title seniority
    if any(k in clean_title for k in ["distinguished", "fellow", "vp", "director"]):
        return 10.0
    if any(k in clean_title for k in ["principal", "staff"]):
        return 7.0
    if any(k in clean_title for k in ["lead", "architect", "tech lead"]):
        return 5.0
    if any(k in clean_title for k in ["senior", "sr.", "sr "]):
        return 4.0
    if any(k in clean_title for k in ["junior", "jr.", "jr ", "entry", "associate", "intern", "new grad", "graduate"]):
        return 0.5
    
    return 2.0


def extract_requirements_checklist(
    description: str,
    title: str = "",
    required_skills: Optional[List[str]] = None,
    min_exp: float = 0.0,
    work_mode: str = "remote"
) -> List[str]:
    """
    Synthesizes the core 'What They Need' requirements checklist for a role.
    """
    checklist = []
    
    # 1. Experience requirement
    if min_exp > 0:
        checklist.append(f"Experience: Minimum {min_exp:g}+ years professional experience required")
    else:
        checklist.append("Experience: Open to all experience levels (Entry / Early Career)")

    # 2. Must-have technical skills
    skills = required_skills or []
    if skills:
        top_skills = ", ".join(skills[:5])
        checklist.append(f"Core Tech Stack: {top_skills}")

    # 3. Work mode & location
    mode_str = work_mode.capitalize() if work_mode else "Remote"
    checklist.append(f"Work Arrangement: {mode_str} eligibility")

    # 4. Detect degree/education requirement if present
    desc_lower = description.lower() if description else ""
    if "phd" in desc_lower or "ph.d" in desc_lower:
        checklist.append("Education: PhD in Computer Science, AI/ML, or equivalent research background preferred")
    elif "master" in desc_lower or "m.s." in desc_lower or "ms in" in desc_lower:
        checklist.append("Education: Bachelor's or Master's degree in Computer Science or related quantitative field")
    elif "bachelor" in desc_lower or "b.s." in desc_lower or "bs in" in desc_lower:
        checklist.append("Education: Bachelor's degree in CS, Engineering, or equivalent practical experience")

    # 5. Key domain requirement
    if any(k in desc_lower or k in title.lower() for k in ["distributed system", "high throughput", "low latency", "concurrency"]):
        checklist.append("Domain Focus: Distributed systems, high-scale infrastructure & concurrency")
    elif any(k in desc_lower or k in title.lower() for k in ["llm", "transformer", "pytorch", "genai", "rag"]):
        checklist.append("Domain Focus: Frontier LLM pipelines, vector similarity search & AI inference")
    elif any(k in desc_lower or k in title.lower() for k in ["frontend", "ui", "ux", "react", "nextjs", "css"]):
        checklist.append("Domain Focus: High-performance UI, client-side rendering & responsive interfaces")

    return checklist

class SkillExtractor:
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        skills, _ = extract_skills_from_text(text)
        return skills

    @staticmethod
    def extract_skills_categorized(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        return extract_skills_from_text(text)

