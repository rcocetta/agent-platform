"""
Tests for simple appointment graph
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app.graphs.simple_appointment_graph import SimpleAppointmentGraph

class TestSimpleAppointmentGraph:
    
    @pytest.fixture
    def graph(self, mock_settings):
        """Create a SimpleAppointmentGraph instance for testing"""
        return SimpleAppointmentGraph()

    def test_graph_initialization(self, graph):
        """Test that graph initializes correctly"""
        assert graph is not None
        assert hasattr(graph, 'llm')
        assert hasattr(graph, 'tools')
        assert len(graph.tools) == 4

    def test_parse_intent_book_keywords(self, graph):
        """Test intent parsing with booking keywords"""
        test_cases = [
            "Book me a haircut",
            "I want to schedule an appointment",
            "Can you reserve a slot for me",
            "Book appointment tomorrow"
        ]
        
        for message in test_cases:
            result = graph.parse_intent(message)
            assert result["intent"] == "book"
            assert "entities" in result

    def test_parse_intent_search_keywords(self, graph):
        """Test intent parsing with search keywords"""
        test_cases = [
            "Find me a salon",
            "Search for barbers nearby", 
            "Look for massage therapists"
        ]
        
        for message in test_cases:
            result = graph.parse_intent(message)
            assert result["intent"] == "search"

    def test_parse_intent_check_keywords(self, graph):
        """Test intent parsing with calendar check keywords"""
        test_cases = [
            "Check my calendar",
            "Show my calendar"
        ]
        
        for message in test_cases:
            result = graph.parse_intent(message)
            assert result["intent"] == "check"

    def test_parse_intent_unknown(self, graph):
        """Test intent parsing with unknown messages"""
        test_cases = [
            "Hello there",
            "How are you",
            "What's the weather like"
        ]
        
        for message in test_cases:
            result = graph.parse_intent(message)
            assert result["intent"] == "unknown"

    def test_parse_intent_service_extraction(self, graph):
        """Test service type extraction from messages"""
        # Test haircut detection
        result = graph.parse_intent("Book me a haircut")
        assert result["entities"]["service"] == "haircut"
        
        result = graph.parse_intent("I need a hair appointment")
        assert result["entities"]["service"] == "haircut"
        
        # Test massage detection
        result = graph.parse_intent("Book me a massage")
        assert result["entities"]["service"] == "massage"

    def test_parse_intent_location_extraction(self, graph):
        """Test location extraction from messages"""
        # Test default location
        result = graph.parse_intent("Book me a haircut")
        assert result["entities"]["location"] == "Antibes"
        
        # Test Nice detection
        result = graph.parse_intent("Find me a salon in Nice")
        assert result["entities"]["location"] == "Nice"
        
        # Test Cannes detection
        result = graph.parse_intent("Book appointment in Cannes")
        assert result["entities"]["location"] == "Cannes"

    def test_search_providers(self, graph):
        """Test provider search functionality"""
        entities = {"service": "haircut", "location": "Antibes"}
        providers = graph.search_providers(entities)
        
        assert isinstance(providers, list)
        assert len(providers) >= 1
        
        provider = providers[0]
        assert "id" in provider
        assert "name" in provider
        assert "services" in provider

    def test_get_availability(self, graph):
        """Test availability checking"""
        provider = {
            "id": "1",
            "services": [{"id": "101", "name": "Haircut"}]
        }
        
        slots = graph.get_availability(provider)
        assert isinstance(slots, list)
        
        if len(slots) > 0:  # If there are available slots
            slot = slots[0]
            assert "id" in slot
            assert "start_time" in slot
            assert "end_time" in slot
            assert slot["available"] is True

    def test_get_availability_no_services(self, graph):
        """Test availability with provider having no services"""
        provider = {"id": "1", "services": []}
        slots = graph.get_availability(provider)
        assert slots == []

    def test_create_booking(self, graph):
        """Test booking creation"""
        provider = {
            "id": "1",
            "name": "Test Salon",
            "services": [{"id": "101", "name": "Haircut"}]
        }
        slot = {
            "id": "slot_001",
            "start_time": "2025-09-08T14:00:00",
            "available": True
        }
        
        booking = graph.create_booking(provider, slot)
        
        assert isinstance(booking, dict)
        assert "id" in booking
        assert "confirmation_code" in booking
        assert "provider_name" in booking
        assert "service_name" in booking

    def test_run_unknown_intent(self, graph):
        """Test running graph with unknown intent"""
        result = graph.run("Hello there", "user123", "session456")
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert "actions_taken" in result
        assert result["actions_taken"] == []

    def test_run_successful_booking(self, graph):
        """Test complete booking workflow"""
        result = graph.run("Book me a haircut tomorrow", "user123", "session456")
        
        assert "messages" in result
        assert "actions_taken" in result
        
        if len(result["actions_taken"]) > 0:  # If booking was successful
            assert "searched_providers" in result["actions_taken"]
            
            if "created_booking" in result["actions_taken"]:
                assert "booking" in result
                assert result["booking"]["confirmation_code"] != ""

    def test_run_search_only(self, graph):
        """Test search-only workflow"""  
        result = graph.run("Find me a salon", "user123", "session456")
        
        assert "messages" in result
        assert "actions_taken" in result
        
        # Should at least search for providers
        if len(result["actions_taken"]) > 0:
            assert "searched_providers" in result["actions_taken"]

    def test_run_error_handling(self, graph):
        """Test error handling in workflow"""
        # Mock a tool to raise an exception
        with patch.object(graph.tools[0], '_run', side_effect=Exception("Test error")):
            result = graph.run("Book me a haircut", "user123", "session456")
            
            assert "messages" in result
            assert "actions_taken" in result
            assert "error" in result["actions_taken"]

    def test_run_no_providers_found(self, graph):
        """Test workflow when no providers are found"""
        # Mock search to return empty list
        with patch.object(graph, 'search_providers', return_value=[]):
            result = graph.run("Book me a haircut", "user123", "session456")
            
            assert "messages" in result
            assert "couldn't find any providers" in result["messages"][0]["content"].lower()
            assert "searched_providers" in result["actions_taken"]

    def test_run_no_availability(self, graph):
        """Test workflow when no slots are available"""
        # Mock availability to return empty list
        with patch.object(graph, 'get_availability', return_value=[]):
            result = graph.run("Book me a haircut", "user123", "session456")
            
            assert "messages" in result
            if "no available slots" in result["messages"][0]["content"]:
                assert "searched_providers" in result["actions_taken"]
                assert "checked_availability" in result["actions_taken"]