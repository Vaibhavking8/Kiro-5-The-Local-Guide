#!/usr/bin/env python3
"""
Integration test for the final wiring and error handling.
"""

import sys
import os

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.service_manager import service_manager
import traceback

def test_service_manager():
    """Test service manager integration."""
    print("Testing Service Manager...")
    try:
        status = service_manager.get_service_status()
        available_count = len([s for s in status.values() if s.get('available', False)])
        total_count = len(status)
        print(f"Services available: {available_count}/{total_count}")
        
        for service_name, service_status in status.items():
            state = service_status.get('state', 'unknown')
            available = service_status.get('available', False)
            print(f"  {service_name}: {state} ({'available' if available else 'unavailable'})")
        
        return available_count > 0
    except Exception as e:
        print(f"Service Manager test failed: {e}")
        return False

def test_local_guide_system():
    """Test Local Guide System integration."""
    print("\nTesting Local Guide System...")
    try:
        result = service_manager.get_local_guide_recommendation(
            'korean food recommendations',
            user_profile=None,
            location=(37.5665, 126.9780)
        )
        
        print("Local Guide System test: SUCCESS")
        print(f"Response length: {len(result.get('response', ''))}")
        print(f"Recommendations count: {len(result.get('recommendations', []))}")
        print(f"Authenticity score: {result.get('authenticity_score', 0):.2f}")
        print(f"Fallback used: {result.get('fallback_used', False)}")
        
        return True
    except Exception as e:
        print(f"Local Guide System test: FAILED - {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling mechanisms."""
    print("\nTesting Error Handling...")
    try:
        # Test with invalid input
        result = service_manager.get_local_guide_recommendation(
            '',  # Empty query
            user_profile=None,
            location=None
        )
        
        print("Error handling test: SUCCESS")
        print(f"Empty query handled gracefully: {bool(result.get('response'))}")
        
        return True
    except Exception as e:
        print(f"Error handling test: FAILED - {e}")
        return False

def main():
    """Run all integration tests."""
    print("=== Integration Test Suite ===")
    
    tests = [
        test_service_manager,
        test_local_guide_system,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All integration tests passed!")
        return 0
    else:
        print("❌ Some integration tests failed!")
        return 1

if __name__ == '__main__':
    exit(main())