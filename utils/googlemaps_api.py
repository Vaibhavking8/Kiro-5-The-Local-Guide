"""
Google Maps API integration for interactive maps and place details.
Provides geographic context and place information for Korean attractions.
"""
import os
import requests
from typing import List, Dict, Optional, Any, Tuple
from .base_service import BaseService, retry_with_backoff
from dotenv import load_dotenv
load_dotenv()


class GoogleMapsService(BaseService):
    """Google Maps API service for place details and geographic information."""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        super().__init__("GoogleMaps", api_key)
        self.base_url = "https://maps.googleapis.com/maps/api"
        
        # Seoul city bounds for validation and accurate positioning
        self.seoul_bounds = {
            'north': 37.7013,
            'south': 37.4269,
            'east': 127.1831,
            'west': 126.7342
        }
        
        # Clustering and zoom level configurations
        self.zoom_levels = {
            'city': 11,      # Seoul city overview
            'district': 13,  # District level (Gangnam, Hongdae)
            'neighborhood': 15,  # Neighborhood level
            'street': 17,    # Street level detail
            'building': 19   # Building level detail
        }
        
        # Clustering thresholds for multiple locations
        self.clustering_config = {
            'min_zoom_for_individual': 15,  # Show individual markers at zoom 15+
            'cluster_radius': 50,           # Pixels for clustering
            'max_cluster_size': 10          # Max items per cluster
        }
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Google Maps API with retry logic."""
        if not self.api_key:
            raise ValueError("Google Maps API key not configured")
        
        params['key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') != 'OK' and data.get('status') != 'ZERO_RESULTS':
            raise ValueError(f"Google Maps API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
        
        return data
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Places ID
        
        Returns:
            Detailed place information with cultural context
        """
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,rating,price_level,opening_hours,photos,reviews,types,website,formatted_phone_number'
        }
        
        try:
            data = self._make_request(self._api_request, "place/details/json", params)
            if not data or data.get('status') == 'ZERO_RESULTS':
                return None
            
            result = data.get('result', {})
            return self._enrich_place_details(result)
            
        except Exception as e:
            self.logger.error(f"Error getting place details for {place_id}: {e}")
            return self._get_fallback_place_details(place_id)
    
    def find_nearby_places(self, location: Tuple[float, float], place_type: str = "tourist_attraction", 
                          radius: int = 1500) -> List[Dict[str, Any]]:
        """
        Find places near a location with Korean cultural relevance.
        
        Args:
            location: (latitude, longitude) tuple
            place_type: Type of place to search for
            radius: Search radius in meters
        
        Returns:
            List of nearby places with cultural context
        """
        lat, lng = location
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': place_type,
            'language': 'en'
        }
        
        try:
            data = self._make_request(self._api_request, "place/nearbysearch/json", params)
            if not data:
                return []
            
            results = data.get('results', [])
            return self._filter_korean_relevant_places(results)
            
        except Exception as e:
            self.logger.error(f"Error finding nearby places at {location}: {e}")
            return self._get_fallback_nearby_places(location, place_type)
    
    def get_accurate_korean_attractions(self, query: str = "korean attractions", 
                                      location: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Get Korean attractions with enhanced positioning accuracy.
        
        Args:
            query: Search query for attractions
            location: Optional location bias (latitude, longitude)
        
        Returns:
            List of Korean attractions with accurate positioning
        """
        # Use Seoul center as default with wider search radius
        search_location = location or (37.5665, 126.9780)
        
        params = {
            'query': f"{query} Seoul Korea",
            'location': f"{search_location[0]},{search_location[1]}",
            'radius': 15000,  # 15km radius for Seoul area
            'language': 'en',
            'type': 'tourist_attraction'
        }
        
        try:
            data = self._make_request(self._api_request, "place/textsearch/json", params)
            if not data:
                return self._get_fallback_korean_attractions()
            
            results = data.get('results', [])
            
            # Enhanced filtering and positioning accuracy
            accurate_attractions = []
            for place in results:
                if self._validate_korean_attraction(place):
                    enhanced_place = self._enhance_attraction_positioning(place)
                    if enhanced_place:
                        accurate_attractions.append(enhanced_place)
            
            return accurate_attractions[:20]  # Return top 20 accurate results
            
        except Exception as e:
            self.logger.error(f"Error getting Korean attractions: {e}")
            return self._get_fallback_korean_attractions()
    
    def discover_nearby_amenities(self, location: Tuple[float, float], 
                                 amenity_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover nearby amenities (restaurants, hotels, transport) with cultural context.
        
        Args:
            location: (latitude, longitude) tuple
            amenity_types: List of amenity types to search for
        
        Returns:
            Dictionary of amenities by type with cultural context
        """
        if not amenity_types:
            amenity_types = ['restaurant', 'lodging', 'subway_station', 'bus_station']
        
        amenities = {}
        
        for amenity_type in amenity_types:
            try:
                places = self._search_amenity_type(location, amenity_type)
                amenities[amenity_type] = places if places else []
            except Exception as e:
                self.logger.error(f"Error finding {amenity_type} near {location}: {e}")
                amenities[amenity_type] = self._get_fallback_amenities(location, amenity_type)
        
        return amenities
    
    def get_optimized_map_view(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate optimal zoom level and clustering for multiple locations.
        
        Args:
            locations: List of location dictionaries with lat/lng
        
        Returns:
            Map view configuration with clustering and zoom settings
        """
        if not locations:
            return self._get_default_seoul_view()
        
        if len(locations) == 1:
            return self._get_single_location_view(locations[0])
        
        # Calculate bounds for multiple locations
        bounds = self._calculate_bounds(locations)
        
        # Determine appropriate zoom level
        zoom_level = self._calculate_optimal_zoom(bounds)
        
        # Apply clustering if needed
        clustering_config = self._get_clustering_config(locations, zoom_level)
        
        return {
            'center': self._calculate_center(bounds),
            'zoom': zoom_level,
            'bounds': bounds,
            'clustering': clustering_config,
            'total_locations': len(locations)
        }
        """
        Search for places using text query with optional location bias.
        
        Args:
            query: Text search query
            location: Optional location bias (latitude, longitude)
        
        Returns:
            List of matching places
        """
        params = {
            'query': query,
            'language': 'en'
        }
        
        # Add location bias for Seoul area
        if location:
            lat, lng = location
            params['location'] = f"{lat},{lng}"
            params['radius'] = 10000  # 10km radius
        else:
            # Default to Seoul city center
            params['location'] = "37.5665,126.9780"
            params['radius'] = 25000  # 25km radius for Seoul area
        
        try:
            data = self._make_request(self._api_request, "place/textsearch/json", params)
            if not data:
                return []
            
            results = data.get('results', [])
            return self._filter_korean_relevant_places(results)
            
        except Exception as e:
            self.logger.error(f"Error searching places for '{query}': {e}")
            return self._get_fallback_search_places(query)
    
    def get_place_photos(self, photo_reference: str, max_width: int = 400) -> Optional[str]:
        """
        Get photo URL for a place photo reference.
        
        Args:
            photo_reference: Photo reference from place details
            max_width: Maximum width of the photo
        
        Returns:
            Photo URL or None if unavailable
        """
        if not photo_reference:
            return None
        
        params = {
            'photoreference': photo_reference,
            'maxwidth': max_width
        }
        
        try:
            # For photos, we return the URL directly
            url = f"{self.base_url}/place/photo"
            params['key'] = self.api_key
            return f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
        except Exception as e:
            self.logger.error(f"Error getting photo URL: {e}")
            return None
    
    def _enrich_place_details(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich place details with Korean cultural context."""
        enriched = {
            'place_id': place_data.get('place_id'),
            'name': place_data.get('name', 'Unknown Place'),
            'address': place_data.get('formatted_address', ''),
            'location': {
                'lat': place_data.get('geometry', {}).get('location', {}).get('lat'),
                'lng': place_data.get('geometry', {}).get('location', {}).get('lng')
            },
            'rating': place_data.get('rating', 0),
            'price_level': place_data.get('price_level', 1),
            'types': place_data.get('types', []),
            'opening_hours': place_data.get('opening_hours', {}),
            'website': place_data.get('website'),
            'phone': place_data.get('formatted_phone_number'),
            'photos': []
        }
        
        # Add photo URLs
        photos = place_data.get('photos', [])
        for photo in photos[:3]:  # Limit to 3 photos
            photo_ref = photo.get('photo_reference')
            if photo_ref:
                photo_url = self.get_place_photos(photo_ref)
                if photo_url:
                    enriched['photos'].append(photo_url)
        
        # Add cultural context based on place types and location
        enriched['cultural_context'] = self._generate_cultural_context(enriched)
        enriched['neighborhood'] = self._determine_neighborhood(enriched['location'])
        
        return enriched
    
    def _filter_korean_relevant_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and enrich places for Korean cultural relevance."""
        korean_relevant = []
        
        for place in places:
            # Check if place is in Seoul area
            location = place.get('geometry', {}).get('location', {})
            lat, lng = location.get('lat'), location.get('lng')
            
            if not self._is_in_seoul(lat, lng):
                continue
            
            enriched_place = {
                'place_id': place.get('place_id'),
                'name': place.get('name', 'Unknown Place'),
                'location': {'lat': lat, 'lng': lng},
                'rating': place.get('rating', 0),
                'price_level': place.get('price_level', 1),
                'types': place.get('types', []),
                'vicinity': place.get('vicinity', ''),
                'cultural_context': self._generate_cultural_context({'location': {'lat': lat, 'lng': lng}, 'types': place.get('types', [])}),
                'neighborhood': self._determine_neighborhood({'lat': lat, 'lng': lng})
            }
            
            korean_relevant.append(enriched_place)
        
        return korean_relevant
    
    def _is_in_seoul(self, lat: Optional[float], lng: Optional[float]) -> bool:
        """Check if coordinates are within Seoul city bounds."""
        if not lat or not lng:
            return False
        
        return (self.seoul_bounds['south'] <= lat <= self.seoul_bounds['north'] and
                self.seoul_bounds['west'] <= lng <= self.seoul_bounds['east'])
    
    def _determine_neighborhood(self, location: Dict[str, float]) -> str:
        """Determine Seoul neighborhood based on coordinates."""
        lat, lng = location.get('lat'), location.get('lng')
        if not lat or not lng:
            return 'unknown'
        
        # Approximate neighborhood boundaries (enhanced accuracy)
        if 37.5480 <= lat <= 37.5580 and 126.9180 <= lng <= 126.9950:
            return 'hongdae'
        elif 37.5600 <= lat <= 37.5680 and 126.9780 <= lng <= 126.9880:
            return 'myeongdong'
        elif 37.5300 <= lat <= 37.5400 and 126.9900 <= lng <= 127.0000:
            return 'itaewon'
        elif 37.4950 <= lat <= 37.5150 and 127.0200 <= lng <= 127.0400:
            return 'gangnam'
        else:
            return 'seoul'
    
    def _validate_korean_attraction(self, place: Dict[str, Any]) -> bool:
        """Validate that a place is a legitimate Korean attraction with accurate positioning."""
        location = place.get('geometry', {}).get('location', {})
        lat, lng = location.get('lat'), location.get('lng')
        
        # Must be within Seoul bounds
        if not self._is_in_seoul(lat, lng):
            return False
        
        # Check for Korean cultural relevance
        name = place.get('name', '').lower()
        types = place.get('types', [])
        
        korean_indicators = [
            'korean', 'seoul', 'hanok', 'palace', 'temple', 'market',
            'dongdaemun', 'myeongdong', 'hongdae', 'gangnam', 'itaewon'
        ]
        
        cultural_types = [
            'tourist_attraction', 'museum', 'place_of_worship', 
            'cultural_center', 'historical_landmark'
        ]
        
        has_korean_name = any(indicator in name for indicator in korean_indicators)
        has_cultural_type = any(ctype in types for ctype in cultural_types)
        
        return has_korean_name or has_cultural_type
    
    def _enhance_attraction_positioning(self, place: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance attraction data with accurate positioning and cultural context."""
        location = place.get('geometry', {}).get('location', {})
        lat, lng = location.get('lat'), location.get('lng')
        
        if not lat or not lng:
            return None
        
        enhanced = {
            'place_id': place.get('place_id'),
            'name': place.get('name', 'Unknown Attraction'),
            'location': {
                'lat': round(lat, 6),  # Enhanced precision
                'lng': round(lng, 6)
            },
            'address': place.get('formatted_address', ''),
            'rating': place.get('rating', 0),
            'price_level': place.get('price_level', 1),
            'types': place.get('types', []),
            'photos': self._extract_photo_urls(place.get('photos', [])),
            'cultural_context': self._generate_cultural_context({
                'location': {'lat': lat, 'lng': lng},
                'types': place.get('types', []),
                'name': place.get('name', '')
            }),
            'neighborhood': self._determine_neighborhood({'lat': lat, 'lng': lng}),
            'positioning_accuracy': 'high'  # Mark as high accuracy
        }
        
        return enhanced
    
    def _search_amenity_type(self, location: Tuple[float, float], amenity_type: str) -> List[Dict[str, Any]]:
        """Search for specific amenity type near location."""
        lat, lng = location
        
        # Adjust search radius based on amenity type
        radius_map = {
            'restaurant': 800,      # 800m for restaurants
            'lodging': 1500,        # 1.5km for hotels
            'subway_station': 1000, # 1km for subway
            'bus_station': 500      # 500m for bus stops
        }
        
        radius = radius_map.get(amenity_type, 1000)
        
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': amenity_type,
            'language': 'en'
        }
        
        data = self._make_request(self._api_request, "place/nearbysearch/json", params)
        if not data:
            return []
        
        results = data.get('results', [])
        enhanced_amenities = []
        
        for place in results[:10]:  # Limit to top 10 per type
            enhanced_place = self._enhance_amenity_data(place, amenity_type)
            if enhanced_place:
                enhanced_amenities.append(enhanced_place)
        
    def search_places_by_text(self, query: str, location: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Search for places using text query with optional location bias.
        
        Args:
            query: Text search query
            location: Optional location bias (latitude, longitude)
        
        Returns:
            List of matching places
        """
        params = {
            'query': query,
            'language': 'en'
        }
        
        # Add location bias for Seoul area
        if location:
            lat, lng = location
            params['location'] = f"{lat},{lng}"
            params['radius'] = 10000  # 10km radius
        else:
            # Default to Seoul city center
            params['location'] = "37.5665,126.9780"
            params['radius'] = 25000  # 25km radius for Seoul area
        
        try:
            data = self._make_request(self._api_request, "place/textsearch/json", params)
            if not data:
                return []
            
            results = data.get('results', [])
            return self._filter_korean_relevant_places(results)
            
        except Exception as e:
            self.logger.error(f"Error searching places for '{query}': {e}")
            return self._get_fallback_search_places(query)
    
    def _enhance_amenity_data(self, place: Dict[str, Any], amenity_type: str) -> Dict[str, Any]:
        """Enhance amenity data with cultural context."""
        location = place.get('geometry', {}).get('location', {})
        lat, lng = location.get('lat'), location.get('lng')
        
        enhanced = {
            'place_id': place.get('place_id'),
            'name': place.get('name', f'Korean {amenity_type.title()}'),
            'location': {'lat': lat, 'lng': lng},
            'rating': place.get('rating', 0),
            'price_level': place.get('price_level', 1),
            'vicinity': place.get('vicinity', ''),
            'types': place.get('types', []),
            'amenity_type': amenity_type,
            'cultural_context': self._generate_amenity_cultural_context(place, amenity_type),
            'neighborhood': self._determine_neighborhood({'lat': lat, 'lng': lng})
        }
        
        return enhanced
    
    def _generate_amenity_cultural_context(self, place: Dict[str, Any], amenity_type: str) -> str:
        """Generate cultural context for amenities."""
        name = place.get('name', '').lower()
        neighborhood = self._determine_neighborhood(place.get('geometry', {}).get('location', {}))
        
        context_templates = {
            'restaurant': {
                'hongdae': "Experience authentic Korean dining in the heart of youth culture",
                'myeongdong': "Tourist-friendly Korean restaurant with English menus",
                'itaewon': "International Korean fusion in Seoul's multicultural district",
                'gangnam': "Upscale Korean dining experience in Seoul's business district",
                'default': "Traditional Korean dining experience"
            },
            'lodging': {
                'hongdae': "Stay in Seoul's vibrant nightlife and student district",
                'myeongdong': "Central location for shopping and Korean street food",
                'itaewon': "International-friendly accommodation with English support",
                'gangnam': "Modern luxury accommodation in Seoul's upscale area",
                'default': "Korean hospitality accommodation"
            },
            'subway_station': {
                'default': "Gateway to Korean urban culture and efficient city transport"
            },
            'bus_station': {
                'default': "Local Korean public transport hub"
            }
        }
        
        templates = context_templates.get(amenity_type, {})
        return templates.get(neighborhood, templates.get('default', f"Korean {amenity_type} experience"))
    
    def _calculate_bounds(self, locations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate geographic bounds for multiple locations."""
        lats = [loc['location']['lat'] for loc in locations if 'location' in loc]
        lngs = [loc['location']['lng'] for loc in locations if 'location' in loc]
        
        if not lats or not lngs:
            return self._get_default_seoul_bounds()
        
        return {
            'north': max(lats),
            'south': min(lats),
            'east': max(lngs),
            'west': min(lngs)
        }
    
    def _calculate_optimal_zoom(self, bounds: Dict[str, float]) -> int:
        """Calculate optimal zoom level based on bounds."""
        lat_diff = bounds['north'] - bounds['south']
        lng_diff = bounds['east'] - bounds['west']
        
        # Calculate zoom based on the larger dimension
        max_diff = max(lat_diff, lng_diff)
        
        if max_diff > 0.1:      # > ~11km
            return self.zoom_levels['city']
        elif max_diff > 0.05:   # > ~5.5km
            return self.zoom_levels['district']
        elif max_diff > 0.02:   # > ~2.2km
            return self.zoom_levels['neighborhood']
        elif max_diff > 0.01:   # > ~1.1km
            return self.zoom_levels['street']
        else:
            return self.zoom_levels['building']
    
    def _calculate_center(self, bounds: Dict[str, float]) -> Dict[str, float]:
        """Calculate center point from bounds."""
        return {
            'lat': (bounds['north'] + bounds['south']) / 2,
            'lng': (bounds['east'] + bounds['west']) / 2
        }
    
    def _get_clustering_config(self, locations: List[Dict[str, Any]], zoom_level: int) -> Dict[str, Any]:
        """Get clustering configuration based on locations and zoom level."""
        should_cluster = (
            len(locations) > 5 and 
            zoom_level < self.clustering_config['min_zoom_for_individual']
        )
        
        return {
            'enabled': should_cluster,
            'radius': self.clustering_config['cluster_radius'],
            'max_cluster_size': self.clustering_config['max_cluster_size'],
            'min_zoom_individual': self.clustering_config['min_zoom_for_individual']
        }
    
    def _get_default_seoul_view(self) -> Dict[str, Any]:
        """Get default Seoul city view."""
        return {
            'center': {'lat': 37.5665, 'lng': 126.9780},
            'zoom': self.zoom_levels['city'],
            'bounds': self._get_default_seoul_bounds(),
            'clustering': {'enabled': False},
            'total_locations': 0
        }
    
    def _get_single_location_view(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimized view for single location."""
        loc = location.get('location', {'lat': 37.5665, 'lng': 126.9780})
        
        return {
            'center': loc,
            'zoom': self.zoom_levels['neighborhood'],
            'bounds': {
                'north': loc['lat'] + 0.01,
                'south': loc['lat'] - 0.01,
                'east': loc['lng'] + 0.01,
                'west': loc['lng'] - 0.01
            },
            'clustering': {'enabled': False},
            'total_locations': 1
        }
    
    def _get_default_seoul_bounds(self) -> Dict[str, float]:
        """Get default Seoul city bounds."""
        return self.seoul_bounds.copy()
    
    def _extract_photo_urls(self, photos: List[Dict[str, Any]]) -> List[str]:
        """Extract photo URLs from photos array."""
        photo_urls = []
        for photo in photos[:3]:  # Limit to 3 photos
            photo_ref = photo.get('photo_reference')
            if photo_ref:
                photo_url = self.get_place_photos(photo_ref)
                if photo_url:
                    photo_urls.append(photo_url)
        return photo_urls
    
    def _get_fallback_korean_attractions(self) -> List[Dict[str, Any]]:
        """Provide fallback Korean attractions when API is unavailable."""
        return [
            {
                'place_id': 'fallback_gyeongbok',
                'name': 'Gyeongbokgung Palace',
                'location': {'lat': 37.5796, 'lng': 126.9770},
                'rating': 4.5,
                'cultural_context': 'Historic royal palace showcasing Korean traditional architecture',
                'neighborhood': 'seoul',
                'positioning_accuracy': 'fallback'
            },
            {
                'place_id': 'fallback_bukchon',
                'name': 'Bukchon Hanok Village',
                'location': {'lat': 37.5824, 'lng': 126.9833},
                'rating': 4.3,
                'cultural_context': 'Traditional Korean village with authentic hanok houses',
                'neighborhood': 'seoul',
                'positioning_accuracy': 'fallback'
            }
        ]
    
    def _get_fallback_amenities(self, location: Tuple[float, float], amenity_type: str) -> List[Dict[str, Any]]:
        """Provide fallback amenities when API is unavailable."""
        lat, lng = location
        neighborhood = self._determine_neighborhood({'lat': lat, 'lng': lng})
        
        return [
            {
                'place_id': f'fallback_{amenity_type}_1',
                'name': f'Korean {amenity_type.title()}',
                'location': {'lat': lat + 0.001, 'lng': lng + 0.001},
                'rating': 4.0,
                'cultural_context': self._generate_amenity_cultural_context({}, amenity_type),
                'neighborhood': neighborhood,
                'amenity_type': amenity_type
            }
        ]
    
    def _generate_cultural_context(self, place_data: Dict[str, Any]) -> str:
        """Generate cultural context based on place type and location."""
        types = place_data.get('types', [])
        name = place_data.get('name', '').lower()
        location = place_data.get('location', {})
        neighborhood = place_data.get('neighborhood') or self._determine_neighborhood(location)
        
        # Enhanced context mapping with neighborhood-specific insights
        context_map = {
            'restaurant': {
                'hongdae': "Experience authentic Korean dining in the heart of youth culture and nightlife",
                'myeongdong': "Tourist-friendly Korean restaurant with international appeal",
                'itaewon': "Korean-international fusion dining in Seoul's multicultural district",
                'gangnam': "Upscale Korean dining experience in Seoul's modern business district",
                'default': "Authentic Korean dining experience with traditional flavors"
            },
            'tourist_attraction': {
                'hongdae': "Cultural landmark in Seoul's vibrant youth and arts district",
                'myeongdong': "Popular cultural site in Seoul's main shopping district",
                'itaewon': "Cultural attraction in Seoul's international neighborhood",
                'gangnam': "Modern cultural landmark in Seoul's upscale district",
                'default': "Cultural landmark showcasing Korean heritage and history"
            },
            'shopping_mall': {
                'hongdae': "Youth-oriented shopping with Korean street fashion and culture",
                'myeongdong': "International shopping destination with Korean beauty and fashion",
                'itaewon': "Multicultural shopping experience with global and Korean brands",
                'gangnam': "Luxury shopping experience in Seoul's most affluent district",
                'default': "Modern Korean shopping experience with local and international brands"
            },
            'subway_station': {
                'default': "Gateway to Korean urban culture and Seoul's efficient subway system"
            },
            'park': {
                'default': "Traditional Korean leisure space for relaxation and cultural activities"
            },
            'museum': {
                'default': "Korean cultural and historical exhibits showcasing the nation's heritage"
            },
            'place_of_worship': {
                'default': "Traditional Korean spiritual site with cultural and historical significance"
            }
        }
        
        # Find the most relevant place type
        for place_type in types:
            if place_type in context_map:
                type_contexts = context_map[place_type]
                if isinstance(type_contexts, dict):
                    return type_contexts.get(neighborhood, type_contexts.get('default', f"Korean cultural experience in {neighborhood}"))
                else:
                    return type_contexts
        
        # Special handling for Korean-specific names
        if any(keyword in name for keyword in ['hanok', 'palace', 'temple', 'market']):
            return f"Traditional Korean cultural site in {neighborhood} with authentic historical significance"
        
        return f"Korean cultural experience in {neighborhood}"
    
    def _get_fallback_place_details(self, place_id: str) -> Dict[str, Any]:
        """Provide fallback place details when API is unavailable."""
        return {
            'place_id': place_id,
            'name': 'Korean Cultural Site',
            'address': 'Seoul, South Korea',
            'location': {'lat': 37.5665, 'lng': 126.9780},
            'rating': 4.0,
            'cultural_context': 'Traditional Korean cultural experience',
            'neighborhood': 'seoul'
        }
    
    def _get_fallback_nearby_places(self, location: Tuple[float, float], place_type: str) -> List[Dict[str, Any]]:
        """Provide fallback nearby places when API is unavailable."""
        return [
            {
                'place_id': 'fallback_nearby_1',
                'name': 'Traditional Korean Restaurant',
                'location': {'lat': location[0] + 0.001, 'lng': location[1] + 0.001},
                'rating': 4.2,
                'cultural_context': 'Authentic Korean dining experience',
                'neighborhood': self._determine_neighborhood({'lat': location[0], 'lng': location[1]})
            }
        ]
    
    def _get_fallback_search_places(self, query: str) -> List[Dict[str, Any]]:
        """Provide fallback search results when API is unavailable."""
        return [
            {
                'place_id': 'fallback_search_1',
                'name': f'Korean Cultural Site - {query}',
                'location': {'lat': 37.5665, 'lng': 126.9780},
                'rating': 4.0,
                'cultural_context': f'Korean cultural experience related to {query}',
                'neighborhood': 'seoul'
            }
        ]
    
    def _handle_fallback(self, error: Exception) -> Dict[str, Any]:
        """Handle fallback when Google Maps API is unavailable."""
        self.logger.warning(f"Google Maps API unavailable, using cached location data: {error}")
        return self._get_fallback_place_details("fallback_place")