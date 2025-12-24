"""
Simple test script to verify API service integrations.
Run this to check if all services are properly configured and working.
"""
import sys
import os

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.service_manager import service_manager
from utils.config import config


def test_service_initialization():
    """Test that all services initialize properly."""
    print("=== Testing Service Initialization ===")
    
    status = service_manager.get_service_status()
    
    for service_name, service_status in status.items():
        available = "✓ Available" if service_status['available'] else "✗ Unavailable"
        state = service_status['state']
        print(f"{service_name.capitalize()}: {available} (State: {state})")
    
    healthy_services = service_manager.get_healthy_services()
    print(f"\nHealthy services: {', '.join(healthy_services) if healthy_services else 'None'}")
    
    return len(healthy_services) > 0


def test_fallback_functionality():
    """Test fallback functionality when services are unavailable."""
    print("\n=== Testing Fallback Functionality ===")
    
    # Test cultural recommendations fallback
    print("Testing cultural recommendations fallback...")
    recommendations = service_manager.get_cultural_recommendations("korean food", ["food", "culture"])
    print(f"Got {len(recommendations)} recommendations")
    
    # Test place search fallback
    print("Testing place search fallback...")
    places = service_manager.search_places("korean restaurant", location=(37.5665, 126.9780))
    print(f"Got {len(places)} places")
    
    # Test response generation fallback
    print("Testing response generation fallback...")
    response = service_manager.generate_response("What should I eat in Seoul?", recommendations)
    print(f"Generated response: {len(response)} characters")
    
    return True


def test_configuration():
    """Test configuration loading and validation."""
    print("\n=== Testing Configuration ===")
    
    config.print_config_status()
    
    # Test service config
    service_config = config.get_service_config()
    print(f"\nService configuration loaded: {len(service_config)} sections")
    
    return True


def main():
    """Run all tests."""
    print("Starting API Service Integration Tests...\n")
    
    tests = [
        ("Configuration", test_configuration),
        ("Service Initialization", test_service_initialization),
        ("Fallback Functionality", test_fallback_functionality)
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
        print("🎉 All tests passed! Services are ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and API keys.")
        for test_name, result, error in results:
            if not result:
                print(f"  - {test_name}: {error or 'Failed'}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)