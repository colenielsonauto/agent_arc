"""
AI email classification using Anthropic Claude 3.5 Sonnet.
🤖 Core intelligence for email routing decisions.
"""

import logging
import httpx
import json
from typing import Dict, Any
from datetime import datetime
from ..utils.config import get_config

logger = logging.getLogger(__name__)

async def classify_email(subject: str, body: str, sender: str = None) -> Dict[str, Any]:
    """
    🤖 Classify email using Claude 3.5 Sonnet
    
    Args:
        subject: Email subject line
        body: Email body content
        sender: Sender email address (optional)
    
    Returns:
        {
            "category": "support|billing|sales|general",
            "confidence": 0.95,
            "reasoning": "Brief explanation",
            "suggested_actions": ["action1", "action2"]
        }
    """
    
    config = get_config()
    
    prompt = f"""
You are an intelligent email classifier for a business. Analyze this email and classify it:

Categories:
- billing: Payment issues, invoices, account billing
- support: Technical problems, how-to questions, product issues  
- sales: Pricing inquiries, product demos, new business
- general: Everything else

Email:
Subject: {subject}
Body: {body}
{f"From: {sender}" if sender else ""}

Respond in JSON format:
{{
    "category": "one of the categories above",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "suggested_actions": ["action1", "action2"]
}}
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
                    "temperature": 0.1,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse AI response
            ai_response = result["content"][0]["text"]
            classification = json.loads(ai_response)
            
            # Add metadata
            classification["ai_model"] = config.anthropic_model
            classification["timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"🎯 AI Classification: {classification['category']} ({classification['confidence']:.2f})")
            return classification
            
    except Exception as e:
        logger.warning(f"🔄 AI classification failed, using fallback: {e}")
        
        # Fallback classification
        return _classify_fallback(subject)

def _classify_fallback(subject: str) -> Dict[str, Any]:
    """Simple keyword-based fallback classification."""
    subject_lower = subject.lower()
    
    if "billing" in subject_lower or "invoice" in subject_lower:
        category, confidence = "billing", 0.85
        actions = ["check_payment", "billing_support"]
    elif "support" in subject_lower or "help" in subject_lower:
        category, confidence = "support", 0.90
        actions = ["technical_assistance", "troubleshooting"]
    elif "sales" in subject_lower or "pricing" in subject_lower:
        category, confidence = "sales", 0.80
        actions = ["schedule_demo", "send_pricing"]
    else:
        category, confidence = "general", 0.60
        actions = ["manual_review", "general_inquiry"]
    
    return {
        "category": category,
        "confidence": confidence,
        "reasoning": f"Keyword-based fallback classification",
        "suggested_actions": actions,
        "ai_model": "fallback",
        "timestamp": datetime.utcnow().isoformat()
    } 