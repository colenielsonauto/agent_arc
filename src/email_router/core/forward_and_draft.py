import os
import json
import base64
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ..config.scopes import GMAIL_SCOPES

logger = logging.getLogger(__name__)

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
        "sla": routing_info["response_time_sla"],
    }

    logger.info("Forward and draft complete: %s", result)
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

    # Try multiple possible paths for credentials in Cloud Function environment
    possible_token_paths = [
        # Cloud Function deployment structure - current working directory
        os.path.join(os.getcwd(), ".secrets", "token.json"),
        # Relative to the deployment directory
        os.path.join(os.path.dirname(__file__), "..", "..", ".secrets", "token.json"),
        # Direct relative paths
        ".secrets/token.json",
        # Legacy workspace paths
        "/workspace/.secrets/token.json",
        # Absolute path in Cloud Function
        "/workspace/serverless_function_source_code/.secrets/token.json",
    ]

    token_path = None
    for path in possible_token_paths:
        if os.path.exists(path):
            token_path = path
            logger.info(f"Found token.json at: {path}")
            break

    if token_path and os.path.exists(token_path):
        try:
            logger.info(f"Attempting to load credentials from: {token_path}")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.info("Successfully loaded OAuth credentials.")
            if creds and creds.valid:
                logger.info("Credentials are valid.")
            elif creds:
                logger.info("Credentials are not valid.")
        except Exception as e:
            logger.error(f"Error loading credentials from {token_path}: {e}")
            creds = None
    else:
        logger.info("token.json not found. Searched paths: %s", possible_token_paths)

    # If there are no (valid) credentials available, try to refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired OAuth token...")
                creds.refresh(Request())
                logger.info("Successfully refreshed OAuth token")

                # Save refreshed credentials back to file
                if token_path:
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                        logger.info(f"Saved refreshed token to {token_path}")

            except Exception as e:
                logger.error(f"Failed to refresh token: {e}", exc_info=True)
                creds = None
        elif creds:
            if not creds.expired:
                logger.info("Credentials are not expired, no refresh needed.")
            elif not creds.refresh_token:
                logger.info("Credentials do not have a refresh token, cannot refresh.")

        if not creds:
            # Try to find oauth_client.json for new authentication
            possible_oauth_paths = [
                os.path.join(os.getcwd(), ".secrets", "oauth_client.json"),
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    ".secrets",
                    "oauth_client.json",
                ),
                ".secrets/oauth_client.json",
                "/workspace/.secrets/oauth_client.json",
                "/workspace/serverless_function_source_code/.secrets/oauth_client.json",
            ]

            oauth_path = None
            for path in possible_oauth_paths:
                if os.path.exists(path):
                    oauth_path = path
                    logger.info("Found oauth_client.json at: %s", path)
                    break

            if not oauth_path:
                logger.error(
                    "oauth_client.json not found. Searched paths: %s",
                    possible_oauth_paths,
                )
                logger.info("Using mock responses.")
                return None

            # Note: In Cloud Function environment, we can't run interactive OAuth flow
            # We rely on pre-existing token.json with refresh token
            logger.info(
                "Cannot run interactive OAuth flow in Cloud Function environment"
            )
            logger.info("Using mock responses.")
            return None

    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Successfully created Gmail service")
        return service
    except Exception as e:
        logger.error("Failed to build Gmail service: %s", e)
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
            message = {"raw": encoded_message}
            result = (
                service.users().messages().send(userId="me", body=message).execute()
            )
            logger.info(f"Gmail message sent successfully: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"Gmail API Error (OAuth2) during send: {e}", exc_info=True)
            raise

    # Mock successful email send for testing (fallback when OAuth fails)
    logger.warning(
        "Using mock response because Gmail service was unavailable "
        "(authentication failed)."
    )
    return {
        "id": "mock_message_id_oauth_12345",
        "threadId": "mock_thread_id_oauth_67890",
        "labelIds": ["SENT"],
        "snippet": f"Mock OAuth2: Forwarded email to {routing_info['email']}",
    }


def generate_draft_reply(email_data, details, classification):
    """Generate AI-powered draft reply"""
    # Use the draft from analysis_result instead of generating a new one
    # This function is now mainly for formatting the final response

    # Get response time SLA for the classification
    sla = load_routing_config(classification)['response_time_sla']

    # Placeholder draft reply
    draft = f"""Dear {details.get('sender', 'Valued Customer')},

Thank you for contacting us regarding: {details.get('request', 'your inquiry')}

We have received your message and it has been forwarded to our {classification} team.
You can expect a response within {sla}.

Best regards,
Customer Service Team
"""

    logger.info("Generated draft reply")
    return draft


def call_vertex_ai_for_reply(prompt, email_content, context):
    """Call Vertex AI to generate reply content"""
    # TODO: Implement Vertex AI call for reply generation
    # TODO: Include context about classification and extracted details
    # TODO: Format response appropriately
    pass
