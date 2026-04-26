from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ParsedJD(BaseModel):
    role: str
    company: str
    domain: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience: float
    max_experience: Optional[float] = None
    education: str
    key_responsibilities: List[str]
    location: Optional[str] = "Remote/Any"
    employment_type: Optional[str] = "Full-time"
    raw_text: str


class Candidate(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    location: str
    current_role: str
    current_company: str
    years_experience: float
    skills: List[str]
    education: str
    education_level: str   # "high_school", "bachelor", "master", "phd"
    domains: List[str]
    past_roles: List[str]
    bio: str
    available: bool
    availability_note: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    salary_expectation: Optional[str] = None
    notice_period: Optional[str] = None


class MatchResult(BaseModel):
    candidate: Candidate
    match_score: float
    skill_score: float
    experience_score: float
    domain_score: float
    education_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    bonus_skills: List[str]
    explanation: str


class ConversationMessage(BaseModel):
    role: str   # "recruiter" | "candidate"
    content: str


class OutreachResult(BaseModel):
    candidate_id: str
    conversation: List[ConversationMessage]
    interest_score: float
    availability_score: float
    sentiment_score: float
    engagement_score: float
    interest_summary: str
    key_signals: List[str]


class ShortlistedCandidate(BaseModel):
    rank: int
    candidate: Candidate
    match_score: float
    interest_score: float
    combined_score: float
    match_explanation: str
    interest_summary: str
    matched_skills: List[str]
    missing_skills: List[str]
    key_signals: List[str]
    conversation: List[ConversationMessage]


class AnalyzeRequest(BaseModel):
    jd_text: str
    company_name: Optional[str] = "TechCorp"
    top_n: Optional[int] = 10


class AnalyzeResponse(BaseModel):
    parsed_jd: ParsedJD
    shortlist: List[ShortlistedCandidate]
    total_candidates_evaluated: int
    processing_time_seconds: float
    mode: str  # "ai" or "fallback"
