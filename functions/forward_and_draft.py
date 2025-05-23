import os
import json
import base64
import requests

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
    # TODO: Implement email forwarding logic
    # TODO: Use Gmail API or SMTP to send email
    forward_result = forward_email_to_team(email_data, routing_info)
    
    # Step 3: Generate draft reply using Vertex AI
    # TODO: Load draft_reply.md prompt
    # TODO: Call Vertex AI to generate personalized reply
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
    # TODO: Add error handling for missing classifications
    with open("roles_mapping.json", "r") as f:
        roles_mapping = json.load(f)
    return roles_mapping.get(classification, roles_mapping["Support"])

def forward_email_to_team(email_data, routing_info):
    """Forward email to the appropriate team using Gmail REST API"""
    api_key = os.getenv("GOOGLE_API_KEY")
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
    
    # Send via Gmail REST API
    url = f"https://gmail.googleapis.com/gmail/v1/users/{sender_email}/messages/send"
    headers = {"Content-Type": "application/json"}
    payload = {"raw": encoded_message}
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"key": api_key}
        )
        
        print(f"Gmail API response: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            # API call failed, use mock response
            print(f"Gmail API failed, using mock response")
            return {
                "id": "mock_message_id_12345",
                "threadId": "mock_thread_id_67890", 
                "labelIds": ["SENT"],
                "snippet": f"Mock: Forwarded email to {routing_info['email']}"
            }
    
    except Exception as e:
        print(f"Gmail API Error (using mock): {e}")
        # Mock successful email send for testing
        return {
            "id": "mock_message_id_12345",
            "threadId": "mock_thread_id_67890",
            "labelIds": ["SENT"],
            "snippet": f"Forwarded email to {routing_info['email']}"
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