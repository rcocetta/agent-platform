"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.schemas import ChatRequest, ChatResponse, Message, MessageRole
from app.graphs.simple_appointment_graph import SimpleAppointmentGraph
from app.api.session import create_session, add_message_to_session
import uuid
from datetime import datetime
import logging

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the appointment graph
try:
    appointment_graph = SimpleAppointmentGraph()
except Exception as e:
    logger.error(f"Failed to initialize SimpleAppointmentGraph: {e}")
    appointment_graph = None

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # Prevent API abuse and cost explosion
async def process_chat(request: Request, chat_request: ChatRequest):
    """
    Process a chat message using the appointment booking agent
    """
    try:
        # Get client IP for session management
        client_ip = get_remote_address(request)
        
        # Create session if not provided
        session_id = chat_request.session_id or create_session(client_ip)
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=chat_request.message,
            timestamp=datetime.utcnow(),
            metadata=chat_request.metadata
        )
        
        # Add user message to session
        add_message_to_session(session_id, user_message)
        
        # Check if appointment graph is available
        if appointment_graph is None:
            # Fallback response if graph isn't initialized
            response_text = "I'm sorry, the appointment booking service is currently unavailable. Please try again later."
            actions_taken = ["service_unavailable"]
        else:
            # Process through the appointment graph
            try:
                # Run the graph synchronously
                result = appointment_graph.run(
                    message=chat_request.message,
                    user_id=chat_request.user_id,
                    session_id=session_id
                )
                
                # Extract response from the result
                messages = result.get("messages", [])
                if messages:
                    response_text = messages[-1]["content"]
                else:
                    response_text = "I processed your request, but I don't have a specific response at the moment."
                
                # Extract actions taken
                actions_taken = result.get("actions_taken", [])
                    
            except Exception as e:
                # Log error without exposing user data
                logger.error(f"Error processing chat request: {type(e).__name__} - {str(e)[:100]}")
                response_text = "I encountered an error while processing your request. Please try again."
                actions_taken = ["error"]
        
        # Create assistant message
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.utcnow()
        )
        
        # Add assistant message to session
        add_message_to_session(session_id, assistant_message)
        
        # Create response
        response = ChatResponse(
            response=response_text,
            session_id=session_id,
            metadata={
                "channel": chat_request.channel,
                "user_id": chat_request.user_id
            },
            actions_taken=actions_taken
        )
        
        return response
        
    except Exception as e:
        # Log error without exposing sensitive data
        logger.error(f"Unexpected error in chat endpoint: {type(e).__name__} - {str(e)[:100]}")
        raise HTTPException(status_code=500, detail="Internal server error")

