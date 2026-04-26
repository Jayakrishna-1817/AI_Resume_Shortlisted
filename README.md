# TalentAI — AI-Powered Talent Scouting & Engagement Agent

> Built for **Catalyst Hackathon by Deccan AI** | Submitted by **Sikhakolli Jaya Krishna**

An end-to-end AI agent that fully automates the recruiter workflow:

**JD Input → AI Parsing → Candidate Matching → Conversational Outreach → Ranked Shortlist → Email Outreach**
  
### 🚀 Live Demo & Links
- **Frontend App (Vercel)**: [https://ai-resume-shortlisted.vercel.app/](https://ai-resume-shortlisted.vercel.app/)
- **Backend API (Render)**: [https://ai-resume-shortlisted.onrender.com/docs](https://ai-resume-shortlisted.onrender.com/docs)
- **GitHub Repository**: [https://github.com/Jayakrishna-1817/AI_Resume_Shortlisted](https://github.com/Jayakrishna-1817/AI_Resume_Shortlisted)

---

## What It Does

| Step | Description |
|------|-------------|
| 1. JD Parsing | Extracts structured requirements (role, skills, experience, domain) from any free-form job description using OpenRouter LLMs (Llama 3.3, Gemma, Qwen) with a rule-based fallback |
| 2. Candidate Matching | Multi-factor scoring (Skills, Experience, Domain, Education) with AI-generated natural language explanations for every match |
| 3. Conversational Outreach | Simulates a realistic 2-turn recruiter-to-candidate conversation for each shortlisted candidate, analysed by AI to compute a genuine Interest Score |
| 4. Candidate Registration | Candidates can upload their resumes (PDF or Text). AI parses them and adds them to the live talent pool |
| 5. Ranked Shortlist | Outputs a ranked list sorted by Combined Score (60% Match + 40% Interest), with full score breakdowns and conversation transcripts |
| 6. Email Outreach | Sends AI-drafted personalised outreach emails to candidates via Gmail SMTP |

---

## Quick Start (Local)

### Prerequisites

- Python 3.9+
- Node.js 18+
- An [OpenRouter API Key](https://openrouter.ai/keys) (free tier is sufficient)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create your environment file
copy .env.example .env
```

Edit `.env` and fill in your credentials:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Optional — for AI email drafting
GEMINI_API_KEY=your_gemini_key_here

# Optional — for sending real emails
SMTP_EMAIL=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### 2. Start the Backend

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

- API server: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173

---

## Project Structure

```
Agent/
├── backend/
│   ├── main.py                      # FastAPI app — all routes, parallel processing
│   ├── agents/
│   │   ├── llm_client.py            # Centralised LLM caller — OpenRouter + Gemini + mock fallback
│   │   ├── jd_parser.py             # AI JD parsing + robust rule-based fallback
│   │   ├── candidate_matcher.py     # Multi-factor scoring engine (parallel)
│   │   ├── conversation_agent.py    # Outreach simulation + interest scoring
│   │   ├── resume_parser.py         # PDF/text resume parser (AI + fallback)
│   │   └── email_sender.py          # SMTP email sender with Gemini-drafted body
│   ├── data/
│   │   └── candidates.py            # 25 mock candidate profiles (diverse roles)
│   ├── models/
│   │   └── schemas.py               # Pydantic data models
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                         # Your local secrets (git-ignored)
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # React entry point
│   │   ├── App.jsx                  # Main orchestration — routing, state, API calls
│   │   ├── index.css                # Dark glassmorphism design system
│   │   └── components/
│   │       ├── JDInput.jsx          # JD text input with 3 sample JDs
│   │       ├── ParsedJD.jsx         # Structured JD display panel
│   │       ├── CandidateRow.jsx     # Expandable candidate card with scores + conversation
│   │       └── CandidateRegistration.jsx  # Resume upload UI
│   ├── index.html
│   ├── vite.config.js               # Vite dev server with API proxy
│   └── package.json
└── README.md
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Frontend (React + Vite)                    │
│   JD Input | Steps Bar | Loading View | Shortlist Grid      │
│   ParsedJD | CandidateRow | CandidateRegistration           │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP /api/*  (proxied via Vite)
┌────────────────────────▼─────────────────────────────────────┐
│                  Backend (Python FastAPI)                     │
│                                                              │
│  POST /api/analyze                                           │
│  ┌─────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │  JD Parser  │ → │ Candidate Matcher│ → │ Convo Agent   │  │
│  │  (AI/Rule)  │   │  (Parallel x10) │   │ (Parallel x8) │  │
│  └─────────────┘   └─────────────────┘   └───────────────┘  │
│                                                              │
│  POST /api/upload-resumes    GET /api/candidates             │
│  POST /api/send-email        POST /api/parse-jd              │
└────────────────────────┬─────────────────────────────────────┘
                         │
             ┌───────────▼──────────────┐
             │   LLM Client Layer       │
             │   1. OpenRouter (Llama,  │
             │      Gemma, Qwen, etc.)  │
             │   2. Google Gemini       │
             │   3. Rule-based fallback │
             └──────────────────────────┘
                         │
             ┌───────────▼──────────────┐
             │  Candidate Pool          │
             │  25 mock profiles +      │
             │  uploaded resumes        │
             └──────────────────────────┘
```

---

## Scoring Logic

### Match Score (0–100)

| Factor | Weight | How it's calculated |
|--------|--------|---------------------|
| Skill Similarity | 40% | Hybrid Jaccard + TF-IDF cosine similarity on skill lists |
| Experience | 25% | Candidate years vs JD minimum — bonus for seniority |
| Domain Alignment | 20% | Exact match = 100, related domain = 60, different = 25 |
| Education | 15% | Required level vs candidate level (bachelor/master/PhD) |

**AI Explainability**: Every candidate gets a 2–3 sentence natural language explanation generated by the LLM describing exactly why they fit or don't fit.

### Interest Score (0–100)

| Factor | Weight | How it's calculated |
|--------|--------|---------------------|
| Availability | 40% | Actively looking = 90, passive = 30 |
| AI Sentiment | 40% | LLM analyses candidate's conversation tone and positivity |
| Engagement | 20% | Response depth — length and specificity of answers |

### Combined Score

```
Combined Score = 0.60 × Match Score + 0.40 × Interest Score
```

Candidates are ranked by Combined Score (descending). Ties are broken by Match Score.

---

## API Reference

### POST `/api/analyze` — Full Pipeline

Runs the complete JD parsing → matching → outreach → ranking pipeline.

**Request:**
```json
{
  "jd_text": "Senior Java Engineer with 4+ years...",
  "company_name": "AutoRABIT",
  "top_n": 8
}
```

**Response:**
```json
{
  "parsed_jd": {
    "role": "Senior Java Engineer",
    "company": "AutoRABIT",
    "domain": "software_engineering",
    "required_skills": ["Java", "Spring Boot", "Docker"],
    "preferred_skills": ["Kubernetes", "AWS"],
    "min_experience": 4.0,
    "education": "Bachelor's Degree",
    "location": "Hyderabad / Remote",
    "employment_type": "Full-time",
    "key_responsibilities": ["Design scalable backend APIs", "..."]
  },
  "shortlist": [
    {
      "rank": 1,
      "candidate": {
        "name": "Rohit Gupta",
        "current_role": "Backend Engineer",
        "current_company": "Flipkart",
        "years_experience": 6,
        "location": "Hyderabad",
        "available": true,
        "email": "rohit@example.com"
      },
      "match_score": 87.4,
      "interest_score": 79.2,
      "combined_score": 84.1,
      "skill_score": 91.0,
      "experience_score": 95.0,
      "domain_score": 100.0,
      "education_score": 100.0,
      "matched_skills": ["Java", "Spring Boot", "Docker"],
      "missing_skills": ["Kubernetes"],
      "bonus_skills": ["Kafka", "Redis"],
      "match_explanation": "Rohit's 6 years of backend engineering experience at Flipkart, combined with deep expertise in Java and Spring Boot, makes him a strong fit for this role...\n\nTechnical Breakdown: [Match] Skills: Java, Spring Boot | [OK] Experience: 6yr meets 4yr requirement | [OK] Domain: exact match",
      "interest_summary": "Highly interested — actively looking and responded positively",
      "key_signals": ["[Available] Currently available", "Expressed strong interest", "Mentioned availability for call"],
      "availability_score": 90.0,
      "sentiment_score": 85.0,
      "engagement_score": 78.0,
      "conversation": [
        { "role": "recruiter", "content": "Hi Rohit! I'm reaching out from AutoRABIT..." },
        { "role": "candidate", "content": "Thanks for reaching out! I'm actively looking..." },
        { "role": "recruiter", "content": "Great! The role requires Java, Spring Boot..." },
        { "role": "candidate", "content": "That aligns perfectly with my current stack..." }
      ]
    }
  ],
  "total_candidates_evaluated": 25,
  "processing_time_seconds": 8.3
}
```

---

### POST `/api/upload-resumes` — Register Candidates

Upload PDF or text resume files. AI parses them and adds them to the talent pool.

**Request:** `multipart/form-data` with `files[]`

**Response:**
```json
{
  "message": "Processed 2 resumes",
  "results": [
    { "filename": "resume_john.pdf", "status": "success", "candidate": { "name": "John Doe", ... } },
    { "filename": "resume_bad.pdf",  "status": "error",   "message": "Could not extract text" }
  ]
}
```

---

### GET `/api/candidates` — List Candidate Pool

Returns all candidates currently in the in-memory pool (mock + uploaded).

```json
{
  "count": 27,
  "candidates": [ { "id": "a1b2c3", "name": "...", ... } ]
}
```

---

### POST `/api/send-email` — Send Outreach Email

Sends a real email to a candidate via Gmail SMTP. Requires SMTP credentials in `.env`.

**Request:**
```json
{
  "candidate": { "name": "Rohit Gupta", "email": "rohit@example.com", ... },
  "jd": { "role": "Senior Java Engineer", "company": "AutoRABIT", ... },
  "custom_message": "Optional custom HTML body (if omitted, Gemini drafts one)"
}
```

**Response:**
```json
{ "status": "success", "message": "Email sent successfully via SMTP." }
```

---

### POST `/api/parse-jd` — Parse JD Only

Parse a JD without running matching or outreach.

```json
POST /api/parse-jd
{ "jd_text": "...", "company_name": "MyCompany" }
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Vite 5 | UI framework and dev server |
| Styling | Vanilla CSS (dark glassmorphism) | Design system, animations |
| Backend | Python FastAPI + Uvicorn | REST API server |
| Parallelism | `concurrent.futures.ThreadPoolExecutor` | Parallel candidate scoring & outreach |
| LLM Primary | OpenRouter API (Llama 3.3 70B, Gemma 3 27B, Qwen 72B) | JD parsing, explanations, conversations |
| LLM Optional | Google Gemini 1.5 Flash | Email drafting |
| NLP Matching | scikit-learn TF-IDF + cosine similarity | Skill matching |
| PDF Parsing | pypdf | Resume text extraction |
| HTTP Client | httpx | LLM API calls with timeout |
| Env Config | python-dotenv | Secrets management |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | API key from openrouter.ai — used for all LLM calls |
| `LLM_MODEL` | No | Primary model (default: `meta-llama/llama-3.3-70b-instruct:free`) |
| `GEMINI_API_KEY` | No | Google Gemini key — used for email drafting |
| `SMTP_EMAIL` | No | Gmail address for sending real emails |
| `SMTP_PASSWORD` | No | Gmail App Password (not your login password) |

---

## LLM Fallback Chain

The system is designed to **always work**, even if all AI APIs are unavailable:

```
1. Primary Model (LLM_MODEL from .env)
       |
       | rate limited / error
       v
2. Fallback Models (tried in order):
   - meta-llama/llama-3.3-70b-instruct:free
   - google/gemma-3-27b-it:free
   - qwen/qwen-2.5-72b-instruct:free
   - google/gemma-2-9b-it:free
   - mistralai/mistral-7b-instruct:free
       |
       | all rate limited
       v
3. Rule-based Fallback (no API needed)
   - JD Parser: regex-based skill/domain/experience extraction
   - Conversation: pre-written realistic response templates
   - Interest Score: keyword-based sentiment analysis
```

Parsed JD panel shows **"Gemini AI Mode"** or **"Rule-based Mode"** so you always know which path ran.

---

## Features

- **Multi-LLM with automatic fallback** — never crashes, always returns results
- **Parallel processing** — all 8 candidate outreach calls run simultaneously (ThreadPoolExecutor)
- **Explainable scoring** — every candidate shows WHY they were ranked
- **Simulated 2-turn conversation** — realistic recruiter/candidate dialogue per candidate
- **CSV export** — one-click download of the full ranked shortlist
- **Resume upload** — PDF or text, AI-parsed in real time
- **3 built-in sample JDs** — ML Engineer, Backend Engineer, Data Scientist
- **Responsive dark UI** — glassmorphism design with step animations
- **Swagger API docs** — http://localhost:8000/docs
- **Email outreach** — AI-drafted emails sent via Gmail SMTP

---

## Candidate Data Model

Each candidate in the pool has the following schema:

```python
{
  "id": "a1b2c3d4",               # 8-char unique ID
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "phone": "+91-9876543210",
  "location": "Bangalore",
  "current_role": "ML Engineer",
  "current_company": "Infosys",
  "years_experience": 5,
  "skills": ["Python", "PyTorch", "TensorFlow", "NLP"],
  "domains": ["machine_learning", "data_science"],
  "education": "M.Tech in AI — IIT Hyderabad",
  "education_level": "master",      # none / bachelor / master / phd
  "available": True,                # actively looking
  "availability_note": "Notice period serving",
  "notice_period": "30 days",
  "salary_expectation": "25-30 LPA",
  "bio": "ML Engineer with 5 years..."
}
```

---

## Innovation & Trade-offs

### What makes this different

- **Interest Score** — goes beyond resume matching; models candidate enthusiasm via simulated dialogue
- **Full pipeline in one click** — JD → ranked shortlist in under 15 seconds
- **Explainability** — every score has a breakdown so recruiters understand the reasoning
- **Graceful degradation** — 5-model LLM chain with rule-based fallback means 100% uptime

### Known Trade-offs

| Trade-off | Reason |
|-----------|--------|
| In-memory candidate pool | No database dependency — runs entirely locally |
| Simulated conversations | Real system would integrate LinkedIn/email APIs |
| Mock candidate data | 25 profiles — real system would scrape or connect to ATS |
| Free-tier LLMs | Occasional rate limits — mitigated by fallback chain |

---

## Contact

Built by **Sikhakolli Jaya Krishna** for Catalyst Hackathon by Deccan AI

- GitHub: [github.com/Jayakrishna-1817](https://github.com/Jayakrishna-1817)
- Hackathon: Catalyst by Deccan AI — April 2026
