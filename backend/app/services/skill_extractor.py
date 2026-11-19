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
