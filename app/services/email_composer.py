"""
AI-powered email response generation.
✍️ Creates personalized response drafts using Claude 3.5 Sonnet.
"""

import logging
import httpx
from ..utils.config import get_config

logger = logging.getLogger(__name__)

async def generate_customer_acknowledgment(email_data: dict, classification: dict) -> str:
    """
    ✍️ Generate brief customer acknowledgment (NOT detailed response)
    """
    config = get_config()
    
    prompt = f"""
You are a professional customer service assistant. Generate a BRIEF acknowledgment email for a customer.

Customer Email:
Subject: {email_data['subject']}
Message: {email_data['stripped_text'] or email_data['body_text']}
Classification: {classification['category']}

Generate a SHORT, professional acknowledgment that:
1. Thanks them for contacting us
2. Confirms we received their {classification['category']} inquiry  
3. Mentions estimated response time (if relevant)
4. Stays under 150 words
5. Does NOT provide solutions or detailed responses
6. Only mentions specific details if you're 100% certain they're accurate

Keep it brief, professional, and reassuring. This is just an acknowledgment, not the full response.

Acknowledgment:
"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": config.anthropic_api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": config.anthropic_model,
                    "max_tokens": 300,  # Shorter for acknowledgments
                    "temperature": 0.3,  # Lower temperature for consistency
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            acknowledgment = result["content"][0]["text"].strip()
            logger.info(f"✍️ Generated customer acknowledgment ({len(acknowledgment)} characters)")
            return acknowledgment
            
    except Exception as e:
        logger.error(f"❌ Acknowledgment generation failed: {e}")
        return _generate_fallback_acknowledgment(classification)

async def generate_team_analysis(email_data: dict, classification: dict) -> str:
    """
    ✍️ Generate detailed team analysis and response suggestions
    """
    config = get_config()
    
    prompt = f"""
You are an expert customer service analyst. Analyze this email and provide detailed insights for the team member who will handle it.

Customer Email:
From: {email_data['from']}
Subject: {email_data['subject']}
Message: {email_data['stripped_text'] or email_data['body_text']}

Classification: {classification['category']} (confidence: {classification['confidence']})

Provide a comprehensive analysis including:
1. Key issues or requests identified
2. Customer sentiment and urgency level
3. Suggested response approach
4. Any red flags or special considerations
5. Recommended next steps
6. Draft response suggestions (if applicable)

Make this detailed and actionable for the team member.

Team Analysis:
"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": config.anthropic_api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": config.anthropic_model,
                    "max_tokens": 800,  # Longer for detailed analysis
                    "temperature": 0.4,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            analysis = result["content"][0]["text"].strip()
            logger.info(f"✍️ Generated team analysis ({len(analysis)} characters)")
            return analysis
            
    except Exception as e:
        logger.error(f"❌ Team analysis generation failed: {e}")
        return _generate_fallback_team_analysis(classification)

def _generate_fallback_acknowledgment(classification: dict) -> str:
    """Generate simple fallback acknowledgment."""
    category = classification.get('category', 'general')
    
    fallbacks = {
        "support": "Thank you for contacting our support team. We've received your technical inquiry and our team will respond within 24 hours.",
        "billing": "Thank you for your billing inquiry. Our accounting team will review your request within 24 hours.",
        "sales": "Thank you for your interest in our services. Our sales team will contact you within 24 hours.",
        "general": "Thank you for contacting us. We've received your message and will respond within 24 hours."
    }
    
    return fallbacks.get(category, fallbacks["general"])

def _generate_fallback_team_analysis(classification: dict) -> str:
    """Generate simple fallback team analysis."""
    return f"Email classified as {classification.get('category', 'general')}. Please review the original message and respond accordingly."

async def generate_response_draft(email_data: dict, classification: dict) -> str:
    """
    ✍️ Generate personalized response draft using Claude 3.5 Sonnet
    
    Args:
        email_data: Original email data from Mailgun webhook
        classification: AI classification result
        
    Returns:
        Personalized response draft string
    """
    
    config = get_config()
    
    prompt = f"""
You are a professional customer service assistant. Generate a helpful, personalized draft response.

Original Email:
From: {email_data['from']}
Subject: {email_data['subject']}
Message: {email_data['stripped_text'] or email_data['body_text']}

Classification: {classification['category']} (confidence: {classification['confidence']})
Reasoning: {classification.get('reasoning', 'No reasoning provided')}

Generate a professional response that:
1. Acknowledges their {classification['category']} inquiry
2. Shows understanding of their specific concern
3. Provides helpful next steps or information
4. Maintains a friendly, professional tone
5. Ends with a professional closing

Keep it concise but helpful. Make it feel personal, not robotic.

Draft Response:
"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": config.anthropic_api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": config.anthropic_model,
                    "max_tokens": 500,
                    "temperature": 0.7,  # Higher temperature for more creative responses
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            draft_response = result["content"][0]["text"].strip()
            
            logger.info(f"✍️ Generated response draft ({len(draft_response)} characters)")
            return draft_response
            
    except Exception as e:
        logger.error(f"❌ Response generation failed: {e}")
        
        # Fallback response
        return _generate_fallback_response(classification)

def _generate_fallback_response(classification: dict) -> str:
    """Generate a simple fallback response when AI fails."""
    
    category = classification.get('category', 'general')
    
    fallback_responses = {
        "support": "Thank you for contacting our support team. We've received your technical inquiry and will respond with assistance within 24 hours.",
        "billing": "Thank you for your billing inquiry. Our accounting team has been notified and will review your account within 24 hours.", 
        "sales": "Thank you for your interest in our services. Our sales team will reach out to you within 24 hours to discuss your needs.",
        "general": "Thank you for contacting us. We've received your message and will respond within 24 hours."
    }
    
    return fallback_responses.get(category, fallback_responses["general"]) 