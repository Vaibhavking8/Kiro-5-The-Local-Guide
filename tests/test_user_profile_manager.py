"""
Test script for User Profile Manager functionality.
Tests the enhanced user profile features including personalization and history tracking.
"""

import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.user_profile_manager import UserProfileManager


def create_mock_mongo():
    """Create a mock MongoDB client for testing."""
    mock_mongo = MagicMock()
    mock_db = MagicMock()
    mock_users = MagicMock()
    mock_cache = MagicMock()
    
    mock_mongo.taste_trails_korea = mock_db
    mock_db.users = mock_users
    mock_db.recommendation_cache = mock_cache
    
    return mock_mongo, mock_users, mock_cache


def test_user_profile_creation():
    """Test enhanced user profile creation."""
    print("=== Testing User Profile Creation ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Test user data with enhanced preferences
    user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
        "food_restrictions": ["vegetarian", "no_spicy"],
        "interests": ["culture", "food", "nightlife"],
        "cultural_preferences": ["traditional", "k-pop"],
        "budget_range": "mid-range",
        "travel_style": "couple"
    }
    
    # Mock the insert_one result
    mock_result = MagicMock()
    mock_result.inserted_id = "test_user_id"
    mock_users.insert_one.return_value = mock_result
    
    # Test profile creation
    user_id = profile_manager.create_user_profile(user_data)
    
    # Verify the call was made
    assert mock_users.insert_one.called
    call_args = mock_users.insert_one.call_args[0][0]
    
    # Verify enhanced schema structure
    assert "preferences" in call_args
    assert "history" in call_args
    assert "personalization" in call_args
    
    # Verify preferences structure
    prefs = call_args["preferences"]
    assert prefs["food_restrictions"] == ["vegetarian", "no_spicy"]
    assert prefs["interests"] == ["culture", "food", "nightlife"]
    assert prefs["cultural_preferences"] == ["traditional", "k-pop"]
    assert prefs["budget_range"] == "mid-range"
    assert prefs["travel_style"] == "couple"
    
    # Verify personalization structure
    personalization = call_args["personalization"]
    assert "recommendation_weights" in personalization
    weights = personalization["recommendation_weights"]
    assert all(key in weights for key in ["food", "culture", "nightlife", "shopping", "nature"])
    assert all(weight == 1.0 for weight in weights.values())
    
    print("✓ User profile creation with enhanced schema: PASSED")
    return True


