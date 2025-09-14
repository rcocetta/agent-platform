"""
LangGraph workflow for appointment booking
"""
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import ToolException
from typing import Dict, Any, List
import json
from app.core.schemas import AgentState, Message, MessageRole
from app.core.config import settings
from app.tools.appointment_tools import ALL_TOOLS
from app.mocks.appointment_mocks import get_mock_customer_data
from app.graphs.appointment_constants import get_booking_confirmation_template, DEFAULT_HELP_MESSAGE

class AppointmentGraph:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.3
        )
        self.tools = ALL_TOOLS
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", self.parse_intent)
        workflow.add_node("search_providers", self.search_providers)
        workflow.add_node("get_availability", self.get_availability)
        workflow.add_node("check_calendar", self.check_calendar)
        workflow.add_node("create_booking", self.create_booking)
        workflow.add_node("send_confirmation", self.send_confirmation)
        workflow.add_node("generate_response", self.generate_response)
        
        # Add edges
        workflow.set_entry_point("parse_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "parse_intent",
            self.route_intent,
            {
                "search": "search_providers",
                "book": "search_providers",
                "check": "check_calendar",
                "unknown": "generate_response"
            }
        )
        
        workflow.add_edge("search_providers", "get_availability")
        workflow.add_edge("get_availability", "check_calendar")
        workflow.add_edge("check_calendar", "create_booking")
        workflow.add_edge("create_booking", "send_confirmation")
        workflow.add_edge("send_confirmation", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow
    
    def parse_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user intent from the message"""
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        
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
            ("user", last_message)
        ])
        
        try:
            # Use sync invoke instead of async
            response = self.llm.invoke(prompt.format_messages())
            extracted = json.loads(response.content)
            current_intent = extracted.get("intent", "unknown")
            extracted_entities = extracted
        except Exception as e:
            current_intent = "unknown"
            extracted_entities = {}
        
        return {"current_intent": current_intent, "extracted_entities": extracted_entities}
    
    def route_intent(self, state: Dict[str, Any]) -> str:
        """Route based on parsed intent"""
        intent = state.get("current_intent", "unknown")
        if intent in ["search", "book"]:
            return "search"
        elif intent == "check":
            return "check"
        else:
            return "unknown"
    
    def search_providers(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search for service providers"""
        entities = state.get("extracted_entities", {})
        service_type = entities.get("service", "haircut")
        location = entities.get("location", "Antibes")
        
        # Use the search tool
        search_tool = self.tools[0]  # SearchProvidersTool
        result = search_tool._run(
            service_type=service_type,
            location=location
        )
        
        providers = json.loads(result)
        
        # Create updated messages list
        messages = state.get("messages", [])
        messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=f"Found {len(providers)} providers in {location}"
        ))
        
        return {"search_results": providers, "messages": messages}
    
    def get_availability(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get availability for the first provider"""
        search_results = state.get("search_results", [])
        if not search_results:
            return {}
        
        provider = search_results[0]
        service = provider["services"][0] if provider["services"] else None
        
        if not service:
            return {}
        
        # Use the availability tool
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        availability_tool = self.tools[1]  # GetAvailabilityTool
        result = availability_tool._run(
            provider_id=provider["id"],
            service_id=service["id"],
            date=tomorrow
        )
        
        slots = json.loads(result)
        available_slots = [s for s in slots if s["available"]][:3]  # Top 3 slots
        
        return {"available_slots": available_slots}
    
    def check_calendar(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check user's calendar"""
        available_slots = state.get("available_slots", [])
        if not available_slots:
            return {}
        
        # Use calendar check tool
        calendar_tool = self.tools[3]  # CheckCalendarTool
        slot = available_slots[0]
        user_id = state.get("user_id", "default_user")
        
        result = calendar_tool._run(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            user_id=user_id
        )
        
        calendar_check = json.loads(result)
        
        # If not available, try next slot
        if not calendar_check["available"] and len(available_slots) > 1:
            available_slots = available_slots[1:]
        
        return {"available_slots": available_slots}
    
    def create_booking(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create the booking"""
        available_slots = state.get("available_slots", [])
        search_results = state.get("search_results", [])
        
        if not available_slots or not search_results:
            return {}
        
        provider = search_results[0]
        service = provider["services"][0]
        slot = available_slots[0]
        
        # Use booking tool
        booking_tool = self.tools[2]  # CreateBookingTool
        mock_customer = get_mock_customer_data()
        result = booking_tool._run(
            provider_id=provider["id"],
            service_id=service["id"],
            slot_id=slot["id"],
            customer_name=mock_customer["name"],
            customer_email=mock_customer["email"],
            customer_phone=mock_customer["phone"]
        )
        
        booking = json.loads(result)
        
        return {"booking": booking}
    
    def send_confirmation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send booking confirmation"""
        booking = state.get("booking")
        if not booking:
            return {}
        
        # In production, would send SMS/email here
        messages = state.get("messages", [])
        messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=f"Booking confirmed! Confirmation code: {booking.get('confirmation_code', 'N/A')}"
        ))
        
        return {"messages": messages}
    
    def generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response to user"""
        booking = state.get("booking")
        search_results = state.get("search_results", [])
        messages = state.get("messages", [])
        
        if booking:
            response = get_booking_confirmation_template(booking)
        
        elif search_results:
            providers = search_results[:3]
            response = "I found these options for you:\n\n"
            for i, p in enumerate(providers, 1):
                response += f"{i}. {p['name']} - {p['address']}\n"
                if p['services']:
                    response += f"   Services: {', '.join(s['name'] for s in p['services'][:2])}\n"
        
        else:
            response = DEFAULT_HELP_MESSAGE
        
        messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=response
        ))
        
        return {"messages": messages}
    
    def run(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Run the graph with a user message"""
        initial_state = {
            "messages": [Message(role=MessageRole.USER, content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "current_intent": None,
            "extracted_entities": {},
            "search_results": [],
            "selected_provider": None,
            "available_slots": [],
            "booking": None
        }
        
        result = self.app.invoke(initial_state)
        return result
        
        # Return the last assistant message
        assistant_messages = [m for m in result["messages"] if m.role == MessageRole.ASSISTANT]
        return assistant_messages[-1].content if assistant_messages else "I couldn't process that request."