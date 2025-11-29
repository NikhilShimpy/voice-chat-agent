import openai
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        
        if api_key:
            try:
                self.client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"OpenAI client initialization failed: {e}")
    
    async def process_query(self, query: str) -> str:
        """Process user query and generate intelligent response"""
        if self.client:
            return await self._process_with_openai(query)
        else:
            return self._fallback_response(query)
    
    async def _process_with_openai(self, query: str) -> str:
        """Process query using OpenAI GPT"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a helpful voice assistant. Keep responses:
                        - Concise and natural for speech (under 2 sentences)
                        - Friendly and engaging
                        - Focused on being helpful
                        - Avoid complex formatting or lists"""
                    },
                    {"role": "user", "content": query}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_response(query)
    
    def _fallback_response(self, query: str) -> str:
        """Generate intelligent fallback responses"""
        query_lower = query.lower()
        
        # Greetings
        if any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm your voice assistant. How can I help you today?"
        
        # How are you
        elif any(phrase in query_lower for phrase in ["how are you", "how you doing"]):
            return "I'm doing great! Ready to help you with whatever you need."
        
        # Goodbye
        elif any(word in query_lower for word in ["bye", "goodbye", "see you", "farewell"]):
            return "Goodbye! Feel free to reach out if you need anything else."
        
        # Thanks
        elif any(word in query_lower for word in ["thank", "thanks", "appreciate"]):
            return "You're welcome! Happy to help."
        
        # Name/identity
        elif any(phrase in query_lower for phrase in ["who are you", "what are you", "your name"]):
            return "I'm your voice assistant, powered by advanced AI to help answer your questions."
        
        # Help
        elif "help" in query_lower:
            return "I can answer questions, have conversations, or assist with information. What would you like to know?"
        
        # Weather
        elif "weather" in query_lower:
            return "I don't have access to real-time weather data, but I recommend checking a weather app for current conditions."
        
        # Time
        elif "time" in query_lower:
            return "I can't check the current time, but your device should show the local time."
        
        # Default response
        else:
            return "I understand. Is there anything specific you'd like to know or discuss?"