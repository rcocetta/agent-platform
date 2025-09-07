"""
LangGraph workflow for appointment booking
"""
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import ToolException
from typing import Dict, Any, List
import json
from app.core.schemas import AgentState, Message, MessageRole
from app.core.config import settings
from app.tools.appointment_tools import ALL_TOOLS

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
    
    async def parse_intent(self, state: AgentState) -> Dict[str, Any]:
        """Parse user intent from the message"""
        last_message = state.messages[-1].content if state.messages else ""
        
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
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            extracted = json.loads(response.content)
            state.current_intent = extracted.get("intent", "unknown")
            state.extracted_entities = extracted
        except:
            state.current_intent = "unknown"
            state.extracted_entities = {}
        
        return {"current_intent": state.current_intent, "extracted_entities": state.extracted_entities}
    
    def route_intent(self, state: AgentState) -> str:
        """Route based on parsed intent"""
        intent = state.current_intent
        if intent in ["search", "book"]:
            return "search"
        elif intent == "check":
            return "check"
        else:
            return "unknown"
    
    async def search_providers(self, state: AgentState) -> Dict[str, Any]:
        """Search for service providers"""
        entities = state.extracted_entities
        service_type = entities.get("service", "haircut")
        location = entities.get("location", "Antibes")
        
        # Use the search tool
        search_tool = self.tools[0]  # SearchProvidersTool
        result = await search_tool.arun(
            service_type=service_type,
            location=location
        )
        
        providers = json.loads(result)
        state.search_results = providers
        
        # Add to messages
        state.messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=f"Found {len(providers)} providers in {location}"
        ))
        
        return {"search_results": providers, "messages": state.messages}
    
    async def get_availability(self, state: AgentState) -> Dict[str, Any]:
        """Get availability for the first provider"""
        if not state.search_results:
            return state
        
        provider = state.search_results[0]
        service = provider["services"][0] if provider["services"] else None
        
        if not service:
            return state
        
        # Use the availability tool
        availability_tool = self.tools[1]  # GetAvailabilityTool
        result = await availability_tool.arun(
            provider_id=provider["id"],
            service_id=service["id"],
            date="2024-11-10"  # Tomorrow - would be dynamic in production
        )
        
        slots = json.loads(result)
        available_slots = [s for s in slots if s["available"]][:3]  # Top 3 slots
        state.available_slots = available_slots
        
        return {"available_slots": available_slots}
    
    async def check_calendar(self, state: AgentState) -> Dict[str, Any]:
        """Check user's calendar"""
        if not state.available_slots:
            return state
        
        # Use calendar check tool
        calendar_tool = self.tools[3]  # CheckCalendarTool
        slot = state.available_slots[0]
        
        result = await calendar_tool.arun(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            user_id=state.user_id
        )
        
        calendar_check = json.loads(result)
        
        if not calendar_check["available"]:
            # Try next slot
            if len(state.available_slots) > 1:
                state.available_slots = state.available_slots[1:]
        
        return state
    
    async def create_booking(self, state: AgentState) -> Dict[str, Any]:
        """Create the booking"""
        if not state.available_slots or not state.search_results:
            return state
        
        provider = state.search_results[0]
        service = provider["services"][0]
        slot = state.available_slots[0]
        
        # Use booking tool
        booking_tool = self.tools[2]  # CreateBookingTool
        result = await booking_tool.arun(
            provider_id=provider["id"],
            service_id=service["id"],
            slot_id=slot["id"],
            customer_name="User Name",  # Would come from user profile
            customer_email="user@example.com",
            customer_phone="+33600000000"
        )
        
        booking = json.loads(result)
        state.booking = booking
        
        return {"booking": booking}
    
    async def send_confirmation(self, state: AgentState) -> Dict[str, Any]:
        """Send booking confirmation"""
        if not state.booking:
            return state
        
        # In production, would send SMS/email here
        state.messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=f"Booking confirmed! Confirmation code: {state.booking.get('confirmation_code', 'N/A')}"
        ))
        
        return {"messages": state.messages}
    
    async def generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate final response to user"""
        if state.booking:
            booking = state.booking
            response = f"""✅ Your appointment is confirmed!

📍 {booking.get('provider_name', 'Provider')}
💇 {booking.get('service_name', 'Service')}
📅 {booking.get('start_time', 'Time')}
🎫 Confirmation: {booking.get('confirmation_code', 'N/A')}

You'll receive a confirmation SMS shortly."""
        
        elif state.search_results:
            providers = state.search_results[:3]
            response = "I found these options for you:\n\n"
            for i, p in enumerate(providers, 1):
                response += f"{i}. {p['name']} - {p['address']}\n"
                if p['services']:
                    response += f"   Services: {', '.join(s['name'] for s in p['services'][:2])}\n"
        
        else:
            response = "I can help you book appointments. Try saying 'Book me a haircut tomorrow at 2pm'"
        
        state.messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=response
        ))
        
        return {"messages": state.messages}
    
    async def run(self, message: str, user_id: str, session_id: str) -> str:
        """Run the graph with a user message"""
        initial_state = AgentState(
            messages=[Message(role=MessageRole.USER, content=message)],
            user_id=user_id,
            session_id=session_id
        )
        
        result = await self.app.ainvoke(initial_state)
        
        # Return the last assistant message
        assistant_messages = [m for m in result["messages"] if m.role == MessageRole.ASSISTANT]
        return assistant_messages[-1].content if assistant_messages else "I couldn't process that request."