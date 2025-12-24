"""
Service Manager for coordinating all API integrations.
Provides centralized service management with health monitoring and fallback coordination.
"""
import os
from typing import Dict, Any, List, Optional
from .base_service import BaseService
from .tastedive_api import CulturalDiscoveryEngine
from .algolia_api import SearchService
from .googlemaps_api import GoogleMapsService
from .gemini_api import GeminiService
from .response_generator import ResponseGenerator
from .local_guide_system import LocalGuideSystem


class ServiceManager:
    """Centralized manager for all API services with health monitoring."""
    
    def __init__(self):
        """Initialize all services with environment configuration."""
        self.services = {}
        self._initialize_services()
        
        # Initialize Local Guide System as the main orchestrator
        self.local_guide_system = None
        self._initialize_local_guide_system()
    
    def _initialize_services(self):
        """Initialize all API services with error handling."""
        try:
            self.services['cultural_discovery'] = CulturalDiscoveryEngine()
        except Exception as e:
            print(f"Warning: Cultural Discovery Engine initialization failed: {e}")
            self.services['cultural_discovery'] = None
        
        # Keep TasteDive for backward compatibility
        try:
            self.services['tastedive'] = CulturalDiscoveryEngine()
        except Exception as e:
            print(f"Warning: TasteDive service initialization failed: {e}")
            self.services['tastedive'] = None
        
        try:
            self.services['search'] = SearchService()
        except Exception as e:
            print(f"Warning: Search service initialization failed: {e}")
            self.services['search'] = None
        
        # Keep Algolia for backward compatibility
        try:
            self.services['algolia'] = SearchService()
        except Exception as e:
            print(f"Warning: Algolia service initialization failed: {e}")
            self.services['algolia'] = None
        
        try:
            self.services['googlemaps'] = GoogleMapsService()
        except Exception as e:
            print(f"Warning: Google Maps service initialization failed: {e}")
            self.services['googlemaps'] = None
        
        try:
            self.services['gemini'] = GeminiService()
        except Exception as e:
            print(f"Warning: Gemini service initialization failed: {e}")
            self.services['gemini'] = None
        
        try:
            self.services['response_generator'] = ResponseGenerator()
        except Exception as e:
            print(f"Warning: Response Generator initialization failed: {e}")
            self.services['response_generator'] = None
    
    def _initialize_local_guide_system(self):
        """Initialize the Local Guide System orchestrator."""
        try:
            self.local_guide_system = LocalGuideSystem()
            print("Local Guide System initialized successfully")
        except Exception as e:
            print(f"Warning: Local Guide System initialization failed: {e}")
            self.local_guide_system = None
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get a specific service by name."""
        return self.services.get(service_name)
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services."""
        status = {}
        for name, service in self.services.items():
            if service:
                status[name] = service.get_status()
            else:
                status[name] = {
                    "service": name,
                    "state": "unavailable",
                    "failure_count": 0,
                    "available": False
                }
        
        # Add Local Guide System status
        if self.local_guide_system:
            status['local_guide_system'] = self.local_guide_system.get_status()
        else:
            status['local_guide_system'] = {
                "service": "local_guide_system",
                "state": "unavailable",
                "failure_count": 0,
                "available": False
            }
        
        return status
    
    def get_local_guide_recommendation(self, user_query: str, user_profile: Optional[Dict[str, Any]] = None,
                                     location: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Get culturally authentic Korean recommendations using the Local Guide System.
        
        Args:
            user_query: User's question or request
            user_profile: User profile data for personalization
            location: Optional location context (lat, lng)
        
        Returns:
            Comprehensive recommendation response with cultural context
        """
        if self.local_guide_system and self.local_guide_system.is_available():
            try:
                return self.local_guide_system.get_recommendation(user_query, user_profile, location)
            except Exception as e:
                print(f"Local Guide System failed: {e}")
        
        # Fallback to legacy recommendation system
        return self._get_legacy_recommendations(user_query, user_profile)
    
    def get_healthy_services(self) -> List[str]:
        """Get list of currently healthy services."""
        healthy = []
        for name, service in self.services.items():
            if service and service.is_available():
                healthy.append(name)
        return healthy
    
    def _get_legacy_recommendations(self, user_query: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback to legacy recommendation system when Local Guide System fails."""
        try:
            # Use existing cultural recommendations method
            interests = []
            if user_profile:
                interests = user_profile.get('preferences', {}).get('interests', [])
            
            recommendations = self.get_cultural_recommendations(user_query, interests)
            
            # Generate response using existing method
            response = self.generate_response(user_query, recommendations)
            
            return {
                'response': response,
                'recommendations': recommendations,
                'cultural_context': ['general_culture'],
                'neighborhood_insights': {},
                'authenticity_score': 0.5,
                'personalization_applied': bool(user_profile),
                'fallback_used': True,
                'legacy_system': True
            }
        except Exception as e:
            print(f"Legacy recommendation system also failed: {e}")
            return {
                'response': "<p>I apologize, but I'm having trouble generating recommendations right now. Please try again later.</p>",
                'recommendations': [],
                'cultural_context': [],
                'neighborhood_insights': {},
                'authenticity_score': 0.0,
                'personalization_applied': False,
                'fallback_used': True,
                'error': str(e)
            }

    def get_cultural_recommendations(self, query: str, interests: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get cultural recommendations using the Cultural Discovery Engine.
        Falls back gracefully when services are unavailable.
        """
        recommendations = []
        
        # Try Cultural Discovery Engine first
        cultural_engine = self.get_service('cultural_discovery')
        if cultural_engine and cultural_engine.is_available():
            try:
                if interests:
                    # Get recommendations based on user interests
                    recs = cultural_engine.get_korean_cultural_matches(interests)
                    recommendations.extend(recs)
                    
                    # Also search for query-specific recommendations
                    query_recs = cultural_engine.find_similar_korean_experiences(query, limit=5)
                    recommendations.extend(query_recs)
                else:
                    # Just search based on query
                    recs = cultural_engine.find_similar_korean_experiences(query)
                    recommendations.extend(recs)
                    
            except Exception as e:
                print(f"Cultural Discovery Engine recommendation failed: {e}")
        
        # Fallback to TasteDive service if Cultural Discovery Engine failed
        if not recommendations:
            tastedive = self.get_service('tastedive')
            if tastedive and tastedive.is_available():
                try:
                    if interests:
                        recs = tastedive.get_korean_cultural_matches(interests)
                    else:
                        recs = tastedive.find_similar_korean_experiences(query)
                    recommendations.extend(recs)
                except Exception as e:
                    print(f"TasteDive recommendation failed: {e}")
        
        # Final fallback to local cultural knowledge
        if not recommendations:
            recommendations = self._get_fallback_cultural_recommendations(query, interests)
        
        # Remove duplicates and limit results
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        return unique_recommendations[:10]  # Limit to top 10
    
    def get_culturally_related_experiences(self, visited_place: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get culturally related experiences based on a visited place.
        """
        cultural_engine = self.get_service('cultural_discovery')
        if cultural_engine and cultural_engine.is_available():
            try:
                return cultural_engine.find_culturally_related_locations(visited_place)
            except Exception as e:
                print(f"Cultural relationship discovery failed: {e}")
        
        # Fallback to basic recommendations
        place_name = visited_place.get('name', '')
        return self.get_cultural_recommendations(f"korean culture {place_name}")
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recommendations based on name."""
        seen_names = set()
        unique_recs = []
        
        for rec in recommendations:
            name = rec.get('Name', rec.get('name', ''))
            if name and name not in seen_names:
                seen_names.add(name)
                unique_recs.append(rec)
        
        return unique_recs
    
    def search_places(self, query: str, location: tuple = None, place_type: str = None) -> List[Dict[str, Any]]:
        """
        Search for places using available services with sub-200ms optimization.
        Falls back to Google Maps if Search service is unavailable.
        """
        places = []
        
        # Try Search service first for fast search
        search_service = self.get_service('search')
        if search_service and search_service.is_available():
            try:
                places = search_service.search_places(query, location, place_type)
            except Exception as e:
                print(f"Search service failed: {e}")
        
        # Fallback to Algolia service (backward compatibility)
        if not places:
            algolia = self.get_service('algolia')
            if algolia and algolia.is_available():
                try:
                    places = algolia.search_places(query, location, place_type)
                except Exception as e:
                    print(f"Algolia search failed: {e}")
        
        # Fallback to Google Maps if Search services failed
        if not places:
            googlemaps = self.get_service('googlemaps')
            if googlemaps and googlemaps.is_available():
                try:
                    places = googlemaps.search_places_by_text(query, location)
                except Exception as e:
                    print(f"Google Maps search failed: {e}")
        
        # Final fallback to local data
        if not places:
            places = self._get_fallback_places(query, place_type)
        
        return places
    
    def generate_response(self, question: str, recommendations: List[Any], cultural_context: str = None) -> str:
        """
        Generate natural language response using available services.
        """
        # Try ResponseGenerator first (new implementation)
        response_generator = self.get_service('response_generator')
        if response_generator and response_generator.is_available():
            try:
                return response_generator.generate_response(question, recommendations, cultural_context)
            except Exception as e:
                print(f"Response Generator failed: {e}")
        
        # Fallback to Gemini service (legacy compatibility)
        gemini = self.get_service('gemini')
        if gemini and gemini.is_available():
            try:
                return gemini.generate_local_guide_response(question, recommendations, cultural_context)
            except Exception as e:
                print(f"Gemini response generation failed: {e}")
        
        # Fallback to structured response
        return self._get_fallback_response(question, recommendations)
    
    def _get_fallback_cultural_recommendations(self, query: str, interests: List[str] = None) -> List[Dict[str, Any]]:
        """Provide fallback cultural recommendations when all services fail."""
        fallback_recs = [
            {
                'Name': 'Korean Traditional Music',
                'Type': 'music',
                'wTeaser': 'Experience traditional Korean instruments and melodies'
            },
            {
                'Name': 'Korean Temple Stay',
                'Type': 'experience',
                'wTeaser': 'Immerse yourself in Korean Buddhist culture'
            },
            {
                'Name': 'Korean Cooking Class',
                'Type': 'activity',
                'wTeaser': 'Learn to prepare authentic Korean dishes'
            }
        ]
        
        # Filter by interests if provided
        if interests:
            query_lower = ' '.join(interests).lower()
            if 'music' in query_lower or 'k-pop' in query_lower:
                return [r for r in fallback_recs if r['Type'] == 'music']
            elif 'food' in query_lower or 'cooking' in query_lower:
                return [r for r in fallback_recs if 'cooking' in r['Name'].lower()]
        
        return fallback_recs
    
    def _get_fallback_places(self, query: str, place_type: str = None) -> List[Dict[str, Any]]:
        """Provide fallback place recommendations when all services fail."""
        fallback_places = [
            {
                'name': 'Gyeongbokgung Palace',
                'category': 'attraction',
                'location': {'lat': 37.5796, 'lng': 126.9770},
                'cultural_context': 'Historic royal palace showcasing Korean architecture',
                'neighborhood': 'jongno'
            },
            {
                'name': 'Bukchon Hanok Village',
                'category': 'attraction',
                'location': {'lat': 37.5834, 'lng': 126.9834},
                'cultural_context': 'Traditional Korean houses and cultural heritage',
                'neighborhood': 'jongno'
            },
            {
                'name': 'Insadong Cultural Street',
                'category': 'attraction',
                'location': {'lat': 37.5759, 'lng': 126.9852},
                'cultural_context': 'Traditional arts, crafts, and tea culture',
                'neighborhood': 'jongno'
            }
        ]
        
        if place_type:
            fallback_places = [p for p in fallback_places if p['category'] == place_type]
        
        return fallback_places
    
    def _get_fallback_response(self, question: str, recommendations: List[Any]) -> str:
        """Provide structured fallback response when Gemini is unavailable."""
        if recommendations:
            rec_names = [str(rec.get('Name', rec)) for rec in recommendations[:3] if rec]
            rec_text = ', '.join(rec_names)
            
            return f"""
            <div class="fallback-response">
                <p>Based on your question about Korean culture, here are some recommendations:</p>
                <p><strong>{rec_text}</strong></p>
                <p>These suggestions reflect authentic Korean experiences. Each offers unique insights into Korean culture and traditions.</p>
                <p><em>For more detailed cultural insights, our AI assistant will be back online shortly.</em></p>
            </div>
            """
        else:
            return f"""
            <div class="fallback-response">
                <p>Thank you for your interest in Korean culture!</p>
                <p>While our recommendation system is temporarily unavailable, I'd suggest exploring:</p>
                <ul>
                    <li><strong>Hongdae</strong> - Youth culture and nightlife</li>
                    <li><strong>Myeongdong</strong> - Shopping and street food</li>
                    <li><strong>Itaewon</strong> - International district</li>
                    <li><strong>Gangnam</strong> - Modern Korean lifestyle</li>
                </ul>
                <p><em>Please try your question again in a moment for personalized recommendations.</em></p>
            </div>
            """


# Global service manager instance
service_manager = ServiceManager()