import aiohttp
import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class MurfTTS:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        
    async def stream_tts(self, text: str, voice: str = "falcon_en_us") -> AsyncGenerator[bytes, None]:
        """Stream TTS audio from Murf AI"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "voice": voice,
                "format": "pcm16",
                "sampleRate": 16000,
                "channels": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/synthesize/stream",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        async for chunk in response.content.iter_chunks():
                            if chunk[0]:  # chunk[0] is data, chunk[1] is EOF
                                yield chunk[0]
                    else:
                        error_text = await response.text()
                        logger.error(f"Murf TTS error: {error_text}")
                        # Fallback to local TTS
                        async for chunk in self._fallback_tts(text):
                            yield chunk
                            
        except Exception as e:
            logger.error(f"Murf TTS stream error: {e}")
            # Fallback to local TTS
            async for chunk in self._fallback_tts(text):
                yield chunk
    
    async def _fallback_tts(self, text: str) -> AsyncGenerator[bytes, None]:
        """Fallback TTS when Murf is unavailable"""
        logger.info("Using fallback TTS")
        # Simple fallback - in production, you might use pyttsx3 or other local TTS
        # For now, return empty audio or a simple beep
        yield b""  # Empty audio as fallback
    
    def get_available_voices(self) -> list:
        """Get list of available Murf voices"""
        # This would typically call Murf's voices endpoint
        return [
            {"id": "falcon_en_us", "name": "Falcon US", "language": "en-US"},
            {"id": "falcon_en_uk", "name": "Falcon UK", "language": "en-GB"},
            {"id": "falcon_en_au", "name": "Falcon AU", "language": "en-AU"}
        ]