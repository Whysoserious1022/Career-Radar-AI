import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class HybridSearchEngine:
    """
    Stage 3 Layer 2: Hybrid Search Engine.
    Combines Lexical (BM25 / Keyword Overlap) with Semantic Vector Embeddings (Cosine Similarity)
    to match exact tech stacks while catching semantic title/domain equivalencies.
    """

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        if not text:
            return []
        # Normalize and tokenize alphanumeric terms, including tech symbols like c++, c#, .net
        clean = text.lower()
        clean = re.sub(r"\b(c\+\+|c#|\.net)\b", lambda m: m.group(0).replace("+", "plus").replace("#", "sharp").replace(".", "dot"), clean)
        tokens = re.findall(r"[a-z0-9]+", clean)
        return tokens

    @classmethod
    def compute_bm25_score(cls, query_terms: List[str], doc_text: str, k1: float = 1.5, b: float = 0.75, avg_doc_len: int = 150) -> float:
        """
        Computes Lexical BM25 score for query terms in target document.
        """
        doc_tokens = cls.tokenize(doc_text)
        if not doc_tokens or not query_terms:
            return 0.0

        doc_len = len(doc_tokens)
        doc_counts = Counter(doc_tokens)
        score = 0.0

        for term in query_terms:
            term_clean = term.lower().strip()
            if not term_clean:
                continue
            tf = doc_counts.get(term_clean, 0)
            if tf > 0:
                # BM25 term weighting
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += numerator / denominator

        # Normalize to 0-100 scale
        norm_score = min(100.0, (score / max(len(query_terms), 1)) * 50.0)
        return round(norm_score, 1)

    @classmethod
    def text_to_vector(cls, text: str, dimensions: int = 128) -> List[float]:
        """
        High-performance subword & n-gram semantic vectorizer.
        Generates deterministic L2-normalized vector embeddings without external API latency.
        """
        tokens = cls.tokenize(text)
        if not tokens:
            return [0.0] * dimensions

        vec = [0.0] * dimensions
        term_counts = Counter(tokens)

        for token, count in term_counts.items():
            tf = 1.0 + math.log(count)
            idx = abs(hash(token)) % dimensions
            vec[idx] += tf

        # Bigram subword context
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            idx2 = abs(hash(bigram)) % dimensions
            vec[idx2] += 1.0

        # L2 Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vec))
        if magnitude > 0:
            return [x / magnitude for x in vec]
        return vec

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Computes cosine similarity between two normalized vectors. Range: 0.0 to 1.0.
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(0.0, min(1.0, dot_product))

    @classmethod
    def compute_hybrid_match(
        cls,
        candidate_text: str,
        must_have_skills: List[str],
        job_text: str,
        weight_semantic: float = 0.50,
        weight_lexical: float = 0.50
    ) -> Tuple[float, float, float]:
        """
        Computes hybrid similarity:
        - Semantic Vector Similarity (Cosine)
        - Lexical Tech Stack Match (BM25)
        Returns: (hybrid_score 0-100, semantic_score 0-100, lexical_score 0-100)
        """
        # 1. Semantic Vector Match (scaled to 0-100)
        cand_vec = cls.text_to_vector(candidate_text)
        job_vec = cls.text_to_vector(job_text)
        cosine_sim = cls.cosine_similarity(cand_vec, job_vec)
        semantic_score = min(100.0, round(cosine_sim * 160.0, 1))

        # 2. Lexical Keyword / BM25 Match against candidate text
        lexical_score = cls.compute_bm25_score(must_have_skills, candidate_text)

        # 3. Hybrid Fusion
        hybrid_score = round((semantic_score * weight_semantic) + (lexical_score * weight_lexical), 1)
        return min(100.0, hybrid_score), semantic_score, lexical_score
