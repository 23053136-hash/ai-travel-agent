import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def parse_user_input(text: str) -> dict:
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an intelligent travel data extractor.
    Extract the following entities realistically from the user query:
    1. origin (city name, string)
    2. destination (city name, string)
    3. budget (number, assume INR, default 15000 if not mentioned)

    Return ONLY a JSON object: {{"origin": "City1", "destination": "City2", "budget": 15000}}
    No markdown blocks or backticks.
    Query: "{text}"
    """
    try:
        response = model.generate_content(prompt)
        raw = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print("Gemini Parsing Error:", e)
        return {"origin": "", "destination": "", "budget": 15000}

def format_output_with_gemini(plan_dict: dict) -> dict:
    # Use Gemini to wrap or describe the structured data if needed
    # For a React UI, raw JSON is better, but passing it through Gemini for a "summary" adds Polish.
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Format a short welcoming intro for this travel plan: {json.dumps(plan_dict)}. Max 2 sentences."
        response = model.generate_content(prompt)
        plan_dict["gemini_summary"] = response.text.strip()
    except:
        plan_dict["gemini_summary"] = "Here is your AI generated travel itinerary."
    return plan_dict
