#!/usr/bin/env python3
"""
Test runner for Taste & Trails Korea application.
Runs all tests from the tests directory with proper path setup.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'='*50}")
    print(f"Running: {test_file}")
    print('='*50)
    
    # Set PYTHONPATH to current directory so tests can import utils
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    try:
        result = subprocess.run(
            [sys.executable, f"tests/{test_file}"],
            env=env,
            capture_output=False,
            timeout=30  # 30 second timeout per test
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  Test {test_file} timed out (30s limit)")
        return False
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def main():
    """Run all tests in the tests directory."""
    print("🧪 Taste & Trails Korea Test Runner")
    print("=" * 60)
    
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    # Find all Python test files
    test_files = [f.name for f in tests_dir.glob("test_*.py")]
    
    if not test_files:
        print("❌ No test files found in tests directory!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  📄 {test_file}")
    
    # Run tests
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test(test_file):
            print(f"✅ {test_file} - PASSED")
            passed += 1
        else:
            print(f"❌ {test_file} - FAILED")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total:  {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())