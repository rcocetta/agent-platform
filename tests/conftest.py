"""
Test configuration and fixtures
"""
import pytest
import os
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-development-only"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"

from main import app
from app.core.schemas import Message, MessageRole, Provider, Service, TimeSlot, Booking

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_message():
    """Sample message for testing"""
    return Message(
        role=MessageRole.USER,
        content="Test message",
        timestamp=datetime.utcnow()
    )

@pytest.fixture
def sample_provider():
    """Sample provider for testing"""
    return Provider(
        id="test-provider-1",
        name="Test Salon",
        type="salon",
        address="123 Test Street",
        latitude=43.5807,
        longitude=7.1255,
        services=[
            Service(
                id="service-1",
                name="Haircut",
                duration_minutes=30,
                price=35.0,
                provider_id="test-provider-1"
            )
        ],
        rating=4.5
    )

@pytest.fixture
def sample_time_slot():
    """Sample time slot for testing"""
    return TimeSlot(
        id="slot-1",
        start_time=datetime(2025, 9, 8, 14, 0),
        end_time=datetime(2025, 9, 8, 14, 30),
        available=True,
        price=35.0
    )

@pytest.fixture
def sample_booking():
    """Sample booking for testing"""
    return Booking(
        id="booking-1",
        status="confirmed",
        provider_name="Test Salon",
        service_name="Haircut",
        start_time=datetime(2025, 9, 8, 14, 0),
        end_time=datetime(2025, 9, 8, 14, 30),
        confirmation_code="TEST123"
    )

@pytest.fixture(autouse=True)
def reset_session_state():
    """Reset session state between tests"""
    from app.api.session import sessions
    sessions.clear()
    yield
    sessions.clear()

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch("app.core.config.settings") as mock:
        mock.booksy_api_key = "mock_for_now"
        mock.anthropic_api_key = "sk-ant-test-key"
        mock.debug = True
        mock.environment = "testing"
        yield mock