"""
Tests for core schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.core.schemas import (
    Message, MessageRole, ChatRequest, ChatResponse,
    TimeSlot, Service, Provider, BookingRequest, Booking,
    AgentState, ChannelType
)

class TestMessage:
    def test_message_creation(self):
        message = Message(
            role=MessageRole.USER,
            content="Hello world"
        )
        assert message.role == MessageRole.USER
        assert message.content == "Hello world"
        assert isinstance(message.timestamp, datetime)
        assert message.metadata is None

    def test_message_with_metadata(self):
        metadata = {"channel": "web", "ip": "127.0.0.1"}
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Hi there!",
            metadata=metadata
        )
        assert message.metadata == metadata

    def test_invalid_message_role(self):
        with pytest.raises(ValidationError):
            Message(role="invalid_role", content="test")

class TestChatRequest:
    def test_chat_request_minimal(self):
        request = ChatRequest(
            message="Hello",
            user_id="user123"
        )
        assert request.message == "Hello"
        assert request.user_id == "user123"
        assert request.session_id is None
        assert request.channel == ChannelType.WEB
        assert request.metadata is None

    def test_chat_request_full(self):
        request = ChatRequest(
            message="Book appointment",
            user_id="user456",
            session_id="session789",
            channel=ChannelType.WHATSAPP,
            metadata={"source": "mobile"}
        )
        assert request.message == "Book appointment"
        assert request.user_id == "user456"
        assert request.session_id == "session789"
        assert request.channel == ChannelType.WHATSAPP
        assert request.metadata == {"source": "mobile"}

class TestChatResponse:
    def test_chat_response_creation(self):
        response = ChatResponse(
            response="Your appointment is booked",
            session_id="session123"
        )
        assert response.response == "Your appointment is booked"
        assert response.session_id == "session123"
        assert response.metadata is None
        assert response.actions_taken is None

    def test_chat_response_with_actions(self):
        response = ChatResponse(
            response="Found 3 providers",
            session_id="session456",
            actions_taken=["searched_providers", "checked_availability"]
        )
        assert response.actions_taken == ["searched_providers", "checked_availability"]

class TestProvider:
    def test_provider_creation(self, sample_provider):
        assert sample_provider.id == "test-provider-1"
        assert sample_provider.name == "Test Salon"
        assert sample_provider.type == "salon"
        assert len(sample_provider.services) == 1
        assert sample_provider.rating == 4.5

    def test_provider_validation(self):
        # Test with missing required fields
        with pytest.raises(ValidationError):
            Provider(
                # Missing id, name, type, address, latitude, longitude
                services=[]
            )

class TestService:
    def test_service_creation(self):
        service = Service(
            id="service-1",
            name="Haircut",
            duration_minutes=30,
            price=35.0,
            provider_id="provider-1"
        )
        assert service.id == "service-1"
        assert service.name == "Haircut"
        assert service.duration_minutes == 30
        assert service.price == 35.0
        assert service.provider_id == "provider-1"
        assert service.description is None

    def test_service_with_description(self):
        service = Service(
            id="service-2",
            name="Massage",
            duration_minutes=60,
            price=80.0,
            provider_id="provider-1",
            description="Relaxing full body massage"
        )
        assert service.description == "Relaxing full body massage"

class TestTimeSlot:
    def test_time_slot_creation(self, sample_time_slot):
        assert sample_time_slot.id == "slot-1"
        assert sample_time_slot.available is True
        assert sample_time_slot.price == 35.0
        assert sample_time_slot.start_time < sample_time_slot.end_time

    def test_time_slot_unavailable(self):
        slot = TimeSlot(
            id="slot-2",
            start_time=datetime(2025, 9, 8, 15, 0),
            end_time=datetime(2025, 9, 8, 15, 30),
            available=False
        )
        assert slot.available is False
        assert slot.price is None

class TestBooking:
    def test_booking_creation(self, sample_booking):
        assert sample_booking.id == "booking-1"
        assert sample_booking.status == "confirmed"
        assert sample_booking.provider_name == "Test Salon"
        assert sample_booking.service_name == "Haircut"
        assert sample_booking.confirmation_code == "TEST123"
        assert isinstance(sample_booking.created_at, datetime)

class TestAgentState:
    def test_agent_state_minimal(self):
        state = AgentState(
            user_id="user123",
            session_id="session456"
        )
        assert state.user_id == "user123"
        assert state.session_id == "session456"
        assert state.messages == []
        assert state.current_intent is None
        assert state.extracted_entities == {}
        assert state.search_results is None
        assert state.selected_provider is None
        assert state.available_slots is None
        assert state.booking is None

    def test_agent_state_with_data(self, sample_message, sample_provider):
        state = AgentState(
            messages=[sample_message],
            current_intent="book",
            extracted_entities={"service": "haircut"},
            search_results=[sample_provider],
            user_id="user123",
            session_id="session456"
        )
        assert len(state.messages) == 1
        assert state.current_intent == "book"
        assert state.extracted_entities["service"] == "haircut"
        assert len(state.search_results) == 1