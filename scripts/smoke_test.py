#!/usr/bin/env python3
"""
Email Router MVP - Smoke Test
Verifies complete setup: OAuth, Gmail watch, message processing pipeline.
Run: python scripts/smoke_test.py
"""

import os
import sys
import json
import datetime
from pathlib import Path

# Add src directory to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email_router.config.scopes import GMAIL_SCOPES

# Test configuration
REQUIRED_FILES = [
    '.secrets/token.json',
    '.secrets/oauth_client.json', 
    'src/email_router/config/roles_mapping.json',
    'src/email_router/config/scopes.py',
    'src/email_router/core/ingest_email.py',
    'src/email_router/core/analyze_email.py',
    'src/email_router/core/forward_and_draft.py',
    'src/email_router/handlers/pubsub_handler.py',
    'deployment/main.py'
]

REQUIRED_ENV_VARS = [
    'GOOGLE_API_KEY'
]

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_result(test_name, passed, details=""):
    """Print test result with emoji"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def check_file_exists(file_path):
    """Check if required file exists"""
    full_path = project_root / file_path
    exists = full_path.exists()
    if exists:
        print_result(f"File: {file_path}", True, f"Found at {full_path}")
    else:
        print_result(f"File: {file_path}", False, f"Missing from {full_path}")
    return exists

def check_environment_variables():
    """Check required environment variables"""
    print_section("Environment Variables")
    all_present = True
    
    # Import environment config to load .env file
    from email_router.config.env import GOOGLE_API_KEY
    
    for var in REQUIRED_ENV_VARS:
        if var == 'GOOGLE_API_KEY':
            # Check our loaded environment variable
            if GOOGLE_API_KEY:
                print_result(f"Environment: {var}", True, f"Loaded from .env (length: {len(GOOGLE_API_KEY)})")
            else:
                print_result(f"Environment: {var}", False, "Not found in .env file")
                all_present = False
        else:
            value = os.getenv(var)
            if value:
                print_result(f"Environment: {var}", True, f"Set (length: {len(value)})")
            else:
                print_result(f"Environment: {var}", False, "Not set")
                all_present = False
    
    return all_present

def check_required_files():
    """Check all required project files exist"""
    print_section("Required Files")
    all_exist = True
    
    for file_path in REQUIRED_FILES:
        if not check_file_exists(file_path):
            all_exist = False
    
    return all_exist

def get_gmail_service():
    """Get authenticated Gmail service"""
    creds = None
    token_path = project_root / '.secrets' / 'token.json'
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
        except Exception as e:
            print_result("Token file parsing", False, f"Error: {e}")
            return None
    else:
        print_result("Token file", False, ".secrets/token.json not found")
        return None
    
    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                print_result("Token refresh", True, "Credentials refreshed successfully")
            except Exception as e:
                print_result("Token refresh", False, f"Failed to refresh: {e}")
                return None
        else:
            print_result("Token validity", False, "Invalid credentials, re-authentication needed")
            return None
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        print_result("Gmail service", True, "Service built successfully")
        return service
    except Exception as e:
        print_result("Gmail service", False, f"Failed to build service: {e}")
        return None

def check_oauth_authentication():
    """Test OAuth2 authentication and Gmail API access"""
    print_section("OAuth2 Authentication")
    
    service = get_gmail_service()
    if not service:
        return False
    
    try:
        # Test basic API access
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        print_result("Gmail API access", True, f"Connected as: {email_address}")
        
        # Check scopes in token
        token_path = project_root / '.secrets' / 'token.json'
        with open(token_path, 'r') as f:
            token_data = json.load(f)
        
        token_scopes = token_data.get('scopes', [])
        missing_scopes = set(GMAIL_SCOPES) - set(token_scopes)
        
        if missing_scopes:
            print_result("OAuth scopes", False, f"Missing scopes: {missing_scopes}")
            return False
        else:
            print_result("OAuth scopes", True, f"All required scopes present: {len(GMAIL_SCOPES)}")
        
        return True
        
    except Exception as e:
        print_result("Gmail API access", False, f"API call failed: {e}")
        return False

def check_gmail_watch_status():
    """Check Gmail watch registration status"""
    print_section("Gmail Watch Status")
    
    service = get_gmail_service()
    if not service:
        return False
    
    try:
        # Get user profile to check watch capability
        profile = service.users().getProfile(userId='me').execute()
        history_id = profile.get('historyId')
        
        if history_id:
            print_result("History ID available", True, f"Current historyId: {history_id}")
        else:
            print_result("History ID available", False, "No historyId in profile")
            return False
        
        # Note: Gmail API doesn't provide direct way to check active watches
        # We can only verify by monitoring or attempting to register
        print("📝 Note: Gmail API doesn't provide direct watch status query")
        print("   Active watches can be verified by monitoring Pub/Sub topic or logs")
        
        return True
        
    except Exception as e:
        print_result("Gmail watch check", False, f"Error: {e}")
        return False

def test_message_processing():
    """Test message processing pipeline with sample data"""
    print_section("Message Processing Pipeline")
    
    try:
        # Import pipeline functions
        from email_router.core.ingest_email import ingest_email
        from email_router.core.analyze_email import analyze_email
        from email_router.core.forward_and_draft import forward_and_draft
        
        print_result("Pipeline imports", True, "All functions imported successfully")
        
        # Test with sample data
        sample_event = {
            "emailAddress": "testingemailrouter@gmail.com",
            "historyId": "12345"
        }
        
        # Test ingest (will use test data)
        email_dict = ingest_email(sample_event)
        if email_dict and 'from' in email_dict and 'subject' in email_dict:
            print_result("Email ingestion", True, f"Subject: {email_dict['subject']}")
        else:
            print_result("Email ingestion", False, "Invalid email dict returned")
            return False
        
        # Test analysis
        analysis = analyze_email(email_dict)
        if analysis and 'classification' in analysis:
            print_result("Email analysis", True, f"Classification: {analysis['classification']}")
        else:
            print_result("Email analysis", False, "Invalid analysis returned")
            return False
        
        # Test forwarding (will use mock data)
        result = forward_and_draft(analysis)
        if result and 'forwarded_to' in result:
            print_result("Email forwarding", True, f"Forwarded to: {result['forwarded_to']}")
        else:
            print_result("Email forwarding", False, "Invalid forward result")
            return False
        
        return True
        
    except Exception as e:
        print_result("Pipeline processing", False, f"Error: {e}")
        return False

def test_pubsub_webhook():
    """Test CloudEvent Pub/Sub webhook handler end-to-end"""
    print_section("CloudEvent Pub/Sub Handler")
    
    try:
        import base64
        import json
        from cloudevents.http import CloudEvent
        from email_router.handlers.pubsub_handler import pubsub_webhook
        
        print_result("CloudEvent imports", True, "All imports successful")
        
        # Create test CloudEvent
        sample_gmail_event = {
            "emailAddress": "testingemailrouter@gmail.com",
            "historyId": "12345"
        }
        
        data_json = json.dumps(sample_gmail_event)
        data_b64 = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        
        attrs = {
            "type": "google.cloud.pubsub.messagePublished",
            "source": "test"
        }
        data = {
            "message": {
                "data": data_b64,
                "messageId": "test-message-id",
                "publishTime": "2024-01-01T00:00:00.000Z"
            }
        }
        
        event = CloudEvent(attrs, data)
        print_result("CloudEvent creation", True, "Test event created successfully")
        
        # Test the webhook handler
        result = pubsub_webhook(event)
        
        # Background function should return None
        if result is None:
            print_result("Pub/Sub webhook", True, "Handler completed successfully")
            return True
        else:
            print_result("Pub/Sub webhook", False, f"Unexpected return value: {result}")
            return False
        
    except Exception as e:
        print_result("Pub/Sub webhook test", False, f"Error: {e}")
        return False

def test_gmail_history_api():
    """Test Gmail history API functionality"""
    print_section("Gmail History API")
    
    service = get_gmail_service()
    if not service:
        return False
    
    try:
        # Get current profile for historyId
        profile = service.users().getProfile(userId='me').execute()
        current_history_id = profile.get('historyId')
        
        if not current_history_id:
            print_result("History ID retrieval", False, "No historyId in profile")
            return False
        
        print_result("History ID retrieval", True, f"Current: {current_history_id}")
        
        # Test history listing (may be empty, that's ok)
        try:
            history_response = service.users().history().list(
                userId='me',
                startHistoryId=current_history_id,
                labelId='INBOX'
            ).execute()
            
            history_records = history_response.get('history', [])
            print_result("History API call", True, f"Found {len(history_records)} history records")
            
            return True
            
        except Exception as e:
            if "historyId" in str(e):
                print_result("History API call", True, "No new history (expected for fresh setup)")
                return True
            else:
                raise e
        
    except Exception as e:
        print_result("History API test", False, f"Error: {e}")
        return False

def main():
    """Run complete smoke test suite"""
    print("🚀 Email Router MVP - Smoke Test")
    print(f"📁 Project root: {project_root}")
    
    # Change to project root
    os.chdir(project_root)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Required Files", check_required_files()))
    test_results.append(("Environment Variables", check_environment_variables()))
    test_results.append(("OAuth Authentication", check_oauth_authentication()))
    test_results.append(("Gmail Watch Status", check_gmail_watch_status()))
    test_results.append(("Message Processing", test_message_processing()))
    test_results.append(("CloudEvent Pub/Sub Handler", test_pubsub_webhook()))
    test_results.append(("Gmail History API", test_gmail_history_api()))
    
    # Summary
    print_section("Test Summary")
    passed_tests = sum(1 for name, passed in test_results if passed)
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Email Router MVP is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Smoke test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during smoke test: {e}")
        sys.exit(1) 