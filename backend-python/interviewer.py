import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception:
    client = None
    
MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """You are a strict but fair HR and technical interviewer at a top Indian tech company.
Your goal is to conduct a professional mock interview. 
CRITICAL RULES:
1. Always respond with VALID JSON only. Do not include markdown formatting or outside text.
2. Automatically detect if the user's answer is in Hindi or English (or Hinglish) and provide your feedback and next question in that same language style.
3. Base your questions on the provided Job Description (JD).
"""

def conduct_interview(jd_text, answer, question_number, conversation_history):
    # Prepare the message for Claude
    prompt = f"Job Description:\n{jd_text}\n\n"
    
    if question_number == 1:
        prompt += """This is the START of the interview. Generate the FIRST question based on the JD.
Return ONLY JSON in this format:
{
  "question": "The question here"
}"""
    elif question_number <= 5:
        prompt += f"""The user answered the previous question with: "{answer}"
        
Conversation History (Context):
{json.dumps(conversation_history)}

Evaluate the user's answer, and then generate the NEXT question.
Return ONLY JSON in this format:
{{
  "score": <number out of 10>,
  "good": "What was good about the answer",
  "missing": "What was missing from the answer",
  "suggestion": "A 1-2 line suggestion with a concrete example of a better answer (e.g. 'If you had said X, it would be better')",
  "next_question": "The next interview question"
}}"""
    else:
        prompt += f"""The interview is now COMPLETE. The user's final answer was: "{answer}"
        
Full Conversation History:
{json.dumps(conversation_history)}

Evaluate the entire interview and provide a final report.
Return ONLY JSON in this format:
{{
  "overall_score": <number out of 10>,
  "strongest_answer": "Summary of their best answer",
  "weakest_area": "The main area they need to improve",
  "tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""

    if client is None:
        ui_msg = "Your Gemini API key is missing. Please add GEMINI_API_KEY in backend-python/.env"
        if question_number == 1:
            return {"question": f"[{ui_msg}] Could you explain your experience?"}
        elif question_number <= 5:
            return {"score": 0, "good": "N/A", "missing": "N/A", "suggestion": f"[{ui_msg}]", "next_question": f"[{ui_msg}] Next question?"}
        else:
            return {"overall_score": 0, "strongest_answer": "N/A", "weakest_area": "N/A", "tips": [ui_msg]}

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        print("Error from Gemini:", e)
        # Fallback responses when API keys run out of credits or fail
        error_msg = str(e)
        if "API key not valid" in error_msg or "API_KEY_INVALID" in error_msg:
            ui_msg = "Your Gemini API key is invalid or missing. Please add a valid GEMINI_API_KEY in backend-python/.env"
        elif "credit balance is too low" in error_msg:
            ui_msg = "Your API key has run out of credits. Please add a valid API key with credits in backend-python/.env"
        else:
            ui_msg = f"API Error: {error_msg}"
            
        if question_number == 1:
            return {"question": f"[{ui_msg}] Could you explain your experience with Data Analysis?"}
        elif question_number <= 5:
            return {
                "score": 0,
                "good": "N/A",
                "missing": "N/A",
                "suggestion": f"[{ui_msg}]",
                "next_question": f"[{ui_msg}] Next question?"
            }
        else:
            return {
                "overall_score": 0,
                "strongest_answer": "N/A",
                "weakest_area": "N/A",
                "tips": [ui_msg]
            }
