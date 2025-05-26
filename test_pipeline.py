#!/usr/bin/env python3
"""
Test script for Email Router MVP pipeline
Tests the complete flow: ingest -> analyze -> forward_and_draft
"""

import os
import json
from functions.ingest_email import ingest_email
from functions.analyze_email import analyze_email
from functions.forward_and_draft import forward_and_draft

def test_pipeline():
    """Test the complete email processing pipeline"""
    print("=" * 50)
    print("Testing Email Router MVP Pipeline")
    print("=" * 50)
    
    # Step 1: Test email ingestion
    print("\n1. Testing Email Ingestion...")
    email_data = ingest_email({'data': ''}, None)
    print(f"   Ingested: {email_data}")
    
    # Step 2: Test email analysis (AI classification)
    print("\n2. Testing Email Analysis...")
    analysis_result = analyze_email(email_data)
    print(f"   Classification: {analysis_result['classification']}")
    print(f"   Details: {analysis_result['details']}")
    print(f"   Draft: {analysis_result['draft'][:100]}...")
    
    # Step 3: Test forwarding and draft (with OAuth2 Gmail)
    print("\n3. Testing Forward and Draft (OAuth2)...")
    forward_result = forward_and_draft(analysis_result)
    print(f"   Forwarded to: {forward_result['forwarded_to']}")
    print(f"   Forward status: {forward_result['forward_status']['snippet']}")
    print(f"   SLA: {forward_result['sla']}")
    
    print("\n" + "=" * 50)
    print("Pipeline Test Complete!")
    print("=" * 50)
    
    return {
        "ingestion": email_data,
        "analysis": analysis_result,
        "forwarding": forward_result
    }

def test_with_custom_email():
    """Test pipeline with custom email from test_email.json"""
    print("\n" + "=" * 50)
    print("Testing with Custom Email (test_email.json)")
    print("=" * 50)
    
    # Load test email
    with open('test_email.json', 'r') as f:
        email_data = json.load(f)
    
    print(f"\nUsing test email: {email_data}")
    
    # Process through pipeline
    analysis_result = analyze_email(email_data)
    forward_result = forward_and_draft(analysis_result)
    
    print(f"\nResults:")
    print(f"   Classification: {analysis_result['classification']}")
    print(f"   Forwarded to: {forward_result['forwarded_to']}")
    print(f"   Gmail Status: {forward_result['forward_status']['id']}")
    
    return forward_result

if __name__ == "__main__":
    # Test 1: Default pipeline
    test_pipeline()
    
    # Test 2: Custom email
    test_with_custom_email()
    
    print("\n📧 OAuth2 Notes:")
    print("   - If token.json doesn't exist, browser will open for consent")
    print("   - If OAuth fails, mock responses are used for testing")
    print("   - AI classification still uses GOOGLE_API_KEY (unchanged)") 