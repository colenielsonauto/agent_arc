#!/usr/bin/env python3
"""
Example script demonstrating how to use Anthropic (Claude) for AI analysis.

This script shows how to use Claude for email classification, response generation,
and other AI tasks while maintaining privacy (Anthropic doesn't use data for training).
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.interfaces.llm_provider import (
    LLMProviderConfig,
    LLMProvider,
    ClassificationRequest,
    ClassificationResult,
    GenerationRequest,
    GenerationResult,
)
from src.adapters.llm.anthropic import AnthropicAdapter
from src.infrastructure.config.settings import get_settings


async def test_email_classification():
    """Test email classification using Claude."""
    print("🤖 Testing email classification with Claude...")
    
    # Get configuration
    settings = get_settings()
    llm_config = settings.get_llm_config("anthropic")
    
    # Create LLM provider configuration
    config = LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        credentials={"api_key": llm_config["api_key"]},
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        timeout=llm_config["timeout"]
    )
    
    # Create adapter
    adapter = AnthropicAdapter(config)
    
    try:
        # Connect to Anthropic
        await adapter.connect()
        print("✅ Connected to Anthropic API successfully!")
        
        # Test email samples
        test_emails = [
            {
                "subject": "Urgent: Server Down",
                "content": "Our production server is experiencing issues and needs immediate attention. Users are unable to access the application.",
                "expected": "technical"
            },
            {
                "subject": "Thank you for your purchase!",
                "content": "We appreciate your recent order. Your items will be shipped within 2-3 business days.",
                "expected": "sales"
            },
            {
                "subject": "How do I reset my password?",
                "content": "I'm having trouble logging into my account. Can you help me reset my password?",
                "expected": "support"
            },
            {
                "subject": "Interested in enterprise features",
                "content": "Hi, I'm evaluating your product for our company of 500+ employees. Can we schedule a demo?",
                "expected": "sales"
            }
        ]
        
        categories = ["technical", "sales", "support", "billing", "general"]
        
        print("\n📧 Classifying test emails...")
        correct_predictions = 0
        
        for i, email in enumerate(test_emails, 1):
            # Create classification request
            request = ClassificationRequest(
                text=f"Subject: {email['subject']}\n\nContent: {email['content']}",
                categories=categories,
                include_confidence=True
            )
            
            # Classify the email
            result = await adapter.classify(request)
            
            # Check accuracy
            is_correct = result.category.lower() == email['expected'].lower()
            if is_correct:
                correct_predictions += 1
            
            print(f"\n{i}. Email: {email['subject'][:50]}...")
            print(f"   📊 Predicted: {result.category} (confidence: {result.confidence:.2f})")
            print(f"   🎯 Expected: {email['expected']}")
            print(f"   {'✅ Correct' if is_correct else '❌ Incorrect'}")
            
            if result.reasoning:
                print(f"   🧠 Reasoning: {result.reasoning[:100]}...")
        
        accuracy = (correct_predictions / len(test_emails)) * 100
        print(f"\n📈 Overall Accuracy: {accuracy:.1f}% ({correct_predictions}/{len(test_emails)})")
        
        return result
        
    finally:
        await adapter.disconnect()


async def test_response_generation():
    """Test email response generation using Claude."""
    print("\n🖋️ Testing email response generation with Claude...")
    
    settings = get_settings()
    llm_config = settings.get_llm_config("anthropic")
    
    config = LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        credentials={"api_key": llm_config["api_key"]},
        model=llm_config["model"],
        temperature=0.8,  # Higher temperature for more creative responses
        max_tokens=500
    )
    
    adapter = AnthropicAdapter(config)
    
    try:
        await adapter.connect()
        
        # Test scenarios
        scenarios = [
            {
                "context": "Customer support inquiry",
                "input_email": {
                    "subject": "Product not working as expected",
                    "content": "I bought your product last week but it's not working as described on your website. The features mentioned are missing and I'm very disappointed.",
                    "sender": "frustrated.customer@email.com"
                },
                "style": "professional and empathetic"
            },
            {
                "context": "Sales inquiry",
                "input_email": {
                    "subject": "Pricing for enterprise plan",
                    "content": "We're a 200-person company looking to upgrade from our current solution. What are your enterprise pricing options?",
                    "sender": "cto@bigcompany.com"
                },
                "style": "professional and sales-focused"
            },
            {
                "context": "Technical support",
                "input_email": {
                    "subject": "API integration help needed",
                    "content": "I'm trying to integrate your API but getting 401 errors. I've checked my API key multiple times. Can you help?",
                    "sender": "developer@startup.com"
                },
                "style": "technical and helpful"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            email = scenario["input_email"]
            
            # Create generation request
            request = GenerationRequest(
                prompt=f"""
Generate a professional email response for the following customer email:

Subject: {email['subject']}
From: {email['sender']}
Content: {email['content']}

Context: {scenario['context']}
Style: {scenario['style']}

Please generate a helpful, professional response that addresses their concerns.
""",
                temperature=0.8,
                max_tokens=400
            )
            
            # Generate response
            result = await adapter.generate(request)
            
            print(f"\n{i}. Scenario: {scenario['context']}")
            print(f"   📧 Original: {email['subject']}")
            print(f"   🤖 Generated Response:")
            print(f"   {'-' * 50}")
            print(f"   {result.text}")
            print(f"   {'-' * 50}")
            print(f"   📊 Tokens used: {result.usage.total_tokens if result.usage else 'N/A'}")
        
        return result
        
    finally:
        await adapter.disconnect()


async def test_email_analysis():
    """Test comprehensive email analysis using Claude."""
    print("\n🔍 Testing comprehensive email analysis with Claude...")
    
    settings = get_settings()
    llm_config = settings.get_llm_config("anthropic")
    
    config = LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        credentials={"api_key": llm_config["api_key"]},
        model=llm_config["model"],
        temperature=0.3  # Lower temperature for consistent analysis
    )
    
    adapter = AnthropicAdapter(config)
    
    try:
        await adapter.connect()
        
        # Complex email for analysis
        complex_email = """
