import os
import json
import uuid
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv

# Optional LangChain/LangGraph imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from langgraph.graph import StateGraph, END
except ImportError:
    pass

# Optional OpenAI import for Whisper
try:
    from openai import OpenAI
except ImportError:
    pass

# Optional Boto3 import for SES
try:
    import boto3
except ImportError:
    pass

load_dotenv()

# Initialize API clients
openai_api_key = os.environ.get("OPENAI_API_KEY")
gemini_api_key = os.environ.get("GEMINI_API_KEY")
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")

openai_client = None
using_groq_audio = False
if groq_api_key:
    try:
        openai_client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
        using_groq_audio = True
    except Exception as e:
        print(f"Failed to init Groq (via OpenAI client): {e}")
elif openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Failed to init OpenAI: {e}")

llm = None
if openrouter_api_key:
    try:
        llm = ChatOpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-4o-mini",
            temperature=0.7
        )
    except Exception as e:
        print(f"Failed to init OpenRouter LLM: {e}")
elif gemini_api_key:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=gemini_api_key, temperature=0.7)
    except Exception as e:
        print(f"Failed to init Gemini LLM: {e}")


class InterviewState(TypedDict):
    jd_text: str
    question_number: int
    conversation_history: List[Dict[str, str]]
    current_answer: str
    email: str
    
    # Outputs
    evaluation: Optional[Dict[str, Any]]
    next_question: Optional[str]
    final_report: Optional[Dict[str, Any]]
    error: Optional[str]


