"""
Email template generation for customer and team communications.
📧 Creates beautiful HTML and text templates.
"""

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
    
    # Plain text version
    text_body = f"""
Thank you for contacting our support team!

{draft_response}

We've received your {category} inquiry and our team is already working on it. 
You can expect a detailed response from one of our specialists soon.

If you have any urgent questions, please don't hesitate to reach out.

Best regards,
AI Email Router Support Team

---
This is an automated response. Our team has been notified and will follow up personally.
"""

    # HTML version  
    draft_html = draft_response.replace('\n', '<br>')
    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff;">
        <h3 style="color: #007bff; margin: 0;">Thank you for contacting our support team!</h3>
    </div>
    
    <div style="background: white; padding: 20px; border: 1px solid #e9ecef; border-radius: 6px; margin-bottom: 20px;">
        {draft_html}
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0;"><strong>📋 Status:</strong> We've received your <strong>{category}</strong> inquiry and our team is working on it.</p>
    </div>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0;"><strong>⚡ Need immediate assistance?</strong> If you have any urgent questions, please don't hesitate to reach out.</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; border-top: 3px solid #007bff;">
        <p style="margin: 0; font-weight: bold; color: #007bff;">Best regards,<br>AI Email Router Support Team</p>
        <p style="margin: 10px 0 0 0; font-size: 12px; color: #6c757d;">🤖 Automated response • Team notified • Personal follow-up coming</p>
    </div>
</div>
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

    # HTML version
    draft_html = draft_response.replace('\n', '<br>')
    email_body_html = (email_data['stripped_text'] or email_data['body_text']).replace('\n', '<br>')
    
    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745;">
        <h2 style="color: #2c3e50; margin: 0;">🤖 AI EMAIL ROUTER - FORWARDED MESSAGE</h2>
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0;"><strong>📋 CLASSIFICATION:</strong> <span style="color: #27ae60; font-weight: bold; text-transform: uppercase;">{category}</span> (confidence: <strong>{confidence:.2f}</strong>)</p>
        <p style="margin: 10px 0 0 0;"><strong>💭 REASONING:</strong> {reasoning}</p>
    </div>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #856404; margin-top: 0;">📧 ORIGINAL MESSAGE:</h3>
        <p><strong>From:</strong> {email_data['from']}</p>
        <p><strong>To:</strong> {email_data.get('to', 'N/A')}</p>
        <p><strong>Subject:</strong> {email_data['subject']}</p>
        <div style="background: white; padding: 15px; border-left: 4px solid #ffc107; margin-top: 10px; border-radius: 4px;">
            <p style="margin: 0;">{email_body_html}</p>
        </div>
    </div>
    
    <hr style="border: none; border-top: 2px solid #dee2e6; margin: 30px 0;">
    
    <div style="background: #d1ecf1; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #0c5460; margin-top: 0;">✍️ SUGGESTED RESPONSE DRAFT:</h3>
        <div style="background: white; padding: 15px; border-left: 4px solid #17a2b8; border-radius: 4px;">
            <p style="margin: 0;">{draft_html}</p>
        </div>
    </div>
    
    <div style="background: #d4edda; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0; color: #155724;"><strong>✅ Customer Status:</strong> Automated acknowledgment already sent</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; text-align: center; color: #6c757d; font-size: 12px;">
        <p style="margin: 0;"><strong>📧 Reply to this email to respond to the original sender.</strong></p>
    </div>
</div>
"""
    
    return text_body, html_body 