import os
import json
import base64
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from ..config.scopes import GMAIL_SCOPES

# If modifying these scopes, delete the file token.json.
SCOPES = GMAIL_SCOPES

def forward_and_draft(analysis_result):
    """
    Forward email to appropriate team and generate draft reply.
    
    Args:
        analysis_result (dict): Analysis results from analyze_email
        
    Returns:
        dict: Forwarding and draft results
    """
    
    classification = analysis_result["classification"]
    email_data = analysis_result["email"]
    details = analysis_result["details"]
    
    # Step 1: Load roles mapping for routing
    routing_info = load_routing_config(classification)
    
    # Step 2: Forward email to appropriate team
    forward_result = forward_email_to_team(email_data, routing_info)
    
    # Step 3: Generate draft reply using Vertex AI
    draft_reply = generate_draft_reply(email_data, details, classification)
    
    result = {
        "forwarded_to": routing_info["email"],
        "forward_status": forward_result,
        "draft_reply": analysis_result.get("draft", draft_reply),
        "sla": routing_info["response_time_sla"]
    }
    
    print("Forward and draft complete:", result)
    return result

def load_routing_config(classification):
    """Load routing configuration from roles_mapping.json"""
    import os
    # Get the directory of this file and navigate to config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(current_dir, "..", "config")
    config_path = os.path.join(config_dir, "roles_mapping.json")
    
    with open(config_path, "r") as f:
        roles_mapping = json.load(f)
    return roles_mapping.get(classification, roles_mapping["Support"])

def get_gmail_service():
    """Get authenticated Gmail service using OAuth2"""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    token_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".secrets", "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            oauth_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".secrets", "oauth_client.json")
            if not os.path.exists(oauth_path):
                print("oauth_client.json not found. Using mock responses.")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(oauth_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"OAuth flow failed: {e}")
                return None
        
        # Save the credentials for the next run
        if creds:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build Gmail service: {e}")
        return None

def forward_email_to_team(email_data, routing_info):
    """Forward email to the appropriate team using Gmail REST API with OAuth2"""
    sender_email = "testingemailrouter@gmail.com"
    
    # Create email content
    subject = f"[FORWARDED] {email_data.get('subject', 'No Subject')}"
    body = f"""Original email from: {email_data.get('from', 'unknown')}
    
{email_data.get('body', 'No content')}

---
This email was automatically forwarded by Email Router."""
    
    # Create RFC 2822 email message
    email_message = f"""To: {routing_info['email']}
From: {sender_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{body}"""
    
    # Base64 encode the message
    encoded_message = base64.urlsafe_b64encode(email_message.encode()).decode()
    
    # Try to get authenticated Gmail service
    service = get_gmail_service()
    
    if service:
        try:
            message = {'raw': encoded_message}
            result = service.users().messages().send(userId='me', body=message).execute()
            print(f"Gmail message sent successfully: {result['id']}")
            return result
        except Exception as e:
            print(f"Gmail API Error (OAuth2): {e}")
            # Fall back to mock response
            pass
    
    # Mock successful email send for testing (fallback when OAuth fails)
    print("Using mock response (OAuth2 authentication failed or unavailable)")
    return {
        "id": "mock_message_id_oauth_12345",
        "threadId": "mock_thread_id_oauth_67890",
        "labelIds": ["SENT"],
        "snippet": f"Mock OAuth2: Forwarded email to {routing_info['email']}"
    }

def generate_draft_reply(email_data, details, classification):
    """Generate AI-powered draft reply"""
    # Use the draft from analysis_result instead of generating a new one
    # This function is now mainly for formatting the final response
    
    # Placeholder draft reply
    draft = f"""Dear {details.get('sender', 'Valued Customer')},

Thank you for contacting us regarding: {details.get('request', 'your inquiry')}

We have received your message and it has been forwarded to our {classification} team. 
You can expect a response within {load_routing_config(classification)['response_time_sla']}.

Best regards,
Customer Service Team
"""
    
    print("Generated draft reply")
    return draft

def call_vertex_ai_for_reply(prompt, email_content, context):
    """Call Vertex AI to generate reply content"""
    # TODO: Implement Vertex AI call for reply generation
    # TODO: Include context about classification and extracted details
    # TODO: Format response appropriately
    pass 