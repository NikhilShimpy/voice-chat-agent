import aiohttp
import json
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class DeepgramASR:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket = None
        self.transcript_callback = None
        
    async def start_session(self):
        """Start Deepgram streaming session"""
        try:
            # Deepgram WebSocket connection
            self.websocket = await aiohttp.ClientSession().ws_connect(
                f"wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000&channels=1",
                headers={"Authorization": f"Token {self.api_key}"}
            )
            logger.info("Deepgram session started")
            
            # Start listening for messages
            async def listen():
                async for msg in self.websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"Deepgram WebSocket error: {self.websocket.exception()}")
                        
            # Start listener task
            import asyncio
            asyncio.create_task(listen())
            
        except Exception as e:
            logger.error(f"Deepgram session error: {e}")
            raise
    
    async def _handle_message(self, data: dict):
        """Handle Deepgram WebSocket messages"""
        try:
            transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
            is_final = data.get("is_final", False)
            
            if transcript and self.transcript_callback:
                await self.transcript_callback(transcript, is_final)
                
        except Exception as e:
            logger.error(f"Error handling Deepgram message: {e}")
    
    def set_callback(self, callback: Callable[[str, bool], Awaitable[None]]):
        """Set callback for transcript results"""
        self.transcript_callback = callback
    
    async def start_stream(self):
        """Start audio streaming"""
        pass
    
    async def stop_stream(self):
        """Stop audio streaming"""
        # Send signal to Deepgram that streaming ended
        if self.websocket:
            await self.websocket.send_str(json.dumps({"type": "CloseStream"}))
    
    async def process_audio(self, audio_data: bytes):
        """Process audio chunk through Deepgram"""
        if self.websocket:
            await self.websocket.send_bytes(audio_data)
    
    async def close_session(self):
        """Close Deepgram session"""
        if self.websocket:
            await self.websocket.close()
        logger.info("Deepgram session closed")