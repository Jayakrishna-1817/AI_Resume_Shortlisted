import os
import json
import httpx
import time
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "google/gemma-3-27b-it:free")

# Fallback models for OpenRouter if the primary is rate-limited (429)
FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemma-2-9b-it:free",
    "mistralai/mistral-7b-instruct:free",
]

# Session-based blacklist for models that return 404/400
BLACKLISTED_MODELS = set()

def call_llm(prompt: str, model: str = None) -> str:
    """
    Centralized function to call LLMs. 
    Optimized for SPEED: tries 2 models max before jumping to Mock mode.
    """
    primary_model = model or DEFAULT_MODEL
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model and m not in BLACKLISTED_MODELS]
    
    # Check for placeholder keys
    if OPENROUTER_API_KEY == "your_openrouter_api_key_here" and GEMINI_API_KEY == "your_gemini_api_key_here":
        return _generate_mock_response(prompt)

    # 1. Try Gemini first if configured
    if "gemini" in primary_model.lower() and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            llm = genai.GenerativeModel(primary_model.split("/")[-1])
            response = llm.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini call failed: {e}. Trying OpenRouter...")
    
    # 2. Try OpenRouter model chain (Fast 2-model limit)
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
        for idx, target_model in enumerate(models_to_try):
            # Try up to 4 models before giving up
            if idx >= 4:
                break

            try:
                with httpx.Client() as client:
                    response = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "HTTP-Referer": "https://github.com/hackathon-deccan-ai",
                            "X-Title": "AI Talent Scouting Agent",
                        },
                        json={
                            "model": target_model,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                        timeout=25.0  # Enough for longer JD-parse prompts
                    )
                    
                    if response.status_code in [429, 402]:
                        print(f"Model {target_model} busy. Skipping...")
                        continue

                    if response.status_code in [404, 400]:
                        BLACKLISTED_MODELS.add(target_model)
                        continue

                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    
            except Exception:
                continue
            
    # 3. Emergency Mock Fallback
    prompt_lower = prompt.lower()
    if "parse the following job description" in prompt_lower or "extract the following candidate details" in prompt_lower:
        raise Exception("All AI models are currently busy. Switching to specialized local fallback...")
        
    return _generate_mock_response(prompt)

def _generate_mock_response(prompt: str) -> str:
    """Generates varied and realistic mock responses for conversations when AI is busy."""
    prompt_lower = prompt.lower()
    
    # Mock Interest Analysis
    if "evaluate the candidate's genuine interest" in prompt_lower:
        return json.dumps({
            "interest_score": 85.0,
            "sentiment_score": 90.0,
            "engagement_score": 80.0,
            "availability_score": 90.0,
            "key_signals": ["[Available] Responsive", "[Signal] Professional tone", "[Signal] Expressed interest"],
            "interest_summary": "Positive interest detected (AI fallback active)."
        })
    
    # VARIED CONVERSATION RESPONSES
    if "write a short, realistic, professional response" in prompt_lower:
        if "first reached out" in prompt_lower or "would you be open" in prompt_lower:
            return "Hi! Thanks for reaching out. This sounds like an interesting role. I'd love to learn more about the project and the team's goals."
        
        if "availability" in prompt_lower or "compelling move" in prompt_lower:
            return "I am currently open to exploring new opportunities. I value a collaborative environment and challenging work. I'm available for a brief call to discuss this further."

    # Default text response
    return "I've reviewed the details and I'm interested. Let's discuss next steps!"
