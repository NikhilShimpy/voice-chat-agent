import aiohttp
import json
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class AssemblyAIASR:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.websocket = None
        self.transcript_callback = None
        self.session_url = None
        
    async def start_session(self):
        """Start AssemblyAI streaming session"""
        try:
            # Create real-time streaming session
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self.api_key,
                    "Content-Type": "application/json"
                }
                
                data = {
                    "sample_rate": 16000,
                    "encoding": "pcm_s16le",
                    "channels": 1,
                    "endpointing": 100,
                    "disfluencies": False
                }
                
                async with session.post(
                    "https://api.assemblyai.com/v2/realtime/ws",
                    headers=headers,
                    json=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.session_url = result.get("url")
                        logger.info("AssemblyAI session started")
                    else:
                        raise Exception(f"Failed to start session: {resp.status}")
                        
        except Exception as e:
            logger.error(f"AssemblyAI session error: {e}")
            raise
    
    def set_callback(self, callback: Callable[[str, bool], Awaitable[None]]):
        """Set callback for transcript results"""
        self.transcript_callback = callback
    
    async def start_stream(self):
        """Start audio streaming"""
        # Implementation for starting audio stream to AssemblyAI
        pass
    
    async def stop_stream(self):
        """Stop audio streaming"""
        # Implementation for stopping audio stream
        pass
    
    async def process_audio(self, audio_data: bytes):
        """Process audio chunk through AssemblyAI"""
        if not self.websocket:
            return
            
        try:
            # Send audio data to AssemblyAI
            message = {
                "audio_data": audio_data.hex()
            }
            await self.websocket.send_str(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending audio to AssemblyAI: {e}")
    
    async def close_session(self):
        """Close AssemblyAI session"""
        if self.websocket:
            await self.websocket.close()
        logger.info("AssemblyAI session closed")