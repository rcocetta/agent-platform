"""
LangChain tools for appointment booking
"""
from langchain_core.tools import BaseTool
from pydantic import BaseModel as LangChainBaseModel, Field
from typing import Optional, List, Type
from datetime import datetime, timedelta
import json
from app.core.schemas import Provider, Service, TimeSlot, Booking
from app.core.config import settings
from app.mocks.appointment_mocks import (
    get_mock_providers,
    generate_mock_availability,
    create_mock_booking,
    get_mock_calendar_availability
)

class SearchProvidersInput(LangChainBaseModel):
    service_type: str = Field(description="Type of service (haircut, massage, etc)")
    location: Optional[str] = Field(default="Antibes", description="Location to search")
    date: Optional[str] = Field(default=None, description="Preferred date")

class SearchProvidersTool(BaseTool):
    name: str = "search_providers"
    description: str = "Search for service providers in a location"
    args_schema: Type[LangChainBaseModel] = SearchProvidersInput
    
    def _run(self, service_type: str, location: str = "Antibes", date: Optional[str] = None) -> str:
        """Execute the search"""
        # Mock data for testing
        if settings.booksy_api_key == "mock_for_now":
            providers = get_mock_providers()
            return json.dumps([p.dict() for p in providers])
        
        # Real API call would go here
        return "[]"
    
    async def _arun(self, service_type: str, location: str = "Antibes", date: Optional[str] = None) -> str:
        """Async version"""
        return self._run(service_type, location, date)

class GetAvailabilityInput(LangChainBaseModel):
    provider_id: str = Field(description="Provider ID")
    service_id: str = Field(description="Service ID")
    date: str = Field(description="Date to check availability (YYYY-MM-DD)")

class GetAvailabilityTool(BaseTool):
    name: str = "get_availability"
    description: str = "Get available time slots for a provider and service"
    args_schema: Type[LangChainBaseModel] = GetAvailabilityInput
    
    def _run(self, provider_id: str, service_id: str, date: str) -> str:
        """Get available slots"""
        # Mock data
        if settings.booksy_api_key == "mock_for_now":
            slots = generate_mock_availability(provider_id, service_id, date)
            return json.dumps([s.dict() for s in slots], default=str)
        
        return "[]"
    
    async def _arun(self, provider_id: str, service_id: str, date: str) -> str:
        return self._run(provider_id, service_id, date)

class CreateBookingInput(LangChainBaseModel):
    provider_id: str = Field(description="Provider ID")
    service_id: str = Field(description="Service ID")
    slot_id: str = Field(description="Time slot ID")
    customer_name: str = Field(description="Customer name")
    customer_email: str = Field(description="Customer email")
    customer_phone: str = Field(description="Customer phone")

class CreateBookingTool(BaseTool):
    name: str = "create_booking"
    description: str = "Create a booking for a service"
    args_schema: Type[LangChainBaseModel] = CreateBookingInput
    
    def _run(
        self, 
        provider_id: str, 
        service_id: str, 
        slot_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str
    ) -> str:
        """Create the booking"""
        # Mock booking
        if settings.booksy_api_key == "mock_for_now":
            booking = create_mock_booking(
                provider_id, service_id, slot_id, 
                customer_name, customer_email, customer_phone
            )
            return booking.json()
        
        return "{}"
    
    async def _arun(
        self,
        provider_id: str, 
        service_id: str, 
        slot_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str
    ) -> str:
        return self._run(provider_id, service_id, slot_id, customer_name, customer_email, customer_phone)

class CheckCalendarInput(LangChainBaseModel):
    start_time: str = Field(description="Start time to check")
    end_time: str = Field(description="End time to check")
    user_id: str = Field(description="User ID")

class CheckCalendarTool(BaseTool):
    name: str = "check_calendar"
    description: str = "Check user's calendar for availability"
    args_schema: Type[LangChainBaseModel] = CheckCalendarInput
    
    def _run(self, start_time: str, end_time: str, user_id: str) -> str:
        """Check calendar availability"""
        # Mock response - always available for now
        if settings.booksy_api_key == "mock_for_now":
            calendar_data = get_mock_calendar_availability(start_time, end_time, user_id)
            return json.dumps(calendar_data)
        
        # Real API call would go here
        return json.dumps({"available": True, "conflicts": []})
    
    async def _arun(self, start_time: str, end_time: str, user_id: str) -> str:
        return self._run(start_time, end_time, user_id)

# Export all tools
ALL_TOOLS = [
    SearchProvidersTool(),
    GetAvailabilityTool(),
    CreateBookingTool(),
    CheckCalendarTool()
]