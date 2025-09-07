"""
Session management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.core.schemas import Message
import uuid
from datetime import datetime

router = APIRouter()

# In-memory session storage (replace with database in production)
sessions: Dict[str, List[Message]] = {}

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session history by session ID
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": sessions[session_id],
        "message_count": len(sessions[session_id])
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its history
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {"message": f"Session {session_id} deleted successfully"}

@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    session_list = []
    for session_id, messages in sessions.items():
        session_list.append({
            "session_id": session_id,
            "message_count": len(messages),
            "last_message": messages[-1].timestamp if messages else None
        })
    
    return {"sessions": session_list}

def create_session() -> str:
    """Create a new session and return its ID"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return session_id

def add_message_to_session(session_id: str, message: Message):
    """Add a message to a session"""
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append(message)