from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # ASR Configuration
    asr_provider: str = "assemblyai"  # assemblyai or deepgram
    asr_api_key: str
    
    # TTS Configuration
    murf_api_key: str
    
    # LLM Configuration (Optional)
    openai_api_key: str = ""
    
    # Server Configuration
    port: int = 8000
    node_env: str = "development"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-vercel-app.vercel.app"
    ]
    
    # Optional Monitoring
    sentry_dsn: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()