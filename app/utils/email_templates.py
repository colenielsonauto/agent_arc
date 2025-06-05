"""
Email template generation for customer and team communications.
📧 Creates beautiful HTML and text templates.
"""

def generate_ticket_id() -> str:
    """Generate a simple ticket ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_customer_template(draft_response: str, classification: dict) -> tuple[str, str]:
    """
    Create customer-facing auto-reply (text + HTML).
    
    Args:
        draft_response: AI-generated response content
        classification: Email classification result
        
    Returns:
        Tuple of (text_body, html_body)
    """
    
    category = classification.get('category', 'general')
    
    # Determine response time based on category
    response_times = {
        "support": "within 4 hours",
        "billing": "within 24 hours", 
        "sales": "within 2 hours",
        "general": "within 24 hours"
    }
    response_time = response_times.get(category, "within 24 hours")
    ticket_id = generate_ticket_id()
    
    # Plain text version
    text_body = f"""
{draft_response}

Expected Response Time: {response_time}

Best regards,
Support Team

---
Ticket #: {ticket_id}
This is an automated acknowledgment. A team member will follow up personally.
"""

    # Clean, modern HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Contacting Us</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Thank You for Contacting Us</h1>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 40px 30px;">
            <div style="background-color: #f8f9ff; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 30px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; color: #2d3748; line-height: 1.6; font-size: 16px;">{draft_response}</p>
            </div>
            
            <div style="background-color: #f0f9ff; border: 1px solid #e0f2fe; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="color: #0369a1; font-size: 18px; margin-right: 8px;">⏱️</span>
                    <strong style="color: #0369a1;">Expected Response Time:</strong>
                </div>
                <p style="margin: 0; color: #075985; font-size: 16px; font-weight: 600;">{response_time}</p>
            </div>
            
            <div style="text-align: center; color: #64748b; font-size: 14px; line-height: 1.5;">
                <p>Ticket #: <strong>{ticket_id}</strong></p>
                <p>Best regards,<br><strong>Support Team</strong></p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: #64748b; font-size: 12px;">
                🤖 This is an automated acknowledgment. A team member will follow up personally.
            </p>
        </div>
        
    </div>
</body>
</html>
"""
    
    return text_body, html_body

def create_team_template(email_data: dict, classification: dict, draft_response: str) -> tuple[str, str]:
    """
    Create team-facing forwarded email (text + HTML).
    
    Args:
        email_data: Original email data from webhook
        classification: AI classification result  
        draft_response: AI-generated response draft
        
    Returns:
        Tuple of (text_body, html_body)
    """
    
    category = classification.get('category', 'general')
    confidence = classification.get('confidence', 0.0)
    reasoning = classification.get('reasoning', 'No reasoning provided')
    
    # Plain text version
    text_body = f"""
🤖 AI EMAIL ROUTER - FORWARDED MESSAGE

📋 CLASSIFICATION: {category} (confidence: {confidence:.2f})
💭 REASONING: {reasoning}

📧 ORIGINAL MESSAGE:
From: {email_data['from']}
To: {email_data.get('to', 'N/A')}
Subject: {email_data['subject']}

{email_data['stripped_text'] or email_data['body_text']}

---

✍️ SUGGESTED RESPONSE DRAFT:

{draft_response}

---
Reply to this email to respond to the original sender.
The customer has already received an automated acknowledgment.
"""

    # Enhanced HTML with better UX
    analysis_html = draft_response.replace('\n', '<br>')
    email_body_html = (email_data['stripped_text'] or email_data['body_text']).replace('\n', '<br>')
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Email Analysis</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 25px; color: white;">
            <h1 style="margin: 0; font-size: 22px; font-weight: 600;">🤖 AI Email Analysis</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Automated classification and analysis</p>
        </div>
        
        <!-- Classification Card -->
        <div style="margin: 20px; background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px;">
            <div style="margin-bottom: 15px;">
                <span style="font-size: 24px; margin-right: 10px;">📋</span>
                <span style="color: #166534; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; font-size: 18px;">{category}</span>
                <span style="margin-left: 15px; background: #16a34a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{confidence:.0%} CONFIDENT</span>
            </div>
            <p style="margin: 0; color: #166534; font-weight: 500;">{reasoning}</p>
        </div>
        
        <!-- Original Email Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: #f9fafb; padding: 15px; border-bottom: 1px solid #e5e7eb;">
                <h3 style="margin: 0; color: #374151; font-size: 16px;">📧 Original Message</h3>
            </div>
            <div style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: #374151;">From:</strong> <span style="color: #6b7280;">{email_data['from']}</span><br>
                    <strong style="color: #374151;">Subject:</strong> <span style="color: #6b7280;">{email_data['subject']}</span>
                </div>
                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 0 6px 6px 0;">
                    <p style="margin: 0; color: #1e293b; line-height: 1.6;">{email_body_html}</p>
                </div>
            </div>
        </div>
        
        <!-- AI Analysis Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 15px; border-bottom: 1px solid #93c5fd;">
                <h3 style="margin: 0; color: #1e40af; font-size: 16px;">🔍 AI Analysis & Recommendations</h3>
            </div>
            <div style="padding: 20px;">
                <div style="color: #1e293b; line-height: 1.7;">{analysis_html}</div>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="margin: 20px; text-align: center; padding: 20px;">
            <p style="color: #6b7280; margin-bottom: 15px; font-size: 14px;">
                ✅ Customer has already received an automated acknowledgment
            </p>
            <div style="background: #f0f9ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 15px; margin-top: 20px;">
                <p style="margin: 0; color: #3730a3; font-weight: 600;">
                    📧 Reply to this email to respond directly to the customer
                </p>
            </div>
        </div>
        
    </div>
</body>
</html>
"""
    
    return text_body, html_body 