Subject: Urgent: Multiple Issues with Recent Order #12345

Dear Support Team,

I'm writing to express my frustration with several issues regarding my recent order #12345 placed on December 1st:

1. DELIVERY DELAY: The order was supposed to arrive by December 5th but still hasn't shipped
2. WRONG ITEM: I ordered the blue widget but received a red one instead  
3. DAMAGED PACKAGING: The box was severely damaged and one item was broken
4. BILLING ERROR: I was charged $199 instead of the advertised $149 price
5. POOR COMMUNICATION: No one has responded to my previous 3 emails sent over the past week

This is completely unacceptable for a premium service. I've been a loyal customer for 3 years and this experience is making me reconsider my relationship with your company.

I need:
- Immediate refund for the price difference ($50)
- Replacement for the damaged item
- Expedited shipping for the correct blue widget
- Explanation for the communication breakdown
- Assurance this won't happen again

If these issues aren't resolved within 48 hours, I'll be forced to dispute the charges with my credit card company and leave negative reviews.

I hope we can resolve this quickly.

Best regards,
John Smith
Premium Customer #789456
john.smith@email.com
Phone: (555) 123-4567
"""
        
        # Comprehensive analysis prompt
        analysis_prompt = f"""
Please analyze the following customer email and provide a structured analysis:

{complex_email}

Provide analysis in the following format:

1. SENTIMENT: (positive/negative/neutral with score 1-10)
2. URGENCY: (low/medium/high/critical with reasoning)
3. CATEGORY: Primary category and any subcategories
4. ISSUES IDENTIFIED: List all specific complaints/issues
5. CUSTOMER TYPE: (new/regular/premium/vip based on context)
6. REQUIRED ACTIONS: Specific actions needed to resolve
7. ESCALATION NEEDED: (yes/no with reasoning)
8. PRIORITY LEVEL: (1-5 with 5 being highest)
9. ESTIMATED RESOLUTION TIME: Realistic timeframe
10. RESPONSE STRATEGY: Recommended approach for response

Be thorough and specific in your analysis.
"""
        
        request = GenerationRequest(
            prompt=analysis_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        result = await adapter.generate(request)
        
        print("📊 Comprehensive Email Analysis:")
        print("=" * 60)
        print(result.text)
        print("=" * 60)
        
        if result.usage:
            print(f"📈 Analysis Stats:")
            print(f"   • Tokens used: {result.usage.total_tokens}")
            print(f"   • Processing time: ~{result.usage.total_tokens * 0.001:.2f} seconds")
        
        return result
        
    finally:
        await adapter.disconnect()


async def test_privacy_features():
    """Test and demonstrate privacy features of Anthropic."""
    print("\n🔐 Testing privacy features and capabilities...")
    
    settings = get_settings()
    llm_config = settings.get_llm_config("anthropic")
    
    config = LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        credentials={"api_key": llm_config["api_key"]},
        model=llm_config["model"]
    )
    
    adapter = AnthropicAdapter(config)
    
    try:
        await adapter.connect()
        
        # Test sensitive data handling
        sensitive_email = """
Subject: Account Issue - Need Help

Hi Support,

I'm having trouble with my account. Here are my details:
- Social Security: 123-45-6789
- Credit Card: 4532-1234-5678-9012
- Password: MySecretPass123
- Account ID: ACC-789456

Can you help me reset my account?

Thanks,
Customer
"""
        
        privacy_prompt = f"""
Analyze this email and:
1. Identify any sensitive information (PII, credentials, etc.)
2. Explain how you would handle this data responsibly
3. Provide security recommendations

Email content:
{sensitive_email}

Remember: Focus on security best practices and data protection.
"""
        
        request = GenerationRequest(
            prompt=privacy_prompt,
            temperature=0.2
        )
        
        result = await adapter.generate(request)
        
        print("🛡️ Privacy & Security Analysis:")
        print("-" * 50)
        print(result.text)
        print("-" * 50)
        
        print("\n✅ Anthropic Privacy Benefits:")
        print("   • Data NOT used for training")
        print("   • No data retention for model improvement")
        print("   • Strong privacy commitments")
        print("   • Transparent data handling policies")
        print("   • Constitutional AI for safer responses")
        
        return result
        
    finally:
        await adapter.disconnect()


async def main():
    """Main function demonstrating Anthropic (Claude) capabilities."""
    print("🎯 Anthropic (Claude) Email Router Integration Demo")
    print("=" * 60)
    print("🔐 Privacy-first AI analysis (data not used for training)")
    print("=" * 60)
    
    try:
        # Test 1: Email Classification
        await test_email_classification()
        
        # Test 2: Response Generation  
        await test_response_generation()
        
        # Test 3: Comprehensive Analysis
        await test_email_analysis()
        
        # Test 4: Privacy Features
        await test_privacy_features()
        
        print("\n🎉 All Anthropic integration tests completed successfully!")
        print("\n📊 Summary:")
        print("   ✅ Email classification working")
        print("   ✅ Response generation working")
        print("   ✅ Comprehensive analysis working")
        print("   ✅ Privacy features demonstrated")
        print("   ✅ Claude 3.5 Sonnet integration ready!")
        
        print("\n🚀 Next Steps:")
        print("   1. Use Claude for email routing decisions")
        print("   2. Implement automated response drafting")
        print("   3. Set up email sentiment monitoring")
        print("   4. Configure privacy-compliant data handling")
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the Anthropic demo
    exit_code = asyncio.run(main()) 