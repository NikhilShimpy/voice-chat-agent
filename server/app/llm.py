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
            except Exception as e:
                logger.error(f"OpenAI client initialization failed: {e}")
    
    async def process_query(self, query: str) -> str:
        """Process user query and generate response"""
        if self.client:
            return await self._process_with_openai(query)
        else:
            return self._fallback_response(query)
    
    async def _process_with_openai(self, query: str) -> str:
        """Process query using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural for speech."},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_response(query)
    
    def _fallback_response(self, query: str) -> str:
        """Generate fallback response when no LLM is available"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today?"
        elif any(word in query_lower for word in ["how are you", "how you doing"]):
            return "I'm doing well, thank you for asking!"
        elif any(word in query_lower for word in ["bye", "goodbye", "see you"]):
            return "Goodbye! Have a great day!"
        elif "weather" in query_lower:
            return "I don't have access to weather information right now."
        elif "time" in query_lower:
            return "I'm not able to check the current time at the moment."
        else:
            return "I understand. Is there anything else I can help you with?"