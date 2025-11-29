import aiohttp
import json
import logging
import asyncio
from typing import Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

class DeepgramASR:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.transcript_callback: Optional[Callable[[str, bool], Awaitable[None]]] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        
    async def start_session(self):
        """Start Deepgram real-time session"""
        try:
            logger.info("Starting Deepgram real-time session...")
            
            self.session = aiohttp.ClientSession()
            
            # Connect to Deepgram real-time WebSocket
            self.websocket = await self.session.ws_connect(
                "wss://api.deepgram.com/v1/listen",
                params={
                    "encoding": "linear16",
                    "sample_rate": 16000,
                    "channels": 1,
                    "interim_results": "true",
                    "endpointing": "100",
                    "punctuate": "true",
                    "model": "general",
                    "language": "en-US"
                },
                headers={"Authorization": f"Token {self.api_key}"}
            )
            
            self.is_connected = True
            logger.info("✅ Deepgram real-time WebSocket connected successfully")
            
            # Start listening for messages
            asyncio.create_task(self._listen_messages())
            
        except Exception as e:
            logger.error(f"❌ Deepgram session error: {e}")
            if self.session:
                await self.session.close()
            raise
    
    async def _listen_messages(self):
        """Listen for messages from Deepgram WebSocket"""
        try:
            logger.info("Starting Deepgram message listener...")
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    error = self.websocket.exception()
                    logger.error(f"Deepgram WebSocket error: {error}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("Deepgram WebSocket closed")
                    break
        except Exception as e:
            logger.error(f"Error in Deepgram message listener: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle messages from Deepgram"""
        try:
            message_type = data.get("type")
            
            if message_type == "Results":
                # Check if we have a final transcript
                is_final = data.get("is_final", False)
                transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "").strip()
                
                if transcript and self.transcript_callback:
                    logger.info(f"Deepgram transcript (final={is_final}): {transcript}")
                    await self.transcript_callback(transcript, is_final)
                    
            elif message_type == "error":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"Deepgram error: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error handling Deepgram message: {e}")
    
    def set_callback(self, callback: Callable[[str, bool], Awaitable[None]]):
        """Set callback for transcript results"""
        self.transcript_callback = callback
    
    async def start_stream(self):
        """Start audio streaming"""
        if self.websocket and self.is_connected:
            logger.info("Deepgram audio stream started")
    
    async def stop_stream(self):
        """Stop audio streaming"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send_str(json.dumps({"type": "CloseStream"}))
                logger.info("Deepgram stream closed")
            except Exception as e:
                logger.error(f"Error closing Deepgram stream: {e}")
    
    async def process_audio(self, audio_data: bytes):
        """Process audio chunk through Deepgram"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send_bytes(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {e}")
    
    async def close_session(self):
        """Close Deepgram session"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        logger.info("Deepgram session closed")