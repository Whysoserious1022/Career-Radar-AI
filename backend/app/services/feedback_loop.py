import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple

class CandidateBehavioralFeedbackEngine:
    """
    Stage 4: Feedback Loop & Continuous Profile Refinement.
    - Captures implicit signals (viewed, clicked_apply, saved, applied, dismissed).
    - Shifts preference vector toward saved/applied tech stacks and roles.
    - Automatically suppresses or penalizes repeatedly dismissed companies and role categories.
    - Computes freshness decay boosting early opportunities (< 48 hours).
    """

    @classmethod
    def compute_freshness_boost(cls, discovered_at: Optional[datetime]) -> Tuple[float, str]:
        """
        Boosts jobs posted within the last 24-48 hours where early applicants have higher interview rates.
        Returns: (boost_percentage, explanation)
        """
        if not discovered_at:
            return 0.0, ""
        now = datetime.now(timezone.utc)
        if discovered_at.tzinfo is None:
            discovered_at = discovered_at.replace(tzinfo=timezone.utc)
        
        hours_old = max(0.0, (now - discovered_at).total_seconds() / 3600.0)
        if hours_old <= 24.0:
            return 15.0, "🔥 Fresh Role: Discovered within the last 24 hours (Early Applicant Advantage)."
        elif hours_old <= 48.0:
            return 8.0, "⚡ Active Opening: Posted in the last 48 hours."
        elif hours_old <= 168.0:  # 7 days
            return 3.0, ""
        else:
            return 0.0, ""

    @classmethod
    def compute_behavioral_adjustment(
        cls,
        candidate_signals: Dict[str, Any],
        job_company: str,
        job_skills: List[str],
        job_role_category: str
    ) -> Tuple[float, List[str]]:
        """
        Re-ranks roles according to candidate's implicit behavioral history:
        - Positive Shift (+10-20%): Companies/skills the user saved or applied to
        - Negative Suppression (-30-50%): Companies or categories repeatedly dismissed
        """
        score_adj = 0.0
        reasons = []

        saved_companies: Set[str] = set(candidate_signals.get("saved_companies", []))
        applied_companies: Set[str] = set(candidate_signals.get("applied_companies", []))
        dismissed_companies: Set[str] = set(candidate_signals.get("dismissed_companies", []))
        preferred_skills: Set[str] = set(candidate_signals.get("engaged_skills", []))
        dismissed_categories: Set[str] = set(candidate_signals.get("dismissed_categories", []))

        comp_lower = job_company.lower().strip()

        # 1. Positive Signal Shift: Target Company / Engaged Skills
        if comp_lower in applied_companies:
            score_adj += 12.0
            reasons.append(f"Preferred Employer: High interest demonstrated in {job_company}.")
        elif comp_lower in saved_companies:
            score_adj += 8.0
            reasons.append(f"Saved Network: Matches employer from your saved pipeline.")

        # Boost if job required skills overlap with skills candidate frequently applies for
        skill_overlap = [s for s in (job_skills or []) if s.lower() in preferred_skills]
        if len(skill_overlap) >= 2:
            score_adj += 7.0
            reasons.append(f"Behavioral Fit: Focuses on skills you actively target ({', '.join(skill_overlap[:2])}).")

        # 2. Negative Signal Suppression
        if comp_lower in dismissed_companies:
            score_adj -= 25.0
            reasons.append(f"Suppressed: You previously dismissed roles from {job_company}.")

        if job_role_category.lower() in dismissed_categories:
            score_adj -= 20.0
            reasons.append(f"Category Deprioritized: Matches roles you frequently mark as irrelevant.")

        return score_adj, reasons
