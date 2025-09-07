"""
Tests for session API endpoints
"""
import pytest
from unittest.mock import patch
from app.core.schemas import Message, MessageRole

class TestSessionAPI:
    def test_list_empty_sessions(self, client):
        """Test listing sessions when none exist"""
        # Clear sessions first
        with patch('app.api.session.sessions', {}):
            response = client.get("/api/sessions")
            
            assert response.status_code == 200
            data = response.json()
            assert data["sessions"] == []

    def test_get_nonexistent_session(self, client):
        """Test getting a session that doesn't exist"""
        response = client.get("/api/session/nonexistent-session-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Session not found"

    def test_delete_nonexistent_session(self, client):
        """Test deleting a session that doesn't exist"""
        response = client.delete("/api/session/nonexistent-session-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Session not found"

    def test_session_workflow(self, client):
        """Test complete session workflow: create, get, delete"""
        # Create a session by sending a chat message (this will create a session)
        chat_response = client.post("/api/chat", json={
            "message": "Hello test",
            "user_id": "test_user"
        })
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        session_id = chat_data["session_id"]
        
        # Get the session
        get_response = client.get(f"/api/session/{session_id}")
        assert get_response.status_code == 200
        
        session_data = get_response.json()
        assert session_data["session_id"] == session_id
        assert "messages" in session_data
        assert "message_count" in session_data
        assert session_data["message_count"] >= 2  # User message + assistant response
        
        # Check message structure
        messages = session_data["messages"]
        assert len(messages) >= 2
        
        user_message = messages[0]
        assert user_message["role"] == "user"
        assert user_message["content"] == "Hello test"
        assert "timestamp" in user_message
        
        assistant_message = messages[1]
        assert assistant_message["role"] == "assistant"
        assert "content" in assistant_message
        assert "timestamp" in assistant_message

    def test_list_sessions_after_creation(self, client):
        """Test listing sessions after creating some"""
        # Create multiple sessions by sending chat messages
        chat_response1 = client.post("/api/chat", json={
            "message": "Test message 1",
            "user_id": "user1"
        })
        chat_response2 = client.post("/api/chat", json={
            "message": "Test message 2", 
            "user_id": "user2"
        })
        
        session_id1 = chat_response1.json()["session_id"]
        session_id2 = chat_response2.json()["session_id"]
        
        # List all sessions
        response = client.get("/api/sessions")
        assert response.status_code == 200
        
        data = response.json()
        sessions = data["sessions"]
        
        # Should have at least our 2 sessions
        session_ids = [s["session_id"] for s in sessions]
        assert session_id1 in session_ids
        assert session_id2 in session_ids
        
        # Check session structure
        for session in sessions:
            assert "session_id" in session
            assert "message_count" in session
            assert "last_message" in session
            assert session["message_count"] >= 2

    def test_delete_session(self, client):
        """Test deleting a session"""
        # Create a session
        chat_response = client.post("/api/chat", json={
            "message": "Test for deletion",
            "user_id": "test_user"
        })
        
        session_id = chat_response.json()["session_id"]
        
        # Verify session exists
        get_response = client.get(f"/api/session/{session_id}")
        assert get_response.status_code == 200
        
        # Delete the session
        delete_response = client.delete(f"/api/session/{session_id}")
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        assert delete_data["message"] == f"Session {session_id} deleted successfully"
        
        # Verify session no longer exists
        get_response_after = client.get(f"/api/session/{session_id}")
        assert get_response_after.status_code == 404

    def test_session_message_ordering(self, client):
        """Test that messages in session are in correct order"""
        # Create session with multiple messages
        session_id = None
        messages_sent = ["First message", "Second message", "Third message"]
        
        for i, message in enumerate(messages_sent):
            chat_request = {"message": message, "user_id": "test_user"}
            if session_id:
                chat_request["session_id"] = session_id
                
            response = client.post("/api/chat", json=chat_request)
            if not session_id:
                session_id = response.json()["session_id"]
        
        # Get session and verify message order
        get_response = client.get(f"/api/session/{session_id}")
        session_data = get_response.json()
        messages = session_data["messages"]
        
        # Should have user messages in correct order
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assert len(user_messages) == 3
        
        for i, expected_content in enumerate(messages_sent):
            assert user_messages[i]["content"] == expected_content