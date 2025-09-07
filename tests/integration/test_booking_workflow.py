"""
Integration tests for complete booking workflow
"""
import pytest
from datetime import datetime
import uuid

@pytest.mark.integration
class TestBookingWorkflowIntegration:
    """End-to-end integration tests for appointment booking"""
    
    def test_complete_booking_workflow(self, client):
        """Test complete booking workflow from start to finish"""
        user_id = f"test_user_{uuid.uuid4()}"
        
        # Step 1: Send booking request
        booking_response = client.post("/api/chat", json={
            "message": "Book me a haircut tomorrow at 2pm",
            "user_id": user_id
        })
        
        assert booking_response.status_code == 200
        booking_data = booking_response.json()
        session_id = booking_data["session_id"]
        
        # Verify response structure
        assert "response" in booking_data
        assert "session_id" in booking_data
        assert "actions_taken" in booking_data
        
        # Step 2: Check if booking was successful
        if "created_booking" in booking_data["actions_taken"]:
            # Successful booking path
            assert "confirmation" in booking_data["response"].lower()
            assert "searched_providers" in booking_data["actions_taken"]
            assert "checked_availability" in booking_data["actions_taken"]
            
            # Step 3: Verify session contains conversation history
            session_response = client.get(f"/api/session/{session_id}")
            assert session_response.status_code == 200
            
            session_data = session_response.json()
            assert session_data["session_id"] == session_id
            assert len(session_data["messages"]) >= 2  # User + Assistant
            
            # Check user message
            user_message = session_data["messages"][0]
            assert user_message["role"] == "user"
            assert user_message["content"] == "Book me a haircut tomorrow at 2pm"
            
            # Check assistant response
            assistant_message = session_data["messages"][1]
            assert assistant_message["role"] == "assistant"
            assert "confirmation" in assistant_message["content"].lower()

    def test_search_workflow(self, client):
        """Test search workflow without booking"""
        user_id = f"test_user_{uuid.uuid4()}"
        
        # Send search request
        search_response = client.post("/api/chat", json={
            "message": "Find me a salon in Nice",
            "user_id": user_id
        })
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        # Should have searched for providers
        actions = search_data["actions_taken"]
        if len(actions) > 0:
            assert "searched_providers" in actions
            
        # Response should contain information about providers or booking confirmation
        response_text = search_data["response"]
        assert len(response_text) > 0

    def test_multiple_interactions_same_session(self, client):
        """Test multiple interactions within the same session"""
        user_id = f"test_user_{uuid.uuid4()}"
        
        # First interaction - general greeting
        response1 = client.post("/api/chat", json={
            "message": "Hello",
            "user_id": user_id
        })
        
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Second interaction - booking request in same session
        response2 = client.post("/api/chat", json={
            "message": "Book me a massage",
            "user_id": user_id,
            "session_id": session_id
        })
        
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
        
        # Third interaction - another question
        response3 = client.post("/api/chat", json={
            "message": "What's the price?",
            "user_id": user_id,
            "session_id": session_id
        })
        
        assert response3.status_code == 200
        assert response3.json()["session_id"] == session_id
        
        # Verify all messages are in session
        session_response = client.get(f"/api/session/{session_id}")
        session_data = session_response.json()
        
        user_messages = [msg for msg in session_data["messages"] if msg["role"] == "user"]
        assert len(user_messages) == 3
        assert user_messages[0]["content"] == "Hello"
        assert user_messages[1]["content"] == "Book me a massage"
        assert user_messages[2]["content"] == "What's the price?"

    def test_different_service_types(self, client):
        """Test booking different types of services"""
        services = [
            ("Book me a haircut", "haircut"),
            ("I need a massage", "massage"),
            ("Schedule a hair appointment", "hair")
        ]
        
        for message, expected_service in services:
            user_id = f"test_user_{uuid.uuid4()}"
            
            response = client.post("/api/chat", json={
                "message": message,
                "user_id": user_id
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have some response
            assert len(data["response"]) > 0
            assert isinstance(data["actions_taken"], list)

    def test_different_locations(self, client):
        """Test booking in different locations"""
        locations = [
            "Book me a haircut in Antibes",
            "Find me a salon in Nice",
            "Schedule appointment in Cannes"
        ]
        
        for message in locations:
            user_id = f"test_user_{uuid.uuid4()}"
            
            response = client.post("/api/chat", json={
                "message": message,
                "user_id": user_id
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have processed the location
            assert len(data["response"]) > 0

    def test_session_persistence_across_requests(self, client):
        """Test that session state persists across multiple requests"""
        user_id = f"test_user_{uuid.uuid4()}"
        
        # Create initial session
        response1 = client.post("/api/chat", json={
            "message": "Hello",
            "user_id": user_id
        })
        
        session_id = response1.json()["session_id"]
        
        # Make several more requests
        messages = [
            "I want to book an appointment",
            "Book me a haircut",
            "What's the confirmation number?"
        ]
        
        for message in messages:
            response = client.post("/api/chat", json={
                "message": message,
                "user_id": user_id,
                "session_id": session_id
            })
            
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id
        
        # Verify complete conversation history
        session_response = client.get(f"/api/session/{session_id}")
        session_data = session_response.json()
        
        user_messages = [msg for msg in session_data["messages"] if msg["role"] == "user"]
        expected_messages = ["Hello"] + messages
        
        assert len(user_messages) == len(expected_messages)
        for i, expected in enumerate(expected_messages):
            assert user_messages[i]["content"] == expected

    def test_concurrent_users(self, client):
        """Test multiple users can interact concurrently"""
        user_ids = [f"user_{i}_{uuid.uuid4()}" for i in range(3)]
        session_ids = []
        
        # Create sessions for multiple users
        for user_id in user_ids:
            response = client.post("/api/chat", json={
                "message": f"Hello from {user_id}",
                "user_id": user_id
            })
            
            assert response.status_code == 200
            session_ids.append(response.json()["session_id"])
        
        # Each user makes additional requests
        for i, (user_id, session_id) in enumerate(zip(user_ids, session_ids)):
            response = client.post("/api/chat", json={
                "message": f"Book me a haircut - user {i}",
                "user_id": user_id,
                "session_id": session_id
            })
            
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id
        
        # Verify each session has correct messages
        for i, session_id in enumerate(session_ids):
            session_response = client.get(f"/api/session/{session_id}")
            session_data = session_response.json()
            
            user_messages = [msg for msg in session_data["messages"] if msg["role"] == "user"]
            assert len(user_messages) == 2
            assert user_ids[i] in user_messages[0]["content"]
            assert f"user {i}" in user_messages[1]["content"]

    def test_health_check_integration(self, client):
        """Test health check works with full system"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # System should be healthy even while processing requests
        # Make a chat request
        client.post("/api/chat", json={
            "message": "Test health",
            "user_id": "health_test_user"
        })
        
        # Health should still be good
        response2 = client.get("/api/health")
        assert response2.status_code == 200
        assert response2.json()["status"] == "healthy"

    def test_error_resilience(self, client):
        """Test system resilience to edge cases"""
        edge_cases = [
            "",  # Empty message
            " ",  # Whitespace only
            "a" * 1000,  # Very long message
            "🚀🎉🔥",  # Emoji only
            "Book me a 🪄✨ magical haircut 🌟",  # Mixed content
        ]
        
        for message in edge_cases:
            response = client.post("/api/chat", json={
                "message": message,
                "user_id": "edge_case_user"
            })
            
            # Should handle gracefully
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            assert isinstance(data["actions_taken"], list)