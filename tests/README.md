# Tests Directory

This directory contains all test files for the Taste & Trails Korea application.

## Test Files

- `integration_test.py` - Integration tests for service coordination
- `template_test.py` - Template rendering and data structure tests
- `test_core_integration.py` - Core system integration tests
- `test_fixes.py` - Tests for bug fixes and error handling
- `test_map_enhancements.py` - Google Maps service tests
- `test_security_enhancements.py` - Security and authentication tests
- `test_services.py` - API service integration tests
- `test_ui_fixes.py` - UI functionality tests
- `test_user_profile_manager.py` - User profile management tests

## Running Tests

### Individual Tests
```bash
# Run from project root
python tests/test_services.py
python tests/test_ui_fixes.py
```

### All Tests
```bash
# Run from project root
python run_tests.py
```

### With Environment Setup
```bash
# Set Python path and run
PYTHONPATH=. python tests/test_services.py
```

## Test Requirements

All tests require:
- Python 3.8+
- All dependencies from `requirements.txt`
- Proper environment variables in `.env` file
- MongoDB running (for integration tests)
- Internet connection (for API tests)

## Notes

- Tests automatically add the parent directory to Python path
- Some tests make actual API calls and may take time
- UI tests require the Flask application to be running
- Integration tests verify the complete system functionality