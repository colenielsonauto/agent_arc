#!/usr/bin/env python3
"""
AI-powered email classifier using Anthropic Claude.
This upgrades the basic rule-based classification to real AI.
"""

import asyncio
import os
import httpx
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIEmailClassifier:
    """
    AI-powered email classifier using Anthropic Claude.
    """
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        self.base_url = "https://api.anthropic.com"
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
    
    async def classify_email(self, subject: str, body: str, sender: str = None) -> Dict[str, Any]:
        """
        Classify an email using AI.
        
        Args:
            subject: Email subject line
            body: Email body content
            sender: Sender email address (optional)
            
        Returns:
            Classification result with category, confidence, reasoning, and actions
        """
        
        # Create the prompt for Claude
        prompt = f"""
You are an intelligent email classifier for a business. Analyze the following email and classify it into one of these categories:

Categories:
- billing: Payment issues, invoices, account billing
- support: Technical problems, how-to questions, product issues  
- sales: Pricing inquiries, product demos, new business
- hr: Job applications, employee questions, company policies
- legal: Contracts, legal notices, compliance issues
- marketing: Partnerships, advertising, promotional content
- general: Everything else

Email to classify:
Subject: {subject}
Body: {body}
{f"From: {sender}" if sender else ""}

Respond in this exact JSON format:
{{
    "category": "one of the categories above",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why you chose this category",
    "suggested_actions": ["action1", "action2", "action3"],
    "key_indicators": ["keyword1", "keyword2"]
}}

Be precise and confident in your classification. Focus on the main intent of the email.
"""

        try:
            # Make request to Anthropic API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 500,
                        "temperature": 0.1,  # Low temperature for consistent classification
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract the AI response
                ai_response = result["content"][0]["text"]
                
                # Parse JSON response from Claude
                import json
                try:
                    classification = json.loads(ai_response)
                    
                    # Add metadata
                    classification["ai_model"] = self.model
                    classification["processing_timestamp"] = datetime.utcnow().isoformat()
                    
                    return classification
                    
                except json.JSONDecodeError:
                    # Fallback if AI doesn't return valid JSON
                    return {
                        "category": "general",
                        "confidence": 0.5,
                        "reasoning": "AI response parsing failed",
                        "suggested_actions": ["manual_review"],
                        "key_indicators": [],
                        "ai_model": self.model,
                        "processing_timestamp": datetime.utcnow().isoformat(),
                        "raw_ai_response": ai_response
                    }
        
        except Exception as e:
            # Fallback classification
            return {
                "category": "general", 
                "confidence": 0.0,
                "reasoning": f"AI classification failed: {str(e)}",
                "suggested_actions": ["manual_review", "retry_classification"],
                "key_indicators": [],
                "ai_model": self.model,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

async def test_ai_classifier():
    """Test the AI classifier with sample emails."""
    
    classifier = AIEmailClassifier()
    
    # Test emails
    test_emails = [
        {
            "subject": "Invoice #12345 payment failed",
            "body": "Your payment for invoice #12345 could not be processed. Please update your payment method.",
            "sender": "billing@company.com"
        },
        {
            "subject": "Help! My account is locked",
            "body": "I can't log into my account and need urgent help. The error says my account is suspended.",
            "sender": "user@email.com"
        },
        {
            "subject": "Interested in your premium plan",
            "body": "Hi, I'd like to learn more about your premium pricing and schedule a demo.",
            "sender": "prospect@company.com"
        }
    ]
    
    print("🤖 Testing AI Email Classifier")
    print("=" * 50)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n📧 Test Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"From: {email['sender']}")
        
        print("\n🔍 AI Classification:")
        result = await classifier.classify_email(
            subject=email['subject'],
            body=email['body'],
            sender=email['sender']
        )
        
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Actions: {', '.join(result['suggested_actions'])}")
        
        if 'error' in result:
            print(f"⚠️ Error: {result['error']}")

async def integrate_with_api():
    """Show how to integrate AI classifier with the FastAPI endpoint."""
    
    print("\n🔗 Integration Example:")
    print("To upgrade your FastAPI app, replace the placeholder logic in /classify endpoint with:")
    print("""
# In src/api/main.py, replace the classify_email function with:

@app.post("/classify", response_model=EmailClassificationResponse)
async def classify_email(request: EmailClassificationRequest):
    try:
        start_time = datetime.utcnow()
        
        # Use AI classifier
        classifier = AIEmailClassifier()
        result = await classifier.classify_email(
            subject=request.subject,
            body=request.body,
            sender=request.sender
        )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return EmailClassificationResponse(
            category=result['category'],
            confidence=result['confidence'],
            reasoning=result['reasoning'],
            suggested_actions=result['suggested_actions'],
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"AI classification failed: {e}")
        raise HTTPException(status_code=500, detail="AI classification failed")
""")

if __name__ == "__main__":
    asyncio.run(test_ai_classifier())
    asyncio.run(integrate_with_api()) 