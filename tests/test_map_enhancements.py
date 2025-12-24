#!/usr/bin/env python3
"""
Test script for Interactive Map Service enhancements.
Tests the new functionality for Korean attraction positioning, nearby amenity discovery, and clustering.
"""

import sys
import os
# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.googlemaps_api import GoogleMapsService
from utils.config import config

def test_map_enhancements():
    """Test the enhanced Interactive Map Service functionality."""
    print("Testing Interactive Map Service Enhancements...")
    
    # Initialize the service
    maps_service = GoogleMapsService()
    print(f"✓ GoogleMapsService initialized")
    
    # Test 1: Korean attraction positioning accuracy
    print("\n1. Testing Korean attraction positioning accuracy...")
    try:
        attractions = maps_service.get_accurate_korean_attractions("korean palace", (37.5665, 126.9780))
        print(f"✓ Found {len(attractions)} Korean attractions")
        
        if attractions:
            first_attraction = attractions[0]
            print(f"  - Sample attraction: {first_attraction['name']}")
            print(f"  - Location: {first_attraction['location']}")
            print(f"  - Cultural context: {first_attraction['cultural_context']}")
            print(f"  - Neighborhood: {first_attraction['neighborhood']}")
            print(f"  - Positioning accuracy: {first_attraction.get('positioning_accuracy', 'standard')}")
    except Exception as e:
        print(f"✗ Error testing Korean attractions: {e}")
    
    # Test 2: Nearby amenity discovery with cultural context
    print("\n2. Testing nearby amenity discovery...")
    try:
        seoul_center = (37.5665, 126.9780)
        amenities = maps_service.discover_nearby_amenities(seoul_center, ['restaurant', 'subway_station'])
        print(f"✓ Found amenities: {list(amenities.keys())}")
        
        for amenity_type, places in amenities.items():
            print(f"  - {amenity_type}: {len(places)} places")
            if places:
                sample = places[0]
                print(f"    Sample: {sample['name']} - {sample['cultural_context']}")
    except Exception as e:
        print(f"✗ Error testing amenity discovery: {e}")
    
    # Test 3: Map view optimization and clustering
    print("\n3. Testing map view optimization...")
    try:
        # Create sample locations for testing
        sample_locations = [
            {'location': {'lat': 37.5796, 'lng': 126.9770}},  # Gyeongbokgung
            {'location': {'lat': 37.5824, 'lng': 126.9833}},  # Bukchon
            {'location': {'lat': 37.5665, 'lng': 126.9780}},  # Seoul center
            {'location': {'lat': 37.5547, 'lng': 126.9707}},  # Myeongdong
            {'location': {'lat': 37.5519, 'lng': 126.9918}},  # Hongdae
        ]
        
        map_config = maps_service.get_optimized_map_view(sample_locations)
        print(f"✓ Map optimization completed")
        print(f"  - Center: {map_config['center']}")
        print(f"  - Zoom level: {map_config['zoom']}")
        print(f"  - Clustering enabled: {map_config['clustering']['enabled']}")
        print(f"  - Total locations: {map_config['total_locations']}")
    except Exception as e:
        print(f"✗ Error testing map optimization: {e}")
    
    # Test 4: Neighborhood determination accuracy
    print("\n4. Testing neighborhood determination...")
    test_locations = [
        ({'lat': 37.5519, 'lng': 126.9918}, 'hongdae'),
        ({'lat': 37.5665, 'lng': 126.9780}, 'myeongdong'),
        ({'lat': 37.5350, 'lng': 126.9950}, 'itaewon'),
        ({'lat': 37.5050, 'lng': 127.0300}, 'gangnam'),
    ]
    
    for location, expected in test_locations:
        neighborhood = maps_service._determine_neighborhood(location)
        status = "✓" if neighborhood == expected else "✗"
        print(f"  {status} {location} -> {neighborhood} (expected: {expected})")
    
    # Test 5: Cultural context generation
    print("\n5. Testing cultural context generation...")
    test_places = [
        {'types': ['restaurant'], 'neighborhood': 'hongdae', 'name': 'Korean BBQ'},
        {'types': ['tourist_attraction'], 'neighborhood': 'seoul', 'name': 'Gyeongbokgung Palace'},
        {'types': ['subway_station'], 'neighborhood': 'gangnam', 'name': 'Gangnam Station'},
    ]
    
    for place_data in test_places:
        context = maps_service._generate_cultural_context(place_data)
        print(f"  ✓ {place_data['name']}: {context}")
    
    print("\n✅ Interactive Map Service enhancement testing completed!")

if __name__ == "__main__":
    test_map_enhancements()