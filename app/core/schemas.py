"""
Base schemas for the platform
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    VOICE = "voice"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    channel: ChannelType = ChannelType.WEB
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
    actions_taken: Optional[List[str]] = None

class TimeSlot(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    available: bool = True
    price: Optional[float] = None

class Service(BaseModel):
    id: str
    name: str
    duration_minutes: int
    price: float
    provider_id: str
    description: Optional[str] = None

class Provider(BaseModel):
    id: str
    name: str
    type: str
    address: str
    latitude: float
    longitude: float
    services: List[Service]
    rating: Optional[float] = None

class BookingRequest(BaseModel):
    user_id: str
    provider_id: str
    service_id: str
    slot_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    notes: Optional[str] = None

class Booking(BaseModel):
    id: str
    status: str
    provider_name: str
    service_name: str
    start_time: datetime
    end_time: datetime
    confirmation_code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class AgentState(BaseModel):
    """State for LangGraph agents"""
    messages: List[Message] = []
    current_intent: Optional[str] = None
    extracted_entities: Dict[str, Any] = {}
    search_results: Optional[List[Provider]] = None
    selected_provider: Optional[Provider] = None
    available_slots: Optional[List[TimeSlot]] = None
    booking: Optional[Booking] = None
    user_id: str
    session_id: str