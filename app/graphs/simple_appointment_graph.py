"""
Simplified LangGraph workflow for appointment booking
"""
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.tools.appointment_tools import ALL_TOOLS
import json

class SimpleAppointmentGraph:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.3
        )
        self.tools = ALL_TOOLS
    
    def run(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Simple workflow without LangGraph for now"""
        try:
            # Step 1: Parse intent
            intent_result = self.parse_intent(message)
            
            if intent_result["intent"] == "unknown":
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I can help you book appointments. Try saying 'Book me a haircut tomorrow at 2pm'"
                    }],
                    "actions_taken": []
                }
            
            # Step 2: Search providers
            search_result = self.search_providers(intent_result["entities"])
            
            # Step 3: Get availability for first provider
            if search_result:
                availability_result = self.get_availability(search_result[0])
                
                # Step 4: Create booking with first available slot
                if availability_result:
                    booking_result = self.create_booking(search_result[0], availability_result[0])
                    
                    return {
                        "messages": [{
                            "role": "assistant", 
                            "content": f"✅ Your appointment is confirmed!\n\n📍 {booking_result.get('provider_name')}\n💇 {booking_result.get('service_name')}\n📅 {booking_result.get('start_time')}\n🎫 Confirmation: {booking_result.get('confirmation_code')}\n\nYou'll receive a confirmation SMS shortly."
                        }],
                        "search_results": search_result,
                        "available_slots": availability_result,
                        "booking": booking_result,
                        "actions_taken": ["searched_providers", "checked_availability", "created_booking"]
                    }
                else:
                    return {
                        "messages": [{
                            "role": "assistant",
                            "content": f"Found {search_result[0]['name']} but no available slots for your preferred time. Please try a different time."
                        }],
                        "search_results": search_result,
                        "actions_taken": ["searched_providers", "checked_availability"]
                    }
            else:
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I couldn't find any providers for your request. Please try a different service or location."
                    }],
                    "actions_taken": ["searched_providers"]
                }
                
        except Exception as e:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": f"I encountered an error: {str(e)}. Please try again."
                }],
                "actions_taken": ["error"]
            }
    
    def parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse user intent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an appointment booking assistant. 
            Analyze the user's message and extract:
            1. Intent: search, book, check, or unknown
            2. Service type: haircut, massage, etc.
            3. Date/time preference
            4. Location preference
            
            Respond in JSON format:
            {
                "intent": "book",
                "service": "haircut", 
                "datetime": "tomorrow at 2pm",
                "location": "Antibes"
            }"""),
            ("user", message)
        ])
        
        # Use simple keyword matching for testing (since we don't have a real Anthropic API key)
        try:
            message_lower = message.lower()
            
            # Simple keyword-based intent detection
            if any(word in message_lower for word in ["book", "schedule", "appointment", "reserve"]):
                intent = "book"
            elif any(word in message_lower for word in ["search", "find", "look for"]):
                intent = "search"
            elif any(word in message_lower for word in ["check", "calendar"]):
                intent = "check"
            else:
                intent = "unknown"
            
            # Simple entity extraction
            service = "haircut"  # default
            if "massage" in message_lower:
                service = "massage"
            elif "haircut" in message_lower or "hair" in message_lower:
                service = "haircut"
                
            location = "Antibes"  # default
            if "nice" in message_lower:
                location = "Nice"
            elif "cannes" in message_lower:
                location = "Cannes"
                
            entities = {
                "service": service,
                "location": location,
                "datetime": "tomorrow at 2pm"
            }
            
            return {
                "intent": intent,
                "entities": entities
            }
        except:
            return {"intent": "unknown", "entities": {}}
    
    def search_providers(self, entities: Dict[str, Any]) -> list:
        """Search for providers"""
        search_tool = self.tools[0]  # SearchProvidersTool
        result = search_tool._run(
            service_type=entities.get("service", "haircut"),
            location=entities.get("location", "Antibes")
        )
        return json.loads(result)
    
    def get_availability(self, provider: Dict[str, Any]) -> list:
        """Get availability"""
        if not provider.get("services"):
            return []
            
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        availability_tool = self.tools[1]  # GetAvailabilityTool
        result = availability_tool._run(
            provider_id=provider["id"],
            service_id=provider["services"][0]["id"],
            date=tomorrow
        )
        slots = json.loads(result)
        return [s for s in slots if s["available"]][:3]  # Top 3 slots
    
    def create_booking(self, provider: Dict[str, Any], slot: Dict[str, Any]) -> Dict[str, Any]:
        """Create a booking"""
        booking_tool = self.tools[2]  # CreateBookingTool
        result = booking_tool._run(
            provider_id=provider["id"],
            service_id=provider["services"][0]["id"],
            slot_id=slot["id"],
            customer_name="User Name",
            customer_email="user@example.com", 
            customer_phone="+33600000000"
        )
        return json.loads(result)