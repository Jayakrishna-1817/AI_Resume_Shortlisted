import os
import json
import uuid
import re
from pypdf import PdfReader
from agents.llm_client import call_llm

def extract_resume_text(file_path: str) -> str:
    """Extracts text from a PDF or text file."""
    if file_path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t: text += t + "\n"
            return text
        except Exception:
            return ""
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def parse_resume_with_ai(file_path: str) -> dict:
    """Uses AI to parse the resume text into a structured candidate dictionary."""
    text = extract_resume_text(file_path)
    if not text.strip():
        raise ValueError("Could not extract any text from the provided file.")

    prompt = f"""
    You are an expert AI recruiter. Extract the following candidate details from the resume text below.
    Return ONLY a valid JSON object matching this schema exactly, nothing else (no markdown wrapping).
    Schema:
    {{
        "name": "string (Candidate Full Name, or 'Unknown')",
        "email": "string (Extract email address, or 'unknown@email.com')",
        "phone": "string (Extract phone number, or 'Unknown')",
        "location": "string (Extract location, or 'Unknown')",
        "current_role": "string (Most recent job title, or 'Unknown')",
        "current_company": "string (Most recent company, or 'Unknown')",
        "years_experience": number (Total years of experience as a float, e.g. 5.0, estimate if needed),
        "skills": ["string", "string"],
        "education": "string (Highest degree and university, or 'Unknown')",
        "education_level": "string (bachelor, master, phd, or none)",
        "domains": ["string"],
        "bio": "string (A short 1-2 sentence summary of the candidate)"
    }}

    Resume Text:
    {text[:8000]}
    """
    
    try:
        response_text = call_llm(prompt)
        # clean backticks if model ignored instructions
        out = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(out)
        return _enrich_candidate(data)
    except Exception as e:
        print(f"[Resume Parser] AI failed: {e}. Using rule-based fallback.")
        return parse_resume_fallback(text)

def _enrich_candidate(data: dict) -> dict:
    """Add necessary fields for the matching engine."""
    data["id"] = str(uuid.uuid4())[:8]
    data["available"] = True # default true for parsed resumes
    data["salary_expectation"] = "Negotiable"
    data["notice_period"] = "Unknown"
    data["past_roles"] = []
    if "years_experience" not in data: data["years_experience"] = 2.0
    if "skills" not in data: data["skills"] = []
    return data

def parse_resume_fallback(text: str) -> dict:
    """Basic rule-based parsing when all AI models are rate-limited."""
    text_clean = re.sub(r'\s+', ' ', text)
    
    # Simple regex for common fields
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    
    # Try to find name (usually first line)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = lines[0] if lines else "Candidate"
    if len(name) > 40: name = name[:37] + "..."
    
    # Skill extraction
    from agents.jd_parser import _SKILL_KEYWORDS
    found_skills = []
    for s in _SKILL_KEYWORDS:
        if re.search(rf'\b{re.escape(s)}\b', text, re.IGNORECASE):
            found_skills.append(s)

    # Role detection
    role = "Software Engineer"
    for r in ["Developer", "Intern", "Analyst", "Scientist", "Designer", "Manager"]:
        if r.lower() in text_clean.lower():
            role = r
            break

    data = {
        "name": name,
        "email": email_match.group(0) if email_match else "unknown@email.com",
        "phone": phone_match.group(0) if phone_match else "Unknown",
        "location": "Hyderabad, India" if "hyderabad" in text.lower() else "Unknown",
        "current_role": role,
        "current_company": "Unknown",
        "years_experience": 1.0 if "intern" in text.lower() else 3.0,
        "skills": list(set(found_skills[:12])),
        "education": "Bachelor's Degree",
        "education_level": "bachelor",
        "domains": ["software_engineering"],
        "bio": f"Candidate profile extracted via rule-based logic from resume text."
    }
    
    return _enrich_candidate(data)
