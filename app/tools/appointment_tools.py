"""
LangChain tools for appointment booking
"""
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field
from typing import Optional, List, Type
from datetime import datetime, timedelta
import json
import random
from app.core.schemas import Provider, Service, TimeSlot, Booking
from app.core.config import settings

class SearchProvidersInput(LangChainBaseModel):
    service_type: str = Field(description="Type of service (haircut, massage, etc)")
    location: Optional[str] = Field(default="Antibes", description="Location to search")
    date: Optional[str] = Field(default=None, description="Preferred date")

class SearchProvidersTool(BaseTool):
    name = "search_providers"
    description = "Search for service providers in a location"
    args_schema: Type[LangChainBaseModel] = SearchProvidersInput
    
    def _run(self, service_type: str, location: str = "Antibes", date: Optional[str] = None) -> str:
        """Execute the search"""
        # Mock data for testing
        if settings.booksy_api_key == "mock_for_now":
            providers = [
                Provider(
                    id="1",
                    name="Salon Elegance Antibes",
                    type="salon",
                    address="15 Rue de la République, Antibes",
                    latitude=43.5807,
                    longitude=7.1255,
                    services=[
                        Service(
                            id="101",
                            name="Haircut",
                            duration_minutes=30,
                            price=35.0,
                            provider_id="1"
                        ),
                        Service(
                            id="102",
                            name="Hair Color",
                            duration_minutes=90,
                            price=85.0,
                            provider_id="1"
                        )
                    ],
                    rating=4.8
                ),
                Provider(
                    id="2",
                    name="Le Barbier d'Antibes",
                    type="barber",
                    address="8 Place Nationale, Antibes",
                    latitude=43.5812,
                    longitude=7.1260,
                    services=[
                        Service(
                            id="201",
                            name="Men's Haircut",
                            duration_minutes=25,
                            price=28.0,
                            provider_id="2"
                        ),
                        Service(
                            id="202",
                            name="Beard Trim",
                            duration_minutes=15,
                            price=18.0,
                            provider_id="2"
                        )
                    ],
                    rating=4.9
                )
            ]
            
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
    name = "get_availability"
    description = "Get available time slots for a provider and service"
    args_schema: Type[LangChainBaseModel] = GetAvailabilityInput
    
    def _run(self, provider_id: str, service_id: str, date: str) -> str:
        """Get available slots"""
        # Mock data
        if settings.booksy_api_key == "mock_for_now":
            slots = []
            base_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Generate slots from 9 AM to 6 PM
            for hour in range(9, 18):
                for minute in [0, 30]:
                    start_time = base_date.replace(hour=hour, minute=minute)
                    end_time = start_time + timedelta(minutes=30)
                    
                    slots.append(TimeSlot(
                        id=f"{provider_id}_{service_id}_{hour}_{minute}",
                        start_time=start_time,
                        end_time=end_time,
                        available=random.random() > 0.3,  # 70% availability
                        price=35.0 if service_id == "101" else 28.0
                    ))
            
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
    name = "create_booking"
    description = "Create a booking for a service"
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
            booking = Booking(
                id=f"BOOK_{datetime.now().timestamp()}",
                status="confirmed",
                provider_name="Salon Elegance" if provider_id == "1" else "Le Barbier",
                service_name="Haircut",
                start_time=datetime.now() + timedelta(days=1, hours=14),
                end_time=datetime.now() + timedelta(days=1, hours=14, minutes=30),
                confirmation_code=f"CONF{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))}"
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
    name = "check_calendar"
    description = "Check user's calendar for availability"
    args_schema: Type[LangChainBaseModel] = CheckCalendarInput
    
    def _run(self, start_time: str, end_time: str, user_id: str) -> str:
        """Check calendar availability"""
        # Mock response - always available for now
        return json.dumps({
            "available": True,
            "conflicts": []
        })
    
    async def _arun(self, start_time: str, end_time: str, user_id: str) -> str:
        return self._run(start_time, end_time, user_id)

# Export all tools
ALL_TOOLS = [
    SearchProvidersTool(),
    GetAvailabilityTool(),
    CreateBookingTool(),
    CheckCalendarTool()
]