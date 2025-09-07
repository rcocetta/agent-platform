"""
Core configuration for the agent platform
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: Optional[str] = None
    
    # Database
    database_url: str = "postgresql://localhost/agent_platform"
    redis_url: str = "redis://localhost:6379"
    
    # Auth
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    booksy_api_key: Optional[str] = "mock_for_now"
    google_calendar_client_id: Optional[str] = None
    google_calendar_client_secret: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # App settings
    app_name: str = "Agent Platform"
    debug: bool = True
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()