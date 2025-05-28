#!/usr/bin/env python3
"""
Gmail Watch Registration Tool
Registers Gmail watch on inbox to send push notifications to Pub/Sub topic.
"""

import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.scopes import GMAIL_SCOPES

# Gmail API scopes - need both send and readonly for watch
SCOPES = GMAIL_SCOPES

# Project configuration
PROJECT_ID = "email-router-460622"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/email-inbound"

def get_gmail_service():
    """Get authenticated Gmail service using OAuth2 (reusing existing logic)"""
    creds = None
    
    # Look for token.json in project root
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.secrets', 'token.json')
    oauth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.secrets', 'oauth_client.json')
    
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Refreshing OAuth2 credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(oauth_path):
                print(f"❌ oauth_client.json not found at {oauth_path}")
                print("   Please ensure OAuth2 credentials are properly configured.")
                return None
            
            try:
                print("🔐 Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(oauth_path, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ OAuth2 authentication successful!")
            except Exception as e:
                print(f"❌ OAuth flow failed: {e}")
                return None
        
        # Save the credentials for the next run
        if creds:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Credentials saved to {token_path}")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Failed to build Gmail service: {e}")
        return None

def register_gmail_watch():
    """Register Gmail watch on inbox to send notifications to Pub/Sub"""
    print("=" * 60)
    print("📧 Gmail Watch Registration Tool")
    print("=" * 60)
    
    # Get authenticated Gmail service
    print("\n1. 🔐 Authenticating with Gmail API...")
    service = get_gmail_service()
    
    if not service:
        print("❌ Failed to authenticate with Gmail API")
        return False
    
    print("✅ Gmail API authentication successful!")
    
    # Get current user email for verification
    try:
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        print(f"👤 Connected as: {email_address}")
    except Exception as e:
        print(f"⚠️  Could not get user profile: {e}")
        email_address = "Unknown"
    
    # Register Gmail watch
    print(f"\n2. 📡 Registering Gmail watch...")
    print(f"   📮 Target: INBOX")
    print(f"   🔔 Pub/Sub Topic: {TOPIC_NAME}")
    
    watch_request = {
        "labelIds": ["INBOX"],
        "topicName": TOPIC_NAME
    }
    
    try:
        result = service.users().watch(userId="me", body=watch_request).execute()
        
        print("✅ Gmail watch registered successfully!")
        print(f"   📊 History ID: {result.get('historyId', 'N/A')}")
        print(f"   ⏰ Expiration: {result.get('expiration', 'N/A')}")
        
        # The expiration is in milliseconds since epoch
        if 'expiration' in result:
            import datetime
            exp_timestamp = int(result['expiration']) / 1000
            exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
            exp_iso = exp_date.isoformat()
            print(f"   📅 Expires: {exp_iso} ({exp_date.strftime('%Y-%m-%d %H:%M:%S')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to register Gmail watch: {e}")
        
        # Provide helpful error messages for common issues
        if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
            print("\n💡 Troubleshooting:")
            print("   - Ensure Gmail API is enabled in Google Cloud Console")
            print("   - Verify OAuth2 client has necessary permissions")
            print("   - Check that Pub/Sub topic exists and has proper IAM permissions")
        elif "topic" in str(e).lower():
            print(f"\n💡 Pub/Sub Topic Issue:")
            print(f"   - Verify topic exists: {TOPIC_NAME}")
            print(f"   - Check IAM permissions for gmail-api-push@system.gserviceaccount.com")
        
        return False

def check_existing_watch():
    """Check if there's already an active watch"""
    print("\n3. 🔍 Checking for existing watches...")
    
    service = get_gmail_service()
    if not service:
        return False
    
    try:
        # Note: Gmail API doesn't have a direct way to list active watches
        # We can only check by trying to stop (which we won't do) or by monitoring
        print("   ℹ️  Gmail API doesn't provide a direct way to list active watches")
        print("   📝 Monitor Pub/Sub topic for incoming messages to verify watch is active")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not check existing watches: {e}")
        return False

def main():
    """Main execution function"""
    try:
        # Change to project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        
        print(f"📁 Working directory: {project_root}")
        
        # Register Gmail watch
        success = register_gmail_watch()
        
        if success:
            check_existing_watch()
            print("\n" + "=" * 60)
            print("🎉 Gmail Watch Setup Complete!")
            print("=" * 60)
            print(f"📧 Emails to testingemailrouter@gmail.com will now trigger:")
            print(f"   1. Push notification to: {TOPIC_NAME}")
            print(f"   2. Process through Email Router MVP pipeline")
            print(f"\n💡 Next Steps:")
            print(f"   - Set up Pub/Sub pull subscription or Cloud Function")
            print(f"   - Implement message processing logic")
            print(f"   - Test with a real email")
        else:
            print("\n❌ Gmail Watch Setup Failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 