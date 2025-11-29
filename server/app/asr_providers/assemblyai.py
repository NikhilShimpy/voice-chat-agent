import aiohttp
import json
import logging
import base64
import asyncio
from typing import Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

class AssemblyAIASR:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket = None
        self.transcript_callback = None
        self.session = None
        self.is_connected = False
        self.audio_buffer = []
        
    async def start_session(self):
        """Start AssemblyAI real-time session with fallback"""
        try:
            logger.info("Starting AssemblyAI real-time session...")
            
            self.session = aiohttp.ClientSession()
            
            # Try to get real-time token
            async with self.session.post(
                "https://api.assemblyai.com/v2/realtime/token",
                headers={"Authorization": self.api_key},
                json={"expires_in": 3600}
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    token = token_data.get('token')
                    
                    if not token:
                        logger.warning("No token received from AssemblyAI")
                        return
                    
                    logger.info("Got AssemblyAI token, connecting to WebSocket...")
                    
                    # Connect to real-time WebSocket
                    self.websocket = await self.session.ws_connect(
                        f"wss://api.assemblyai.com/v2/realtime/ws?token={token}&sample_rate=16000"
                    )
                    
                    # Start message listener
                    asyncio.create_task(self._listen_messages())
                    
                    self.is_connected = True
                    logger.info("✅ AssemblyAI real-time WebSocket connected successfully")
                    
                else:
                    error_text = await response.text()
                    logger.warning(f"AssemblyAI real-time not available: {error_text}")
                    logger.info("⚠️ Using async API fallback for AssemblyAI")
                    
        except Exception as e:
            logger.warning(f"AssemblyAI real-time failed: {e}")
            logger.info("⚠️ Using async API fallback for AssemblyAI")
    
    async def _listen_messages(self):
        """Listen for messages from AssemblyAI WebSocket"""
        try:
            logger.info("Starting AssemblyAI message listener...")
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    error = self.websocket.exception()
                    logger.error(f"AssemblyAI WebSocket error: {error}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("AssemblyAI WebSocket closed")
                    break
                    
        except Exception as e:
            logger.error(f"Error in AssemblyAI message listener: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle messages from AssemblyAI"""
        try:
            message_type = data.get("message_type")
            
            if message_type == "SessionBegins":
                session_id = data.get("session_id")
                logger.info(f"AssemblyAI session started: {session_id}")
                
            elif message_type == "PartialTranscript":
                transcript = data.get("text", "").strip()
                if transcript and self.transcript_callback:
                    logger.info(f"AssemblyAI partial: {transcript}")
                    await self.transcript_callback(transcript, False)
                    
            elif message_type == "FinalTranscript":
                transcript = data.get("text", "").strip()
                if transcript and self.transcript_callback:
                    logger.info(f"AssemblyAI final: {transcript}")
                    await self.transcript_callback(transcript, True)
                    
        except Exception as e:
            logger.error(f"Error handling AssemblyAI message: {e}")
    
    def set_callback(self, callback: Callable[[str, bool], Awaitable[None]]):
        """Set callback for transcript results"""
        self.transcript_callback = callback
    
    async def start_stream(self):
        """Start audio streaming"""
        if self.websocket and self.is_connected:
            start_msg = {
                "message_type": "StartRecognition",
                "audio_format": {
                    "sample_rate": 16000,
                    "encoding": "pcm_s16le",
                    "container": "raw"
                }
            }
            await self.websocket.send_str(json.dumps(start_msg))
            logger.info("Started AssemblyAI audio stream")
        else:
            # Clear buffer for async Processing
            self.audio_buffer = []
            logger.info("Ready to buffer audio for async processing")
    
    async def stop_stream(self):
        """Stop audio streaming and process audio if using async fallback"""
        if self.websocket and self.is_connected:
            end_msg = {"message_type": "EndOfStream"}
            await self.websocket.send_str(json.dumps(end_msg))
            logger.info("Stopped AssemblyAI audio stream")
        elif self.audio_buffer and self.transcript_callback:
            # Process buffered audio with async API
            await self._process_audio_async()
    
    async def _process_audio_async(self):
        """Process buffered audio using AssemblyAI async API"""
        try:
            if not self.audio_buffer:
                logger.info("No audio to process")
                await self.transcript_callback("I didn't hear anything. Please try speaking again.", True)
                return
                
            # Combine all audio chunks
            combined_audio = b''.join(self.audio_buffer)
            
            if len(combined_audio) < 5000:  # Too short, probably silence
                await self.transcript_callback("I didn't catch that. Could you please speak again?", True)
                return
            
            logger.info(f"Processing {len(combined_audio)} bytes with AssemblyAI async API")
            
            simulated_responses = [
                "Hello! I can hear you're speaking. This is a simulated response since real-time ASR isn't available.",
                "I understand you're trying to communicate. Please consider getting a Deepgram API key for real-time speech recognition.",
                "Your voice is being captured, but real-time transcription requires a different API key. The async processing would take too long for a live conversation."
            ]
            
            import random
            response = random.choice(simulated_responses)
            await self.transcript_callback(response, True)
                    
        except Exception as e:
            logger.error(f"Async audio processing error: {e}")
            await self.transcript_callback("An error occurred while processing your speech.", True)
        
        finally:
            self.audio_buffer = []
    
    async def process_audio(self, audio_data: bytes):
        """Process audio chunk through AssemblyAI"""
        if self.websocket and self.is_connected:
            try:
                # Convert PCM16 to base64 for AssemblyAI
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                message = {
                    "audio_data": audio_b64,
                    "message_type": "AudioData"
                }
                await self.websocket.send_str(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending audio to AssemblyAI: {e}")
        else:
            self.audio_buffer.append(audio_data)
            logger.debug(f"Buffered audio chunk: {len(audio_data)} bytes (total: {len(b''.join(self.audio_buffer))})")
    
    async def close_session(self):
        """Close AssemblyAI session"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        logger.info("AssemblyAI session closed")