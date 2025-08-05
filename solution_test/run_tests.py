#!/usr/bin/env python3
"""
Test Runner for ABEND End-to-End Tests

This script runs the complete end-to-end test suite for the ABEND system
using FastAPI TestClient to validate all functionality.

Usage:
    python solution_test/run_tests.py
    
Or with pytest:
    pytest solution_test/test_abend_e2e.py -v
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from solution_test.test_abend_e2e import run_all_tests


def main():
    """Main test runner function."""
    print("ABEND System End-to-End Test Runner")
    print("=" * 40)
    print("Testing complete ABEND workflow including:")
    print("  • ABEND creation and retrieval")
    print("  • Audit log functionality") 
    print("  • API endpoint validation")
    print("  • Error handling")
    print("  • Pagination and filtering")
    print("=" * 40)
    
    try:
        success = run_all_tests()
        
        if success:
            print(f"\n🎉 SUCCESS: All ABEND tests passed!")
            print(f"The ABEND system is working correctly end-to-end.")
            return 0
        else:
            print(f"\n❌ FAILURE: Some tests failed!")
            print(f"Please review the test output and fix any issues.")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test runner failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
