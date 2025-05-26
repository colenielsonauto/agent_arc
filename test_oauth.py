#!/usr/bin/env python3
"""
Simple test for OAuth2 Gmail functionality
"""

import os
import json
from functions.forward_and_draft import forward_email_to_team, load_routing_config

def test_oauth_gmail():
    """Test OAuth2 Gmail integration with mock email data"""
    print("=" * 50)
    print("Testing OAuth2 Gmail Integration")
    print("=" * 50)
    
    # Mock email data
    email_data = {
        "from": "test@example.com",
        "subject": "Test OAuth2 Integration",
        "body": "This is a test email to verify OAuth2 Gmail sending."
    }
    
    # Get routing info for Support
    routing_info = load_routing_config("Support")
    print(f"Routing to: {routing_info['email']}")
    
    # Test Gmail sending with OAuth2
    print("\nTesting Gmail send with OAuth2...")
    try:
        result = forward_email_to_team(email_data, routing_info)
        print(f"✅ Success! Message ID: {result['id']}")
        print(f"   Snippet: {result['snippet']}")
        
        if "mock" in result['id'].lower():
            print("   📧 Note: Used mock response (OAuth2 not fully configured)")
        else:
            print("   📧 Note: Real Gmail API call succeeded!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("OAuth2 Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_oauth_gmail() 