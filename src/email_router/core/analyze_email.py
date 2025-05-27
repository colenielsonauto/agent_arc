import os
import json
import base64
import google.genai as genai

# Global client variable - will be initialized lazily
client = None

def get_genai_client():
    """Get or initialize the GenAI client lazily"""
    global client
    if client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            client = genai.Client(api_key=api_key)
        else:
            return None
    return client

def load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    import os
    # Get the directory of this file and navigate to prompts
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(current_dir, "..", "prompts")
    prompt_path = os.path.join(prompts_dir, filename)
    with open(prompt_path, "r") as f:
        return f.read().strip()

# Preload prompts
prompt_classify = load_prompt("classify_intent.md")
prompt_extract  = load_prompt("extract_details.md")
prompt_draft    = load_prompt("draft_reply.md")

def analyze_email(email_data: dict) -> dict:
    """
    Analyze email content using GenAI SDK:
      1. Classify intent via gemini-1.5-flash
      2. Extract structured details via gemini-1.5-pro
      3. Draft a response via gemini-1.5-pro
    """
    subject = email_data.get("subject", "")
    body    = email_data.get("body", "")

    try:
        # Get client lazily
        client = get_genai_client()
        if not client:
            raise Exception("No GOOGLE_API_KEY available")

        # 1. Classification
        classify_input = f"SUBJECT: {subject}\nBODY: {body}\n\n{prompt_classify}"
        classify_response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=classify_input
        )
        # Parse JSON response for classification
        classification = json.loads(classify_response.text)["label"]

        # 2. Detail Extraction  
        extract_input = f"{body}\n\n{prompt_extract}"
        extract_response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=extract_input
        )
        details = json.loads(extract_response.text)

        # 3. Draft Reply
        draft_input = f"{body}\n\n{prompt_draft}"
        draft_response = client.models.generate_content(
            model="gemini-1.5-pro", 
            contents=draft_input
        )
        draft = draft_response.text

    except Exception as e:
        print(f"API Error (using mock data): {e}")
        # Mock responses for testing when API is not available
        classification = "Support"
        details = {
            "sender": email_data.get("from", "unknown"),
            "request": f"Inquiry about: {subject}",
            "deadline": None,
            "attachments": []
        }
        draft = f"Thank you for your message regarding '{subject}'. We have received your inquiry and will respond shortly."

    result = {
        "email": email_data,
        "classification": classification,
        "details": details,
        "draft": draft
    }

    print("Analysis result:", result)
    return result
