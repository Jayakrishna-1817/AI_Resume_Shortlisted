"""JD Parser Agent — uses Gemini AI to extract structured requirements from raw job description text."""

import json
import os
import re
from agents.llm_client import call_llm

def parse_jd_with_ai(jd_text: str, company_name: str) -> dict:
    """Parse job description using AI."""
    prompt = f"""You are an expert HR assistant. Parse the following Job Description and extract structured information.

Job Description:
{jd_text}

Return a valid JSON object with exactly these fields:
{{
  "role": "exact job title",
  "company": "{company_name}",
  "domain": "primary domain (software_engineering/data_science/machine_learning/devops/design/product_management/marketing/finance/security/mobile/analytics)",
  "required_skills": ["list", "of", "must-have", "skills"],
  "preferred_skills": ["list", "of", "nice-to-have", "skills"],
  "min_experience": <number of years as float>,
  "max_experience": <number or null>,
  "education": "minimum education requirement",
  "key_responsibilities": ["up to 5 key responsibilities"],
  "location": "location or Remote",
  "employment_type": "Full-time/Part-time/Contract"
}}

Return ONLY the JSON. No markdown, no explanation."""

    try:
        raw = call_llm(prompt)
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        parsed["raw_text"] = jd_text
        parsed["company"] = company_name
        return parsed
    except Exception as e:
        print(f"[JD Parser] AI failed: {e}. Using fallback.")
        return parse_jd_fallback(jd_text, company_name)


# ---------------------------------------------------------------------------
# Rule-based fallback — works without any API key
# ---------------------------------------------------------------------------

_SKILL_KEYWORDS = [
    "Python", "Java", "Go", "Golang", "Kotlin", "Swift", "C++", "C#", "JavaScript",
    "TypeScript", "React", "Vue", "Angular", "Node.js", "FastAPI", "Django", "Flask",
    "Spring Boot", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "Ansible", "Jenkins", "CI/CD", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Kafka", "Spark", "Airflow", "dbt", "Snowflake", "BigQuery", "TensorFlow",
    "PyTorch", "Scikit-learn", "NLP", "LLM", "MLflow", "Kubeflow", "MLOps",
    "Pandas", "NumPy", "SQL", "Power BI", "Tableau", "Figma", "Sketch",
    "Machine Learning", "Deep Learning", "Computer Vision", "Transformers",
    "REST APIs", "GraphQL", "Microservices", "Linux", "Git", "Agile", "Scrum",
    "JIRA", "Selenium", "Pytest", "Penetration Testing", "Cybersecurity",
]

_DOMAIN_KEYWORDS = {
    "machine_learning": ["machine learning", "ml", "deep learning", "neural", "ai", "artificial intelligence", "llm", "nlp"],
    "data_science": ["data science", "data scientist", "analytics", "statistical", "data analysis"],
    "data_engineering": ["data engineer", "data pipeline", "etl", "spark", "kafka", "airflow"],
    "devops": ["devops", "sre", "site reliability", "infrastructure", "platform engineer"],
    "cloud": ["cloud", "aws", "azure", "gcp", "kubernetes", "terraform"],
    "frontend": ["frontend", "front-end", "react", "vue", "angular", "ui developer"],
    "backend": ["backend", "back-end", "server-side", "api developer"],
    "software_engineering": ["software engineer", "software developer", "sde", "swe", "full stack"],
    "mobile": ["android", "ios", "mobile developer", "react native", "flutter"],
    "security": ["security engineer", "cybersecurity", "penetration", "soc analyst"],
    "design": ["ux designer", "ui designer", "product designer", "design lead"],
    "product_management": ["product manager", "product owner", "pm ", "head of product"],
    "marketing": ["marketing", "seo", "content", "growth", "brand"],
    "finance": ["finance", "financial analyst", "accounting", "investment"],
    "analytics": ["analyst", "business intelligence", "bi developer", "reporting"],
}


