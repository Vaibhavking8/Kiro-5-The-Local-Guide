"""
Gemini API integration for natural language response generation.
Enhanced with circuit breaker pattern and retry logic for resilience.
"""
import google.generativeai as genai
import os
import markdown as md
from typing import Optional, Dict, Any
from .base_service import BaseService, retry_with_backoff
from dotenv import load_dotenv
load_dotenv()

# Set your Gemini API key here or via environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.5 Flash model for faster responses
MODEL = genai.GenerativeModel('gemini-2.5-flash')


class GeminiService(BaseService):
    """Gemini API service for natural language response generation."""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or GEMINI_API_KEY
        super().__init__("Gemini", api_key)
        
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = MODEL
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini API with retry logic."""
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        response = self.model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response from Gemini API")
        
        return response.text.strip()
    
    def generate_local_guide_response(self, user_question: str, recommendations: list, 
                                    cultural_context: Optional[str] = None) -> str:
        """
        Generate natural language response as a Korean local guide.
        
        Args:
            user_question: User's original question
            recommendations: List of recommendations from other services
            cultural_context: Additional Korean cultural context
        
        Returns:
            Natural, conversational response with Korean cultural insights
        """
        context_info = f"\nAdditional cultural context: {cultural_context}" if cultural_context else ""
        
        prompt = f"""
        You are a knowledgeable Korean local guide assistant. The user asked: "{user_question}"
        
        Here are relevant recommendations: {recommendations}{context_info}
        
        Respond as a friendly Korean local guide with these guidelines:
        - Use Korean cultural knowledge and local insights
        - Include practical tips and cultural etiquette when relevant
        - Mention neighborhood characteristics (Hongdae, Myeongdong, Itaewon, Gangnam)
        - Add local slang or cultural references when appropriate
        - Prioritize authentic experiences over tourist traps
        - Keep the tone conversational and helpful
        - Include cultural context about food, customs, or social aspects when relevant
        
        Provide a natural, engaging response that feels like advice from a knowledgeable local friend.
        """
        
        try:
            response = self._make_request(self._generate_content, prompt)
            if response:
                return markdown_to_html(response)
            else:
                return self._get_fallback_response(user_question, recommendations)
                
        except Exception as e:
            self.logger.error(f"Error generating local guide response: {e}")
            return self._get_fallback_response(user_question, recommendations)
    
    def extract_entity_with_context(self, question: str) -> Dict[str, Any]:
        """
        Extract main entity and context from user question.
        
        Args:
            question: User's question
        
        Returns:
            Dictionary with entity, type, and context information
        """
        prompt = f"""
        Analyze this question and extract key information:
        Question: "{question}"
        
        Return in this format:
        Entity: [main entity name]
        Type: [place/restaurant/attraction/activity/cultural]
        Intent: [what the user wants to know]
        Korean_Related: [yes/no - is this related to Korean culture]
        """
        
        try:
            response = self._make_request(self._generate_content, prompt)
            if response:
                return self._parse_entity_response(response)
            else:
                return self._get_fallback_entity_extraction(question)
                
        except Exception as e:
            self.logger.error(f"Error extracting entity from '{question}': {e}")
            return self._get_fallback_entity_extraction(question)
    
    def _parse_entity_response(self, response: str) -> Dict[str, Any]:
        """Parse structured entity extraction response."""
        lines = response.split('\n')
        result = {
            'entity': '',
            'type': 'place',
            'intent': '',
            'korean_related': False
        }
        
        for line in lines:
            if line.startswith('Entity:'):
                result['entity'] = line.replace('Entity:', '').strip()
            elif line.startswith('Type:'):
                result['type'] = line.replace('Type:', '').strip().lower()
            elif line.startswith('Intent:'):
                result['intent'] = line.replace('Intent:', '').strip()
            elif line.startswith('Korean_Related:'):
                result['korean_related'] = 'yes' in line.lower()
        
        return result
    
    def _get_fallback_response(self, question: str, recommendations: list) -> str:
        """Provide fallback response when Gemini API is unavailable."""
        self.logger.info("Providing fallback response due to Gemini API unavailability")
        
        if recommendations:
            rec_text = ", ".join([str(rec) for rec in recommendations[:3]])
            fallback = f"""
            <p>Based on your question about Korean culture, here are some recommendations: {rec_text}</p>
            <p>These suggestions reflect authentic Korean experiences. For more detailed cultural insights, 
            please try your question again when our AI assistant is available.</p>
            """
        else:
            fallback = f"""
            <p>Thank you for your question about Korean culture. While our AI assistant is temporarily unavailable, 
            I'd recommend exploring traditional neighborhoods like Hongdae for youth culture, Myeongdong for shopping and street food, 
            or Itaewon for international experiences.</p>
            <p>Please try your question again in a moment for more personalized recommendations.</p>
            """
        
        return fallback
    
    def _get_fallback_entity_extraction(self, question: str) -> Dict[str, Any]:
        """Provide fallback entity extraction when API is unavailable."""
        # Simple keyword-based extraction
        korean_keywords = ['korean', 'korea', 'seoul', 'busan', 'k-pop', 'kimchi', 'bulgogi']
        is_korean_related = any(keyword in question.lower() for keyword in korean_keywords)
        
        # Extract potential entity (first noun-like word)
        words = question.split()
        entity = next((word for word in words if len(word) > 3 and word.isalpha()), "korean culture")
        
        return {
            'entity': entity,
            'type': 'place',
            'intent': 'seeking recommendations',
            'korean_related': is_korean_related
        }
    
    def _handle_fallback(self, error: Exception) -> str:
        """Handle fallback when Gemini API is unavailable."""
        self.logger.warning(f"Gemini API unavailable, using structured fallback response: {error}")
        return self._get_fallback_response("general inquiry", [])

def markdown_to_html(text):
    # Use the markdown module to convert markdown to HTML
    # Extensions can be added for extra features if needed
    return md.markdown(text, extensions=['extra', 'sane_lists', 'smarty'])

def extract_entity(question):
    """
    Use Gemini to extract the main entity (e.g., place, artist, movie, etc.) from the user's question.
    """
    prompt = f"""
    Extract the main entity (such as a place, artist, movie, etc.) from the following question. 
    Only return the entity name, nothing else.
    Question: {question}
    """
    response = MODEL.generate_content(prompt)
    entity = response.text.strip().split('\n')[0]
    return entity

def generate_reply(question, qloo_data):
    """
    Use Gemini to generate a contextual, conversational, and insightful reply using the user's question and Qloo's recommendations.
    """
    prompt = f"""
    The user asked: "{question}"
    Here are some related cultural recommendations from a knowledge API: {qloo_data}
    Your task is to:
    - Analyze the recommendations and their relevance to the user's question.
    - Provide a helpful, friendly, and insightful answer.
    - If the recommendations are a list, explain their context and why they are relevant.
    - If possible, add interesting facts or cultural context about the recommendations.
    - Make the answer sound natural and conversational, as if you are a knowledgeable local guide.
    - If the recommendations are empty or not relevant, politely inform the user and suggest how they might rephrase their question.
    """
    response = MODEL.generate_content(prompt)
    return markdown_to_html(response.text.strip()) 


def markdown_to_html(text):
    """Use the markdown module to convert markdown to HTML."""
    return md.markdown(text, extensions=['extra', 'sane_lists', 'smarty'])


# Legacy compatibility functions for existing app.py
def extract_entity(question):
    """
    Legacy compatibility function for existing app.py.
    Use Gemini to extract the main entity from the user's question.
    """
    service = GeminiService()
    result = service.extract_entity_with_context(question)
    return result.get('entity', '')


def generate_reply(question, qloo_data):
    """
    Legacy compatibility function for existing app.py.
    Use Gemini to generate a contextual, conversational reply.
    """
    service = GeminiService()
    return service.generate_local_guide_response(question, qloo_data)