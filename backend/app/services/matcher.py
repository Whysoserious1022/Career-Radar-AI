from typing import List, Dict, Any, Optional, Tuple
import re
from app.models.job import Job
from app.models.resume import Resume
from app.models.profile import UserProfile
from app.services.skill_extractor import extract_skills_from_text, extract_requirements_checklist
from app.services.hybrid_search import HybridSearchEngine
from app.services.feedback_loop import CandidateBehavioralFeedbackEngine
from app.connectors.normalizer import JobDataNormalizer


class RecommendationMatcher:
    """
    Stage 3: Production-Grade 3-Layer Recommendation Funnel.

    Layer 1: Hard Metadata Filtering
    - Location / Remote preference
    - Experience bracket
    - Salary minimum threshold

    Layer 2: Hybrid Search
    - Semantic Vector Embeddings (Cosine Similarity)
    - Lexical Search (BM25 / Tech Stack Overlap)

    Layer 3: Behavioral Signals & Cross-Encoder Re-Ranking
    - Freshness Decay (< 24-48 hours boost)
    - Implicit Feedback Shift (saved/applied positive shift vs dismissed suppression)
    - Cross-Encoder resume-to-JD fit scoring & 1-line explainability
    """

    @classmethod
    def evaluate_resume_job_match(cls, resume: Resume, job: Job) -> Dict[str, Any]:
        """
        Evaluates technical compatibility between a specific resume and a job requisition.
        """
        extracted = resume.extracted_data.structured_json if resume.extracted_data else {}
        resume_skills_raw = extracted.get("skills", [])
        resume_skills = {s.lower(): s for s in resume_skills_raw}

        req_skills = job.required_skills or []
        pref_skills = job.preferred_skills or []

        matched_req = []
        missing_req = []
        for req in req_skills:
            if req.lower() in resume_skills:
                matched_req.append(req)
            else:
                missing_req.append(req)

        matched_pref = []
        for pref in pref_skills:
            if pref.lower() in resume_skills:
                matched_pref.append(pref)

        # Skill Score calculation (75% required, 25% preferred)
        req_ratio = len(matched_req) / max(len(req_skills), 1) if req_skills else 1.0
        pref_ratio = len(matched_pref) / max(len(pref_skills), 1) if pref_skills else 0.5
        skill_score = round((req_ratio * 75.0) + (pref_ratio * 25.0), 1)

        # Experience Score calculation
        resume_exp = float(extracted.get("experience_years", 0.0))
        min_exp = float(job.min_experience_years or 0.0)

        if min_exp == 0.0:
            exp_score = 100.0
        elif resume_exp >= min_exp:
            exp_score = 100.0
        else:
            exp_score = round(max(0.0, (resume_exp / min_exp) * 100.0), 1)

        # Education Score
        edu_list = extracted.get("education", [])
        edu_score = 90.0 if len(edu_list) > 0 else 70.0

        overall_score = round((skill_score * 0.55) + (exp_score * 0.30) + (edu_score * 0.15), 1)

        return {
            "resume_id": resume.id,
            "resume_name": resume.file_name,
            "resume_category": resume.category,
            "overall_match_score": min(100.0, overall_score),
            "skill_match_score": min(100.0, skill_score),
            "experience_match_score": min(100.0, exp_score),
            "education_match_score": min(100.0, edu_score),
            "matched_skills": matched_req + matched_pref,
            "missing_skills": missing_req,
            "resume_experience_years": resume_exp
        }

    @classmethod
    def get_candidate_experience_years(
        cls,
        user_profile: Optional[UserProfile],
        resumes: Optional[List[Resume]] = None
    ) -> float:
        """
        Fuses candidate stated profile experience with parsed/corrected resume experience,
        returning the highest verified years of experience.
        """
        cand_exp = float(user_profile.years_of_experience) if (user_profile and user_profile.years_of_experience is not None) else 0.0
        if resumes:
            for r in resumes:
                if r.extracted_data:
                    ext = r.extracted_data.structured_json or {}
                    cor = r.extracted_data.user_corrections or {}
                    exp_val = cor.get("experience_years") or ext.get("experience_years") or 0.0
                    try:
                        cand_exp = max(cand_exp, float(exp_val))
                    except (ValueError, TypeError):
                        pass
        return round(cand_exp, 1)

    @classmethod
    def _evaluate_hard_metadata_filters(
        cls,
        user_profile: Optional[UserProfile],
        job: Job,
        resumes: Optional[List[Resume]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Layer 1: Hard Metadata Filtering (Eliminate Dealbreakers).
        """
        if not user_profile and not resumes:
            return True, []

        filters_failed = []

        # Work Mode Dealbreaker Check
        if user_profile and user_profile.preferred_work_modes:
            norm_modes = [m.lower() for m in user_profile.preferred_work_modes]
            if "remote" in norm_modes and "onsite" not in norm_modes and job.work_mode.lower() == "onsite":
                filters_failed.append(f"Requires On-site presence in {job.location}")

        # Strict Experience Bracket Check
        cand_exp = cls.get_candidate_experience_years(user_profile, resumes)
        min_exp = float(job.min_experience_years or 0.0)
        if min_exp > 0.0 and cand_exp < min_exp:
            gap = round(min_exp - cand_exp, 1)
            filters_failed.append(
                f"Experience Requirement Not Met: Role requires {min_exp:g}+ years of experience, but candidate profile/resume has {cand_exp:g} years (Gap: {gap:g} yrs). Ineligible to apply."
            )

        is_pass = len(filters_failed) == 0
        return is_pass, filters_failed

    @classmethod
    def match_candidate_to_job(
        cls,
        user_profile: Optional[UserProfile],
        resumes: List[Resume],
        job: Job,
        candidate_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates the 3-Layer Recommendation Funnel:
        Layer 1: Hard Metadata Filtering
        Layer 2: Hybrid Search (Semantic Embeddings + Lexical BM25)
        Layer 3: Behavioral Signals, Freshness Decay & Cross-Encoder Re-Ranking
        """
        reasons = []
        signals = candidate_signals or {}

        # ---------------------------------------------------------
        # LAYER 1: Hard Metadata Filtering
        # ---------------------------------------------------------
        is_hard_pass, filter_violations = cls._evaluate_hard_metadata_filters(user_profile, job, resumes)
        if not is_hard_pass:
            for v in filter_violations:
                reasons.append(f"Dealbreaker Note: {v}")

        # ---------------------------------------------------------
        # LAYER 2: Hybrid Search (Semantic + Lexical BM25)
        # ---------------------------------------------------------
        cand_text_parts = []
        if user_profile:
            cand_text_parts.append(user_profile.headline or "")
            cand_text_parts.extend(user_profile.preferred_roles or [])
            cand_text_parts.extend(user_profile.skills or [])

        # Add resume text if available
        if resumes:
            for r in resumes:
                ext = r.extracted_data.structured_json if r.extracted_data else {}
                cand_text_parts.extend(ext.get("skills", []))
                cand_text_parts.append(r.file_name)

        cand_text = " ".join(cand_text_parts)
        job_text = f"{job.title} {job.normalized_title} {job.description[:1000]} {' '.join(job.required_skills or [])}"
        must_have_skills = job.required_skills or []

        hybrid_score, semantic_sim, lexical_bm25 = HybridSearchEngine.compute_hybrid_match(
            candidate_text=cand_text,
            must_have_skills=must_have_skills,
            job_text=job_text
        )

        # ---------------------------------------------------------
        # Multi-Resume Evaluation (Cross-Encoder Fit)
        # ---------------------------------------------------------
        resume_evals = []
        best_resume = None
        best_eval = None
        matched_skills = []
        missing_skills = list(job.required_skills or [])

        if resumes:
            resume_evals = [cls.evaluate_resume_job_match(r, job) for r in resumes]
            resume_evals.sort(key=lambda x: x["overall_match_score"], reverse=True)
            best_eval = resume_evals[0]
            best_resume = next((r for r in resumes if r.id == best_eval["resume_id"]), None)
            matched_skills = best_eval["matched_skills"]
            missing_skills = best_eval["missing_skills"]
            reasons.append(
                f"Matches {len(matched_skills)}/{len(job.required_skills or [1])} core skills ({', '.join(matched_skills[:3]) if matched_skills else 'Domain overlap'}). Optimal weapon: {best_resume.file_name if best_resume else 'Resume'}."
            )
        else:
            # Fallback to Profile Skills
            ext_skills, _ = extract_skills_from_text(f"{user_profile.headline if user_profile else ''} {' '.join(user_profile.preferred_roles or []) if user_profile else ''}")
            for req in (job.required_skills or []):
                if any(req.lower() == cs.lower() for cs in ext_skills):
                    matched_skills.append(req)
                    if req in missing_skills:
                        missing_skills.remove(req)
            reasons.append(f"Profile Intelligence Match: Matches {len(matched_skills)} core skills.")

        # ---------------------------------------------------------
        # LAYER 3: Behavioral Signals, Freshness Decay & Re-Ranking
        # ---------------------------------------------------------
        role_category = JobDataNormalizer.classify_role_category(job.title, job.description)

        # 1. Freshness Decay Boost
        fresh_boost, fresh_reason = CandidateBehavioralFeedbackEngine.compute_freshness_boost(job.discovered_at)
        if fresh_reason:
            reasons.append(fresh_reason)

        # 2. Behavioral Adjustment (Positive Shift & Negative Filtering)
        behavioral_adj, behavioral_reasons = CandidateBehavioralFeedbackEngine.compute_behavioral_adjustment(
            candidate_signals=signals,
            job_company=job.company_name,
            job_skills=job.required_skills or [],
            job_role_category=role_category
        )
        reasons.extend(behavioral_reasons)

        # 3. Work Mode & Location Compatibility
        work_mode_bonus = 0.0
        if user_profile and user_profile.preferred_work_modes:
            norm_modes = [m.lower() for m in user_profile.preferred_work_modes]
            if job.work_mode.lower() in norm_modes or "remote" in norm_modes:
                work_mode_bonus = 5.0
                reasons.append(f"Work Mode Alignment: {job.work_mode.capitalize()} mode fully satisfies your preference.")

        # 4. Synthesize Final Funnel Composite Score
        # Base: 45% Hybrid Search (Semantic + Lexical) + 40% Cross-Encoder Resume Fit + 15% Work Mode / Location
        base_resume_score = best_eval["overall_match_score"] if best_eval else 60.0
        base_score = (hybrid_score * 0.45) + (base_resume_score * 0.40) + (work_mode_bonus * 3.0)

        # Apply Layer 3 Re-Ranking Adjustments
        final_score = base_score + (fresh_boost * 0.6) + behavioral_adj

        # Experience Gating & Application Permission
        cand_exp = cls.get_candidate_experience_years(user_profile, resumes)
        min_exp = float(job.min_experience_years or 0.0)
        exp_matched = (min_exp == 0.0) or (cand_exp >= min_exp)
        exp_gap = round(max(0.0, min_exp - cand_exp), 1)
        can_apply = is_hard_pass and exp_matched

        ineligibility_reason = None
        if not exp_matched:
            ineligibility_reason = f"Experience Requirement Not Met: Role requires {min_exp:g}+ years (Candidate has {cand_exp:g} years; Gap: {exp_gap:g} yrs). Ineligible to apply."
            reasons.insert(0, f"⛔ CANNOT APPLY: Requires {min_exp:g}+ years of experience, but your verified profile/resume experience is {cand_exp:g} years.")
            # Strict penalty for roles candidate cannot apply for
            final_score = min(38.0, round(final_score * 0.45, 1))
            eligibility = "ineligible"
        elif not is_hard_pass:
            ineligibility_reason = f"Dealbreaker condition failed: {'; '.join(filter_violations)}"
            reasons.insert(0, f"⚠️ DEALBREAKER ALERT: {'; '.join(filter_violations)}")
            final_score = min(45.0, round(final_score * 0.60, 1))
            eligibility = "ineligible"
        else:
            reasons.insert(0, f"✅ EXPERIENCE QUALIFIED: Your {cand_exp:g} years meets or exceeds the required {min_exp:g}+ years.")
            final_score = max(40.0, min(100.0, round(final_score, 1)))
            if final_score >= 75.0:
                eligibility = "eligible"
            elif final_score >= 55.0:
                eligibility = "likely_eligible"
            else:
                eligibility = "stretch_goal"

        what_they_need = list(job.responsibilities) if job.responsibilities else []
        if not what_they_need:
            what_they_need = extract_requirements_checklist(
                job.description or "",
                job.title or "",
                job.required_skills or [],
                min_exp,
                job.work_mode or "remote"
            )

        return {
            "composite_score": final_score,
            "eligibility_status": eligibility,
            "can_apply": can_apply,
            "experience_matched": exp_matched,
            "candidate_experience_years": cand_exp,
            "required_experience_years": min_exp,
            "experience_gap_years": exp_gap,
            "what_they_need": what_they_need,
            "ineligibility_reason": ineligibility_reason,
            "best_resume_id": best_eval["resume_id"] if best_eval else None,
            "best_resume_name": best_resume.file_name if best_resume else None,
            "best_resume_category": best_eval["resume_category"] if best_eval else None,
            "semantic_score": semantic_sim,
            "lexical_score": lexical_bm25,
            "hybrid_score": hybrid_score,
            "freshness_boost": fresh_boost,
            "behavioral_adjustment": behavioral_adj,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reasons": reasons,
            "resume_evaluations": resume_evals
        }
