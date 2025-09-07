"""
Session management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.core.schemas import Message
import uuid
from datetime import datetime, timedelta
import asyncio
from threading import Lock
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Session configuration
MAX_SESSIONS_TOTAL = 1000
MAX_SESSIONS_PER_IP = 10
SESSION_TTL_HOURS = 24
MAX_MESSAGES_PER_SESSION = 100

# In-memory session storage with metadata
sessions: Dict[str, Dict] = {}
session_lock = Lock()

class SessionManager:
    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        with session_lock:
            for session_id, session_data in sessions.items():
                if current_time - session_data["created_at"] > timedelta(hours=SESSION_TTL_HOURS):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
        
        return len(expired_sessions)
    
    @staticmethod
    def enforce_session_limits(client_ip: str = None):
        """Enforce session limits"""
        with session_lock:
            # Total session limit
            if len(sessions) >= MAX_SESSIONS_TOTAL:
                # Remove oldest sessions
                oldest_sessions = sorted(
                    sessions.items(),
                    key=lambda x: x[1]["created_at"]
                )[:len(sessions) - MAX_SESSIONS_TOTAL + 1]
                
                for session_id, _ in oldest_sessions:
                    del sessions[session_id]
                    logger.warning(f"Removed old session due to total limit: {session_id}")
            
            # Per-IP session limit
            if client_ip:
                ip_sessions = [
                    s for s in sessions.items() 
                    if s[1].get("client_ip") == client_ip
                ]
                
                if len(ip_sessions) >= MAX_SESSIONS_PER_IP:
                    # Remove oldest sessions for this IP
                    oldest_ip_sessions = sorted(
                        ip_sessions,
                        key=lambda x: x[1]["created_at"]
                    )[:len(ip_sessions) - MAX_SESSIONS_PER_IP + 1]
                    
                    for session_id, _ in oldest_ip_sessions:
                        del sessions[session_id]
                        logger.warning(f"Removed old session for IP {client_ip}: {session_id}")

# Initialize cleanup task (started when server starts)
async def periodic_cleanup():
    while True:
        try:
            cleaned = SessionManager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        await asyncio.sleep(3600)  # Run every hour

# Cleanup task will be started by FastAPI startup event

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session history by session ID
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions[session_id]
    return {
        "session_id": session_id,
        "messages": session_data["messages"],
        "message_count": len(session_data["messages"]),
        "created_at": session_data["created_at"],
        "last_activity": session_data["last_activity"]
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
    for session_id, session_data in sessions.items():
        messages = session_data["messages"]
        session_list.append({
            "session_id": session_id,
            "message_count": len(messages),
            "created_at": session_data["created_at"],
            "last_activity": session_data["last_activity"],
            "client_ip": session_data.get("client_ip", "unknown")
        })
    
    return {"sessions": session_list, "total_sessions": len(sessions)}

def create_session(client_ip: str = None) -> str:
    """Create a new session and return its ID"""
    # Cleanup expired sessions first
    SessionManager.cleanup_expired_sessions()
    
    # Enforce limits
    SessionManager.enforce_session_limits(client_ip)
    
    session_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    
    with session_lock:
        sessions[session_id] = {
            "messages": [],
            "created_at": current_time,
            "last_activity": current_time,
            "client_ip": client_ip,
            "message_count": 0
        }
    
    return session_id

def add_message_to_session(session_id: str, message: Message):
    """Add a message to a session"""
    with session_lock:
        if session_id not in sessions:
            sessions[session_id] = {
                "messages": [],
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "client_ip": None,
                "message_count": 0
            }
        
        session_data = sessions[session_id]
        
        # Enforce message limit per session
        if len(session_data["messages"]) >= MAX_MESSAGES_PER_SESSION:
            # Remove oldest messages to make room
            session_data["messages"] = session_data["messages"][-(MAX_MESSAGES_PER_SESSION-1):]
        
        session_data["messages"].append(message)
        session_data["last_activity"] = datetime.utcnow()
        session_data["message_count"] += 1