def transcribe_audio(audio_path: str) -> str:
    """Transcribes an audio file using OpenAI Whisper (or Groq Whisper)."""
    if not openai_client:
        return "(Transcription unavailable: Missing API Key. Assuming simulated answer.)"
    
    try:
        model_name = "whisper-large-v3" if using_groq_audio else "whisper-1"
        with open(audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model=model_name, 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return f"(Transcription error: {str(e)})"


def send_report_email(email_address: str, report_data: Dict[str, Any]):
    """Sends the final report via AWS SES."""
    if not email_address or "@" not in email_address:
        print("Invalid or missing email address.")
        return
        
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    ses_sender = os.environ.get("SES_SENDER_EMAIL", "test@example.com") # Must be verified in SES
    
    try:
        ses_client = boto3.client(
            'ses',
            region_name=aws_region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        
        subject = "Your Mirror AI Mock Interview Report"
        
        body_text = f"""
Hello!

Thank you for completing your mock interview. Here is your final report:

Overall Score: {report_data.get('overall_score', 'N/A')}/10
Strongest Answer: {report_data.get('strongest_answer', 'N/A')}
Weakest Area: {report_data.get('weakest_area', 'N/A')}

Tips for improvement:
{chr(10).join(f"- {tip}" for tip in report_data.get('tips', []))}

Best,
Mirror AI Team
"""
        
        response = ses_client.send_email(
            Destination={'ToAddresses': [email_address]},
            Message={
                'Body': {'Text': {'Charset': "UTF-8", 'Data': body_text}},
                'Subject': {'Charset': "UTF-8", 'Data': subject},
            },
            Source=ses_sender,
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send email via SES: {e}")


# --- LangGraph Nodes ---

SYSTEM_PROMPT = """You are a supportive, experienced HR and technical interviewer at a top tech company conducting a mock interview to HELP the candidate improve.
Your goal is to conduct a professional mock interview based on the provided Job Description (JD).
CRITICAL RULES:
1. Always respond with VALID JSON only. Do not include markdown formatting like ```json or outside text.
2. Automatically detect if the user's answer is in Hindi or English (or Hinglish) and provide your feedback and next question in that same language style.
3. Base your questions on the provided Job Description (JD).
4. You will ask exactly 12 questions. The first 10 questions should be important general and technical questions. The last 2 questions MUST be the most important coding questions. If the JD is about Software Engineering, ask DSA (Data Structures and Algorithms) questions. If the JD is about Machine Learning, ask both DSA and SQL questions.
5. If the user says they don't know the answer or gives a very short/unclear answer, acknowledge it briefly in your feedback and move on to a completely DIFFERENT question. NEVER ask the same question twice. Ensure every question is unique.
6. VERY IMPORTANT: Escape any double quotes inside your JSON string values.
7. SCORING GUIDELINES (be fair and generous — this is a learning tool, not a rejection filter):
   - Score 9-10: Excellent answer, covers all key points with good examples or depth.
   - Score 7-8: Good answer, covers most key points even if missing some minor details.
   - Score 5-6: Average answer, shows basic understanding but lacks depth or examples.
   - Score 3-4: Weak answer, only partially correct or very vague.
   - Score 1-2: Blank, completely wrong, or "I don't know" with zero attempt.
   - If the candidate gives a reasonable answer (even if not perfect), lean toward 7 or higher. Do NOT be overly strict. A candidate who clearly understands the concept but misses edge cases still deserves a 7.
8. Your feedback in "good", "missing", and "suggestion" must be SPECIFIC and ACTIONABLE — not generic. Reference what the user actually said.
"""

def generate_first_question(state: InterviewState) -> InterviewState:
    if llm is None:
        state["next_question"] = "[Error: Gemini API Key missing] Could you explain your experience?"
        return state
        
    prompt = f"Job Description:\n{state['jd_text']}\n\nThis is the START of the interview. Generate the FIRST question based on the JD.\nReturn ONLY JSON in this format:\n{{\n  \"question\": \"The question here\"\n}}"
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]
        
        data = json.loads(text)
        state["next_question"] = data.get("question", "Could you tell me about yourself?")
    except Exception as e:
        print("Error from Gemini:", e)
        state["next_question"] = "[API Error] Could you tell me about yourself?"
        
    return state


def evaluate_and_generate_next(state: InterviewState) -> InterviewState:
    if llm is None:
        state["evaluation"] = {"score": 0, "good": "N/A", "missing": "N/A", "suggestion": "[Error: API key missing]"}
        state["next_question"] = "[Error: API key missing] Next question?"
        return state

    prompt = f"""Job Description:
{state['jd_text']}

The user answered the previous question with: "{state['current_answer']}"
        
Conversation History (Context):
{json.dumps(state['conversation_history'])}

Evaluate the user's answer, and then generate the NEXT question.
Return ONLY JSON in this format:
{{
  "score": <number out of 10>,
  "good": "What was good about the answer",
  "missing": "What was missing from the answer",
  "suggestion": "A 1-2 line suggestion with a concrete example of a better answer",
  "next_question": "The next interview question"
}}"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]
            
        data = json.loads(text)
        state["evaluation"] = {
            "score": data.get("score", 0),
            "good": data.get("good", "N/A"),
            "missing": data.get("missing", "N/A"),
            "suggestion": data.get("suggestion", "N/A")
        }
        state["next_question"] = data.get("next_question", "Next question?")
    except Exception as e:
        print("Error from Gemini:", e)
        state["evaluation"] = {"score": 0, "good": "Error", "missing": "Error", "suggestion": str(e)}
        state["next_question"] = "Error generating next question."
        
    return state


def generate_final_report(state: InterviewState) -> InterviewState:
    if llm is None:
        state["final_report"] = {"overall_score": 0, "strongest_answer": "N/A", "weakest_area": "N/A", "tips": ["[Error: API key missing]"]}
        return state

    prompt = f"""Job Description:
{state['jd_text']}

The interview is now COMPLETE. The user's final answer was: "{state['current_answer']}"
        
Full Conversation History:
{json.dumps(state['conversation_history'])}

Evaluate the entire interview and provide a final report.
Return ONLY JSON in this format:
{{
  "overall_score": <number out of 10>,
  "strongest_answer": "Summary of their best answer",
  "weakest_area": "The main area they need to improve",
  "tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]
            
        data = json.loads(text)
        state["final_report"] = data
        
        # Trigger AWS SES Email
        if state.get("email"):
            send_report_email(state["email"], data)
            
    except Exception as e:
        print("Error from Gemini:", e)
        state["final_report"] = {"overall_score": 0, "strongest_answer": "Error", "weakest_area": "Error", "tips": [str(e)]}
        
    return state


# Build LangGraph
try:
    workflow = StateGraph(InterviewState)

    workflow.add_node("start_interview", generate_first_question)
    workflow.add_node("evaluate_answer", evaluate_and_generate_next)
    workflow.add_node("final_report", generate_final_report)

    # We use a conditional edge based on question_number
    def route_question(state: InterviewState) -> str:
        if state["question_number"] == 1:
            return "start_interview"
        elif state["question_number"] <= 12:
            return "evaluate_answer"
        else:
            return "final_report"

    workflow.set_conditional_entry_point(
        route_question,
        {
            "start_interview": "start_interview",
            "evaluate_answer": "evaluate_answer",
            "final_report": "final_report"
        }
    )

    workflow.add_edge("start_interview", END)
    workflow.add_edge("evaluate_answer", END)
    workflow.add_edge("final_report", END)

    app_graph = workflow.compile()
except Exception as e:
    print(f"Failed to build LangGraph: {e}")
    app_graph = None


def conduct_interview_graph(jd_text: str, answer: str, question_number: int, conversation_history: list, email: str = "") -> dict:
    """Wrapper function to execute the LangGraph and return the expected dictionary format for app.py."""
    if app_graph is None:
        return {"error": "LangGraph is not initialized. Please check dependencies (langchain, langgraph, langchain-google-genai)."}
        
    initial_state = {
        "jd_text": jd_text,
        "question_number": int(question_number),
        "conversation_history": conversation_history,
        "current_answer": answer,
        "email": email,
        "evaluation": None,
        "next_question": None,
        "final_report": None,
        "error": None
    }
    
    result_state = app_graph.invoke(initial_state)
    
    # Format the output to match what the frontend expects
    if question_number == 1:
        return {"question": result_state["next_question"]}
    elif question_number <= 12:
        eval_data = result_state.get("evaluation", {})
        return {
            "score": eval_data.get("score", 0),
            "good": eval_data.get("good", "N/A"),
            "missing": eval_data.get("missing", "N/A"),
            "suggestion": eval_data.get("suggestion", "N/A"),
            "next_question": result_state.get("next_question", "Next question?")
        }
    else:
        return result_state.get("final_report", {
            "overall_score": 0,
            "strongest_answer": "N/A",
            "weakest_area": "N/A",
            "tips": ["Error generating report"]
        })
