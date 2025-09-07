"""
Tests for chat API endpoint
"""
import pytest
from unittest.mock import patch, MagicMock

class TestChatAPI:
    def test_chat_minimal_request(self, client):
        """Test chat with minimal required fields"""
        response = client.post("/api/chat", json={
            "message": "Hello",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        assert "metadata" in data
        assert "actions_taken" in data
        
        # Check metadata structure
        metadata = data["metadata"]
        assert metadata["channel"] == "web"
        assert metadata["user_id"] == "test_user"

    def test_chat_full_request(self, client):
        """Test chat with all optional fields"""
        response = client.post("/api/chat", json={
            "message": "Book me a haircut",
            "user_id": "test_user",
            "session_id": "existing_session",
            "channel": "whatsapp",
            "metadata": {"source": "mobile"}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == "existing_session"
        assert data["metadata"]["channel"] == "whatsapp"

    def test_chat_unknown_intent(self, client):
        """Test chat with unknown intent message"""
        response = client.post("/api/chat", json={
            "message": "Hello, how are you?",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "book appointments" in data["response"].lower()
        assert data["actions_taken"] == []

    def test_chat_booking_intent(self, client):
        """Test chat with booking intent"""
        response = client.post("/api/chat", json={
            "message": "Book me a haircut tomorrow",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "actions_taken" in data
        
        # Should have taken some actions
        actions = data["actions_taken"]
        if "searched_providers" in actions:
            assert len(actions) > 0
            
        # If booking was successful
        if "created_booking" in actions:
            assert "confirmation" in data["response"].lower()

    def test_chat_search_intent(self, client):
        """Test chat with search intent"""
        response = client.post("/api/chat", json={
            "message": "Find me a salon in Nice",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "actions_taken" in data
        
        # Should have searched for providers
        if len(data["actions_taken"]) > 0:
            assert "searched_providers" in data["actions_taken"]

    def test_chat_creates_session(self, client):
        """Test that chat creates a new session if none provided"""
        response = client.post("/api/chat", json={
            "message": "Test message",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        session_id = data["session_id"]
        assert session_id is not None
        assert len(session_id) > 0
        
        # Verify session was created by getting it
        session_response = client.get(f"/api/session/{session_id}")
        assert session_response.status_code == 200

    def test_chat_uses_existing_session(self, client):
        """Test that chat uses existing session when provided"""
        # First request to create a session
        response1 = client.post("/api/chat", json={
            "message": "First message",
            "user_id": "test_user"
        })
        
        session_id = response1.json()["session_id"]
        
        # Second request using same session
        response2 = client.post("/api/chat", json={
            "message": "Second message",
            "user_id": "test_user",
            "session_id": session_id
        })
        
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
        
        # Verify both messages are in the session
        session_response = client.get(f"/api/session/{session_id}")
        session_data = session_response.json()
        
        user_messages = [msg for msg in session_data["messages"] if msg["role"] == "user"]
        assert len(user_messages) >= 2
        assert user_messages[0]["content"] == "First message"
        assert user_messages[1]["content"] == "Second message"

    def test_chat_invalid_request_missing_fields(self, client):
        """Test chat with missing required fields"""
        # Missing user_id
        response = client.post("/api/chat", json={
            "message": "Hello"
        })
        assert response.status_code == 422
        
        # Missing message
        response = client.post("/api/chat", json={
            "user_id": "test_user"
        })
        assert response.status_code == 422

    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        response = client.post("/api/chat", json={
            "message": "",
            "user_id": "test_user"
        })
        
        # Should still process but with unknown intent
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_chat_response_format(self, client):
        """Test chat response format is correct"""
        response = client.post("/api/chat", json={
            "message": "Test message",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure matches ChatResponse schema
        required_fields = ["response", "session_id", "metadata", "actions_taken"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["response"], str)
        assert isinstance(data["session_id"], str)
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["actions_taken"], list)

    @patch('app.graphs.simple_appointment_graph.SimpleAppointmentGraph')
    def test_chat_graph_initialization_error(self, mock_graph_class, client):
        """Test chat when graph initialization fails"""
        # Mock graph initialization to fail
        mock_graph_class.side_effect = Exception("Graph init error")
        
        # Restart the app to trigger initialization error
        with patch('app.api.chat.appointment_graph', None):
            response = client.post("/api/chat", json={
                "message": "Test message",
                "user_id": "test_user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "service is currently unavailable" in data["response"]

    def test_chat_different_channels(self, client):
        """Test chat with different channel types"""
        channels = ["web", "whatsapp", "telegram", "sms", "voice"]
        
        for channel in channels:
            response = client.post("/api/chat", json={
                "message": "Test message",
                "user_id": "test_user",
                "channel": channel
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["channel"] == channel