def _detect_domain(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        count = 0
        for kw in keywords:
            # Use word-boundary matching to avoid false positives
            # e.g. 'ai' in 'maintain', 'ml' in 'xml'
            pattern = r'(?<![a-z])' + re.escape(kw) + r'(?![a-z])'
            if re.search(pattern, text_lower):
                count += 1
        scores[domain] = count
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "software_engineering"


def _extract_skills(text: str) -> list:
    found = []
    for skill in _SKILL_KEYWORDS:
        if skill.lower() in text.lower():
            found.append(skill)
    return found


def _extract_experience(text: str) -> float:
    text_lower = text.lower()
    # Check for intern/fresher keywords first
    if any(kw in text_lower for kw in ["intern", "internship", "fresher", "graduate trainee", "current 2027", "current 2026"]):
        return 0.0
        
    patterns = [
        r"(\d+)\+?\s*years?",
        r"(\d+)\s*-\s*(\d+)\s*years?",
        r"minimum\s+(\d+)\s+years?",
        r"at\s+least\s+(\d+)\s+years?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return 2.0


def _extract_education(text: str) -> str:
    text_lower = text.lower()
    if "phd" in text_lower or "doctorate" in text_lower:
        return "PhD"
    if "master" in text_lower or "m.tech" in text_lower or "mba" in text_lower:
        return "Master's Degree"
    if "bachelor" in text_lower or "b.tech" in text_lower or "b.e" in text_lower:
        return "Bachelor's Degree"
    return "Bachelor's Degree"


def _extract_role(text: str) -> str:
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    # 1. Look for explicit "Role Title:" or "Position:" label
    for line in lines[:15]:
        lower = line.lower()
        if ":" in line and any(kw in lower for kw in ["role title", "position", "job title", "role"]):
            candidate = line.split(":", 1)[1].strip().strip('–-').strip()
            if len(candidate) > 3:
                return candidate[:80]
    # 2. Look for a line that reads like a job title
    for line in lines[:8]:
        lower = line.lower()
        if any(kw in lower for kw in ["intern", "engineer", "developer", "scientist", "analyst", "manager", "architect"]):
            # Skip lines that are clearly company/hiring announcements
            if not any(skip in lower for skip in ["is hiring", "we are hiring", "now hiring", "looking for"]):
                return line[:80]
    # 3. Fall back to first meaningful line
    return lines[0][:80] if lines else "Software Engineer"


def parse_jd_fallback(jd_text: str, company_name: str) -> dict:
    """Rule-based JD parser — no API key required."""
    skills = _extract_skills(jd_text)
    # Split into required (first 60%) and preferred (rest)
    split = max(3, int(len(skills) * 0.6))
    required_skills = skills[:split]
    preferred_skills = skills[split:]

    # Extract responsibilities (lines starting with - or bullet)
    resp_lines = []
    for line in jd_text.splitlines():
        stripped = line.strip().lstrip("-•*").strip()
        if len(stripped) > 20 and any(
            kw in stripped.lower() for kw in ["build", "develop", "design", "manage", "lead", "implement", "create", "maintain", "collaborate", "work", "own", "drive", "write", "test", "review", "contribute", "debug", "document"]
        ):
            resp_lines.append(stripped[:120])
        if len(resp_lines) >= 5:
            break

    if not resp_lines:
        resp_lines = ["Develop and maintain software systems", "Collaborate with cross-functional teams"]

    min_exp = _extract_experience(jd_text)

    # Detect employment type
    text_lower = jd_text.lower()
    if "internship" in text_lower or "intern" in text_lower:
        employment_type = "Internship"
    elif "contract" in text_lower or "freelance" in text_lower:
        employment_type = "Contract"
    elif "part-time" in text_lower or "part time" in text_lower:
        employment_type = "Part-time"
    else:
        employment_type = "Full-time"

    # Extract location from text
    location = "Remote / Any"
    loc_patterns = [
        r'location\s*[:\-]?\s*([\w,\s/()]+)',
        r'(?:based in|located in|office in)\s+([\w,\s]+)',
    ]
    for pat in loc_patterns:
        m = re.search(pat, jd_text, re.IGNORECASE)
        if m:
            loc = m.group(1).strip().split('\n')[0].strip()
            if 3 < len(loc) < 60:
                location = loc
                break

    return {
        "role": _extract_role(jd_text),
        "company": company_name,
        "domain": _detect_domain(jd_text),
        "required_skills": required_skills if required_skills else ["Java", "Problem Solving"],
        "preferred_skills": preferred_skills,
        "min_experience": min_exp,
        "max_experience": min_exp + 5,
        "education": _extract_education(jd_text),
        "key_responsibilities": resp_lines,
        "location": location,
        "employment_type": employment_type,
        "raw_text": jd_text,
    }
