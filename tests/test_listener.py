"""
Unit tests for listener.py - CloudEvent Pub/Sub handler
"""
import base64
import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloudevents.http import CloudEvent
from listener import pubsub_webhook

class TestListener(unittest.TestCase):
    """Test cases for the CloudEvent Pub/Sub webhook listener"""
    
    def create_cloudevent(self, data_dict):
        """Helper to create valid CloudEvent with base64-encoded data"""
        data_json = json.dumps(data_dict)
        data_b64 = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        
        attrs = {
            "type": "google.cloud.pubsub.messagePublished",
            "source": "test"
        }
        data = {
            "message": {
                "data": data_b64,
                "messageId": "test-message-id",
                "publishTime": "2024-01-01T00:00:00.000Z"
            }
        }
        
        return CloudEvent(attrs, data)
    
    @patch('functions.forward_and_draft.get_gmail_service')
    @patch('listener.forward_and_draft')
    @patch('listener.analyze_email') 
    @patch('listener.ingest_email')
    def test_pubsub_webhook_success(self, mock_ingest, mock_analyze, mock_forward, mock_gmail_service):
        """Test successful email processing pipeline with real Gmail schema"""
        # Setup mocks
        mock_email_dict = {
            "from": "test@example.com",
            "subject": "Test Email",
            "body": "Test message body"
        }
        mock_analysis = {
            "email": mock_email_dict,
            "classification": "Support",
            "details": {"sender": "test@example.com"},
            "draft": "Thank you for your message."
        }
        mock_result = {
            "forwarded_to": "support@company.com",
            "forward_status": {"id": "12345"},
            "sla": "4 hours"
        }
        
        # Mock Gmail service and API responses
        mock_service = MagicMock()
        mock_gmail_service.return_value = mock_service
        
        # Mock history.list() response
        mock_service.users().history().list().execute.return_value = {
            "history": [{
                "messagesAdded": [{
                    "message": {"id": "msg123"}
                }]
            }]
        }
        
        # Mock messages.get() response
        mock_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Subject", "value": "Test Email"}
                ],
                "body": {"data": "VGVzdCBtZXNzYWdlIGJvZHk="}  # "Test message body" in base64
            }
        }
        
        mock_ingest.return_value = mock_email_dict
        mock_analyze.return_value = mock_analysis
        mock_forward.return_value = mock_result
        
        # Create test CloudEvent with realistic Gmail push schema
        gmail_event = {
            "emailAddress": "testingemailrouter@gmail.com",
            "historyId": "12345"
        }
        event = self.create_cloudevent(gmail_event)
        
        # Call function directly (no HTTP request)
        result = pubsub_webhook(event)
        
        # Assertions - function should complete without error
        self.assertIsNone(result)  # Background function returns None
        
        # Verify Gmail API calls were made correctly
        mock_service.users().history().list.assert_called_with(
            userId='me', 
            startHistoryId='12345', 
            labelId='INBOX'
        )
        mock_service.users().messages().get.assert_called_with(
            userId='me',
            id='msg123',
            format='full'
        )
        
        # Verify pipeline functions were called once
        mock_analyze.assert_called_once_with(mock_email_dict)
        mock_forward.assert_called_once_with(mock_analysis)
    
    def test_invalid_cloudevent_data(self):
        """Test handling of invalid CloudEvent data structure"""
        attrs = {"type": "google.cloud.pubsub.messagePublished", "source": "test"}
        data = {"invalid": "structure"}  # Missing message.data
        event = CloudEvent(attrs, data)
        
        with self.assertRaises(ValueError) as context:
            pubsub_webhook(event)
        
        self.assertIn("Invalid CloudEvent message data", str(context.exception))
    
    def test_invalid_base64_data(self):
        """Test handling of invalid base64 data"""
        attrs = {"type": "google.cloud.pubsub.messagePublished", "source": "test"}
        data = {"message": {"data": "invalid-base64!@#$"}}
        event = CloudEvent(attrs, data)
        
        with self.assertRaises(ValueError) as context:
            pubsub_webhook(event)
        
        self.assertIn("Invalid CloudEvent message data", str(context.exception))
    
    def test_invalid_json_in_data(self):
        """Test handling of invalid JSON in decoded data"""
        invalid_json = "not json data"
        data_b64 = base64.b64encode(invalid_json.encode('utf-8')).decode('utf-8')
        
        attrs = {"type": "google.cloud.pubsub.messagePublished", "source": "test"}
        data = {"message": {"data": data_b64}}
        event = CloudEvent(attrs, data)
        
        with self.assertRaises(ValueError) as context:
            pubsub_webhook(event)
        
        self.assertIn("Invalid CloudEvent message data", str(context.exception))
    
    def test_missing_history_id(self):
        """Test handling of missing historyId in Gmail event"""
        # Create CloudEvent without historyId
        gmail_event = {"emailAddress": "test@gmail.com"}
        event = self.create_cloudevent(gmail_event)
        
        # Should raise exception to trigger Pub/Sub retry
        with self.assertRaises(ValueError) as context:
            pubsub_webhook(event)
        
        self.assertIn("Missing historyId", str(context.exception))
    
    @patch('listener.ingest_email')
    def test_pipeline_exception_handling(self, mock_ingest):
        """Test handling of exceptions during pipeline processing"""
        # Make ingest_email raise an exception
        mock_ingest.side_effect = Exception("Pipeline error")
        
        # Create valid CloudEvent with historyId
        gmail_event = {
            "emailAddress": "testingemailrouter@gmail.com",
            "historyId": "12345"
        }
        event = self.create_cloudevent(gmail_event)
        
        # Should re-raise exception to trigger Pub/Sub retry
        with self.assertRaises(Exception) as context:
            pubsub_webhook(event)
        
        self.assertIn("Pipeline error", str(context.exception))

if __name__ == '__main__':
    unittest.main() 