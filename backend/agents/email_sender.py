import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import google.generativeai as genai

def draft_email_with_ai(candidate: dict, jd: dict) -> str:
    """Uses Gemini to draft a highly personalized recruitment email."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "your_gemini_api_key_here":
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Draft a personalized recruiter outreach email to the following candidate for the given job.
        Candidate Name: {candidate.get("name", "Candidate")}
        Candidate Current Role: {candidate.get("current_role", "Professional")}
        Job Title: {jd.get("role", "Open Role")}
        Company: {jd.get("company", "Our Company")}
        
        The email should be professional, compelling, and mention 1-2 reasons why their profile matches our job.
        Do NOT include a subject line in the output, ONLY the email body. Use HTML formatting (<br>, <p>, <strong>).
        Keep it under 150 words.
        """
        try:
            return model.generate_content(prompt).text.strip()
        except:
            pass
    
    # Fallback template if API fails
    return f"""
    <p>Hi {candidate.get("name", "there")},</p>
    <p>I came across your profile and was impressed by your experience as a {candidate.get("current_role", "professional")}. 
    We are currently looking for a <strong>{jd.get("role", "Open Role")}</strong> at {jd.get("company", "our company")} and think you'd be a great fit.</p>
    <p>Would you be open to a quick chat this week?</p>
    <p>Best,<br>Recruitment Team</p>
    """

def send_outreach_email(candidate: dict, jd: dict, custom_message: str = None) -> dict:
    """Sends a real email using SMTP. Strictly enforces credential usage."""
    smtp_email = os.getenv("SMTP_EMAIL", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    
    recipient = candidate.get("email", "")
    
    if not recipient or "@" not in recipient or recipient.endswith("example.com"):
        return {"success": False, "error": f"Invalid candidate email address: {recipient}"}
        
    if not smtp_email or not smtp_pass or smtp_email == "your_email@gmail.com":
        raise ValueError("SMTP credentials (SMTP_EMAIL, SMTP_PASSWORD) are not set in .env. Real emails cannot be sent.")
        
    body = custom_message if custom_message else draft_email_with_ai(candidate, jd)
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Opportunity: {jd.get('role', 'Open Role')} at {jd.get('company', 'Our Company')}"
        msg["From"] = f"TalentAI Agent <{smtp_email}>"
        msg["To"] = recipient

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_pass)
        server.sendmail(smtp_email, recipient, msg.as_string())
        server.quit()
        
        return {"success": True, "message": "Email sent successfully via SMTP."}
    except Exception as e:
        return {"success": False, "error": str(e)}
