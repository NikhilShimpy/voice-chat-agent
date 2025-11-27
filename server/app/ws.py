from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
import logging
from .asr_providers.assemblyai import AssemblyAIASR
from .asr_providers.deepgram import DeepgramASR
from .murf import MurfTTS
from .llm import LLMProcessor
from .config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_json(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Initialize providers based on configuration
    if settings.asr_provider == "assemblyai":
        asr_provider = AssemblyAIASR(settings.asr_api_key)
    else:
        asr_provider = DeepgramASR(settings.asr_api_key)
    
    tts_provider = MurfTTS(settings.murf_api_key)
    llm_processor = LLMProcessor(settings.openai_api_key)
    
    current_voice = "falcon_en_us"
    current_lang = "en-US"
    
    try:
        # Initialize ASR session
        await asr_provider.start_session()
        
        async def handle_asr_transcript(transcript: str, is_final: bool):
            """Handle ASR transcript results"""
            await manager.send_json(websocket, {
                "type": "transcript",
                "text": transcript,
                "is_final": is_final
            })
            
            # If final transcript, process with LLM and generate TTS
            if is_final and transcript.strip():
                try:
                    # Get response from LLM
                    response = await llm_processor.process_query(transcript)
                    
                    # Generate TTS audio
                    async for audio_chunk in tts_provider.stream_tts(response, voice=current_voice):
                        await manager.send_json(websocket, {
                            "type": "audio_chunk",
                            "payload": base64.b64encode(audio_chunk).decode('utf-8')
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": "Failed to generate response"
                    })
        
        # Set ASR callback
        asr_provider.set_callback(handle_asr_transcript)
        
        # Main message loop
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "start":
                    await asr_provider.start_stream()
                    await manager.send_json(websocket, {"type": "status", "status": "recording"})
                    
                elif msg_type == "stop":
                    await asr_provider.stop_stream()
                    await manager.send_json(websocket, {"type": "status", "status": "stopped"})
                    
                elif msg_type == "config":
                    current_voice = data.get("voice", current_voice)
                    current_lang = data.get("lang", current_lang)
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON message")
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_json(websocket, {
            "type": "error",
            "message": str(e)
        })
    finally:
        manager.disconnect(websocket)
        await asr_provider.close_session()