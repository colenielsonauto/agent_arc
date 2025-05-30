#!/usr/bin/env python3
"""
Example script demonstrating how to send emails using the Mailgun adapter.

This script shows how to use the email router's Mailgun integration
to send emails programmatically.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.interfaces.email_provider import (
    EmailProviderConfig,
    EmailProvider,
    EmailAddress,
    EmailAttachment,
)
from src.adapters.email.mailgun import MailgunAdapter
from src.infrastructure.config.settings import get_settings


async def send_simple_message():
    """
    Send a simple email using the Mailgun adapter.
    
    This is equivalent to the original send_simple_message() function
    but uses the email router's architecture.
    """
    print("🚀 Initializing Mailgun email adapter...")
    
    # Get configuration from settings
    settings = get_settings()
    email_config = settings.get_email_config("mailgun")
    
    # Create email provider configuration
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
        polling_interval=email_config["polling_interval"],
        batch_size=email_config["batch_size"],
    )
    
    # Create and configure the adapter
    adapter = MailgunAdapter(config)
    
    try:
        # Connect to Mailgun
        print("🔌 Connecting to Mailgun API...")
        await adapter.connect()
        print("✅ Connected successfully!")
        
        # Create email addresses
        to_address = EmailAddress(
            email="colenielson6@gmail.com",
            name="Cole Nielson"
        )
        
        # Send the email
        print("📧 Sending email...")
        message_id = await adapter.send_email(
            to=[to_address],
            subject="Hello Cole Nielson",
            body_text="Congratulations Cole Nielson, you just sent an email with Mailgun! You are truly awesome!"
        )
        
        print(f"✅ Email sent successfully!")
        print(f"📬 Message ID: {message_id}")
        
        return message_id
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise
        
    finally:
        # Always disconnect
        print("🔌 Disconnecting from Mailgun...")
        await adapter.disconnect()
        print("✅ Disconnected successfully!")


async def send_html_email():
    """Send an email with both text and HTML content."""
    print("🚀 Sending HTML email...")
    
    settings = get_settings()
    email_config = settings.get_email_config("mailgun")
    
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
    )
    
    adapter = MailgunAdapter(config)
    
    try:
        await adapter.connect()
        
        # Create email with HTML content
        message_id = await adapter.send_email(
            to=[EmailAddress(email="colenielson6@gmail.com", name="Cole Nielson")],
            subject="🎉 HTML Email Test",
            body_text="This is the plain text version of the email.",
            body_html="""
            <html>
                <body>
                    <h1 style="color: #333;">🎉 Hello Cole!</h1>
                    <p>This is an <strong>HTML email</strong> sent through the Mailgun adapter.</p>
                    <p>Features demonstrated:</p>
                    <ul>
                        <li>✨ Rich HTML formatting</li>
                        <li>🎨 Custom styling</li>
                        <li>📧 Professional email layout</li>
                    </ul>
                    <p>You are truly <em>awesome</em>! 🚀</p>
                </body>
            </html>
            """
        )
        
        print(f"✅ HTML email sent! Message ID: {message_id}")
        return message_id
        
    finally:
        await adapter.disconnect()


async def send_email_with_attachment():
    """Send an email with a file attachment."""
    print("🚀 Sending email with attachment...")
    
    settings = get_settings()
    email_config = settings.get_email_config("mailgun")
    
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
    )
    
    adapter = MailgunAdapter(config)
    
    try:
        await adapter.connect()
        
        # Create a sample attachment
        attachment_content = b"""Hello Cole!

This is a sample text file attached to demonstrate
the Mailgun adapter's attachment functionality.

The email router supports various file types and
makes it easy to send attachments programmatically.

Best regards,
The Email Router System
"""
        
        attachment = EmailAttachment(
            filename="welcome.txt",
            content_type="text/plain",
            size=len(attachment_content),
            data=attachment_content
        )
        
        message_id = await adapter.send_email(
            to=[EmailAddress(email="colenielson6@gmail.com", name="Cole Nielson")],
            subject="📎 Email with Attachment",
            body_text="Hi Cole! Please find the attached welcome file.",
            attachments=[attachment]
        )
        
        print(f"✅ Email with attachment sent! Message ID: {message_id}")
        return message_id
        
    finally:
        await adapter.disconnect()


async def get_domain_stats():
    """Get statistics about the Mailgun domain."""
    print("📊 Getting domain statistics...")
    
    settings = get_settings()
    email_config = settings.get_email_config("mailgun")
    
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
    )
    
    adapter = MailgunAdapter(config)
    
    try:
        await adapter.connect()
        
        # Get domain information
        domain_info = await adapter.get_domain_info()
        print(f"📋 Domain info: {domain_info}")
        
        # Get adapter info
        adapter_info = adapter.get_info()
        print(f"🔧 Adapter info: {adapter_info}")
        
        return domain_info
        
    finally:
        await adapter.disconnect()


async def test_email_validation():
    """Test email address validation using Mailgun."""
    print("✔️ Testing email validation...")
    
    settings = get_settings()
    email_config = settings.get_email_config("mailgun")
    
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
    )
    
    adapter = MailgunAdapter(config)
    
    try:
        await adapter.connect()
        
        # Test email addresses
        test_emails = [
            "colenielson6@gmail.com",
            "invalid.email@nonexistent-domain.xyz",
            "test@example.com"
        ]
        
        for email in test_emails:
            try:
                result = await adapter.validate_email(email)
                print(f"📧 {email}: {result}")
            except Exception as e:
                print(f"❌ Error validating {email}: {e}")
        
    finally:
        await adapter.disconnect()


async def main():
    """Main function demonstrating various Mailgun adapter features."""
    print("🎯 Mailgun Email Router Integration Demo")
    print("=" * 50)
    
    try:
        # Example 1: Simple email (equivalent to original function)
        print("\n1️⃣ Sending simple email...")
        await send_simple_message()
        
        # Example 2: HTML email
        print("\n2️⃣ Sending HTML email...")
        await send_html_email()
        
        # Example 3: Email with attachment
        print("\n3️⃣ Sending email with attachment...")
        await send_email_with_attachment()
        
        # Example 4: Domain statistics
        print("\n4️⃣ Getting domain statistics...")
        await get_domain_stats()
        
        # Example 5: Email validation
        print("\n5️⃣ Testing email validation...")
        await test_email_validation()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in main: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the examples
    exit_code = asyncio.run(main()) 