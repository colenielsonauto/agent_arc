#!/usr/bin/env python3
"""
Gmail Authentication Test
Tests Gmail API authentication and permissions without registering watch.
"""

import os
import sys

# Add project root to path to import from functions
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Add src directory to Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from email_router.core.forward_and_draft import get_gmail_service

def test_gmail_auth():
    """Test Gmail API authentication and basic permissions"""
    print("=" * 50)
    print("🔐 Gmail Authentication Test")
    print("=" * 50)
    
    # Test authentication
    print("\n1. Testing OAuth2 authentication...")
    service = get_gmail_service()
    
    if not service:
        print("❌ Failed to authenticate with Gmail API")
        print("\n💡 Troubleshooting:")
        print("   - Ensure .secrets/oauth_client.json exists and is valid")
        print("   - Check that Gmail API is enabled")
        print("   - Verify OAuth2 client permissions")
        return False
    
    print("✅ Gmail API authentication successful!")
    
    # Test basic Gmail API access
    print("\n2. Testing Gmail API access...")
    try:
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        print(f"👤 Connected as: {email_address}")
        print(f"📧 Messages total: {profile.get('messagesTotal', 'Unknown')}")
        print(f"📊 History ID: {profile.get('historyId', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to get user profile: {e}")
        return False
    
    # Test inbox access (readonly scope)
    print("\n3. Testing inbox access (readonly scope)...")
    try:
        messages = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX'], 
            maxResults=1
        ).execute()
        
        message_count = len(messages.get('messages', []))
        print(f"✅ Inbox access successful! Found {message_count} message(s)")
        
        if message_count > 0:
            # Get details of first message to test detailed access
            msg_id = messages['messages'][0]['id']
            message = service.users().messages().get(
                userId='me', 
                id=msg_id,
                format='metadata'
            ).execute()
            print(f"📄 Latest message ID: {msg_id}")
            
            # Extract subject from headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            print(f"📋 Subject: {subject[:50]}...")
            
    except Exception as e:
        print(f"❌ Failed to access inbox: {e}")
        print("   This might indicate missing 'gmail.readonly' scope")
        return False
    
    # Success summary
    print("\n" + "=" * 50)
    print("✅ Gmail Authentication Test PASSED!")
    print("=" * 50)
    print("📧 Ready for Gmail watch registration")
    print("🔔 All required permissions verified")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Run: python scripts/watch_gmail.py")
    print(f"   2. Verify Pub/Sub topic permissions")
    print(f"   3. Test with real email")
    
    return True

def main():
    """Main execution function"""
    try:
        # Change to project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        
        success = test_gmail_auth()
        
        if not success:
            print("\n❌ Gmail Authentication Test FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 