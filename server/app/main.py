from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from .config import settings
from .ws import router as ws_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Chat Agent API", 
    version="1.0.0",
    description="Low-latency voice chat with real-time ASR and TTS"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router
app.include_router(ws_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Voice Chat Agent API", 
        "status": "healthy",
        "version": "1.0.0",
        "asr_provider": settings.asr_provider
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return JSONResponse(content={"status": "healthy"})

@app.get("/config")
async def get_config():
    """Return public configuration (no secrets)"""
    return {
        "asr_provider": settings.asr_provider,
        "supported_voices": ["falcon_en_us", "falcon_en_uk", "falcon_en_au"],
        "supported_languages": ["en-US", "en-GB", "en-AU"],
        "features": {
            "asr": True,
            "tts": True,
            "llm": bool(settings.openai_api_key)
        }
    }

# Error handlers
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)