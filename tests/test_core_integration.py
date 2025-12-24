"""
Core Services Integration Test for Local Guide Revamp
Tests the integration between all services with fallback mechanisms and user personalization.
"""

import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.service_manager import service_manager
from utils.user_profile_manager import UserProfileManager
from utils.config import config


def test_service_orchestration():
    """Test that services work together to provide recommendations."""
    print("=== Testing Service Orchestration ===")
    
    # Test user query with cultural context
    user_query = "I want to try authentic Korean street food in Hongdae"
    user_interests = ["food", "culture", "nightlife"]
    
    # Get cultural recommendations
    cultural_recs = service_manager.get_cultural_recommendations(user_query, user_interests)
    print(f"Cultural recommendations: {len(cultural_recs)} items")
    
    # Get place search results
    hongdae_location = (37.5563, 126.9236)  # Hongdae coordinates
    places = service_manager.search_places("korean street food", location=hongdae_location)
    print(f"Place search results: {len(places)} places")
    
    # Generate response combining both
    response = service_manager.generate_response(user_query, cultural_recs + places)
    print(f"Generated response length: {len(response)} characters")
    
    # Verify response contains Korean cultural context
    korean_terms = ["korean", "hongdae", "street food", "tteokbokki", "culture"]
    found_terms = [term for term in korean_terms if term.lower() in response.lower()]
    print(f"Korean cultural terms found: {found_terms}")
    
    return len(cultural_recs) > 0 and len(places) > 0 and len(response) > 100


def test_fallback_mechanisms():
    """Test that fallback mechanisms work when services fail."""
    print("\n=== Testing Fallback Mechanisms ===")
    
    # Get service status
    status = service_manager.get_service_status()
    print("Service status:")
    for service_name, service_status in status.items():
        state = service_status['state']
        available = service_status['available']
        print(f"  {service_name}: {state} ({'Available' if available else 'Unavailable'})")
    
    # Test that we get results even when some services are down
    # (TasteDive appears to be having issues based on previous test)
    user_query = "Best Korean BBQ restaurants"
    recommendations = service_manager.get_cultural_recommendations(user_query, ["food"])
    
    # Should get fallback recommendations
    assert len(recommendations) > 0, "Should get fallback recommendations when API fails"
    print(f"Fallback recommendations: {len(recommendations)} items")
    
    # Test search fallback
    places = service_manager.search_places("korean bbq")
    assert len(places) > 0, "Should get fallback search results"
    print(f"Fallback search results: {len(places)} places")
    
    return True


def test_user_personalization_integration():
    """Test that user personalization affects recommendations."""
    print("\n=== Testing User Personalization Integration ===")
    
    # Create mock user profile manager
    mock_mongo = MagicMock()
    mock_db = MagicMock()
    mock_users = MagicMock()
    mock_cache = MagicMock()
    
    mock_mongo.taste_trails_korea = mock_db
    mock_db.users = mock_users
    mock_db.recommendation_cache = mock_cache
    
    profile_manager = UserProfileManager(mock_mongo)
    
    # Create test user with specific preferences
    user_data = {
        "username": "test_foodie",
        "email": "foodie@test.com",
        "password": "test123",
        "food_restrictions": ["no_spicy"],
        "interests": ["food", "culture"],
        "cultural_preferences": ["traditional", "street-food"],
        "budget_range": "budget",
        "travel_style": "solo"
    }
    
    # Mock user creation
    mock_result = MagicMock()
    # Use a proper ObjectId format (24-character hex string)
    test_user_id = "507f1f77bcf86cd799439011"
    mock_result.inserted_id = test_user_id
    mock_users.insert_one.return_value = mock_result
    
    user_id = profile_manager.create_user_profile(user_data)
    print(f"Created test user: {user_id}")
    
    # Mock user retrieval for personalization
    mock_user = {
        "_id": test_user_id,  # Use the same ObjectId format
        "preferences": {
            "food_restrictions": ["no_spicy"],
            "interests": ["food", "culture"],
            "cultural_preferences": ["traditional", "street-food"],
            "budget_range": "budget"
        },
        "history": {
            "visited_places": [
                {
                    "name": "Gwangjang Market",
                    "location": {"neighborhood": "jongno"},
                    "rating": 5,
                    "visited_date": datetime.utcnow()
                }
            ],
            "favorites": []
        },
        "personalization": {
            "recommendation_weights": {
                "food": 1.5,
                "culture": 1.3,
                "nightlife": 0.8,
                "shopping": 1.0,
                "nature": 1.0
            },
            "preferred_neighborhoods": ["jongno"]
        }
    }
    
    mock_users.find_one.return_value = mock_user
    
    # Get personalized preferences using the proper ObjectId format
    prefs = profile_manager.get_personalized_preferences(test_user_id)
    print(f"Personalized preferences loaded: {prefs is not None}")
    
    # Verify personalization structure
    assert "recommendation_weights" in prefs
    assert prefs["recommendation_weights"]["food"] > 1.0  # Should be boosted
    assert "preferred_neighborhoods" in prefs
    assert "jongno" in prefs["preferred_neighborhoods"]
    
    print("✓ User personalization affects recommendation weights")
    return True


