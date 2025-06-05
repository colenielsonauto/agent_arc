"""
Essential tests for MVP webhook endpoint.
🧪 Tests core email processing functionality.
"""

import pytest
import os
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["MAILGUN_API_KEY"] = "test-key" 
os.environ["MAILGUN_DOMAIN"] = "test.domain.com"

from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "ai_classifier" in data["components"]
    assert "email_sender" in data["components"]

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "AI Email Router" in data["service"]
    assert data["status"] == "active"
    assert "/webhooks/mailgun/inbound" in data["webhook"]

def test_webhook_endpoint_valid_data():
    """Test Mailgun webhook endpoint with valid data."""
    form_data = {
        "from": "test@example.com",
        "subject": "Test Support Email",
        "body-plain": "I need help with my account",
        "recipient": "support@yourcompany.com",
        "stripped-text": "I need help with my account"
    }
    
    response = client.post("/webhooks/mailgun/inbound", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "processing started" in data["message"]

def test_webhook_endpoint_missing_data():
    """Test webhook endpoint with minimal data."""
    form_data = {
        "from": "test@example.com"
        # Missing subject and body
    }
    
    response = client.post("/webhooks/mailgun/inbound", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"  # Should still accept and process

def test_webhook_endpoint_empty_request():
    """Test webhook endpoint with empty request."""
    response = client.post("/webhooks/mailgun/inbound", data={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"  # Should handle gracefully

def test_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200 