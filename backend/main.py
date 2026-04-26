"""FastAPI Backend — AI Talent Scouting Agent API."""

import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from agents.jd_parser import parse_jd_with_ai
from agents.candidate_matcher import rank_candidates
from agents.conversation_agent import simulate_outreach
from agents.resume_parser import parse_resume_with_ai
from agents.email_sender import send_outreach_email
from data.candidates import CANDIDATES as MOCK_CANDIDATES

app = FastAPI(
    title="AI Talent Scouting Agent",
    description="Automated recruiter: JD parsing → candidate matching → conversational outreach → ranked shortlist",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory candidate pool (initialized with mock data)
CANDIDATES = list(MOCK_CANDIDATES)

class AnalyzeRequest(BaseModel):
    jd_text: str
    company_name: Optional[str] = "TechCorp"
    top_n: Optional[int] = 8

class EmailRequest(BaseModel):
    candidate: dict
    jd: dict
    custom_message: Optional[str] = None

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Talent Scouting Agent is running"}

@app.get("/api/candidates")
def get_candidates():
    """Return the full candidate pool."""
    return {"count": len(CANDIDATES), "candidates": CANDIDATES}

@app.post("/api/upload-resumes")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Parses uploaded resumes using AI and adds them to the candidate pool."""
    global CANDIDATES
    results = []
    for file in files:
        try:
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp:
                content = await file.read()
                temp.write(content)
                temp_path = temp.name
            
            # Parse using Gemini
            candidate_data = parse_resume_with_ai(temp_path)
            CANDIDATES.append(candidate_data)
            results.append({"filename": file.filename, "status": "success", "candidate": candidate_data})
            
            # Clean up
            os.remove(temp_path)
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "message": str(e)})

    return {"message": f"Processed {len(files)} resumes", "results": results}

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """
    Full pipeline:
    1. Parse JD (Gemini AI or rule-based fallback)
    2. Match + score all candidates
    3. Simulate conversational outreach for top matches
    4. Return ranked shortlist with Match + Interest scores
    """
    if not req.jd_text or len(req.jd_text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Please provide a more detailed job description (min 30 chars).")

    if not CANDIDATES:
        raise HTTPException(status_code=400, detail="Candidate pool is empty. Please upload resumes first.")

    start = time.time()
    mode = "ai"

    # Step 1: Parse JD
    try:
        jd_parsed = parse_jd_with_ai(req.jd_text.strip(), req.company_name or "TechCorp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD parsing failed: {str(e)}")

    # Step 2: Match candidates
    top_n = min(req.top_n or 8, len(CANDIDATES))
    top_matches = rank_candidates(jd_parsed, CANDIDATES, top_n=top_n)

    # Step 3: Simulate outreach for ALL candidates in parallel
    def _process_match(rank_idx_match):
        rank_idx, match = rank_idx_match
        candidate = match["candidate"]
        outreach = simulate_outreach(candidate, jd_parsed)
        combined = round(0.60 * match["match_score"] + 0.40 * outreach["interest_score"], 2)
        return {
            "rank": rank_idx + 1,
            "candidate": candidate,
            "match_score": match["match_score"],
            "interest_score": outreach["interest_score"],
            "combined_score": combined,
            "skill_score": match["skill_score"],
            "experience_score": match["experience_score"],
            "domain_score": match["domain_score"],
            "education_score": match["education_score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "bonus_skills": match["bonus_skills"],
            "match_explanation": match["explanation"],
            "interest_summary": outreach["interest_summary"],
            "key_signals": outreach["key_signals"],
            "conversation": outreach["conversation"],
            "availability_score": outreach["availability_score"],
            "sentiment_score": outreach["sentiment_score"],
            "engagement_score": outreach["engagement_score"],
        }

    shortlist = []
    with ThreadPoolExecutor(max_workers=min(top_n, 8)) as executor:
        futures = {executor.submit(_process_match, item): item for item in enumerate(top_matches)}
        for future in as_completed(futures):
            shortlist.append(future.result())

    shortlist.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, item in enumerate(shortlist):
        item["rank"] = i + 1

    elapsed = round(time.time() - start, 2)

    return {
        "parsed_jd": jd_parsed,
        "shortlist": shortlist,
        "total_candidates_evaluated": len(CANDIDATES),
        "processing_time_seconds": elapsed,
    }

@app.post("/api/send-email")
def send_email(req: EmailRequest):
    """Sends a real email to the candidate."""
    try:
        result = send_outreach_email(req.candidate, req.jd, req.custom_message)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"status": "success", "message": result["message"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/api/parse-jd")
def parse_jd_only(req: AnalyzeRequest):
    """Parse only the JD and return structured output."""
    jd_parsed = parse_jd_with_ai(req.jd_text.strip(), req.company_name or "TechCorp")
    return jd_parsed
