"""
Local Guide System orchestration for authentic Korean cultural recommendations.
Coordinates all services to provide culturally authentic Korean travel advice.
"""
import os
from typing import Dict, Any, List, Optional, Tuple
from .base_service import BaseService
from .tastedive_api import CulturalDiscoveryEngine
from .algolia_api import SearchService
from .googlemaps_api import GoogleMapsService
from .gemini_api import GeminiService
from .response_generator import ResponseGenerator
from .user_profile_manager import UserProfileManager


class LocalGuideSystem(BaseService):
    """
    AI-powered Korean local guide system that orchestrates all services.
    
    Provides culturally authentic Korean travel advice by coordinating:
    - Cultural Discovery Engine (TasteDive) for cultural similarity matching
    - Search Service (Algolia) for fast place search and filtering
    - Google Maps Service for geographic context and place details
    - Gemini Service for natural language response generation
    - User Profile Manager for personalization
    """
    
    def __init__(self, user_profile_manager: Optional[UserProfileManager] = None):
        super().__init__("LocalGuideSystem")
        
        # Initialize all coordinated services
        self.cultural_engine = CulturalDiscoveryEngine()
        self.search_service = SearchService()
        self.map_service = GoogleMapsService()
        self.response_generator = ResponseGenerator()
        self.gemini_service = GeminiService()  # Keep for backward compatibility
        self.user_profile_manager = user_profile_manager
        
        # Korean cultural context from product.md
        self.korean_cultural_context = self._initialize_korean_cultural_context()
        
        # Seoul neighborhood insights for specific recommendations
        self.neighborhood_insights = self._initialize_neighborhood_insights()
        
        # Authentic experience prioritization weights
        self.authenticity_weights = {
            'traditional': 1.0,
            'local': 0.9,
            'cultural': 0.8,
            'authentic': 0.8,
            'heritage': 0.7,
            'modern_korean': 0.6,
            'tourist': 0.2,
            'generic': 0.1
        }
    
    def _initialize_korean_cultural_context(self) -> Dict[str, Any]:
        """Initialize Korean cultural context from product.md knowledge."""
        return {
            'cultural_norms': {
                'tipping': 'Tipping is not customary in South Korea',
                'punctuality': 'People value punctuality and personal space',
                'transport': 'Public transport is preferred over taxis for short distances',
                'subway_etiquette': 'Speaking loudly on subways is considered rude'
            },
            'food_culture': {
                'tteokbokki': 'Spicy-sweet street food popular among students',
                'samgyeopsal': 'Social meal eaten in groups, usually at night',
                'banchan': 'Korean meals often include shared side dishes (banchan)',
                'street_food_timing': 'Street food is best explored after sunset',
                'restaurant_specialization': 'Restaurants often specialize in only one dish',
                'substitutions': 'Asking for substitutions is uncommon',
                'closing_hours': 'Many places close between 3–5 PM'
            },
            'local_slang': {
                'daebak': 'Amazing',
                'hwaiting': 'Encouragement',
                'maknae': 'Youngest person in a group'
            },
            'tourist_pitfalls': [
                'Restaurants often specialize in only one dish',
                'Asking for substitutions is uncommon',
                'Many places close between 3–5 PM'
            ]
        }
    
    def _initialize_neighborhood_insights(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Seoul neighborhood-specific insights."""
        return {
            'hongdae': {
                'character': 'Youth culture, street food, nightlife',
                'best_for': ['nightlife', 'indie music', 'street performances', 'young crowd'],
                'cultural_significance': 'University area representing Korean youth culture',
                'authentic_experiences': ['Live music venues', 'Street food after 9 PM', 'Indie shops'],
                'avoid_tourist_traps': ['Overpriced themed cafes', 'Chain restaurants in main area']
            },
            'myeongdong': {
                'character': 'Shopping and tourist street food',
                'best_for': ['shopping', 'cosmetics', 'street food', 'first-time visitors'],
                'cultural_significance': 'Major commercial district showcasing Korean consumer culture',
                'authentic_experiences': ['Korean cosmetics shopping', 'Street food stalls', 'Department stores'],
                'avoid_tourist_traps': ['Overpriced restaurants targeting tourists', 'Generic souvenir shops']
            },
            'itaewon': {
                'character': 'International food and nightlife',
                'best_for': ['international cuisine', 'nightlife', 'multicultural experience'],
                'cultural_significance': 'International district showing Korea\'s global connections',
                'authentic_experiences': ['Halal Korean fusion', 'International bars', 'Multicultural events'],
                'avoid_tourist_traps': ['Generic Western food', 'Overpriced foreigner-targeted venues']
            },
            'gangnam': {
                'character': 'Cafés, fine dining, upscale shopping',
                'best_for': ['luxury shopping', 'high-end dining', 'modern Korean lifestyle'],
                'cultural_significance': 'Represents modern Korean affluence and K-pop culture',
                'authentic_experiences': ['High-end Korean BBQ', 'Designer shopping', 'Trendy cafes'],
                'avoid_tourist_traps': ['K-pop tourist shops', 'Overpriced themed restaurants']
            },
            'jongno': {
                'character': 'Historic district with traditional culture',
                'best_for': ['history', 'traditional culture', 'palaces', 'temples'],
                'cultural_significance': 'Historic heart of Seoul with traditional Korean culture',
                'authentic_experiences': ['Palace visits', 'Traditional tea houses', 'Hanbok rental'],
                'avoid_tourist_traps': ['Tourist-focused traditional restaurants', 'Overpriced hanbok rentals']
            },
            'insadong': {
                'character': 'Traditional arts and crafts with tea culture',
                'best_for': ['traditional arts', 'crafts shopping', 'tea culture', 'cultural experiences'],
                'cultural_significance': 'Traditional arts district preserving Korean cultural heritage',
                'authentic_experiences': ['Traditional tea ceremonies', 'Artisan workshops', 'Antique shopping'],
                'avoid_tourist_traps': ['Mass-produced "traditional" items', 'Tourist-focused tea houses']
            }
        }
    
    def get_recommendation(self, user_query: str, user_profile: Optional[Dict[str, Any]] = None,
                          location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Generate culturally authentic Korean recommendations based on user query.
        
        Args:
            user_query: User's question or request
            user_profile: User profile data for personalization
            location: Optional location context (lat, lng)
        
        Returns:
            Comprehensive recommendation response with cultural context
        """
        try:
            # Step 1: Analyze user intent and extract cultural context
            intent_analysis = self._analyze_user_intent(user_query)
            
            # Step 2: Get personalized preferences if user profile available
            personalization_context = self._get_personalization_context(user_profile)
            
            # Step 3: Generate recommendations using coordinated services
            recommendations = self._coordinate_recommendation_services(
                user_query, intent_analysis, personalization_context, location
            )
            
            # Step 4: Apply authentic experience prioritization
            prioritized_recommendations = self._prioritize_authentic_experiences(recommendations)
            
            # Step 5: Add neighborhood-specific insights
            enriched_recommendations = self._add_neighborhood_insights(prioritized_recommendations)
            
            # Step 6: Generate natural language response with cultural context
            response = self._generate_cultural_response(
                user_query, enriched_recommendations, intent_analysis, personalization_context
            )
            
            return {
                'response': response,
                'recommendations': enriched_recommendations,
                'cultural_context': intent_analysis.get('cultural_themes', []),
                'neighborhood_insights': self._extract_relevant_neighborhood_insights(enriched_recommendations),
                'authenticity_score': self._calculate_overall_authenticity_score(enriched_recommendations),
                'personalization_applied': bool(personalization_context)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation for '{user_query}': {e}")
            return self._handle_recommendation_fallback(user_query, user_profile)
    
    def _analyze_user_intent(self, user_query: str) -> Dict[str, Any]:
        """Analyze user intent and extract cultural themes."""
        # Use ResponseGenerator's Gemini service for intent analysis if available
        if self.response_generator and self.response_generator.is_available():
            try:
                intent_data = self.response_generator.gemini_service.extract_entity_with_context(user_query)
                
                # Enhance with Korean cultural theme detection
                cultural_themes = self._detect_cultural_themes(user_query)
                intent_data['cultural_themes'] = cultural_themes
                intent_data['neighborhood_focus'] = self._detect_neighborhood_focus(user_query)
                
                return intent_data
            except Exception as e:
                self.logger.warning(f"ResponseGenerator intent analysis failed: {e}")
        
        # Fallback to legacy Gemini service
        if self.gemini_service and self.gemini_service.is_available():
            try:
                intent_data = self.gemini_service.extract_entity_with_context(user_query)
                
                # Enhance with Korean cultural theme detection
                cultural_themes = self._detect_cultural_themes(user_query)
                intent_data['cultural_themes'] = cultural_themes
                intent_data['neighborhood_focus'] = self._detect_neighborhood_focus(user_query)
                
                return intent_data
            except Exception as e:
                self.logger.warning(f"Gemini intent analysis failed: {e}")
        
        # Fallback intent analysis
        return self._fallback_intent_analysis(user_query)
    
    def _detect_cultural_themes(self, query: str) -> List[str]:
        """Detect Korean cultural themes in user query."""
        query_lower = query.lower()
        themes = []
        
        theme_keywords = {
            'food_culture': ['food', 'eat', 'restaurant', 'cuisine', 'dining', 'korean food', 'bbq', 'kimchi'],
            'traditional_culture': ['traditional', 'temple', 'palace', 'hanbok', 'heritage', 'history'],
            'modern_culture': ['k-pop', 'kpop', 'modern', 'trendy', 'fashion', 'technology'],
            'nightlife': ['nightlife', 'bar', 'club', 'night', 'party', 'drink'],
            'shopping': ['shopping', 'buy', 'store', 'market', 'cosmetics', 'fashion'],
            'nature': ['park', 'nature', 'hiking', 'mountain', 'river', 'outdoor'],
            'entertainment': ['music', 'movie', 'show', 'performance', 'concert', 'theater']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                themes.append(theme)
        
        return themes if themes else ['general_culture']
    
    def _detect_neighborhood_focus(self, query: str) -> Optional[str]:
        """Detect if user is asking about specific Seoul neighborhoods."""
        query_lower = query.lower()
        
        for neighborhood in self.neighborhood_insights.keys():
            if neighborhood in query_lower:
                return neighborhood
        
        # Check for alternative neighborhood names
        neighborhood_aliases = {
            'hongik': 'hongdae',
            'university': 'hongdae',
            'shopping': 'myeongdong',
            'international': 'itaewon',
            'foreigner': 'itaewon',
            'rich': 'gangnam',
            'luxury': 'gangnam',
            'palace': 'jongno',
            'traditional': 'insadong',
            'art': 'insadong'
        }
        
        for alias, neighborhood in neighborhood_aliases.items():
            if alias in query_lower:
                return neighborhood
        
        return None
    
    def _get_personalization_context(self, user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract personalization context from user profile."""
        if not user_profile:
            return {}
        
        return {
            'interests': user_profile.get('preferences', {}).get('interests', []),
            'food_restrictions': user_profile.get('preferences', {}).get('food_restrictions', []),
            'cultural_preferences': user_profile.get('preferences', {}).get('cultural_preferences', []),
            'budget_range': user_profile.get('preferences', {}).get('budget_range', 'mid-range'),
            'travel_style': user_profile.get('preferences', {}).get('travel_style', 'solo'),
            'visited_places': [place['name'] for place in user_profile.get('history', {}).get('visited_places', [])],
            'favorite_places': [fav['name'] for fav in user_profile.get('history', {}).get('favorites', [])],
            'preferred_neighborhoods': user_profile.get('personalization', {}).get('preferred_neighborhoods', [])
        }
    
    def _coordinate_recommendation_services(self, user_query: str, intent_analysis: Dict[str, Any],
                                          personalization_context: Dict[str, Any],
                                          location: Optional[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Coordinate all services to generate comprehensive recommendations."""
        all_recommendations = []
        
        # Get cultural recommendations from TasteDive
        if self.cultural_engine and self.cultural_engine.is_available():
            try:
                cultural_recs = self.cultural_engine.find_similar_korean_experiences(
                    user_query, content_type="all", limit=8
                )
                for rec in cultural_recs:
                    rec['source'] = 'cultural_discovery'
                    rec['recommendation_type'] = 'cultural_experience'
                all_recommendations.extend(cultural_recs)
            except Exception as e:
                self.logger.warning(f"Cultural discovery failed: {e}")
        
        # Get place recommendations from search service
        if self.search_service and self.search_service.is_available():
            try:
                # Default to Seoul center if no location provided
                search_location = location or (37.5665, 126.9780)
                
                place_recs = self.search_service.search_places(
                    user_query, location=search_location, place_type=None
                )
                for rec in place_recs:
                    rec['source'] = 'search_service'
                    rec['recommendation_type'] = 'place'
                all_recommendations.extend(place_recs[:6])  # Limit place results
            except Exception as e:
                self.logger.warning(f"Search service failed: {e}")
        
        # Get neighborhood-specific recommendations if neighborhood detected
        neighborhood_focus = intent_analysis.get('neighborhood_focus')
        if neighborhood_focus and self.search_service:
            try:
                neighborhood_recs = self.search_service.search_by_neighborhood(
                    neighborhood_focus, place_type=None
                )
                for rec in neighborhood_recs:
                    rec['source'] = 'neighborhood_search'
                    rec['recommendation_type'] = 'neighborhood_place'
                all_recommendations.extend(neighborhood_recs[:4])  # Limit neighborhood results
            except Exception as e:
                self.logger.warning(f"Neighborhood search failed: {e}")
        
        # Apply personalization filtering
        if personalization_context:
            all_recommendations = self._apply_personalization_filtering(
                all_recommendations, personalization_context
            )
        
        return all_recommendations
    
    def _apply_personalization_filtering(self, recommendations: List[Dict[str, Any]],
                                       personalization_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply personalization filtering based on user preferences and history."""
        filtered_recommendations = []
        
        user_interests = set(personalization_context.get('interests', []))
        visited_places = set(personalization_context.get('visited_places', []))
        food_restrictions = personalization_context.get('food_restrictions', [])
        cultural_preferences = set(personalization_context.get('cultural_preferences', []))
        
        for rec in recommendations:
            # Skip already visited places
            rec_name = rec.get('Name', rec.get('name', ''))
            if rec_name in visited_places:
                continue
            
            # Apply food restrictions for restaurant recommendations
            if rec.get('category') == 'restaurant' or 'restaurant' in rec.get('Type', '').lower():
                if self._violates_food_restrictions(rec, food_restrictions):
                    continue
            
            # Boost recommendations matching user interests
            rec['personalization_score'] = self._calculate_personalization_score(
                rec, user_interests, cultural_preferences
            )
            
            filtered_recommendations.append(rec)
        
        # Sort by personalization score
        filtered_recommendations.sort(key=lambda x: x.get('personalization_score', 0), reverse=True)
        
        return filtered_recommendations
    
    def _violates_food_restrictions(self, recommendation: Dict[str, Any], restrictions: List[str]) -> bool:
        """Check if recommendation violates user's food restrictions."""
        if not restrictions:
            return False
        
        # Safely get and convert all text fields to strings
        name = str(recommendation.get('Name', '')) if recommendation.get('Name') is not None else ''
        teaser = str(recommendation.get('wTeaser', '')) if recommendation.get('wTeaser') is not None else ''
        description = str(recommendation.get('description', '')) if recommendation.get('description') is not None else ''
        cultural_tags = recommendation.get('cultural_tags', [])
        
        # Ensure cultural_tags is a list and all elements are strings
        if not isinstance(cultural_tags, list):
            cultural_tags = []
        cultural_tags_str = ' '.join(str(tag) for tag in cultural_tags if tag is not None)
        
        rec_text = f"{name} {teaser} {description} {cultural_tags_str}".lower()
        
        restriction_keywords = {
            'vegetarian': ['meat', 'beef', 'pork', 'chicken', 'fish', 'seafood', 'bbq'],
            'vegan': ['meat', 'beef', 'pork', 'chicken', 'fish', 'seafood', 'dairy', 'egg', 'bbq'],
            'no_spicy': ['spicy', 'hot', 'chili', 'gochujang', 'kimchi'],
            'halal': ['pork', 'alcohol', 'wine', 'beer'],
            'gluten_free': ['wheat', 'noodle', 'bread', 'flour']
        }
        
        for restriction in restrictions:
            if restriction.lower() in restriction_keywords:
                keywords = restriction_keywords[restriction.lower()]
                if any(keyword in rec_text for keyword in keywords):
                    return True
        
        return False
    
    def _calculate_personalization_score(self, recommendation: Dict[str, Any],
                                       user_interests: set, cultural_preferences: set) -> float:
        """Calculate personalization score based on user preferences."""
        score = 0.0
        
        # Safely get and convert all text fields to strings
        name = str(recommendation.get('Name', '')) if recommendation.get('Name') is not None else ''
        teaser = str(recommendation.get('wTeaser', '')) if recommendation.get('wTeaser') is not None else ''
        description = str(recommendation.get('description', '')) if recommendation.get('description') is not None else ''
        cultural_tags = recommendation.get('cultural_tags', [])
        
        # Ensure cultural_tags is a list and all elements are strings
        if not isinstance(cultural_tags, list):
            cultural_tags = []
        cultural_tags_str = ' '.join(str(tag) for tag in cultural_tags if tag is not None)
        
        rec_text = f"{name} {teaser} {description} {cultural_tags_str}".lower()
        
        # Interest matching
        for interest in user_interests:
            if interest.lower() in rec_text:
                score += 0.3
        
        # Cultural preference matching
        for preference in cultural_preferences:
            if preference.lower() in rec_text:
                score += 0.2
        
        # Boost for high cultural relevance
        cultural_relevance = recommendation.get('cultural_relevance', 0)
        score += cultural_relevance * 0.1
        
        return score
    
    def _prioritize_authentic_experiences(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize authentic local experiences over tourist attractions."""
        for rec in recommendations:
            authenticity_score = self._calculate_authenticity_score(rec)
            rec['authenticity_score'] = authenticity_score
        
        # Sort by authenticity score, then by cultural relevance
        recommendations.sort(
            key=lambda x: (x.get('authenticity_score', 0), x.get('cultural_relevance', 0)),
            reverse=True
        )
        
        return recommendations
    
    def _calculate_authenticity_score(self, recommendation: Dict[str, Any]) -> float:
        """Calculate authenticity score based on cultural indicators."""
        score = 0.5  # Base score
        
        # Safely get and convert all text fields to strings
        name = str(recommendation.get('Name', '')) if recommendation.get('Name') is not None else ''
        teaser = str(recommendation.get('wTeaser', '')) if recommendation.get('wTeaser') is not None else ''
        description = str(recommendation.get('description', '')) if recommendation.get('description') is not None else ''
        cultural_context = str(recommendation.get('cultural_context', '')) if recommendation.get('cultural_context') is not None else ''
        cultural_tags = recommendation.get('cultural_tags', [])
        
        # Ensure cultural_tags is a list and all elements are strings
        if not isinstance(cultural_tags, list):
            cultural_tags = []
        cultural_tags_str = ' '.join(str(tag) for tag in cultural_tags if tag is not None)
        
        rec_text = f"{name} {teaser} {description} {cultural_context} {cultural_tags_str}".lower()
        
        # Apply authenticity weights
        for keyword, weight in self.authenticity_weights.items():
            if keyword in rec_text:
                score += weight * 0.1
        
        # Boost for local knowledge source
        if recommendation.get('source') == 'local_knowledge':
            score += 0.2
        
        # Boost for neighborhood-specific recommendations
        if recommendation.get('neighborhood') in self.neighborhood_insights:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _add_neighborhood_insights(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add neighborhood-specific cultural insights to recommendations."""
        for rec in recommendations:
            neighborhood = rec.get('neighborhood', '')
            if neighborhood is None:
                neighborhood = ''
            neighborhood = str(neighborhood).lower()
            
            if neighborhood in self.neighborhood_insights:
                insights = self.neighborhood_insights[neighborhood]
                
                # Add neighborhood character
                existing_context = rec.get('cultural_context', '')
                if existing_context is None:
                    existing_context = ''
                
                # Ensure existing_context is a string
                existing_context = str(existing_context)
                
                if existing_context and not existing_context.endswith('.'):
                    existing_context += '. '
                elif existing_context:
                    existing_context += ' '
                
                character = insights.get('character', '')
                if character:
                    rec['cultural_context'] = existing_context + f"Located in {neighborhood.title()}: {character}"
                
                rec['neighborhood_insights'] = {
                    'best_for': insights.get('best_for', []),
                    'cultural_significance': insights.get('cultural_significance', ''),
                    'authentic_experiences': insights.get('authentic_experiences', []),
                    'avoid_tourist_traps': insights.get('avoid_tourist_traps', [])
                }
        
        return recommendations
    
    def _generate_cultural_response(self, user_query: str, recommendations: List[Dict[str, Any]],
                                  intent_analysis: Dict[str, Any], personalization_context: Dict[str, Any]) -> str:
        """Generate natural language response with Korean cultural context."""
        # Prepare cultural context for response generation
        cultural_themes = intent_analysis.get('cultural_themes', [])
        neighborhood_focus = intent_analysis.get('neighborhood_focus')
        
        # Add relevant Korean cultural norms and insights
        cultural_context_elements = []
        
        # Add food culture context if relevant
        if 'food_culture' in cultural_themes:
            cultural_context_elements.extend([
                self.korean_cultural_context['food_culture']['banchan'],
                self.korean_cultural_context['food_culture']['street_food_timing']
            ])
        
        # Add neighborhood insights if relevant
        if neighborhood_focus and neighborhood_focus in self.neighborhood_insights:
            insights = self.neighborhood_insights[neighborhood_focus]
            cultural_context_elements.append(f"{neighborhood_focus.title()}: {insights['character']}")
        
        # Add cultural norms
        cultural_context_elements.extend([
            self.korean_cultural_context['cultural_norms']['tipping'],
            self.korean_cultural_context['cultural_norms']['punctuality']
        ])
        
        # Ensure all elements are strings
        cultural_context_elements = [str(elem) for elem in cultural_context_elements if elem is not None]
        cultural_context_text = '. '.join(cultural_context_elements)
        
        # Generate response using ResponseGenerator if available
        if self.response_generator and self.response_generator.is_available():
            try:
                return self.response_generator.generate_response(
                    user_query, recommendations, cultural_context_text, personalization_context
                )
            except Exception as e:
                self.logger.warning(f"ResponseGenerator failed: {e}")
        
        # Fallback to legacy Gemini service
        if self.gemini_service and self.gemini_service.is_available():
            try:
                return self.gemini_service.generate_local_guide_response(
                    user_query, recommendations, cultural_context_text
                )
            except Exception as e:
                self.logger.warning(f"Gemini response generation failed: {e}")
        
        # Fallback to structured response
        return self._generate_fallback_response(user_query, recommendations, cultural_context_elements)
    
    def _generate_fallback_response(self, user_query: str, recommendations: List[Dict[str, Any]],
                                  cultural_context: List[str]) -> str:
        """Generate structured fallback response when Gemini is unavailable."""
        if not recommendations:
            # Ensure cultural_context has at least one element
            cultural_tip = cultural_context[0] if cultural_context else "Tipping is not customary in South Korea."
            return f"""
            <div class="local-guide-response">
                <p>안녕하세요! (Hello!) As your Korean local guide, I'd love to help you explore authentic Korean culture.</p>
                <p>For your question about Korean experiences, I recommend exploring these neighborhoods:</p>
                <ul>
                    <li><strong>Hongdae</strong> - Youth culture and nightlife</li>
                    <li><strong>Myeongdong</strong> - Shopping and street food</li>
                    <li><strong>Itaewon</strong> - International district</li>
                    <li><strong>Insadong</strong> - Traditional arts and tea culture</li>
                </ul>
                <p><em>Cultural tip: {cultural_tip}</em></p>
            </div>
            """
        
        # Group recommendations by type
        places = [r for r in recommendations if r.get('recommendation_type') == 'place']
        experiences = [r for r in recommendations if r.get('recommendation_type') == 'cultural_experience']
        
        response_parts = ['<div class="local-guide-response">']
        response_parts.append('<p>안녕하세요! (Hello!) Here are my authentic Korean recommendations:</p>')
        
        if places:
            response_parts.append('<h4>🏮 Places to Visit:</h4>')
            response_parts.append('<ul>')
            for place in places[:3]:
                name = place.get('Name', place.get('name', 'Korean Place'))
                context = place.get('cultural_context', 'Authentic Korean experience')
                # Ensure name and context are strings
                name = str(name) if name is not None else 'Korean Place'
                context = str(context) if context is not None else 'Authentic Korean experience'
                response_parts.append(f'<li><strong>{name}</strong> - {context}</li>')
            response_parts.append('</ul>')
        
        if experiences:
            response_parts.append('<h4>🎭 Cultural Experiences:</h4>')
            response_parts.append('<ul>')
            for exp in experiences[:3]:
                name = exp.get('Name', 'Korean Cultural Experience')
                teaser = exp.get('wTeaser', 'Authentic Korean cultural activity')
                # Ensure name and teaser are strings
                name = str(name) if name is not None else 'Korean Cultural Experience'
                teaser = str(teaser) if teaser is not None else 'Authentic Korean cultural activity'
                response_parts.append(f'<li><strong>{name}</strong> - {teaser}</li>')
            response_parts.append('</ul>')
        
        if cultural_context:
            cultural_tip = str(cultural_context[0]) if cultural_context[0] is not None else "Tipping is not customary in South Korea."
            response_parts.append(f'<p><em>💡 Cultural tip: {cultural_tip}</em></p>')
        
        response_parts.append('</div>')
        
        return ''.join(response_parts)
    
    def _extract_relevant_neighborhood_insights(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant neighborhood insights from recommendations."""
        neighborhood_insights = {}
        
        for rec in recommendations:
            neighborhood = rec.get('neighborhood', '')
            if neighborhood is None:
                neighborhood = ''
            neighborhood = str(neighborhood).lower()
            
            if neighborhood in self.neighborhood_insights and neighborhood not in neighborhood_insights:
                neighborhood_insights[neighborhood] = self.neighborhood_insights[neighborhood]
        
        return neighborhood_insights
    
    def _calculate_overall_authenticity_score(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall authenticity score for the recommendation set."""
        if not recommendations:
            return 0.0
        
        total_score = sum(rec.get('authenticity_score', 0) for rec in recommendations)
        return total_score / len(recommendations)
    
    def _fallback_intent_analysis(self, user_query: str) -> Dict[str, Any]:
        """Fallback intent analysis when Gemini is unavailable."""
        query_lower = user_query.lower()
        
        # Simple keyword-based analysis
        entity = 'korean culture'
        intent_type = 'place'
        korean_related = True
        
        # Extract potential entity
        words = user_query.split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                entity = word
                break
        
        # Determine type
        if any(word in query_lower for word in ['eat', 'food', 'restaurant', 'dining']):
            intent_type = 'restaurant'
        elif any(word in query_lower for word in ['visit', 'see', 'attraction', 'place']):
            intent_type = 'attraction'
        elif any(word in query_lower for word in ['music', 'movie', 'show', 'entertainment']):
            intent_type = 'entertainment'
        
        return {
            'entity': entity,
            'type': intent_type,
            'intent': 'seeking recommendations',
            'korean_related': korean_related,
            'cultural_themes': self._detect_cultural_themes(user_query),
            'neighborhood_focus': self._detect_neighborhood_focus(user_query)
        }
    
    def _handle_recommendation_fallback(self, user_query: str, user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle fallback when recommendation generation fails."""
        fallback_recommendations = [
            {
                'Name': 'Gyeongbokgung Palace',
                'Type': 'attraction',
                'cultural_context': 'Historic royal palace showcasing traditional Korean architecture',
                'neighborhood': 'jongno',
                'authenticity_score': 0.9,
                'source': 'fallback'
            },
            {
                'Name': 'Hongdae Street Food',
                'Type': 'food',
                'cultural_context': 'Authentic Korean street food experience in youth culture district',
                'neighborhood': 'hongdae',
                'authenticity_score': 0.8,
                'source': 'fallback'
            },
            {
                'Name': 'Insadong Traditional Tea House',
                'Type': 'experience',
                'cultural_context': 'Traditional Korean tea ceremony and cultural experience',
                'neighborhood': 'insadong',
                'authenticity_score': 0.9,
                'source': 'fallback'
            }
        ]
        
        fallback_response = self._generate_fallback_response(
            user_query, fallback_recommendations, 
            [self.korean_cultural_context['cultural_norms']['tipping']]
        )
        
        return {
            'response': fallback_response,
            'recommendations': fallback_recommendations,
            'cultural_context': ['general_culture'],
            'neighborhood_insights': {},
            'authenticity_score': 0.8,
            'personalization_applied': False,
            'fallback_used': True
        }
    
    def handle_fallback(self, service_failures: List[str]) -> Dict[str, Any]:
        """Handle fallback when multiple services fail."""
        self.logger.warning(f"Multiple service failures: {service_failures}")
        
        return {
            'response': """
            <div class="local-guide-fallback">
                <p>안녕하세요! (Hello!) I'm your Korean local guide, and while some of my services are temporarily unavailable, 
                I can still share authentic Korean cultural insights with you.</p>
                <p>Here are some timeless Korean experiences I always recommend:</p>
                <ul>
                    <li><strong>Traditional Markets</strong> - Visit Namdaemun or Dongdaemun for authentic Korean shopping</li>
                    <li><strong>Korean BBQ</strong> - Try samgyeopsal (pork belly) - it's a social experience, not just a meal</li>
                    <li><strong>Temple Stay</strong> - Experience Korean Buddhist culture at Jogyesa Temple</li>
                    <li><strong>Hanbok Experience</strong> - Rent traditional Korean clothing in Bukchon Hanok Village</li>
                </ul>
                <p><em>Cultural tip: Remember, tipping is not customary in Korea, and many places close between 3-5 PM!</em></p>
            </div>
            """,
            'recommendations': [],
            'cultural_context': ['traditional_culture', 'food_culture'],
            'neighborhood_insights': self.neighborhood_insights,
            'authenticity_score': 1.0,
            'personalization_applied': False,
            'fallback_used': True,
            'service_failures': service_failures
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the Local Guide System and all coordinated services."""
        service_statuses = {}
        
        services = {
            'cultural_engine': self.cultural_engine,
            'search_service': self.search_service,
            'map_service': self.map_service,
            'response_generator': self.response_generator,
            'gemini_service': self.gemini_service  # Legacy compatibility
        }
        
        for name, service in services.items():
            if service:
                service_statuses[name] = service.get_status()
            else:
                service_statuses[name] = {
                    'service': name,
                    'state': 'unavailable',
                    'available': False
                }
        
        # Calculate overall system health
        available_services = sum(1 for status in service_statuses.values() if status.get('available', False))
        total_services = len(service_statuses)
        system_health = available_services / total_services if total_services > 0 else 0
        
        return {
            'service': 'LocalGuideSystem',
            'state': 'healthy' if system_health > 0.5 else 'degraded' if system_health > 0 else 'unavailable',
            'available': system_health > 0,
            'system_health': system_health,
            'service_statuses': service_statuses,
            'korean_cultural_context_loaded': bool(self.korean_cultural_context),
            'neighborhood_insights_loaded': bool(self.neighborhood_insights)
        }