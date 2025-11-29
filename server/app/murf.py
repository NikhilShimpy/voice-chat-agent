import aiohttp
import json
import logging
from typing import AsyncGenerator, List, Dict, Any

logger = logging.getLogger(__name__)

class MurfTTS:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.murf.ai/v1"
        
    async def stream_tts(self, text: str, voice: str = "en_us_001") -> AsyncGenerator[bytes, None]:
        """Stream TTS audio from Murf AI"""
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Map voice IDs to Murf voice parameters
            voice_map = {
                "en_us_001": {"voiceId": "Ronnie", "model": "Falcon"},
                "en_uk_001": {"voiceId": "Reece", "model": "Falcon"}, 
                "en_au_001": {"voiceId": "Matilda", "model": "Falcon"}
            }
            
            voice_params = voice_map.get(voice, {"voiceId": "Ronnie", "model": "Falcon"})
            
            # Murf API payload
            data = {
                "text": text,
                "voiceId": voice_params["voiceId"],
                "model": voice_params["model"],
                "format": "MP3",
                "sampleRate": 24000,
                "channelType": "MONO",
                "prosody": {
                    "rate": "medium",
                    "pitch": "medium"
                }
            }
            
            logger.info(f"Murf TTS Request: {json.dumps(data, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/speech/generate",
                    headers=headers,
                    json=data
                ) as response:
                    
                    if response.status == 200:
                        # Murf returns the complete audio file
                        audio_data = await response.read()
                        logger.info(f"Murf TTS Success: Generated {len(audio_data)} bytes of audio")
                        
                        # Return the audio data
                        yield audio_data
                        
                    elif response.status == 402:
                        error_text = await response.text()
                        logger.error(f"Murf TTS credit limit exceeded: {error_text}")
                        raise Exception("Murf TTS credit limit exceeded. Please check your Murf account.")
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Murf TTS authentication failed: {error_text}")
                        raise Exception("Murf TTS authentication failed. Please check your API key.")
                    else:
                        error_text = await response.text()
                        logger.error(f"Murf TTS API error {response.status}: {error_text}")
                        raise Exception(f"Murf TTS error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Murf TTS stream error: {e}")
            # Fallback - return empty audio
            yield b""
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available Murf voices"""
        try:
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/studio/voices",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    else:
                        logger.error(f"Failed to fetch voices: {response.status}")
                        return self._get_default_voices()
                        
        except Exception as e:
            logger.error(f"Error fetching Murf voices: {e}")
            return self._get_default_voices()
    
    def _get_default_voices(self) -> List[Dict[str, Any]]:
        """Return default voice list if API fails"""
        return [
            {"id": "en_us_001", "name": "Falcon US English (Ronnie)", "language": "en-US", "voiceId": "Ronnie", "model": "Falcon"},
            {"id": "en_uk_001", "name": "Falcon UK English (Reece)", "language": "en-GB", "voiceId": "Reece", "model": "Falcon"},
            {"id": "en_au_001", "name": "Falcon Australian English (Matilda)", "language": "en-AU", "voiceId": "Matilda", "model": "Falcon"}
        ]