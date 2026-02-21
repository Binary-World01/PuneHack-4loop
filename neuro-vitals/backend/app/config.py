"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Neuro-Vitals"
    VERSION: str = "1.0.0"
    
    # AI Model Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    MODEL_PROVIDER: str = "openai"  # "openai", "anthropic", or "mock"
    
    # Feature Flags
    ENABLE_ADVERSARIAL: bool = True
    ENABLE_TRAJECTORY: bool = True
    ENABLE_COMMUNITY: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
