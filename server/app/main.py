from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import json
import base64
import asyncio
from .config import settings

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Chat Agent API",
    version="1.0.0",
    description="Production-ready voice chat with Murf Falcon TTS and real-time ASR"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_json(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "message": "Voice Chat Agent API",
        "status": "healthy",
        "asr_provider": settings.asr_provider,
        "asr_available": bool(settings.asr_api_key),
        "tts_available": bool(settings.murf_api_key),
        "llm_available": bool(settings.openai_api_key)
    }

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})

@app.get("/config")
async def get_config():
    """Return public configuration"""
    return {
        "asr_provider": settings.asr_provider,
        "asr_available": bool(settings.asr_api_key),
        "tts_available": bool(settings.murf_api_key),
        "supported_voices": [
            {"id": "en_us_001", "name": "Falcon US English", "language": "en-US"},
            {"id": "en_uk_001", "name": "Falcon UK English", "language": "en-GB"},
            {"id": "en_au_001", "name": "Falcon Australian English", "language": "en-AU"}
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("🔌 New WebSocket connection established")
    
    # Import providers here to avoid circular imports
    from .asr_providers.assemblyai import AssemblyAIASR
    from .asr_providers.deepgram import DeepgramASR
    from .murf import MurfTTS
    from .llm import LLMProcessor
    
    # Initialize providers
    asr_provider = None
    tts_provider = None
    llm_processor = None
    
    try:
        # Initialize ASR provider
               # Initialize ASR provider
        if settings.asr_api_key:
            try:
                logger.info(f"Initializing {settings.asr_provider} ASR provider...")
                if settings.asr_provider == "assemblyai":
                    asr_provider = AssemblyAIASR(settings.asr_api_key)
                else:
                    asr_provider = DeepgramASR(settings.asr_api_key)
                
                await asr_provider.start_session()
                logger.info(f"✅ {settings.asr_provider} ASR provider initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize ASR provider: {e}")
                # Even if initialization fails, create a demo provider
                asr_provider = AssemblyAIASR("demo")
                await asr_provider.start_session()
                logger.info("🔄 Using demo ASR provider as fallback")
        else:
            logger.warning("No ASR API key provided - using demo mode")
            asr_provider = AssemblyAIASR("demo")
            await asr_provider.start_session()
        
        # Initialize TTS provider
        if settings.murf_api_key:
            try:
                tts_provider = MurfTTS(settings.murf_api_key)
                logger.info("✅ Murf TTS provider initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Murf TTS: {e}")
                tts_provider = None
        else:
            logger.warning("No Murf API key provided - TTS functionality disabled")
        
        # Initialize LLM processor
        if settings.openai_api_key:
            llm_processor = LLMProcessor(settings.openai_api_key)
            logger.info("✅ OpenAI LLM processor initialized")
        else:
            llm_processor = LLMProcessor()
            logger.info("⚡ Using fallback LLM responses")
        
        current_voice = "en_us_001"
        is_recording = False
        
        async def handle_asr_transcript(transcript: str, is_final: bool):
            """Handle ASR transcript results"""
            logger.info(f"🎤 ASR Transcript (final={is_final}): {transcript}")
            
            await manager.send_json(websocket, {
                "type": "transcript",
                "text": transcript,
                "is_final": is_final,
                "speaker": "user"
            })
            
            # If final transcript, process with LLM and generate TTS
            if is_final and transcript.strip():
                try:
                    logger.info(f"🤖 Processing query: {transcript}")
                    
                    # Get response from LLM
                    response_text = await llm_processor.process_query(transcript)
                    logger.info(f"🤖 LLM Response: {response_text}")
                    
                    await manager.send_json(websocket, {
                        "type": "transcript",
                        "text": response_text,
                        "is_final": True,
                        "speaker": "agent"
                    })
                    
                    # Generate TTS audio if Murf is available
                    if tts_provider and response_text:
                        logger.info(f"🔊 Generating TTS for: {response_text}")
                        try:
                            audio_chunks = []
                            async for audio_chunk in tts_provider.stream_tts(
                                response_text, 
                                voice=current_voice
                            ):
                                if audio_chunk and len(audio_chunk) > 0:
                                    audio_chunks.append(audio_chunk)
                                    await manager.send_json(websocket, {
                                        "type": "audio_chunk",
                                        "payload": base64.b64encode(audio_chunk).decode('utf-8')
                                    })
                                    logger.info(f"🔊 Sent audio chunk: {len(audio_chunk)} bytes")
                            
                            if audio_chunks:
                                total_audio = sum(len(chunk) for chunk in audio_chunks)
                                logger.info(f"✅ TTS completed: {total_audio} total bytes sent")
                            else:
                                logger.warning("❌ No audio chunks generated by TTS")
                                
                        except Exception as e:
                            logger.error(f"❌ TTS generation error: {e}")
                            await manager.send_json(websocket, {
                                "type": "error",
                                "message": f"TTS Error: {str(e)}"
                            })
                    else:
                        logger.warning("⚠️ TTS not available - skipping audio generation")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing response: {e}")
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": f"Failed to generate response: {str(e)}"
                    })
        
        # Set ASR callback if ASR provider is available
        if asr_provider:
            asr_provider.set_callback(handle_asr_transcript)
            logger.info("✅ ASR callback set")
        
        # Send initial status
        await manager.send_json(websocket, {
            "type": "status",
            "status": "connected",
            "message": "Voice chat agent ready",
            "capabilities": {
                "asr": asr_provider is not None,
                "tts": tts_provider is not None,
                "llm": llm_processor is not None
            }
        })
        logger.info("✅ Initial status sent to client")
        
        # Main message loop
        while True:
            try:
                data = await websocket.receive()
                logger.debug(f"📥 Received WebSocket data type: {list(data.keys())}")
                
                if "text" in data:
                    message_data = json.loads(data["text"])
                    message_type = message_data.get("type")
                    logger.info(f"📥 Received message: {message_type}")
                    
                    if message_type == "start":
                        if asr_provider:
                            await asr_provider.start_stream()
                            is_recording = True
                            await manager.send_json(websocket, {
                                "type": "status", 
                                "status": "recording"
                            })
                            logger.info("🎤 Recording started - ready for audio")
                        else:
                            await manager.send_json(websocket, {
                                "type": "error",
                                "message": "ASR not available - cannot start recording"
                            })
                            
                    elif message_type == "stop":
                        if asr_provider:
                            await asr_provider.stop_stream()
                        is_recording = False
                        await manager.send_json(websocket, {
                            "type": "status", 
                            "status": "stopped"
                        })
                        logger.info("⏹️ Recording stopped")
                        
                    elif message_type == "config":
                        current_voice = message_data.get("voice", current_voice)
                        logger.info(f"⚙️ Configuration updated: voice={current_voice}")
                
                elif "bytes" in data:
                    # Handle binary audio data
                    audio_data = data["bytes"]
                    logger.debug(f"🎵 Received audio chunk: {len(audio_data)} bytes")
                    
                    if is_recording and asr_provider:
                        await asr_provider.process_audio(audio_data)
                    elif is_recording and not asr_provider:
                        logger.warning("⚠️ Audio received but no ASR provider available")
                    
            except Exception as e:
                logger.error(f"❌ Error processing WebSocket message: {e}")
                await manager.send_json(websocket, {
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await manager.send_json(websocket, {
            "type": "error",
            "message": f"Connection error: {str(e)}"
        })
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up WebSocket connection...")
        if asr_provider:
            await asr_provider.close_session()
        manager.disconnect(websocket)
        logger.info("✅ WebSocket connection cleaned up")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)