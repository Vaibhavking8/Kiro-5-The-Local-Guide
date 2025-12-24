"""
Response Generator with Gemini integration for natural language response generation.
Implements Korean-informed language patterns and local guide persona with cultural context.
"""
import os
import markdown as md
from typing import Optional, Dict, Any, List
from .base_service import BaseService, retry_with_backoff
from .gemini_api import GeminiService
from dotenv import load_dotenv

load_dotenv()


class ResponseGenerator(BaseService):
    """
    Response Generator for creating natural, conversational responses with Korean cultural context.
    
    Uses Gemini API to create authentic local guide responses with Korean-informed language patterns.
    Includes fallback to structured responses when Gemini is unavailable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("ResponseGenerator", api_key)
        
        # Initialize Gemini service for natural language generation
        self.gemini_service = GeminiService(api_key)
        
        # Korean cultural context for authentic responses
        self.korean_cultural_context = self._initialize_korean_cultural_context()
        
        # Local guide persona characteristics
        self.local_guide_persona = self._initialize_local_guide_persona()
        
        # Response templates for fallback scenarios
        self.fallback_templates = self._initialize_fallback_templates()
    
    def _initialize_korean_cultural_context(self) -> Dict[str, Any]:
        """Initialize Korean cultural context for authentic responses."""
        return {
            'greetings': {
                'formal': '안녕하세요! (Annyeonghaseyo!)',
                'casual': '안녕! (Annyeong!)',
                'local_guide': '안녕하세요! (Hello!)'
            },
            'cultural_norms': {
                'tipping': 'Tipping is not customary in South Korea',
                'punctuality': 'Koreans value punctuality and personal space',
                'transport': 'Public transport is preferred over taxis for short distances',
                'subway_etiquette': 'Speaking loudly on subways is considered rude',
                'restaurant_culture': 'Restaurants often specialize in only one dish',
                'closing_hours': 'Many places close between 3–5 PM'
            },
            'food_culture': {
                'banchan': 'Korean meals often include shared side dishes (banchan)',
                'street_food_timing': 'Street food is best explored after sunset',
                'samgyeopsal': 'Samgyeopsal is a social meal eaten in groups, usually at night',
                'tteokbokki': 'Tteokbokki is a spicy-sweet street food popular among students'
            },
            'local_slang': {
                'daebak': 'Amazing',
                'hwaiting': 'Encouragement/Fighting!',
                'maknae': 'Youngest person in a group',
                'oppa': 'Older brother (used by females)',
                'unnie': 'Older sister (used by females)'
            },
            'neighborhood_characteristics': {
                'hongdae': 'Youth culture, street food, nightlife',
                'myeongdong': 'Shopping and tourist street food',
                'itaewon': 'International food and nightlife',
                'gangnam': 'Cafés, fine dining, upscale shopping',
                'insadong': 'Traditional arts and crafts with tea culture',
                'jongno': 'Historic district with traditional culture'
            }
        }
    
    def _initialize_local_guide_persona(self) -> Dict[str, Any]:
        """Initialize local guide persona characteristics."""
        return {
            'tone': 'friendly, knowledgeable, enthusiastic',
            'expertise': 'Korean culture, food, neighborhoods, customs',
            'communication_style': 'conversational, helpful, culturally aware',
            'priorities': ['authentic experiences', 'cultural context', 'practical tips'],
            'language_patterns': [
                'Uses Korean greetings and expressions naturally',
                'Explains cultural significance of recommendations',
                'Provides practical cultural tips',
                'Shares local insights and neighborhood knowledge',
                'Prioritizes authentic over touristy experiences'
            ]
        }
    
    def _initialize_fallback_templates(self) -> Dict[str, str]:
        """Initialize structured response templates for fallback scenarios."""
        return {
            'general_recommendation': """
            <div class="local-guide-response">
                <p>{greeting} As your Korean local guide, I'd love to help you explore authentic Korean culture!</p>
                {recommendations_section}
                {cultural_context_section}
                {practical_tips_section}
            </div>
            """,
            'neighborhood_specific': """
            <div class="local-guide-response">
                <p>{greeting} Let me tell you about {neighborhood} - {neighborhood_character}!</p>
                {neighborhood_recommendations}
                {cultural_insights}
                {local_tips}
            </div>
            """,
            'food_recommendation': """
            <div class="local-guide-response">
                <p>{greeting} Korean food culture is amazing! Here's what I recommend:</p>
                {food_recommendations}
                {dining_etiquette}
                {cultural_context}
            </div>
            """,
            'cultural_experience': """
            <div class="local-guide-response">
                <p>{greeting} For authentic Korean cultural experiences, I suggest:</p>
                {cultural_activities}
                {cultural_significance}
                {practical_advice}
            </div>
            """
        }
    
    def generate_response(self, user_query: str, recommendations: List[Dict[str, Any]], 
                         cultural_context: Optional[str] = None, 
                         user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate natural language response with Korean cultural context.
        
        Args:
            user_query: User's original question
            recommendations: List of recommendations from other services
            cultural_context: Additional Korean cultural context
            user_context: User profile and personalization context
        
        Returns:
            Natural, conversational response with Korean cultural insights
        """
        try:
            # Use Gemini service if available
            if self.gemini_service and self.gemini_service.is_available():
                return self._generate_gemini_response(
                    user_query, recommendations, cultural_context, user_context
                )
            else:
                return self._generate_fallback_response(
                    user_query, recommendations, cultural_context, user_context
                )
                
        except Exception as e:
            self.logger.error(f"Error generating response for '{user_query}': {e}")
            return self._generate_emergency_fallback(user_query)
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _generate_gemini_response(self, user_query: str, recommendations: List[Dict[str, Any]], 
                                 cultural_context: Optional[str] = None,
                                 user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using Gemini API with Korean cultural context."""
        
        # Prepare cultural context for the prompt
        cultural_elements = self._prepare_cultural_context(user_query, cultural_context)
        
        # Prepare user personalization context
        personalization_context = self._prepare_personalization_context(user_context)
        
        # Create comprehensive prompt for Gemini
        prompt = self._create_gemini_prompt(
            user_query, recommendations, cultural_elements, personalization_context
        )
        
        # Generate response using Gemini service
        response = self.gemini_service._generate_content(prompt)
        
        # Convert markdown to HTML and return
        return self._format_response(response)
    
    def _prepare_cultural_context(self, user_query: str, additional_context: Optional[str] = None) -> Dict[str, Any]:
        """Prepare relevant Korean cultural context based on user query."""
        query_lower = user_query.lower()
        relevant_context = {}
        
        # Add greeting
        relevant_context['greeting'] = self.korean_cultural_context['greetings']['local_guide']
        
        # Add relevant cultural norms
        if any(word in query_lower for word in ['tip', 'money', 'pay']):
            relevant_context['tipping'] = self.korean_cultural_context['cultural_norms']['tipping']
        
        if any(word in query_lower for word in ['time', 'when', 'schedule']):
            relevant_context['punctuality'] = self.korean_cultural_context['cultural_norms']['punctuality']
            relevant_context['closing_hours'] = self.korean_cultural_context['cultural_norms']['closing_hours']
        
        if any(word in query_lower for word in ['transport', 'taxi', 'subway', 'bus']):
            relevant_context['transport'] = self.korean_cultural_context['cultural_norms']['transport']
            relevant_context['subway_etiquette'] = self.korean_cultural_context['cultural_norms']['subway_etiquette']
        
        # Add relevant food culture
        if any(word in query_lower for word in ['food', 'eat', 'restaurant', 'dining']):
            relevant_context['banchan'] = self.korean_cultural_context['food_culture']['banchan']
            relevant_context['restaurant_culture'] = self.korean_cultural_context['cultural_norms']['restaurant_culture']
            
            if 'street food' in query_lower:
                relevant_context['street_food_timing'] = self.korean_cultural_context['food_culture']['street_food_timing']
            
            if any(word in query_lower for word in ['bbq', 'samgyeopsal', 'pork']):
                relevant_context['samgyeopsal'] = self.korean_cultural_context['food_culture']['samgyeopsal']
        
        # Add neighborhood context
        for neighborhood, character in self.korean_cultural_context['neighborhood_characteristics'].items():
            if neighborhood in query_lower:
                relevant_context[f'{neighborhood}_character'] = f"{neighborhood.title()}: {character}"
        
        # Add local slang context
        relevant_context['local_expressions'] = self.korean_cultural_context['local_slang']
        
        # Add additional context if provided
        if additional_context:
            relevant_context['additional'] = additional_context
        
        return relevant_context
    
    def _prepare_personalization_context(self, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare personalization context from user profile."""
        if not user_context:
            return {}
        
        return {
            'interests': user_context.get('interests', []),
            'food_restrictions': user_context.get('food_restrictions', []),
            'cultural_preferences': user_context.get('cultural_preferences', []),
            'budget_range': user_context.get('budget_range', 'mid-range'),
            'travel_style': user_context.get('travel_style', 'solo'),
            'visited_places': user_context.get('visited_places', []),
            'preferred_neighborhoods': user_context.get('preferred_neighborhoods', [])
        }
    
    def _create_gemini_prompt(self, user_query: str, recommendations: List[Dict[str, Any]], 
                             cultural_context: Dict[str, Any], 
                             personalization_context: Dict[str, Any]) -> str:
        """Create comprehensive prompt for Gemini API."""
        
        # Format recommendations for the prompt
        recommendations_text = self._format_recommendations_for_prompt(recommendations)
        
        # Format cultural context
        cultural_context_text = self._format_cultural_context_for_prompt(cultural_context)
        
        # Format personalization context
        personalization_text = self._format_personalization_for_prompt(personalization_context)
        
        prompt = f"""
        You are an authentic Korean local guide assistant with deep cultural knowledge and a friendly, enthusiastic personality. 
        The user asked: "{user_query}"
        
        Here are relevant recommendations: {recommendations_text}
        
        Korean Cultural Context to incorporate:
        {cultural_context_text}
        
        User Personalization Context:
        {personalization_text}
        
        Response Guidelines:
        1. Start with a Korean greeting: "{cultural_context.get('greeting', '안녕하세요!')}"
        2. Use Korean-informed language patterns naturally (include Korean words/phrases with translations)
        3. Provide authentic cultural insights and context for each recommendation
        4. Include practical cultural tips and etiquette when relevant
        5. Mention neighborhood characteristics and local insights
        6. Prioritize authentic experiences over tourist traps
        7. Keep the tone conversational, friendly, and knowledgeable like a local friend
        8. Include cultural significance and social aspects when discussing food or activities
        9. Use local slang or cultural references appropriately: {cultural_context.get('local_expressions', {})}
        10. Structure the response with clear sections but maintain conversational flow
        
        Avoid:
        - Generic tourist advice
        - Overly formal language
        - Recommendations without cultural context
        - Ignoring user's personalization preferences
        
        Create a natural, engaging response that feels like advice from a knowledgeable Korean local friend who understands both Korean culture and the user's preferences.
        """
        
        return prompt
    
    def _format_recommendations_for_prompt(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations for inclusion in Gemini prompt."""
        if not recommendations:
            return "No specific recommendations available - provide general Korean cultural guidance."
        
        formatted_recs = []
        for i, rec in enumerate(recommendations[:8], 1):  # Limit to 8 recommendations
            name = rec.get('Name', rec.get('name', f'Recommendation {i}'))
            rec_type = rec.get('Type', rec.get('recommendation_type', 'place'))
            description = rec.get('wTeaser', rec.get('description', ''))
            cultural_context = rec.get('cultural_context', '')
            neighborhood = rec.get('neighborhood', '')
            
            rec_text = f"{i}. {name} ({rec_type})"
            if description:
                rec_text += f" - {description}"
            if cultural_context:
                rec_text += f" | Cultural Context: {cultural_context}"
            if neighborhood:
                rec_text += f" | Neighborhood: {neighborhood}"
            
            formatted_recs.append(rec_text)
        
        return "\n".join(formatted_recs)
    
    def _format_cultural_context_for_prompt(self, cultural_context: Dict[str, Any]) -> str:
        """Format cultural context for inclusion in Gemini prompt."""
        context_items = []
        
        for key, value in cultural_context.items():
            if key == 'local_expressions':
                expressions = ", ".join([f"{k} ({v})" for k, v in value.items()])
                context_items.append(f"Local expressions: {expressions}")
            elif isinstance(value, str):
                context_items.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(context_items) if context_items else "General Korean cultural context"
    
    def _format_personalization_for_prompt(self, personalization_context: Dict[str, Any]) -> str:
        """Format personalization context for inclusion in Gemini prompt."""
        if not personalization_context:
            return "No specific user preferences available."
        
        context_items = []
        
        if personalization_context.get('interests'):
            context_items.append(f"User interests: {', '.join(personalization_context['interests'])}")
        
        if personalization_context.get('food_restrictions'):
            context_items.append(f"Food restrictions: {', '.join(personalization_context['food_restrictions'])}")
        
        if personalization_context.get('cultural_preferences'):
            context_items.append(f"Cultural preferences: {', '.join(personalization_context['cultural_preferences'])}")
        
        if personalization_context.get('budget_range'):
            context_items.append(f"Budget range: {personalization_context['budget_range']}")
        
        if personalization_context.get('travel_style'):
            context_items.append(f"Travel style: {personalization_context['travel_style']}")
        
        if personalization_context.get('preferred_neighborhoods'):
            context_items.append(f"Preferred neighborhoods: {', '.join(personalization_context['preferred_neighborhoods'])}")
        
        return "\n".join(context_items) if context_items else "No specific user preferences."
    
    def _format_response(self, response: str) -> str:
        """Format response by converting markdown to HTML."""
        try:
            # Convert markdown to HTML
            html_response = md.markdown(response, extensions=['extra', 'sane_lists', 'smarty'])
            
            # Wrap in local guide response div if not already wrapped
            if not html_response.strip().startswith('<div class="local-guide-response">'):
                html_response = f'<div class="local-guide-response">{html_response}</div>'
            
            return html_response
        except Exception as e:
            self.logger.warning(f"Error formatting response: {e}")
            return f'<div class="local-guide-response"><p>{response}</p></div>'
    
    def _generate_fallback_response(self, user_query: str, recommendations: List[Dict[str, Any]], 
                                   cultural_context: Optional[str] = None,
                                   user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate structured fallback response when Gemini is unavailable."""
        self.logger.info("Generating fallback response due to Gemini API unavailability")
        
        # Determine response type based on query
        response_type = self._determine_response_type(user_query)
        
        # Get appropriate template
        template = self.fallback_templates.get(response_type, self.fallback_templates['general_recommendation'])
        
        # Prepare template variables
        template_vars = self._prepare_fallback_template_vars(
            user_query, recommendations, cultural_context, user_context, response_type
        )
        
        # Format template with variables
        try:
            formatted_response = template.format(**template_vars)
            return formatted_response
        except Exception as e:
            self.logger.error(f"Error formatting fallback template: {e}")
            return self._generate_emergency_fallback(user_query)
    
    def _determine_response_type(self, user_query: str) -> str:
        """Determine the type of response needed based on user query."""
        query_lower = user_query.lower()
        
        # Check for neighborhood-specific queries
        neighborhoods = ['hongdae', 'myeongdong', 'itaewon', 'gangnam', 'insadong', 'jongno']
        if any(neighborhood in query_lower for neighborhood in neighborhoods):
            return 'neighborhood_specific'
        
        # Check for food-related queries
        if any(word in query_lower for word in ['food', 'eat', 'restaurant', 'dining', 'cuisine']):
            return 'food_recommendation'
        
        # Check for cultural experience queries
        if any(word in query_lower for word in ['culture', 'traditional', 'experience', 'activity', 'temple', 'palace']):
            return 'cultural_experience'
        
        return 'general_recommendation'
    
    def _prepare_fallback_template_vars(self, user_query: str, recommendations: List[Dict[str, Any]], 
                                       cultural_context: Optional[str], user_context: Optional[Dict[str, Any]],
                                       response_type: str) -> Dict[str, str]:
        """Prepare variables for fallback template formatting."""
        
        # Base variables
        vars_dict = {
            'greeting': self.korean_cultural_context['greetings']['local_guide'],
            'recommendations_section': self._format_recommendations_section(recommendations),
            'cultural_context_section': self._format_cultural_context_section(cultural_context),
            'practical_tips_section': self._format_practical_tips_section(user_query)
        }
        
        # Add response-type specific variables
        if response_type == 'neighborhood_specific':
            neighborhood = self._extract_neighborhood_from_query(user_query)
            if neighborhood:
                vars_dict.update({
                    'neighborhood': neighborhood.title(),
                    'neighborhood_character': self.korean_cultural_context['neighborhood_characteristics'].get(neighborhood, 'Unique Korean district'),
                    'neighborhood_recommendations': self._format_neighborhood_recommendations(recommendations, neighborhood),
                    'cultural_insights': self._format_neighborhood_cultural_insights(neighborhood),
                    'local_tips': self._format_neighborhood_tips(neighborhood)
                })
        
        elif response_type == 'food_recommendation':
            vars_dict.update({
                'food_recommendations': self._format_food_recommendations(recommendations),
                'dining_etiquette': self._format_dining_etiquette(),
                'cultural_context': self._format_food_cultural_context()
            })
        
        elif response_type == 'cultural_experience':
            vars_dict.update({
                'cultural_activities': self._format_cultural_activities(recommendations),
                'cultural_significance': self._format_cultural_significance(),
                'practical_advice': self._format_cultural_practical_advice()
            })
        
        return vars_dict
    
    def _format_recommendations_section(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations section for fallback response."""
        if not recommendations:
            return "<p>Here are some authentic Korean experiences I always recommend:</p>"
        
        sections = []
        
        # Group recommendations by type
        places = [r for r in recommendations if r.get('recommendation_type') == 'place' or r.get('Type') == 'place']
        experiences = [r for r in recommendations if r.get('recommendation_type') == 'cultural_experience']
        food = [r for r in recommendations if 'restaurant' in str(r.get('Type', '')).lower() or 'food' in str(r.get('category', '')).lower()]
        
        if places:
            sections.append("<h4>🏮 Places to Visit:</h4>")
            sections.append("<ul>")
            for place in places[:3]:
                name = place.get('Name', place.get('name', 'Korean Place'))
                context = place.get('cultural_context', 'Authentic Korean experience')
                sections.append(f"<li><strong>{name}</strong> - {context}</li>")
            sections.append("</ul>")
        
        if food:
            sections.append("<h4>🍜 Food Experiences:</h4>")
            sections.append("<ul>")
            for item in food[:3]:
                name = item.get('Name', item.get('name', 'Korean Food'))
                description = item.get('wTeaser', item.get('description', 'Authentic Korean cuisine'))
                sections.append(f"<li><strong>{name}</strong> - {description}</li>")
            sections.append("</ul>")
        
        if experiences:
            sections.append("<h4>🎭 Cultural Experiences:</h4>")
            sections.append("<ul>")
            for exp in experiences[:3]:
                name = exp.get('Name', 'Korean Cultural Experience')
                teaser = exp.get('wTeaser', 'Authentic Korean cultural activity')
                sections.append(f"<li><strong>{name}</strong> - {teaser}</li>")
            sections.append("</ul>")
        
        return "".join(sections) if sections else "<p>Let me share some authentic Korean experiences with you!</p>"
    
    def _format_cultural_context_section(self, cultural_context: Optional[str]) -> str:
        """Format cultural context section for fallback response."""
        if cultural_context:
            return f"<p><em>💡 Cultural insight: {cultural_context}</em></p>"
        
        # Default cultural tip
        return f"<p><em>💡 Cultural tip: {self.korean_cultural_context['cultural_norms']['tipping']}</em></p>"
    
    def _format_practical_tips_section(self, user_query: str) -> str:
        """Format practical tips section based on user query."""
        query_lower = user_query.lower()
        tips = []
        
        if any(word in query_lower for word in ['time', 'when', 'hours']):
            tips.append(self.korean_cultural_context['cultural_norms']['closing_hours'])
        
        if any(word in query_lower for word in ['transport', 'travel', 'get around']):
            tips.append(self.korean_cultural_context['cultural_norms']['transport'])
        
        if any(word in query_lower for word in ['food', 'restaurant', 'eat']):
            tips.append(self.korean_cultural_context['food_culture']['banchan'])
        
        if not tips:
            tips.append(self.korean_cultural_context['cultural_norms']['punctuality'])
        
        tips_html = "<ul>" + "".join([f"<li>{tip}</li>" for tip in tips[:2]]) + "</ul>"
        return f"<h4>🎯 Practical Tips:</h4>{tips_html}"
    
    def _extract_neighborhood_from_query(self, user_query: str) -> Optional[str]:
        """Extract neighborhood name from user query."""
        query_lower = user_query.lower()
        
        for neighborhood in self.korean_cultural_context['neighborhood_characteristics'].keys():
            if neighborhood in query_lower:
                return neighborhood
        
        return None
    
    def _format_neighborhood_recommendations(self, recommendations: List[Dict[str, Any]], neighborhood: str) -> str:
        """Format neighborhood-specific recommendations."""
        neighborhood_recs = [r for r in recommendations if str(r.get('neighborhood', '')).lower() == neighborhood]
        
        if not neighborhood_recs:
            return f"<p>Here are authentic experiences in {neighborhood.title()}:</p>"
        
        items = []
        for rec in neighborhood_recs[:3]:
            name = rec.get('Name', rec.get('name', 'Local Experience'))
            context = rec.get('cultural_context', 'Authentic neighborhood experience')
            items.append(f"<li><strong>{name}</strong> - {context}</li>")
        
        return "<ul>" + "".join(items) + "</ul>"
    
    def _format_neighborhood_cultural_insights(self, neighborhood: str) -> str:
        """Format cultural insights for specific neighborhood."""
        character = self.korean_cultural_context['neighborhood_characteristics'].get(neighborhood, '')
        if character:
            return f"<p><em>🏮 {neighborhood.title()} is known for: {character}</em></p>"
        return ""
    
    def _format_neighborhood_tips(self, neighborhood: str) -> str:
        """Format practical tips for specific neighborhood."""
        tips = {
            'hongdae': 'Best visited after 9 PM for the full nightlife experience',
            'myeongdong': 'Great for first-time visitors, but avoid peak tourist hours',
            'itaewon': 'English is widely spoken here, perfect for international visitors',
            'gangnam': 'Dress nicely - this is Seoul\'s upscale district',
            'insadong': 'Perfect for traditional tea ceremonies and cultural shopping',
            'jongno': 'Visit during weekdays to avoid crowds at palaces'
        }
        
        tip = tips.get(neighborhood, 'Explore like a local and be respectful of cultural norms')
        return f"<p><em>💡 Local tip: {tip}</em></p>"
    
    def _format_food_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format food-specific recommendations."""
        food_recs = [r for r in recommendations if 'food' in str(r.get('Type', '')).lower() or 'restaurant' in str(r.get('category', '')).lower()]
        
        if not food_recs:
            default_foods = [
                "Korean BBQ (Samgyeopsal) - Social dining experience",
                "Street Food in Myeongdong - Best after sunset",
                "Traditional Korean Tea - Try in Insadong"
            ]
            return "<ul>" + "".join([f"<li>{food}</li>" for food in default_foods]) + "</ul>"
        
        items = []
        for rec in food_recs[:3]:
            name = rec.get('Name', rec.get('name', 'Korean Food'))
            description = rec.get('wTeaser', rec.get('description', 'Authentic Korean cuisine'))
            items.append(f"<li><strong>{name}</strong> - {description}</li>")
        
        return "<ul>" + "".join(items) + "</ul>"
    
    def _format_dining_etiquette(self) -> str:
        """Format dining etiquette information."""
        etiquette_tips = [
            self.korean_cultural_context['food_culture']['banchan'],
            self.korean_cultural_context['cultural_norms']['restaurant_culture'],
            self.korean_cultural_context['cultural_norms']['tipping']
        ]
        
        return "<ul>" + "".join([f"<li>{tip}</li>" for tip in etiquette_tips]) + "</ul>"
    
    def _format_food_cultural_context(self) -> str:
        """Format food cultural context."""
        return f"<p><em>🍜 Food culture insight: {self.korean_cultural_context['food_culture']['samgyeopsal']}</em></p>"
    
    def _format_cultural_activities(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format cultural activity recommendations."""
        cultural_recs = [r for r in recommendations if r.get('recommendation_type') == 'cultural_experience']
        
        if not cultural_recs:
            default_activities = [
                "Visit Gyeongbokgung Palace - Traditional Korean architecture",
                "Try Hanbok rental in Bukchon - Traditional Korean clothing experience",
                "Temple stay at Jogyesa - Buddhist cultural immersion"
            ]
            return "<ul>" + "".join([f"<li>{activity}</li>" for activity in default_activities]) + "</ul>"
        
        items = []
        for rec in cultural_recs[:3]:
            name = rec.get('Name', 'Cultural Experience')
            description = rec.get('wTeaser', rec.get('description', 'Authentic Korean cultural activity'))
            items.append(f"<li><strong>{name}</strong> - {description}</li>")
        
        return "<ul>" + "".join(items) + "</ul>"
    
    def _format_cultural_significance(self) -> str:
        """Format cultural significance information."""
        return "<p><em>🏛️ These experiences connect you with Korea's rich cultural heritage and help you understand the values and traditions that shape modern Korean society.</em></p>"
    
    def _format_cultural_practical_advice(self) -> str:
        """Format practical advice for cultural experiences."""
        advice = [
            "Dress modestly when visiting temples and palaces",
            "Learn basic Korean greetings - locals appreciate the effort",
            "Be respectful during cultural ceremonies and performances"
        ]
        
        return "<ul>" + "".join([f"<li>{tip}</li>" for tip in advice]) + "</ul>"
    
    def _generate_emergency_fallback(self, user_query: str) -> str:
        """Generate emergency fallback response when all else fails."""
        return f"""
        <div class="local-guide-response">
            <p>안녕하세요! (Hello!) I'm your Korean local guide, and while I'm having some technical difficulties, 
            I still want to help you explore authentic Korean culture!</p>
            
            <p>For your question about Korean experiences, here are some timeless recommendations:</p>
            
            <ul>
                <li><strong>Gyeongbokgung Palace</strong> - Experience traditional Korean royal architecture</li>
                <li><strong>Hongdae District</strong> - Youth culture, street food, and nightlife</li>
                <li><strong>Insadong</strong> - Traditional arts, crafts, and tea culture</li>
                <li><strong>Korean BBQ Experience</strong> - Social dining with samgyeopsal</li>
            </ul>
            
            <p><em>💡 Cultural tip: {self.korean_cultural_context['cultural_norms']['tipping']}</em></p>
            
            <p>Please try your question again in a moment for more personalized recommendations!</p>
        </div>
        """
    
    def format_local_guide_response(self, data: Dict[str, Any]) -> str:
        """
        Format response data as authentic local guide response.
        
        Args:
            data: Dictionary containing response data and recommendations
        
        Returns:
            Formatted HTML response with Korean cultural context
        """
        try:
            user_query = data.get('user_query', '')
            recommendations = data.get('recommendations', [])
            cultural_context = data.get('cultural_context', '')
            user_context = data.get('user_context', {})
            
            return self.generate_response(user_query, recommendations, cultural_context, user_context)
            
        except Exception as e:
            self.logger.error(f"Error formatting local guide response: {e}")
            return self._generate_emergency_fallback(data.get('user_query', 'Korean culture'))
    
    def _handle_fallback(self, error: Exception) -> str:
        """Handle fallback when ResponseGenerator is unavailable."""
        self.logger.warning(f"ResponseGenerator unavailable, using emergency fallback: {error}")
        return self._generate_emergency_fallback("general inquiry")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current ResponseGenerator status."""
        base_status = super().get_status()
        
        # Add Gemini service status
        gemini_status = self.gemini_service.get_status() if self.gemini_service else {
            'service': 'GeminiService',
            'state': 'unavailable',
            'available': False
        }
        
        base_status.update({
            'gemini_service_status': gemini_status,
            'korean_cultural_context_loaded': bool(self.korean_cultural_context),
            'local_guide_persona_loaded': bool(self.local_guide_persona),
            'fallback_templates_loaded': bool(self.fallback_templates)
        })
        
        return base_status


# Legacy compatibility functions for existing code
def generate_local_guide_response(user_question: str, recommendations: list, 
                                cultural_context: str = None) -> str:
    """
    Legacy compatibility function for existing code.
    Generate natural language response as a Korean local guide.
    """
    generator = ResponseGenerator()
    return generator.generate_response(user_question, recommendations, cultural_context)


def format_local_guide_response(data: Dict[str, Any]) -> str:
    """
    Legacy compatibility function for existing code.
    Format response data as authentic local guide response.
    """
    generator = ResponseGenerator()
    return generator.format_local_guide_response(data)