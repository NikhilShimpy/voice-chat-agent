import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        # ASR Configuration
        self.asr_provider = os.getenv("ASR_PROVIDER", "assemblyai")
        self.asr_api_key = os.getenv("ASR_API_KEY")
        self.murf_api_key = os.getenv("MURF_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Server Configuration
        self.port = int(os.getenv("PORT", "8000"))
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        
        # CORS
        self.allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000", 
            "http://127.0.0.1:5173",
            "http://localhost:5174"
        ]
        
        # Debug: Print all environment variables
        print("🔍 Environment Variables Check:")
        print(f"   Current Directory: {os.getcwd()}")
        print(f"   .env file exists: {os.path.exists('.env')}")
        print(f"   ASR_PROVIDER: {os.getenv('ASR_PROVIDER')}")
        print(f"   ASR_API_KEY: {'✅ SET' if self.asr_api_key else '❌ MISSING'}")
        print(f"   MURF_API_KEY: {'✅ SET' if self.murf_api_key else '❌ MISSING'}")
        print(f"   OPENAI_API_KEY: {'✅ SET' if self.openai_api_key else '❌ NOT SET'}")

settings = Settings()