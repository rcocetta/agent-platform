"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException
from app.core.schemas import ChatRequest, ChatResponse, Message, MessageRole
from app.graphs.simple_appointment_graph import SimpleAppointmentGraph
from app.api.session import create_session, add_message_to_session
import uuid
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the appointment graph
try:
    appointment_graph = SimpleAppointmentGraph()
except Exception as e:
    logger.error(f"Failed to initialize SimpleAppointmentGraph: {e}")
    appointment_graph = None

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process a chat message using the appointment booking agent
    """
    try:
        # Create session if not provided
        session_id = request.session_id or create_session()
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.message,
            timestamp=datetime.utcnow(),
            metadata=request.metadata
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
                    message=request.message,
                    user_id=request.user_id,
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
                logger.error(f"Error processing chat request: {e}")
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
                "channel": request.channel,
                "user_id": request.user_id
            },
            actions_taken=actions_taken
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

