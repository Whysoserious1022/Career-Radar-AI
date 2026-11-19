from typing import List, Dict, Any, Optional, Tuple
from app.models.job import Job
from app.models.resume import Resume
from app.models.profile import UserProfile

class RecommendationMatcher:
    """
    Hybrid Retrieval & Deterministic Matching Engine.
    Executes eligibility checks, skill set intersections, multi-resume competition,
    and produces explainable rationales.
    """

    @classmethod
    def evaluate_resume_job_match(cls, resume: Resume, job: Job) -> Dict[str, Any]:
        """
        Evaluates the specific match between a single resume and a job.
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

        # Skill Score calculation
        req_ratio = len(matched_req) / max(len(req_skills), 1) if req_skills else 1.0
        pref_ratio = len(matched_pref) / max(len(pref_skills), 1) if pref_skills else 0.0
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

        # Composite match score for this resume (55% skills, 30% experience, 15% education)
        overall_score = round((skill_score * 0.55) + (exp_score * 0.30) + (edu_score * 0.15), 1)

        return {
            "resume_id": resume.id,
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
    def match_candidate_to_job(
        cls,
        user_profile: Optional[UserProfile],
        resumes: List[Resume],
        job: Job
    ) -> Dict[str, Any]:
        """
        Executes candidate-level recommendation:
        - Evaluates each candidate resume
        - Selects the optimal resume for the job
        - Incorporates candidate profile preferences
        - Generates human-readable rationales
        """
        if not resumes:
            return {
                "composite_score": 0.0,
                "eligibility_status": "ineligible",
                "best_resume_id": None,
                "best_resume_name": None,
                "best_resume_category": None,
                "matched_skills": [],
                "missing_skills": job.required_skills or [],
                "reasons": ["No active resume uploaded for candidate."],
                "resume_evaluations": []
            }

        resume_evals = [cls.evaluate_resume_job_match(r, job) for r in resumes]
        # Sort by overall match descending
        resume_evals.sort(key=lambda x: x["overall_match_score"], reverse=True)
        best_eval = resume_evals[0]

        best_resume = next((r for r in resumes if r.id == best_eval["resume_id"]), None)
        base_score = best_eval["overall_match_score"]

        # Incorporate profile preferences
        reasons = []
        bonus = 0.0

        # 1. Skill alignment rationale
        matched_cnt = len(best_eval["matched_skills"])
        total_req = len(job.required_skills or [])
        reasons.append(
            f"Strong skill alignment: Matches {matched_cnt} key skills ({', '.join(best_eval['matched_skills'][:4]) if matched_cnt else 'None'})."
        )

        # 2. Multi-resume rationale
        reasons.append(
            f"Best resume category match: '{best_eval['resume_category'].upper()}' achieved highest compatibility ({best_eval['overall_match_score']}%)."
        )

        # 3. Work mode compatibility
        if user_profile and user_profile.preferred_work_modes:
            norm_modes = [m.lower() for m in user_profile.preferred_work_modes]
            if job.work_mode.lower() in norm_modes or "remote" in norm_modes:
                bonus += 5.0
                reasons.append(f"Work mode match: {job.work_mode.capitalize()} fits candidate preference.")
            else:
                reasons.append(f"Work mode notice: Role is {job.work_mode.capitalize()}.")

        # 4. Location match
        if user_profile and user_profile.preferred_locations:
            if any(loc.lower() in job.location.lower() for loc in user_profile.preferred_locations):
                bonus += 5.0
                reasons.append(f"Location match: Role is situated in {job.location}.")

        # 5. Experience alignment
        cand_exp = user_profile.years_of_experience if user_profile and user_profile.years_of_experience else best_eval["resume_experience_years"]
        if cand_exp >= (job.min_experience_years or 0.0):
            reasons.append(f"Experience qualified: {cand_exp:.1f} yrs exceeds minimum {job.min_experience_years or 0.0:.1f} yrs.")
        else:
            reasons.append(f"Experience stretch: Requires {job.min_experience_years or 0.0:.1f} yrs (Candidate: {cand_exp:.1f} yrs).")

        # 6. Missing skills gap coaching
        if best_eval["missing_skills"]:
            reasons.append(f"Skill gap to bridge: Consider highlighting {', '.join(best_eval['missing_skills'][:3])}.")

        final_score = min(100.0, round(base_score + bonus, 1))

        # Eligibility threshold
        if final_score >= 70.0 and best_eval["experience_match_score"] >= 70.0:
            status = "eligible"
        elif final_score >= 50.0:
            status = "likely_eligible"
        else:
            status = "unclear"

        return {
            "composite_score": final_score,
            "eligibility_status": status,
            "best_resume_id": best_eval["resume_id"],
            "best_resume_name": best_resume.file_name if best_resume else None,
            "best_resume_category": best_eval["resume_category"],
            "matched_skills": best_eval["matched_skills"],
            "missing_skills": best_eval["missing_skills"],
            "reasons": reasons,
            "resume_evaluations": resume_evals
        }
