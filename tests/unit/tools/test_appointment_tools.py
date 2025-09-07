"""
Tests for appointment tools
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.tools.appointment_tools import (
    SearchProvidersTool, GetAvailabilityTool, 
    CreateBookingTool, CheckCalendarTool, ALL_TOOLS
)

class TestSearchProvidersTool:
    def test_search_providers_tool_creation(self):
        tool = SearchProvidersTool()
        assert tool.name == "search_providers"
        assert tool.description == "Search for service providers in a location"
        assert tool.args_schema is not None

    def test_search_providers_mock_data(self, mock_settings):
        tool = SearchProvidersTool()
        result = tool._run(service_type="haircut", location="Antibes")
        
        providers = json.loads(result)
        assert isinstance(providers, list)
        assert len(providers) >= 1
        
        # Check first provider structure
        provider = providers[0]
        assert "id" in provider
        assert "name" in provider
        assert "type" in provider
        assert "address" in provider
        assert "services" in provider
        assert "latitude" in provider
        assert "longitude" in provider

    def test_search_providers_different_locations(self, mock_settings):
        tool = SearchProvidersTool()
        
        # Test default location
        result_antibes = tool._run(service_type="haircut", location="Antibes")
        providers_antibes = json.loads(result_antibes)
        
        # Test different location
        result_nice = tool._run(service_type="haircut", location="Nice")
        providers_nice = json.loads(result_nice)
        
        assert isinstance(providers_antibes, list)
        assert isinstance(providers_nice, list)
        assert len(providers_antibes) >= 1
        assert len(providers_nice) >= 1

    def test_search_providers_different_services(self, mock_settings):
        tool = SearchProvidersTool()
        
        # Test haircut
        result_haircut = tool._run(service_type="haircut")
        providers_haircut = json.loads(result_haircut)
        
        # Test massage
        result_massage = tool._run(service_type="massage")
        providers_massage = json.loads(result_massage)
        
        assert len(providers_haircut) >= 1
        assert len(providers_massage) >= 1

class TestGetAvailabilityTool:
    def test_get_availability_tool_creation(self):
        tool = GetAvailabilityTool()
        assert tool.name == "get_availability"
        assert tool.description == "Get available time slots for a provider and service"
        assert tool.args_schema is not None

    def test_get_availability_mock_data(self, mock_settings):
        tool = GetAvailabilityTool()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = tool._run(
            provider_id="1",
            service_id="101",
            date=tomorrow
        )
        
        slots = json.loads(result)
        assert isinstance(slots, list)
        assert len(slots) >= 1
        
        # Check first slot structure
        slot = slots[0]
        assert "id" in slot
        assert "start_time" in slot
        assert "end_time" in slot
        assert "available" in slot
        assert "price" in slot

    def test_get_availability_date_validation(self, mock_settings):
        tool = GetAvailabilityTool()
        
        # Test valid date format
        result = tool._run(
            provider_id="1",
            service_id="101", 
            date="2025-09-08"
        )
        slots = json.loads(result)
        assert isinstance(slots, list)

    def test_get_availability_different_providers(self, mock_settings):
        tool = GetAvailabilityTool()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Test different providers
        result1 = tool._run(provider_id="1", service_id="101", date=tomorrow)
        result2 = tool._run(provider_id="2", service_id="201", date=tomorrow)
        
        slots1 = json.loads(result1)
        slots2 = json.loads(result2)
        
        assert isinstance(slots1, list)
        assert isinstance(slots2, list)

class TestCreateBookingTool:
    def test_create_booking_tool_creation(self):
        tool = CreateBookingTool()
        assert tool.name == "create_booking"
        assert tool.description == "Create a booking for a service"
        assert tool.args_schema is not None

    def test_create_booking_mock_data(self, mock_settings):
        tool = CreateBookingTool()
        
        result = tool._run(
            provider_id="1",
            service_id="101",
            slot_id="slot_001",
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone="+33600000000"
        )
        
        booking = json.loads(result)
        assert isinstance(booking, dict)
        
        # Check booking structure
        assert "id" in booking
        assert "status" in booking
        assert "provider_name" in booking
        assert "service_name" in booking
        assert "start_time" in booking
        assert "end_time" in booking
        assert "confirmation_code" in booking
        
        # Validate booking data
        assert booking["status"] in ["confirmed", "pending"]
        assert len(booking["confirmation_code"]) > 0
        assert booking["provider_name"] != ""
        assert booking["service_name"] != ""

    def test_create_booking_confirmation_codes_unique(self, mock_settings):
        tool = CreateBookingTool()
        
        # Create multiple bookings
        result1 = tool._run(
            provider_id="1", service_id="101", slot_id="slot_001",
            customer_name="John", customer_email="john@test.com", customer_phone="+33600000001"
        )
        result2 = tool._run(
            provider_id="1", service_id="101", slot_id="slot_002", 
            customer_name="Jane", customer_email="jane@test.com", customer_phone="+33600000002"
        )
        
        booking1 = json.loads(result1)
        booking2 = json.loads(result2)
        
        # Confirmation codes should be different
        assert booking1["confirmation_code"] != booking2["confirmation_code"]

class TestCheckCalendarTool:
    def test_check_calendar_tool_creation(self):
        tool = CheckCalendarTool()
        assert tool.name == "check_calendar"
        assert tool.description == "Check user's calendar for availability"
        assert tool.args_schema is not None

    def test_check_calendar_mock_data(self, mock_settings):
        tool = CheckCalendarTool()
        
        result = tool._run(
            start_time="2025-09-08T14:00:00",
            end_time="2025-09-08T14:30:00", 
            user_id="user123"
        )
        
        calendar_check = json.loads(result)
        assert isinstance(calendar_check, dict)
        assert "available" in calendar_check
        assert isinstance(calendar_check["available"], bool)

    def test_check_calendar_different_times(self, mock_settings):
        tool = CheckCalendarTool()
        
        # Test different time slots
        result1 = tool._run(
            start_time="2025-09-08T09:00:00",
            end_time="2025-09-08T09:30:00",
            user_id="user123"
        )
        result2 = tool._run(
            start_time="2025-09-08T18:00:00", 
            end_time="2025-09-08T18:30:00",
            user_id="user123"
        )
        
        check1 = json.loads(result1)
        check2 = json.loads(result2)
        
        assert "available" in check1
        assert "available" in check2

class TestAllTools:
    def test_all_tools_list(self):
        assert len(ALL_TOOLS) == 4
        
        # Check tool types
        tools = [type(tool).__name__ for tool in ALL_TOOLS]
        assert "SearchProvidersTool" in tools
        assert "GetAvailabilityTool" in tools
        assert "CreateBookingTool" in tools
        assert "CheckCalendarTool" in tools

    def test_all_tools_have_required_attributes(self):
        for tool in ALL_TOOLS:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, '_run')
            assert isinstance(tool.name, str)
            assert isinstance(tool.description, str)
            assert len(tool.name) > 0
            assert len(tool.description) > 0