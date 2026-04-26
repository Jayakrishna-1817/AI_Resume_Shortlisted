"""Candidate Matcher Agent — multi-factor scoring with full explainability."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
from typing import List, Dict, Tuple
from agents.llm_client import call_llm


_EDU_RANK = {"high_school": 0, "bachelor": 1, "master": 2, "phd": 3}
_EDU_LABEL = {
    "Bachelor's degree": "bachelor",
    "Master's degree": "master",
    "PhD preferred": "phd",
    "High school": "high_school",
}


def _edu_score(jd_edu: str, candidate_edu_level: str) -> float:
    required_level = _EDU_LABEL.get(jd_edu, "bachelor")
    req_rank = _EDU_RANK.get(required_level, 1)
    cand_rank = _EDU_RANK.get(candidate_edu_level, 1)
    if cand_rank >= req_rank:
        return 100.0
    diff = req_rank - cand_rank
    return max(0.0, 100.0 - diff * 30.0)


def _experience_score(jd_min_exp: float, candidate_exp: float) -> float:
    if candidate_exp >= jd_min_exp:
        # Meets requirement — full score with small bonus for seniority
        bonus = min(10.0, (candidate_exp - jd_min_exp) * 2)
        return min(100.0, 85.0 + bonus)
    # Under-experienced — penalty per missing year
    deficit = jd_min_exp - candidate_exp
    return max(0.0, 85.0 - deficit * 20.0)


def _domain_score(jd_domain: str, candidate_domains: List[str]) -> float:
    if jd_domain in candidate_domains:
        return 100.0
    # Check partial overlap in related domains
    related_groups = [
        {"software_engineering", "backend", "frontend", "mobile"},
        {"data_science", "machine_learning", "analytics", "data_engineering", "business_intelligence"},
        {"devops", "cloud", "infrastructure", "security"},
        {"product_management", "design", "project_management"},
        {"marketing", "analytics", "ecommerce"},
        {"finance", "analytics", "banking"},
    ]
    for group in related_groups:
        if jd_domain in group and any(d in group for d in candidate_domains):
            return 60.0
    return 25.0


def _skill_similarity(jd_skills: List[str], candidate_skills: List[str]) -> Tuple[float, List[str], List[str], List[str]]:
    """TF-IDF cosine similarity + matched/missing skill tracking."""
    if not jd_skills:
        return 50.0, [], [], candidate_skills

    jd_set = {s.lower() for s in jd_skills}
    cand_set = {s.lower() for s in candidate_skills}

    matched = [s for s in jd_skills if s.lower() in cand_set]
    missing = [s for s in jd_skills if s.lower() not in cand_set]
    bonus = [s for s in candidate_skills if s.lower() not in jd_set]

    # Jaccard-based base score
    if not jd_set:
        return 50.0, matched, missing, bonus
    jaccard = len(jd_set & cand_set) / len(jd_set | cand_set)

    # TF-IDF boost for richer similarity
    try:
        docs = [" ".join(jd_skills), " ".join(candidate_skills)]
        vec = TfidfVectorizer()
        tfidf_mat = vec.fit_transform(docs)
        cos_sim = cosine_similarity(tfidf_mat[0], tfidf_mat[1])[0][0]
        score = (0.5 * jaccard + 0.5 * cos_sim) * 100.0
    except Exception:
        score = jaccard * 100.0

    return round(min(100.0, score), 2), matched, missing, bonus


def _generate_ai_explanation(jd_parsed: dict, candidate: dict, matched: List[str], missing: List[str]) -> str:
    """Generate a natural language explanation for the match using AI."""
    prompt = f"""
    You are an expert technical recruiter. Explain why this candidate is or isn't a good match for the job.
    
    Job Role: {jd_parsed.get('role')}
    Key Requirements: {', '.join(jd_parsed.get('required_skills', []))}
    
    Candidate Name: {candidate.get('name')}
    Candidate Role: {candidate.get('current_role')} at {candidate.get('current_company')}
    Candidate Experience: {candidate.get('years_experience')} years
    Matched Skills: {', '.join(matched)}
    Missing Skills: {', '.join(missing)}
    
    Provide a concise (2-3 sentences) professional explanation focusing on the most critical match factors.
    """
    try:
        return call_llm(prompt)
    except Exception:
        return f"{candidate.get('name')} is a {candidate.get('current_role')} with {candidate.get('years_experience')} years of experience. They match on {len(matched)} key skills but lack {len(missing)} requirements."

def compute_match_score(jd_parsed: dict, candidate: dict) -> dict:
    """
    Compute multi-dimensional match score with explainability.

    Returns dict with:
      match_score, skill_score, experience_score, domain_score,
      education_score, matched_skills, missing_skills, bonus_skills, explanation
    """
    all_jd_skills = jd_parsed.get("required_skills", []) + jd_parsed.get("preferred_skills", [])
    candidate_skills = candidate.get("skills", [])

    skill_sc, matched, missing, bonus = _skill_similarity(all_jd_skills, candidate_skills)
    exp_sc = _experience_score(jd_parsed.get("min_experience", 2.0), candidate.get("years_experience", 0.0))
    domain_sc = _domain_score(jd_parsed.get("domain", ""), candidate.get("domains", []))
    edu_sc = _edu_score(jd_parsed.get("education", "Bachelor's degree"), candidate.get("education_level", "bachelor"))

    # Weighted combination
    match_score = (
        0.40 * skill_sc +
        0.25 * exp_sc +
        0.20 * domain_sc +
        0.15 * edu_sc
    )

    # Build explanation
    parts = []
    if matched:
        parts.append(f"[Match] Skills: {', '.join(matched[:5])}" + (f" +{len(matched)-5} more" if len(matched) > 5 else ""))
    if missing:
        parts.append(f"[Gap] Missing: {', '.join(missing[:4])}" + (f" +{len(missing)-4} more" if len(missing) > 4 else ""))
    if bonus:
        parts.append(f"[Bonus] Extra skills: {', '.join(bonus[:3])}")

    cand_exp = candidate.get("years_experience", 0)
    jd_exp = jd_parsed.get("min_experience", 0)
    if cand_exp >= jd_exp:
        parts.append(f"[OK] Experience: {cand_exp}yr meets {jd_exp}yr requirement")
    else:
        parts.append(f"[Gap] Experience: {cand_exp}yr vs {jd_exp}yr required")

    if domain_sc == 100:
        parts.append(f"[OK] Domain: exact match ({jd_parsed.get('domain', '')})")
    elif domain_sc >= 60:
        parts.append(f"[Related] Domain: related field")
    else:
        parts.append(f"[Gap] Domain: different field")

    # Generate AI-powered explanation
    ai_explanation = _generate_ai_explanation(jd_parsed, candidate, matched, missing)
    
    # Prepend basic stats to AI explanation
    stats_summary = " | ".join(parts)
    full_explanation = f"{ai_explanation}\n\nTechnical Breakdown: {stats_summary}"

    return {
        "match_score": round(match_score, 2),
        "skill_score": round(skill_sc, 2),
        "experience_score": round(exp_sc, 2),
        "domain_score": round(domain_sc, 2),
        "education_score": round(edu_sc, 2),
        "matched_skills": matched,
        "missing_skills": missing,
        "bonus_skills": bonus,
        "explanation": full_explanation,
    }


def rank_candidates(jd_parsed: dict, candidates: List[dict], top_n: int = 10) -> List[dict]:
    """Score all candidates and return top N sorted by match score."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _score(candidate):
        return {"candidate": candidate, **compute_match_score(jd_parsed, candidate)}

    results = []
    with ThreadPoolExecutor(max_workers=min(len(candidates), 10)) as executor:
        futures = [executor.submit(_score, c) for c in candidates]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]
