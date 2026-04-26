"""Conversation Agent — simulates recruiter outreach and computes Interest Score."""

import os
import re
import random
import json
from agents.llm_client import call_llm
from typing import List, Dict


# ---------------------------------------------------------------------------
# Conversation builder
# ---------------------------------------------------------------------------

def _recruiter_intro(candidate: dict, jd: dict) -> str:
    return (
        f"Hi {candidate['name'].split()[0]}! I'm reaching out from {jd.get('company', 'our company')}. "
        f"We have an exciting {jd.get('role', 'engineering')} opportunity that I think aligns really well with your background in "
        f"{candidate.get('current_role', 'your field')}. "
        f"The role involves {', '.join(jd.get('key_responsibilities', ['building great products'])[:2])}. "
        f"Would you be open to a quick conversation?"
    )


def _recruiter_followup(candidate: dict, jd: dict) -> str:
    matched = jd.get("required_skills", [])[:3]
    skills_str = ", ".join(matched) if matched else "your core skills"
    return (
        f"Great! The role requires strong expertise in {skills_str}. "
        f"Given your {candidate.get('years_experience', 3)} years of experience, "
        f"you'd be stepping into a senior capacity with ownership over key deliverables. "
        f"The team is small, fast-moving, and the work is genuinely impactful. "
        f"What does your current availability look like, and what would make this a compelling move for you?"
    )


def _generate_candidate_response_ai(candidate: dict, recruiter_msg: str, jd: dict, turn: int) -> str:
    """Use AI to generate a realistic candidate response."""
    available = candidate.get("available", False)
    availability_note = candidate.get("availability_note", "")
    name = candidate["name"].split()[0]

    prompt = f"""You are {candidate['name']}, a {candidate['current_role']} at {candidate['current_company']} with {candidate['years_experience']} years of experience.
Your bio: {candidate['bio']}
Current availability: {"Available - " + availability_note if available else "Not actively looking - " + availability_note}

A recruiter just messaged you:
"{recruiter_msg}"

Write a SHORT, realistic, professional response (2-4 sentences) as {name}.
{"Be genuinely interested and positive." if available else "Be polite but indicate you're not actively looking, though possibly open to very compelling offers."}
Sound like a real person, not a robot. Use natural language."""

    try:
        return call_llm(prompt)
    except Exception:
        return _generate_candidate_response_fallback(candidate, turn)


def _generate_candidate_response_fallback(candidate: dict, turn: int) -> str:
    """Rule-based fallback responses based on availability."""
    name = candidate["name"].split()[0]
    available = candidate.get("available", False)
    note = candidate.get("availability_note", "")

    if available:
        responses_t1 = [
            f"Hi! Thanks for reaching out. Yes, I'm definitely open to exploring new opportunities! {note}. What does the role involve?",
            f"Hello! Great timing actually — {note.lower()}. I'd love to hear more about this position.",
            f"Thanks for thinking of me! I'm actively exploring options right now. Tell me more about the role and the team.",
        ]
        responses_t2 = [
            f"That sounds very interesting! I'm currently on a {candidate.get('notice_period', '30 day')} notice period. The tech stack and the ownership aspect appeal to me. Can we schedule a call?",
            f"I appreciate the detailed breakdown. The {candidate.get('notice_period', '30 day')} notice period works. I'm excited about the scope — let's definitely connect!",
            f"This aligns well with what I'm looking for. I could be available relatively soon. I'm particularly excited about the impact and the tech. Let's move forward!",
        ]
        return random.choice(responses_t1 if turn == 1 else responses_t2)
    else:
        responses_t1 = [
            f"Hi, thanks for reaching out. I'm not actively looking right now, but I'm always open to hearing about exceptional opportunities. What's the role?",
            f"Hello! I'm fairly happy where I am at {candidate['current_company']}, but I don't mind learning more. What makes this role different?",
        ]
        responses_t2 = [
            f"I appreciate the details. Honestly, it would take something quite compelling for me to consider a move — the notice period alone is {candidate.get('notice_period', '60 days')}. But the role does sound interesting. Let me think about it.",
            f"The role sounds solid. I'm not in a rush but I'll be transparent — {note.lower()}. If the compensation and growth trajectory are right, I could potentially consider it.",
        ]
        return random.choice(responses_t1 if turn == 1 else responses_t2)


# ---------------------------------------------------------------------------
# Interest score computation
# ---------------------------------------------------------------------------

_POSITIVE_SIGNALS = [
    "interested", "excited", "love to", "love hearing", "definitely", "great opportunity",
    "open to", "sounds good", "let's connect", "let's talk", "tell me more",
    "move forward", "schedule", "call", "compelling", "align", "perfect timing",
    "actively looking", "exploring", "consider", "yes", "absolutely", "sure",
]

