"""
Test security enhancements for authentication and session management.
Tests password hashing, session security, and API key configuration.
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.user_profile_manager import UserProfileManager
from utils.config import config
from passlib.hash import pbkdf2_sha256
from unittest.mock import Mock, patch
import os


def test_password_hashing_pbkdf2_sha256():
    """Test that passwords are hashed using PBKDF2-SHA256."""
    print("\n=== Testing PBKDF2-SHA256 Password Hashing ===")
    
    # Mock MongoDB client
    mock_client = Mock()
    mock_db = Mock()
    mock_users = Mock()
    mock_client.taste_trails_korea = mock_db
    mock_db.users = mock_users
    
    # Mock the insert_one result
    mock_result = Mock()
    mock_result.inserted_id = "test_user_id"
    mock_users.insert_one.return_value = mock_result
    
    user_manager = UserProfileManager(mock_client)
    
    # Test user data
    user_data = {
        "username": "test_security_user",
        "email": "security@test.com",
        "password": "test_password_123",
        "food_restrictions": [],
        "interests": ["security"],
        "cultural_preferences": []
    }
    
    # Create user profile
    user_id = user_manager.create_user_profile(user_data)
    
    # Verify that insert_one was called
    assert mock_users.insert_one.called
    
    # Get the inserted user data
    inserted_data = mock_users.insert_one.call_args[0][0]
    
    # Verify password is hashed with PBKDF2-SHA256
    assert 'password_hash' in inserted_data
    assert 'password' not in inserted_data  # Plain password should not be stored
    
    # Verify the hash format (PBKDF2-SHA256 hashes start with $pbkdf2-sha256$)
    password_hash = inserted_data['password_hash']
    assert password_hash.startswith('$pbkdf2-sha256$')
    
    # Verify the hash can be verified
    assert pbkdf2_sha256.verify("test_password_123", password_hash)
    assert not pbkdf2_sha256.verify("wrong_password", password_hash)
    
    print("✅ Password hashing with PBKDF2-SHA256 verified")
    return True


def test_password_strength_validation():
    """Test that password strength requirements are enforced."""
    print("\n=== Testing Password Strength Validation ===")
    
    # Mock MongoDB client
    mock_client = Mock()
    mock_db = Mock()
    mock_users = Mock()
    mock_client.taste_trails_korea = mock_db
    mock_db.users = mock_users
    
    user_manager = UserProfileManager(mock_client)
    
    # Test weak password (less than 8 characters)
    weak_user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "weak",  # Only 4 characters
        "food_restrictions": [],
        "interests": [],
        "cultural_preferences": []
    }
    
    # Should raise ValueError for weak password
    try:
        user_manager.create_user_profile(weak_user_data)
        assert False, "Should have raised ValueError for weak password"
    except ValueError as e:
        assert "Password must be at least 8 characters long" in str(e)
        print("✅ Password strength validation working")
    
    return True


def test_account_lockout_mechanism():
    """Test account lockout after failed login attempts."""
    print("\n=== Testing Account Lockout Mechanism ===")
    
    # Mock MongoDB client and operations
    mock_client = Mock()
    mock_db = Mock()
    mock_users = Mock()
    mock_client.taste_trails_korea = mock_db
    mock_db.users = mock_users
    
    user_manager = UserProfileManager(mock_client)
    
    # Mock user with failed attempts
    mock_user = {
        '_id': 'test_user_id',
        'username': 'test_user',
        'password_hash': pbkdf2_sha256.hash('correct_password'),
        'failed_login_attempts': 4  # One away from lockout
    }
    
    # Test failed login that should trigger lockout
    result = user_manager.verify_password(mock_user, 'wrong_password')
    
    # Should return False
    assert not result
    
    # Verify update_one was called to increment failed attempts and set lockout
    assert mock_users.update_one.called
    update_call = mock_users.update_one.call_args
    
    # Check that failed_login_attempts was incremented and account_locked_until was set
    update_data = update_call[0][1]['$set']
    assert update_data['failed_login_attempts'] == 5
    assert 'account_locked_until' in update_data
    
    print("✅ Account lockout mechanism working")
    return True


def test_api_key_environment_loading():
    """Test that API keys are loaded from environment variables only."""
    print("\n=== Testing API Key Environment Loading ===")
    
    # Test that config loads from environment variables
    api_keys = ['TASTEDIVE_API_KEY', 'ALGOLIA_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GEMINI_API_KEY']
    
    for key in api_keys:
        # Get value from config
        config_value = config.get(key)
        # Get value directly from environment
        env_value = os.getenv(key)
        
        # They should match (both could be None if not set)
        assert config_value == env_value, f"Config value for {key} doesn't match environment"
    
    # Test that config doesn't have hardcoded API keys
    config_dict = config.config
    for key, value in config_dict.items():
        if 'API_KEY' in key and value:
            # API keys should not be hardcoded strings (they should come from env)
            assert not value.startswith('sk-') or not value.startswith('AIza'), f"Possible hardcoded API key: {key}"
    
    print("✅ API keys loaded from environment variables only")
    return True


def test_session_security_configuration():
    """Test that session security is properly configured."""
    print("\n=== Testing Session Security Configuration ===")
    
    # Import app to check session configuration
    from app import app
    
    # Check session cookie security settings
    with app.app_context():
        # In development, secure should be False, in production True
        expected_secure = not config.is_development()
        assert app.config.get('SESSION_COOKIE_SECURE') == expected_secure
        
        # HTTPOnly should always be True
        assert app.config.get('SESSION_COOKIE_HTTPONLY') == True
        
        # SameSite should be set for CSRF protection
        assert app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'
        
        # Session lifetime should be configured
        assert 'PERMANENT_SESSION_LIFETIME' in app.config
        lifetime = app.config['PERMANENT_SESSION_LIFETIME']
        assert isinstance(lifetime, timedelta)
        assert lifetime.total_seconds() > 0
    
    print("✅ Session security configuration verified")
    return True


def test_security_validation():
    """Test the security validation method."""
    print("\n=== Testing Security Validation ===")
    
    # Mock MongoDB client
    mock_client = Mock()
    mock_db = Mock()
    mock_users = Mock()
    mock_client.taste_trails_korea = mock_db
    mock_db.users = mock_users
    
    user_manager = UserProfileManager(mock_client)
    
    # Run security validation
    validation_result = user_manager.validate_security_configuration()
    
    # Check that validation returns expected structure
    assert 'secure' in validation_result
    assert 'issues' in validation_result
    assert 'warnings' in validation_result
    assert 'password_hashing' in validation_result
    assert 'session_security' in validation_result
    assert 'account_lockout' in validation_result
    
    # Check that password hashing is correctly identified
    assert validation_result['password_hashing'] == 'PBKDF2-SHA256'
    
    # Check that session security is configured
    assert 'HTTPOnly' in validation_result['session_security']
    
    # Check that account lockout is enabled
    assert 'Enabled' in validation_result['account_lockout']
    
    print("✅ Security validation method working")
    return True


def run_security_tests():
    """Run all security enhancement tests."""
    print("=== Running Security Enhancement Tests ===")
    
    tests = [
        ("PBKDF2-SHA256 Password Hashing", test_password_hashing_pbkdf2_sha256),
        ("Password Strength Validation", test_password_strength_validation),
        ("Account Lockout Mechanism", test_account_lockout_mechanism),
        ("API Key Environment Loading", test_api_key_environment_loading),
        ("Session Security Configuration", test_session_security_configuration),
        ("Security Validation", test_security_validation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n--- Running {test_name} ---")
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with error: {e}")
    
    print(f"\n=== Security Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("✅ All security enhancements are working correctly")
        return 0
    else:
        print("❌ Some security tests failed")
        return 1


if __name__ == "__main__":
    exit_code = run_security_tests()
    exit(exit_code)