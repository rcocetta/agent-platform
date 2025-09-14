"""
Mock data for appointment booking tools
"""
from datetime import datetime, timedelta
from typing import List
import random
import json

from app.core.schemas import Provider, Service, TimeSlot, Booking


def get_mock_providers() -> List[Provider]:
    """Get mock providers with services"""
    return [
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


def generate_mock_availability(provider_id: str, service_id: str, date: str) -> List[TimeSlot]:
    """Generate mock time slots for a given date"""
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
    
    return slots


def create_mock_booking(
    provider_id: str,
    service_id: str,
    slot_id: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str
) -> Booking:
    """Create a mock booking"""
    return Booking(
        id=f"BOOK_{datetime.now().timestamp()}",
        status="confirmed",
        provider_name="Salon Elegance" if provider_id == "1" else "Le Barbier",
        service_name="Haircut",
        start_time=datetime.now() + timedelta(days=1, hours=14),
        end_time=datetime.now() + timedelta(days=1, hours=14, minutes=30),
        confirmation_code=f"CONF{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))}"
    )


def get_mock_calendar_availability(start_time: str, end_time: str, user_id: str) -> dict:
    """Get mock calendar availability - always available for now"""
    return {
        "available": True,
        "conflicts": []
    }


def get_mock_customer_data() -> dict:
    """Get mock customer data for booking"""
    return {
        "name": "User Name",
        "email": "user@example.com", 
        "phone": "+33600000000"
    }