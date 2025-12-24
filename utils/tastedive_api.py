"""
Cultural Discovery Engine with TasteDive API integration.
Provides Korean cultural filtering, similarity matching, and fallback to local knowledge.
"""
import os
import requests
from typing import List, Dict, Optional, Any, Tuple
from .base_service import BaseService, retry_with_backoff
from dotenv import load_dotenv
load_dotenv()

class CulturalDiscoveryEngine(BaseService):
    """
    Cultural Discovery Engine for Korean cultural experiences and entertainment.
    
    Integrates with TasteDive API to find culturally similar experiences,
    implements Korean cultural filtering and similarity matching,
    and provides fallback to local Korean cultural knowledge.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv('TASTEDIVE_API_KEY')
        super().__init__("CulturalDiscoveryEngine", api_key)
        self.base_url = "https://tastedive.com/api/similar"
        
        # Korean cultural keywords for filtering and relevance scoring
        self.korean_cultural_keywords = [
            'korean', 'korea', 'k-pop', 'kpop', 'kdrama', 'seoul', 'busan',
            'korean food', 'korean culture', 'korean music', 'korean film',
            'hallyu', 'korean wave', 'korean traditional', 'korean modern',
            'korean entertainment', 'korean art', 'korean history'
        ]
        
        # Local Korean cultural knowledge database
        self.local_cultural_knowledge = self._initialize_local_knowledge()
    
    def _initialize_local_knowledge(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize local Korean cultural knowledge for fallback scenarios."""
        return {
            'movies': [
                {
                    'Name': 'Parasite',
                    'Type': 'movie',
                    'wTeaser': 'Oscar-winning Korean thriller exploring class dynamics',
                    'cultural_context': 'Reflects modern Korean social issues and architecture',
                    'cultural_relevance': 0.95
                },
                {
                    'Name': 'Oldboy',
                    'Type': 'movie', 
                    'wTeaser': 'Iconic Korean revenge thriller',
                    'cultural_context': 'Showcases Korean cinema\'s psychological depth',
                    'cultural_relevance': 0.90
                },
                {
                    'Name': 'Train to Busan',
                    'Type': 'movie',
                    'wTeaser': 'Korean zombie film with emotional depth',
                    'cultural_context': 'Demonstrates Korean storytelling and family values',
                    'cultural_relevance': 0.85
                },
                {
                    'Name': 'Burning',
                    'Type': 'movie',
                    'wTeaser': 'Psychological drama based on Haruki Murakami',
                    'cultural_context': 'Explores modern Korean youth and social tensions',
                    'cultural_relevance': 0.88
                }
            ],
            'music': [
                {
                    'Name': 'BTS',
                    'Type': 'music',
                    'wTeaser': 'Global K-pop phenomenon',
                    'cultural_context': 'Represents Korean Wave and modern Korean identity',
                    'cultural_relevance': 0.98
                },
                {
                    'Name': 'BLACKPINK',
                    'Type': 'music',
                    'wTeaser': 'International K-pop girl group',
                    'cultural_context': 'Modern Korean pop culture and fashion influence',
                    'cultural_relevance': 0.95
                },
                {
                    'Name': 'IU',
                    'Type': 'music',
                    'wTeaser': 'Beloved Korean singer-songwriter',
                    'cultural_context': 'Represents Korean indie and mainstream music fusion',
                    'cultural_relevance': 0.92
                },
                {
                    'Name': 'Pansori',
                    'Type': 'music',
                    'wTeaser': 'Traditional Korean musical storytelling',
                    'cultural_context': 'UNESCO-recognized Korean traditional performing art',
                    'cultural_relevance': 0.99
                }
            ],
            'shows': [
                {
                    'Name': 'Squid Game',
                    'Type': 'show',
                    'wTeaser': 'Global phenomenon Korean survival drama',
                    'cultural_context': 'Critiques Korean economic inequality and childhood games',
                    'cultural_relevance': 0.96
                },
                {
                    'Name': 'Kingdom',
                    'Type': 'show',
                    'wTeaser': 'Korean zombie historical drama',
                    'cultural_context': 'Blends Korean history with modern storytelling',
                    'cultural_relevance': 0.90
                },
                {
                    'Name': 'Crash Landing on You',
                    'Type': 'show',
                    'wTeaser': 'Korean romantic drama',
                    'cultural_context': 'Showcases Korean-North Korean cultural differences',
                    'cultural_relevance': 0.87
                },
                {
                    'Name': 'Reply 1988',
                    'Type': 'show',
                    'wTeaser': 'Nostalgic Korean family drama',
                    'cultural_context': 'Depicts 1980s Korean family life and neighborhood culture',
                    'cultural_relevance': 0.94
                }
            ],
            'books': [
                {
                    'Name': 'Please Look After Mom',
                    'Type': 'book',
                    'wTeaser': 'Korean literary fiction about family',
                    'cultural_context': 'Explores Korean family dynamics and filial piety',
                    'cultural_relevance': 0.93
                },
                {
                    'Name': 'The Vegetarian',
                    'Type': 'book',
                    'wTeaser': 'Korean psychological fiction',
                    'cultural_context': 'Examines Korean patriarchal society and women\'s autonomy',
                    'cultural_relevance': 0.91
                },
                {
                    'Name': 'Pachinko',
                    'Type': 'book',
                    'wTeaser': 'Multi-generational Korean family saga',
                    'cultural_context': 'Korean diaspora experience and identity',
                    'cultural_relevance': 0.89
                }
            ],
            'experiences': [
                {
                    'Name': 'Korean Temple Stay',
                    'Type': 'experience',
                    'wTeaser': 'Immersive Buddhist cultural experience',
                    'cultural_context': 'Traditional Korean Buddhist practices and meditation',
                    'cultural_relevance': 0.97
                },
                {
                    'Name': 'Korean Cooking Class',
                    'Type': 'experience',
                    'wTeaser': 'Learn authentic Korean cuisine',
                    'cultural_context': 'Korean food culture and communal dining traditions',
                    'cultural_relevance': 0.95
                },
                {
                    'Name': 'Hanbok Experience',
                    'Type': 'experience',
                    'wTeaser': 'Traditional Korean clothing experience',
                    'cultural_context': 'Korean traditional fashion and cultural ceremonies',
                    'cultural_relevance': 0.93
                },
                {
                    'Name': 'Korean Tea Ceremony',
                    'Type': 'experience',
                    'wTeaser': 'Traditional Korean tea culture',
                    'cultural_context': 'Korean mindfulness and hospitality traditions',
                    'cultural_relevance': 0.90
                }
            ]
        }
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to TasteDive API with retry logic."""
        if not self.api_key:
            raise ValueError("TasteDive API key not configured")
        
        params['k'] = self.api_key
        params['f'] = 'json'  # Force JSON response
        
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle both "Similar" and "similar" response formats
        if 'Similar' in data:
            return data
        elif 'similar' in data:
            # Convert lowercase to uppercase for consistency
            return {'Similar': data['similar']}
        else:
            raise ValueError("Invalid TasteDive API response format")
        
        return data
    
    def find_similar_korean_experiences(self, query: str, content_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find culturally similar Korean experiences using TasteDive API with enhanced entity extraction.
        
        Args:
            query: Search query (cultural activity, entertainment, etc.)
            content_type: Type of content (movies, music, shows, books, authors, games, all)
            limit: Maximum number of results
        
        Returns:
            List of similar Korean cultural experiences with relevance scores
        """
        # Use Gemini for better entity extraction and query structuring
        structured_query = self._extract_entities_and_structure_query(query, content_type)
        
        # Handle "all" content type by trying multiple specific types
        if content_type == "all":
            all_results = []
            # TasteDive requires specific types, so we'll try multiple types for "all"
            types_to_try = ['movie', 'music', 'show', 'book']
            results_per_type = max(1, limit // len(types_to_try))
            
            for api_type in types_to_try:
                try:
                    # Use structured query for each type
                    type_query = structured_query.get(api_type, structured_query.get('general', query))
                    type_results = self._get_results_for_type(type_query, api_type, results_per_type)
                    all_results.extend(type_results)
                except Exception as e:
                    self.logger.warning(f"Failed to get results for type {api_type}: {e}")
                    continue
            
            # Sort all results by cultural relevance and limit
            all_results.sort(key=lambda x: x.get('cultural_relevance', 0), reverse=True)
            return all_results[:limit]
        else:
            # Handle specific content type with structured query
            specific_query = structured_query.get(content_type, structured_query.get('general', query))
            return self._get_results_for_type(specific_query, content_type, limit)
    
    def _get_results_for_type(self, query: str, content_type: str, limit: int) -> List[Dict[str, Any]]:
        """Get results for a specific content type from TasteDive API with enhanced query formatting."""
        # Map our content types to TasteDive API types
        type_mapping = {
            'movies': 'movie',
            'music': 'music', 
            'shows': 'show',
            'books': 'book',
            'authors': 'author',
            'games': 'game'
        }
        
        # Use mapped type or original if it's already correct
        api_type = type_mapping.get(content_type, content_type)
        
        # Validate that the type is supported by TasteDive
        valid_types = ['music', 'movie', 'show', 'podcast', 'book', 'game', 'person', 'place', 'brand']
        if api_type not in valid_types:
            self.logger.warning(f"Invalid TasteDive type '{api_type}', using 'movie' as fallback")
            api_type = 'movie'
        
        # Format query for TasteDive API - handle multiple entities
        formatted_query = self._format_query_for_tastedive(query, api_type)
        
        params = {
            'q': formatted_query,
            'type': api_type,  # Use specific type required by TasteDive
            'limit': limit * 2,  # Get more results for better filtering
            'info': 1  # Include additional info
        }
        
        try:
            data = self._make_request(self._api_request, params)
            if not data:
                return self._get_fallback_korean_experiences(query, content_type, limit)
            
            # Handle both "Results" and "results" response formats
            similar_data = data.get('Similar', {})
            similar_items = similar_data.get('Results', similar_data.get('results', []))
            
            # Check if query was Korean-related to adjust scoring
            query_is_korean = any(keyword in query.lower() for keyword in self.korean_cultural_keywords)
            
            # Filter and score for Korean cultural relevance
            korean_relevant = self._filter_and_score_korean_relevance(similar_items, query_is_korean)
            
            # Sort by cultural relevance score and limit results
            korean_relevant.sort(key=lambda x: x.get('cultural_relevance', 0), reverse=True)
            return korean_relevant[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding similar Korean experiences for '{query}' (type: {api_type}): {e}")
            return self._get_fallback_korean_experiences(query, content_type, limit)
    
    def _format_query_for_tastedive(self, query: str, api_type: str) -> str:
        """
        Format query for TasteDive API using proper operators and encoding.
        
        Examples:
        - "movie:parasite, korean cinema" -> "movie:parasite,korean cinema"
        - "music:bts, music:blackpink" -> "music:bts,music:blackpink"
        """
        # Clean up the query - remove extra spaces around commas
        formatted_query = query.replace(', ', ',').replace(' ,', ',')
        
        # If no operators are present, add Korean context
        if ':' not in formatted_query:
            # Add Korean context based on type
            korean_context_map = {
                'movie': 'korean film',
                'music': 'korean music', 
                'show': 'korean drama',
                'book': 'korean literature',
                'game': 'korean game'
            }
            
            korean_context = korean_context_map.get(api_type, 'korean culture')
            
            # If query doesn't already have Korean context, add it
            if not any(keyword in formatted_query.lower() for keyword in self.korean_cultural_keywords):
                formatted_query = f"{formatted_query},{korean_context}"
        
        return formatted_query
    
    def get_korean_cultural_matches(self, interests: List[str]) -> List[Dict[str, Any]]:
        """
        Get Korean cultural matches based on user interests with enhanced entity extraction.
        
        Args:
            interests: List of user interests
        
        Returns:
            List of Korean cultural recommendations with authenticity scores
        """
        all_matches = []
        processed_interests = set()
        
        for interest in interests:
            if interest.lower() in processed_interests:
                continue
            processed_interests.add(interest.lower())
            
            # Use enhanced entity extraction for better TasteDive queries
            structured_queries = self._extract_entities_and_structure_query(interest, "all")
            
            # Try different content types for comprehensive coverage
            for content_type in ['movie', 'music', 'show', 'book']:
                try:
                    # Use structured query if available, otherwise fall back to interest
                    query_to_use = structured_queries.get(content_type, structured_queries.get('general', interest))
                    
                    matches = self._get_results_for_type(
                        query_to_use, 
                        content_type, 
                        limit=3  # Fewer per type for diversity
                    )
                    # Ensure matches are dictionaries before extending
                    if matches and isinstance(matches, list):
                        valid_matches = [m for m in matches if isinstance(m, dict)]
                        all_matches.extend(valid_matches)
                except Exception as e:
                    self.logger.warning(f"Failed to get matches for {interest} ({content_type}): {e}")
                    continue
        
        # Remove duplicates based on name and add cultural relationship mapping
        unique_matches = self._deduplicate_and_map_relationships(all_matches)
        
        # Sort by cultural authenticity and relevance
        unique_matches.sort(key=lambda x: (
            x.get('cultural_relevance', 0) * 0.6 + 
            x.get('authenticity_score', 0) * 0.4
        ), reverse=True)
        
        return unique_matches[:15]  # Return top 15 most culturally relevant
    
    def search_korean_entertainment(self, query: str, media_type: str = "all") -> List[Dict[str, Any]]:
        """
        Search for Korean entertainment content across all media types.
        
        Args:
            query: Search query
            media_type: Type of media (movies, music, shows, books, all)
        
        Returns:
            List of Korean entertainment recommendations with cultural context
        """
        # Ensure Korean context in query
        korean_query = self._enhance_query_with_korean_context(query)
        
        try:
            results = self.find_similar_korean_experiences(korean_query, content_type=media_type)
            
            # Add cultural context to each result
            for result in results:
                result['cultural_context'] = self._generate_cultural_context(result)
                result['media_category'] = self._categorize_media_type(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching Korean entertainment for '{query}': {e}")
            return self._get_fallback_korean_experiences(query, media_type)
    
    def find_culturally_related_locations(self, visited_place: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find culturally related locations and activities based on a visited place.
        
        Args:
            visited_place: Dictionary containing place information
        
        Returns:
            List of culturally related recommendations
        """
        place_name = visited_place.get('name', '')
        place_type = visited_place.get('category', 'attraction')
        cultural_tags = visited_place.get('cultural_tags', [])
        
        # Generate cultural similarity query
        cultural_query = self._generate_cultural_similarity_query(place_name, place_type, cultural_tags)
        
        try:
            # Search for related cultural experiences
            related_experiences = self.find_similar_korean_experiences(cultural_query, limit=8)
            
            # Add location relationship context
            for experience in related_experiences:
                experience['relationship_type'] = self._determine_cultural_relationship(
                    visited_place, experience
                )
                experience['cultural_connection'] = self._explain_cultural_connection(
                    visited_place, experience
                )
            
            return related_experiences
            
        except Exception as e:
            self.logger.error(f"Error finding related locations for '{place_name}': {e}")
            return self._get_fallback_related_experiences(visited_place)
    
    def _extract_entities_and_structure_query(self, query: str, content_type: str = "all") -> Dict[str, str]:
        """
        Use Gemini to extract entities and structure TasteDive queries for better results.
        
        Args:
            query: User's original query
            content_type: Target content type
        
        Returns:
            Dictionary with structured queries for different content types
        """
        try:
            # Import Gemini service for entity extraction
            from .gemini_api import GeminiService
            gemini_service = GeminiService()
            
            if not gemini_service.is_available():
                # Fallback to basic query enhancement
                return {'general': self._enhance_query_with_korean_context(query)}
            
            # Create a prompt for entity extraction and query structuring
            extraction_prompt = f"""
            Analyze this user query and extract specific entities for TasteDive API searches: "{query}"
            
            Extract and format entities for these categories:
            - Movies: Korean films, directors, actors mentioned
            - Music: Korean artists, bands, songs, genres mentioned  
            - Shows: Korean dramas, TV shows, variety shows mentioned
            - Books: Korean authors, books, literature mentioned
            
            Format your response as:
            Movie Query: [specific movie titles, directors, or actors - use "movie:" prefix for titles]
            Music Query: [specific artists, bands, or songs - use "music:" prefix for artists]
            Show Query: [specific show titles or types - use "show:" prefix for titles]  
            Book Query: [specific books or authors - use "book:" prefix for titles]
            General Query: [fallback query with Korean context]
            
            Rules:
            - Use TasteDive operators like "movie:title", "music:artist", "show:title", "book:title"
            - Include Korean context if not already present
            - Separate multiple entities with commas
            - If no specific entities found, enhance with Korean cultural context
            
            Example:
            User: "I love Parasite and want similar Korean content"
            Movie Query: movie:parasite, korean cinema
            Music Query: korean soundtrack, korean film music
            Show Query: korean drama, korean thriller
            Book Query: korean literature, korean social commentary
            General Query: korean parasite similar content
            """
            
            # Get structured response from Gemini
            response = gemini_service._generate_content(extraction_prompt)
            
            # Parse the structured response
            structured_queries = self._parse_entity_extraction_response(response)
            
            # Ensure we have at least a general query
            if not structured_queries:
                structured_queries = {'general': self._enhance_query_with_korean_context(query)}
            
            return structured_queries
            
        except Exception as e:
            self.logger.warning(f"Entity extraction failed: {e}")
            # Fallback to basic query enhancement
            return {'general': self._enhance_query_with_korean_context(query)}
    
    def _parse_entity_extraction_response(self, response: str) -> Dict[str, str]:
        """Parse Gemini's entity extraction response into structured queries."""
        structured_queries = {}
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                if line.startswith('Movie Query:'):
                    query = line.replace('Movie Query:', '').strip()
                    if query and query != '[none]':
                        structured_queries['movie'] = query
                elif line.startswith('Music Query:'):
                    query = line.replace('Music Query:', '').strip()
                    if query and query != '[none]':
                        structured_queries['music'] = query
                elif line.startswith('Show Query:'):
                    query = line.replace('Show Query:', '').strip()
                    if query and query != '[none]':
                        structured_queries['show'] = query
                elif line.startswith('Book Query:'):
                    query = line.replace('Book Query:', '').strip()
                    if query and query != '[none]':
                        structured_queries['book'] = query
                elif line.startswith('General Query:'):
                    query = line.replace('General Query:', '').strip()
                    if query:
                        structured_queries['general'] = query
        
        return structured_queries
    
    def _enhance_query_with_korean_context(self, query: str) -> str:
        """Enhance query with Korean cultural context if not already present."""
        query_lower = query.lower()
        
        # Check if query already has Korean context
        has_korean_context = any(keyword in query_lower for keyword in self.korean_cultural_keywords)
        
        if not has_korean_context:
            # Add Korean context based on query type
            if any(word in query_lower for word in ['music', 'song', 'artist', 'band']):
                return f"{query} korean music"
            elif any(word in query_lower for word in ['movie', 'film', 'cinema']):
                return f"{query} korean film"
            elif any(word in query_lower for word in ['show', 'drama', 'series', 'tv']):
                return f"{query} korean drama"
            elif any(word in query_lower for word in ['book', 'novel', 'literature']):
                return f"{query} korean literature"
            elif any(word in query_lower for word in ['food', 'cuisine', 'restaurant', 'cooking']):
                return f"{query} korean food"
            else:
                return f"{query} korean culture"
        
        return query
    
    def _filter_and_score_korean_relevance(self, items: List[Dict[str, Any]], query_is_korean: bool = False) -> List[Dict[str, Any]]:
        """Filter results for Korean cultural relevance and add scoring."""
        if not items:
            return []
            
        korean_relevant = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            # Handle both "Name" and "name" field formats, with safe string conversion
            name_raw = item.get('Name', item.get('name', ''))
            name = str(name_raw).lower() if name_raw else ''
            
            # Handle both "wTeaser" and "description" field formats, with safe string conversion
            desc_raw = item.get('wTeaser', item.get('description', ''))
            description = str(desc_raw).lower() if desc_raw else ''
            
            # Handle both "Type" and "type" field formats, with safe string conversion
            type_raw = item.get('Type', item.get('type', ''))
            item_type = str(type_raw).lower() if type_raw else ''
            
            # Calculate cultural relevance score
            relevance_score = self._calculate_cultural_relevance_score(name, description, item_type)
            
            # If the original query was Korean-related, be more inclusive
            if query_is_korean and relevance_score < 0.2:
                relevance_score = 0.2  # Boost score for Korean query results
            
            # Lower threshold to be more inclusive (was 0.3, now 0.1)
            if relevance_score > 0.1:  # More inclusive relevance threshold
                item['cultural_relevance'] = relevance_score
                item['authenticity_score'] = self._calculate_authenticity_score(name, description)
                
                # Normalize field names for consistency
                if 'name' in item and 'Name' not in item:
                    item['Name'] = item['name']
                if 'description' in item and 'wTeaser' not in item:
                    item['wTeaser'] = item['description']
                if 'type' in item and 'Type' not in item:
                    item['Type'] = item['type']
                    
                korean_relevant.append(item)
        
        return korean_relevant
    
    def _calculate_cultural_relevance_score(self, name: str, description: str, item_type: str) -> float:
        """Calculate cultural relevance score for Korean content."""
        score = 0.0
        text_content = f"{name} {description}".lower()
        
        # Direct Korean keywords (high weight)
        for keyword in self.korean_cultural_keywords:
            if keyword in text_content:
                if keyword in ['korean', 'korea']:
                    score += 0.4
                elif keyword in ['k-pop', 'kpop', 'kdrama']:
                    score += 0.3
                elif keyword in ['seoul', 'busan']:
                    score += 0.2
                else:
                    score += 0.1
        
        # Cultural context indicators
        cultural_indicators = [
            'traditional', 'modern', 'contemporary', 'authentic', 'cultural',
            'heritage', 'history', 'art', 'music', 'film', 'literature'
        ]
        
        for indicator in cultural_indicators:
            if indicator in text_content:
                score += 0.05
        
        # Bonus for specific Korean cultural elements
        korean_elements = [
            'hanbok', 'kimchi', 'bulgogi', 'bibimbap', 'taekwondo', 'hallyu',
            'chaebol', 'soju', 'makgeolli', 'temple', 'palace', 'hanok'
        ]
        
        for element in korean_elements:
            if element in text_content:
                score += 0.15
        
        # Asian context indicators (lower weight but still relevant)
        asian_indicators = [
            'asian', 'asia', 'east asian', 'oriental', 'confucian', 'buddhist'
        ]
        
        for indicator in asian_indicators:
            if indicator in text_content:
                score += 0.1
        
        # If no specific Korean indicators but has general relevance, give base score
        if score == 0.0 and any(word in text_content for word in ['culture', 'traditional', 'modern', 'art', 'music', 'film']):
            score = 0.15  # Base cultural relevance score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_authenticity_score(self, name: str, description: str) -> float:
        """Calculate authenticity score based on cultural depth indicators."""
        score = 0.5  # Base score
        text_content = f"{name} {description}".lower()
        
        # Authentic cultural elements
        authentic_elements = [
            'traditional', 'heritage', 'historical', 'authentic', 'original',
            'classical', 'folk', 'indigenous', 'ancestral', 'ceremonial'
        ]
        
        for element in authentic_elements:
            if element in text_content:
                score += 0.1
        
        # Modern Korean culture elements
        modern_elements = [
            'contemporary', 'modern', 'current', 'trendy', 'popular', 'mainstream'
        ]
        
        for element in modern_elements:
            if element in text_content:
                score += 0.05
        
        return min(score, 1.0)
    
    def _deduplicate_and_map_relationships(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and map cultural relationships between items."""
        seen_names = set()
        unique_matches = []
        
        for match in matches:
            # Ensure match is a dictionary
            if not isinstance(match, dict):
                continue
                
            name = match.get('Name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                
                # Add cultural relationship mapping
                match['cultural_themes'] = self._extract_cultural_themes(match)
                match['related_genres'] = self._identify_related_genres(match)
                
                unique_matches.append(match)
        
        return unique_matches
    
    def _extract_cultural_themes(self, item: Dict[str, Any]) -> List[str]:
        """Extract cultural themes from item description."""
        name_raw = item.get('Name', '')
        name = str(name_raw).lower() if name_raw else ''
        
        desc_raw = item.get('wTeaser', '')
        description = str(desc_raw).lower() if desc_raw else ''
        
        text = f"{name} {description}"
        
        themes = []
        
        # Theme mapping
        theme_keywords = {
            'family': ['family', 'mother', 'father', 'parent', 'child', 'generation'],
            'love': ['love', 'romance', 'romantic', 'relationship', 'couple'],
            'tradition': ['traditional', 'heritage', 'historical', 'ancient', 'classical'],
            'modern_life': ['modern', 'contemporary', 'urban', 'city', 'technology'],
            'social_issues': ['society', 'social', 'class', 'inequality', 'politics'],
            'coming_of_age': ['youth', 'young', 'growing', 'adolescent', 'teenager'],
            'food_culture': ['food', 'cooking', 'cuisine', 'restaurant', 'dining'],
            'music_dance': ['music', 'song', 'dance', 'performance', 'concert'],
            'spirituality': ['temple', 'buddhist', 'spiritual', 'meditation', 'zen']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _identify_related_genres(self, item: Dict[str, Any]) -> List[str]:
        """Identify related genres for cross-media recommendations."""
        type_raw = item.get('Type', '')
        item_type = str(type_raw).lower() if type_raw else ''
        
        themes = item.get('cultural_themes', [])
        
        genre_mapping = {
            'family': ['drama', 'slice_of_life', 'family_film'],
            'love': ['romance', 'romantic_comedy', 'melodrama'],
            'tradition': ['historical', 'period_piece', 'documentary'],
            'modern_life': ['contemporary', 'urban', 'lifestyle'],
            'social_issues': ['thriller', 'drama', 'documentary'],
            'coming_of_age': ['youth', 'school', 'bildungsroman'],
            'food_culture': ['cooking_show', 'food_documentary', 'lifestyle'],
            'music_dance': ['musical', 'performance', 'variety_show'],
            'spirituality': ['philosophical', 'meditative', 'spiritual']
        }
        
        genres = []
        for theme in themes:
            if theme in genre_mapping:
                genres.extend(genre_mapping[theme])
        
        return list(set(genres))  # Remove duplicates
    
    def _generate_cultural_similarity_query(self, place_name: str, place_type: str, cultural_tags: List[str]) -> str:
        """Generate query for finding culturally similar experiences."""
        base_query = place_name
        
        # Add cultural context from tags
        if cultural_tags:
            cultural_context = ' '.join(cultural_tags)
            base_query = f"{base_query} {cultural_context}"
        
        # Add type-specific context
        type_context = {
            'restaurant': 'korean food culture dining',
            'temple': 'korean buddhist spiritual heritage',
            'palace': 'korean royal history traditional',
            'market': 'korean street food local culture',
            'museum': 'korean art history culture',
            'park': 'korean nature relaxation',
            'shopping': 'korean fashion lifestyle modern'
        }
        
        if place_type in type_context:
            base_query = f"{base_query} {type_context[place_type]}"
        
        return base_query
    
    def _determine_cultural_relationship(self, visited_place: Dict[str, Any], experience: Dict[str, Any]) -> str:
        """Determine the type of cultural relationship between place and experience."""
        place_tags = set(visited_place.get('cultural_tags', []))
        exp_themes = set(experience.get('cultural_themes', []))
        
        # Check for direct theme overlap
        if place_tags.intersection(exp_themes):
            return 'thematic_similarity'
        
        # Check for complementary experiences
        place_type = visited_place.get('category', '')
        exp_type = experience.get('Type', '')
        
        complementary_pairs = {
            'restaurant': ['music', 'show'],  # Food + entertainment
            'temple': ['book', 'music'],      # Spiritual + contemplative
            'palace': ['movie', 'show'],      # Historical + drama
            'market': ['music', 'show']       # Local culture + entertainment
        }
        
        if place_type in complementary_pairs and exp_type in complementary_pairs[place_type]:
            return 'complementary_experience'
        
        return 'cultural_context'
    
    def _explain_cultural_connection(self, visited_place: Dict[str, Any], experience: Dict[str, Any]) -> str:
        """Explain the cultural connection between place and experience."""
        relationship = experience.get('relationship_type', 'cultural_context')
        place_name = visited_place.get('name', 'this place')
        exp_name = experience.get('Name', 'this experience')
        
        explanations = {
            'thematic_similarity': f"Shares similar cultural themes with {place_name}",
            'complementary_experience': f"Complements your visit to {place_name} with related cultural content",
            'cultural_context': f"Provides broader Korean cultural context related to {place_name}"
        }
        
        return explanations.get(relationship, f"Connected to Korean cultural experience at {place_name}")
    
    def _get_fallback_korean_experiences(self, query: str, content_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Provide fallback Korean cultural experiences when API is unavailable."""
        self.logger.info(f"Providing fallback Korean experiences for '{query}' ({content_type})")
        
        # Select appropriate fallback data
        if content_type in self.local_cultural_knowledge:
            fallback_items = self.local_cultural_knowledge[content_type][:limit]
        elif content_type == 'all':
            fallback_items = []
            for category_items in self.local_cultural_knowledge.values():
                fallback_items.extend(category_items[:2])  # 2 from each category
            fallback_items = fallback_items[:limit]
        else:
            # Default fallback for unknown content types
            fallback_items = self.local_cultural_knowledge['experiences'][:limit]
        
        # Add fallback indicator
        for item in fallback_items:
            item['source'] = 'local_knowledge'
            item['fallback_reason'] = 'API unavailable'
        
        return fallback_items
    
    def _get_fallback_related_experiences(self, visited_place: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Provide fallback related experiences when API fails."""
        place_type = visited_place.get('category', 'attraction')
        
        # Map place types to relevant cultural experiences
        type_mapping = {
            'restaurant': self.local_cultural_knowledge['experiences'][:2] + self.local_cultural_knowledge['shows'][:1],
            'temple': self.local_cultural_knowledge['books'][:2] + self.local_cultural_knowledge['music'][:1],
            'palace': self.local_cultural_knowledge['movies'][:2] + self.local_cultural_knowledge['shows'][:1],
            'market': self.local_cultural_knowledge['music'][:2] + self.local_cultural_knowledge['experiences'][:1]
        }
        
        fallback_items = type_mapping.get(place_type, self.local_cultural_knowledge['experiences'][:3])
        
        # Add relationship context
        for item in fallback_items:
            item['source'] = 'local_knowledge'
            item['relationship_type'] = 'cultural_context'
            item['cultural_connection'] = f"Related Korean cultural experience"
        
        return fallback_items
    
    def _generate_cultural_context(self, item: Dict[str, Any]) -> str:
        """Generate cultural context description for an item."""
        name = item.get('Name', '')
        item_type = item.get('Type', '')
        themes = item.get('cultural_themes', [])
        
        if not themes:
            return f"Korean {item_type} representing contemporary Korean culture"
        
        theme_descriptions = {
            'family': 'Korean family values and relationships',
            'love': 'Korean romantic culture and relationships',
            'tradition': 'Korean traditional heritage and customs',
            'modern_life': 'Contemporary Korean lifestyle and society',
            'social_issues': 'Korean social dynamics and contemporary issues',
            'coming_of_age': 'Korean youth culture and personal growth',
            'food_culture': 'Korean culinary traditions and dining culture',
            'music_dance': 'Korean performing arts and entertainment culture',
            'spirituality': 'Korean spiritual traditions and philosophy'
        }
        
        primary_theme = themes[0] if themes else 'culture'
        return theme_descriptions.get(primary_theme, f"Korean {item_type} culture")
    
    def _categorize_media_type(self, item: Dict[str, Any]) -> str:
        """Categorize media type for better organization."""
        type_raw = item.get('Type', '')
        item_type = str(type_raw).lower() if type_raw else ''
        
        category_mapping = {
            'movie': 'Korean Cinema',
            'music': 'Korean Music',
            'show': 'Korean Drama/TV',
            'book': 'Korean Literature',
            'author': 'Korean Literature',
            'game': 'Korean Gaming',
            'experience': 'Korean Cultural Experience'
        }
        
        return category_mapping.get(item_type, 'Korean Culture')
    
    def _handle_fallback(self, error: Exception) -> List[Dict[str, Any]]:
        """Handle fallback when TasteDive API is unavailable."""
        self.logger.warning(f"TasteDive API unavailable, using local Korean cultural knowledge: {error}")
        # Return None to indicate fallback should be handled by the calling method
        return None


# Backward compatibility class for existing integrations
class TasteDiveService(CulturalDiscoveryEngine):
    """Backward compatibility wrapper for existing TasteDive integrations."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        # Update service name for backward compatibility
        self.service_name = "TasteDive"
    
    def find_similar_experiences(self, query: str, content_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Backward compatibility method."""
        return self.find_similar_korean_experiences(query, content_type, limit)


# Legacy compatibility functions for existing app.py
def search_entity(entity_name: str, entity_type: str = "all") -> Optional[str]:
    """
    Legacy compatibility function for existing app.py.
    Returns entity ID (simplified for TasteDive which doesn't use IDs).
    """
    service = TasteDiveService()
    results = service.find_similar_experiences(entity_name, content_type="all", limit=1)
    return entity_name if results else None


def get_recommendations(entity_id: str, entity_type: str = "all") -> List[str]:
    """
    Legacy compatibility function for existing app.py.
    Returns list of recommendation names.
    """
    service = TasteDiveService()
    results = service.find_similar_experiences(entity_id, content_type=entity_type)
    return [item.get('Name', '') for item in results if item.get('Name')]