def test_user_history_tracking():
    """Test user history tracking functionality."""
    print("\n=== Testing User History Tracking ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Use a valid ObjectId string
    test_user_id = "507f1f77bcf86cd799439011"
    
    # Test visited place data
    visited_place = {
        "name": "Myeongdong Street Food",
        "category": "food",
        "location": {
            "lat": 37.5636,
            "lng": 126.9834,
            "neighborhood": "myeongdong"
        },
        "notes": "Amazing tteokbokki!"
    }
    
    # Test history update
    profile_manager.update_user_history(test_user_id, visited_place, 5)
    
    # Verify MongoDB update calls
    assert mock_users.update_one.called
    
    # Check the update call for visited places
    update_calls = mock_users.update_one.call_args_list
    assert len(update_calls) >= 1
    
    # Verify the structure of the update
    first_call = update_calls[0]
    filter_doc = first_call[0][0]
    update_doc = first_call[0][1]
    
    assert "$push" in update_doc
    assert "history.visited_places" in update_doc["$push"]
    
    place_entry = update_doc["$push"]["history.visited_places"]
    assert place_entry["name"] == "Myeongdong Street Food"
    assert place_entry["rating"] == 5
    assert "visited_date" in place_entry
    
    print("✓ User history tracking: PASSED")
    return True


def test_personalized_preferences():
    """Test personalized preferences generation."""
    print("\n=== Testing Personalized Preferences ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Use a valid ObjectId string
    test_user_id = "507f1f77bcf86cd799439011"
    
    # Mock user data with history
    mock_user = {
        "_id": test_user_id,
        "preferences": {
            "food_restrictions": ["vegetarian"],
            "interests": ["culture", "food"],
            "cultural_preferences": ["traditional"]
        },
        "history": {
            "visited_places": [
                {
                    "name": "Bukchon Hanok Village",
                    "location": {"neighborhood": "jongno"},
                    "visited_date": datetime.utcnow(),
                    "rating": 5
                },
                {
                    "name": "Hongdae Club",
                    "location": {"neighborhood": "hongdae"},
                    "visited_date": datetime.utcnow(),
                    "rating": 4
                }
            ],
            "favorites": [
                {"name": "Korean BBQ Place", "category": "food"}
            ]
        },
        "personalization": {
            "recommendation_weights": {
                "food": 1.2,
                "culture": 1.5,
                "nightlife": 0.8,
                "shopping": 1.0,
                "nature": 1.0
            }
        }
    }
    
    mock_users.find_one.return_value = mock_user
    
    # Test personalized preferences
    prefs = profile_manager.get_personalized_preferences(test_user_id)
    
    # Verify the result structure
    assert prefs is not None
    assert "preferences" in prefs
    assert "recommendation_weights" in prefs
    assert "preferred_neighborhoods" in prefs
    assert "visit_history_count" in prefs
    assert "favorites_count" in prefs
    
    # Verify neighborhood analysis
    preferred_neighborhoods = prefs["preferred_neighborhoods"]
    assert "jongno" in preferred_neighborhoods or "hongdae" in preferred_neighborhoods
    
    # Verify counts
    assert prefs["visit_history_count"] == 2
    assert prefs["favorites_count"] == 1
    
    print("✓ Personalized preferences generation: PASSED")
    return True


def test_recommendation_weights_update():
    """Test recommendation weights update based on user activity."""
    print("\n=== Testing Recommendation Weights Update ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Use a valid ObjectId string
    test_user_id = "507f1f77bcf86cd799439011"
    
    # Mock user with current weights
    mock_user = {
        "_id": test_user_id,
        "personalization": {
            "recommendation_weights": {
                "food": 1.0,
                "culture": 1.0,
                "nightlife": 1.0,
                "shopping": 1.0,
                "nature": 1.0
            }
        }
    }
    
    mock_users.find_one.return_value = mock_user
    
    # Test weight update for food category with high rating
    profile_manager._update_recommendation_weights(test_user_id, "food", 5)
    
    # Verify MongoDB update calls
    assert mock_users.update_one.called
    
    # Check for increment operation
    update_calls = mock_users.update_one.call_args_list
    increment_call = None
    
    for call in update_calls:
        update_doc = call[0][1]
        if "$inc" in update_doc:
            increment_call = update_doc
            break
    
    assert increment_call is not None
    assert "$inc" in increment_call
    
    # Verify the weight adjustment
    weight_key = "personalization.recommendation_weights.food"
    assert weight_key in increment_call["$inc"]
    
    # High rating (5) should increase weight
    adjustment = increment_call["$inc"][weight_key]
    assert adjustment > 0  # Should be positive for rating > 3
    
    print("✓ Recommendation weights update: PASSED")
    return True


def test_immediate_profile_update_reflection():
    """Test that profile updates immediately clear cache and update recommendations."""
    print("\n=== Testing Immediate Profile Update Reflection ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Use a valid ObjectId string
    test_user_id = "507f1f77bcf86cd799439011"
    
    # Test preference update
    new_preferences = {
        "interests": ["culture", "nightlife", "shopping"],
        "cultural_preferences": ["modern", "k-pop"],
        "budget_range": "luxury"
    }
    
    profile_manager.update_preferences(test_user_id, new_preferences)
    
    # Verify MongoDB update was called
    assert mock_users.update_one.called
    
    # Verify cache clear was called
    assert mock_cache.delete_many.called
    
    # Check the update structure
    update_call = mock_users.update_one.call_args
    update_doc = update_call[0][1]["$set"]
    
    # Verify immediate timestamp update
    assert "personalization.last_recommendation_update" in update_doc
    
    # Verify preference updates
    assert "preferences.interests" in update_doc
    assert update_doc["preferences.interests"] == ["culture", "nightlife", "shopping"]
    
    print("✓ Immediate profile update reflection: PASSED")
    return True


def test_mongodb_performance_optimization():
    """Test MongoDB performance optimizations."""
    print("\n=== Testing MongoDB Performance Optimization ===")
    
    mock_mongo, mock_users, mock_cache = create_mock_mongo()
    profile_manager = UserProfileManager(mock_mongo)
    
    # Verify index creation was attempted
    assert mock_users.create_index.called
    assert mock_cache.create_index.called
    
    # Check that indexes were created for performance-critical fields
    index_calls = mock_users.create_index.call_args_list
    created_indexes = [call[0][0] for call in index_calls]
    
    # Verify critical indexes
    assert "username" in created_indexes
    assert "email" in created_indexes
    
    print("✓ MongoDB performance optimization: PASSED")
    return True


def main():
    """Run all User Profile Manager tests."""
    print("Starting User Profile Manager Tests...\n")
    
    tests = [
        ("User Profile Creation", test_user_profile_creation),
        ("User History Tracking", test_user_history_tracking),
        ("Personalized Preferences", test_personalized_preferences),
        ("Recommendation Weights Update", test_recommendation_weights_update),
        ("Immediate Profile Update Reflection", test_immediate_profile_update_reflection),
        ("MongoDB Performance Optimization", test_mongodb_performance_optimization)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            print(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAILED - {e}")
    
    print("\n=== Test Summary ===")
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All User Profile Manager tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed.")
        for test_name, result, error in results:
            if not result:
                print(f"  - {test_name}: {error or 'Failed'}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)