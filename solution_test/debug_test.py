#!/usr/bin/env python3
"""
Debug individual test methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_abend_e2e import TestABENDEndToEnd

def run_single_test():
    """Run a single test for debugging"""
    test_instance = TestABENDEndToEnd()
    
    try:
        print("🧪 Running test_abend_creation_flow")
        result = test_instance.test_abend_creation_flow()
        print(f"✅ Test passed! Tracking ID: {result}")
        return result
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    tracking_id = run_single_test()
    if tracking_id:
        print(f"\n🎯 Success! Created ABEND with tracking ID: {tracking_id}")
    else:
        print("\n❌ Test failed!")
