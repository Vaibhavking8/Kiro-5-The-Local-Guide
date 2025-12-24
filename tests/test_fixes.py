#!/usr/bin/env python3
"""
Test the fixes for TasteDive NoneType error and Algolia import issue
"""
import sys
import os
# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_algolia_import():
    """Test Algolia import fix"""
    print("=== Testing Algolia Import Fix ===")
    try:
        from utils.algolia_api import SearchService
        search_service = SearchService()
        print("✅ Algolia SearchService imported successfully")
        print(f"Client available: {search_service.client is not None}")
        return True
    except Exception as e:
        print(f"❌ Algolia import failed: {e}")
        return False

def test_tastedive_nonetype():
    """Test TasteDive NoneType fix"""
    print("\n=== Testing TasteDive NoneType Fix ===")
    try:
        from utils.tastedive_api import CulturalDiscoveryEngine
        engine = CulturalDiscoveryEngine()
        
        # Test with a simple query that should work
        results = engine.find_similar_korean_experiences("korean", content_type="movie", limit=2)
        print(f"✅ TasteDive query successful: {len(results)} results")
        
        # Test the methods that were causing NoneType errors
        if results:
            test_item = results[0]
            themes = engine._extract_cultural_themes(test_item)
            print(f"✅ Cultural themes extraction: {len(themes)} themes")
            
            category = engine._categorize_media_type(test_item)
            print(f"✅ Media type categorization: {category}")
            
        return True
    except Exception as e:
        print(f"❌ TasteDive test failed: {e}")
        return False

def test_service_manager():
    """Test service manager integration"""
    print("\n=== Testing Service Manager Integration ===")
    try:
        from utils.service_manager import service_manager
        
        # Test cultural recommendations
        recommendations = service_manager.get_cultural_recommendations("korean food", ["food"])
        print(f"✅ Service manager recommendations: {len(recommendations)} items")
        
        if recommendations:
            first_rec = recommendations[0]
            print(f"First recommendation: {first_rec.get('Name', 'No name')}")
        
        return True
    except Exception as e:
        print(f"❌ Service manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing fixes for NoneType and Algolia issues...\n")
    
    tests = [
        ("Algolia Import", test_algolia_import),
        ("TasteDive NoneType", test_tastedive_nonetype),
        ("Service Manager Integration", test_service_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    print("\n=== Test Summary ===")
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for test_name, result, error in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if error:
            print(f"  Error: {error}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)