_NEGATIVE_SIGNALS = [
    "not looking", "happy where", "not interested", "no thanks", "pass",
    "not the right time", "committed", "cannot", "unfortunately",
]


def _compute_interest_score_ai(candidate: dict, responses: List[str]) -> Dict:
    """Use AI to analyze the conversation and compute a structured interest score."""
    full_conversation = " ".join(responses)
    
    prompt = f"""
    Analyze the following conversation between a recruiter and a candidate.
    Candidate: {candidate.get('name')} (Currently {candidate.get('available') and 'Available' or 'Not looking'})
    Conversation snippet: {full_conversation}
    
    Evaluate the candidate's genuine interest in the role.
    Return a valid JSON object with:
    {{
        "interest_score": <float 0-100>,
        "sentiment_score": <float 0-100>,
        "engagement_score": <float 0-100>,
        "key_signals": ["list of 3 key signals found"],
        "interest_summary": "1-sentence summary"
    }}
    Return ONLY the JSON.
    """
    
    try:
        raw = call_llm(prompt)
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        
        # Factor in availability manually for robustness
        availability_score = 90.0 if candidate.get("available") else 30.0
        data["interest_score"] = round(0.6 * data["interest_score"] + 0.4 * availability_score, 2)
        data["availability_score"] = availability_score
        
        # Add availability signal if missing
        if candidate.get("available") and "[Available]" not in data["key_signals"]:
            data["key_signals"].insert(0, "[Available] Currently available")
        elif not candidate.get("available") and "[Passive] Not actively looking" not in data["key_signals"]:
            data["key_signals"].insert(0, "[Passive] Not actively looking")
            
        return data
    except Exception as e:
        print(f"Interest AI failed: {e}. Using fallback.")
        return _compute_interest_score_fallback(candidate, responses)


def _compute_interest_score_fallback(candidate: dict, responses: List[str]) -> Dict:
    """Keyword-based fallback interest scoring."""
    full_response = " ".join(responses).lower()
    
    _POSITIVE_SIGNALS = ["interested", "excited", "love to", "open to", "let's connect", "let's talk", "yes"]
    _NEGATIVE_SIGNALS = ["not looking", "happy where", "not interested", "no thanks"]

    # 1. Availability score
    availability_score = 90.0 if candidate.get("available") else 30.0

    # 2. Sentiment
    pos_hits = sum(1 for kw in _POSITIVE_SIGNALS if kw in full_response)
    neg_hits = sum(1 for kw in _NEGATIVE_SIGNALS if kw in full_response)
    sentiment_score = min(100.0, max(0.0, 50.0 + pos_hits * 10 - neg_hits * 20))

    # 3. Engagement
    avg_len = sum(len(r) for r in responses) / max(len(responses), 1)
    engagement_score = min(100.0, avg_len / 2.0)

    interest_score = round(0.4 * availability_score + 0.35 * sentiment_score + 0.25 * engagement_score, 2)

    return {
        "interest_score": interest_score,
        "availability_score": availability_score,
        "sentiment_score": round(sentiment_score, 2),
        "engagement_score": round(engagement_score, 2),
        "key_signals": ["[Fallback] Fallback mode active"] + ([f"[Positive] Positive signals ({pos_hits})"] if pos_hits > 0 else []),
        "interest_summary": "Calculated via fallback logic (AI failed)"
    }


# ---------------------------------------------------------------------------
# Main outreach function
# ---------------------------------------------------------------------------

def simulate_outreach(candidate: dict, jd: dict) -> dict:
    """
    Simulate 2-turn recruiter-candidate conversation.
    Returns conversation + interest score data.
    """
    conversation = []

    # Turn 1: recruiter intro
    msg1 = _recruiter_intro(candidate, jd)
    conversation.append({"role": "recruiter", "content": msg1})

    # Turn 1: candidate response
    resp1 = _generate_candidate_response_ai(candidate, msg1, jd, turn=1)
    conversation.append({"role": "candidate", "content": resp1})

    # Turn 2: recruiter follow-up
    msg2 = _recruiter_followup(candidate, jd)
    conversation.append({"role": "recruiter", "content": msg2})

    # Turn 2: candidate response
    resp2 = _generate_candidate_response_ai(candidate, msg2, jd, turn=2)
    conversation.append({"role": "candidate", "content": resp2})

    candidate_responses = [resp1, resp2]
    scores = _compute_interest_score_ai(candidate, candidate_responses)

    return {
        "candidate_id": candidate["id"],
        "conversation": conversation,
        **scores,
    }