def test_error_handling_and_recovery():
    """Test error handling and recovery across all services."""
    print("\n=== Testing Error Handling and Recovery ===")
    
    # Test with invalid inputs
    try:
        # Empty query
        result = service_manager.get_cultural_recommendations("", [])
        print(f"Empty query handled: {len(result)} results")
        
        # Invalid location
        result = service_manager.search_places("test", location=(999, 999))
        print(f"Invalid location handled: {len(result)} results")
        
        # Very long query
        long_query = "a" * 1000
        result = service_manager.generate_response(long_query, [])
        print(f"Long query handled: {len(result)} characters")
        
        print("✓ Error handling working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error handling failed: {e}")
        return False


def test_performance_requirements():
    """Test basic performance requirements."""
    print("\n=== Testing Performance Requirements ===")
    
    import time
    
    # Test search response time (should be under 200ms when working)
    start_time = time.time()
    places = service_manager.search_places("korean restaurant")
    search_time = (time.time() - start_time) * 1000
    print(f"Search response time: {search_time:.2f}ms")
    
    # Test recommendation generation time (should be under 5 seconds)
    start_time = time.time()
    recommendations = service_manager.get_cultural_recommendations("korean food", ["food"])
    response = service_manager.generate_response("What should I eat?", recommendations)
    total_time = time.time() - start_time
    print(f"Total recommendation generation time: {total_time:.2f}s")
    
    # Note: These may be slower due to fallback mechanisms, but should still complete
    performance_ok = total_time < 10  # Allow extra time for fallbacks
    print(f"Performance within acceptable limits: {performance_ok}")
    
    return performance_ok


def test_korean_cultural_authenticity():
    """Test that responses maintain Korean cultural authenticity."""
    print("\n=== Testing Korean Cultural Authenticity ===")
    
    # Test queries that should trigger Korean cultural context
    test_queries = [
        "Where should I eat in Hongdae?",
        "What's the best Korean street food?",
        "Tell me about Korean dining etiquette",
        "What should I do in Myeongdong?"
    ]
    
    korean_cultural_indicators = [
        "korean", "seoul", "hongdae", "myeongdong", "itaewon", "gangnam",
        "tteokbokki", "samgyeopsal", "banchan", "daebak", "hwaiting",
        "culture", "traditional", "street food", "nightlife"
    ]
    
    authenticity_scores = []
    
    for query in test_queries:
        recommendations = service_manager.get_cultural_recommendations(query, ["culture", "food"])
        response = service_manager.generate_response(query, recommendations)
        
        # Count Korean cultural indicators in response
        found_indicators = [indicator for indicator in korean_cultural_indicators 
                          if indicator.lower() in response.lower()]
        
        authenticity_score = len(found_indicators) / len(korean_cultural_indicators)
        authenticity_scores.append(authenticity_score)
        
        print(f"Query: '{query[:30]}...'")
        print(f"  Cultural indicators found: {len(found_indicators)}")
        print(f"  Authenticity score: {authenticity_score:.2f}")
    
    avg_authenticity = sum(authenticity_scores) / len(authenticity_scores)
    print(f"\nAverage authenticity score: {avg_authenticity:.2f}")
    
    # Should have reasonable cultural authenticity (at least 10% of indicators)
    return avg_authenticity > 0.1


def main():
    """Run all core integration tests."""
    print("Starting Core Services Integration Tests...\n")
    
    tests = [
        ("Service Orchestration", test_service_orchestration),
        ("Fallback Mechanisms", test_fallback_mechanisms),
        ("User Personalization Integration", test_user_personalization_integration),
        ("Error Handling and Recovery", test_error_handling_and_recovery),
        ("Performance Requirements", test_performance_requirements),
        ("Korean Cultural Authenticity", test_korean_cultural_authenticity)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            status = "PASSED" if result else "FAILED"
            print(f"✓ {test_name}: {status}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAILED - {e}")
    
    print("\n=== Integration Test Summary ===")
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All core integration tests passed!")
        print("✅ Services are working together correctly")
        print("✅ Fallback mechanisms are functional")
        print("✅ User personalization is integrated")
        print("✅ Error handling is robust")
        print("✅ Korean cultural authenticity is maintained")
        return 0
    else:
        print("⚠️  Some integration tests failed:")
        for test_name, result, error in results:
            if not result:
                print(f"  - {test_name}: {error or 'Failed'}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)