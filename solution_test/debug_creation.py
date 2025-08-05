#!/usr/bin/env python3
"""
Test just the ABEND creation to validate our fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_abend_e2e import TestABENDEndToEnd

def test_creation_only():
    """Test only ABEND creation to validate our fixes"""
    test_instance = TestABENDEndToEnd()
    
    try:
        print("🧪 Testing ABEND creation...")
        tracking_id = test_instance.test_abend_creation_flow()
        print(f"✅ ABEND created successfully: {tracking_id}")
        
        print("\n🧪 Testing error handling...")
        test_instance.test_error_handling()
        print("✅ Error handling test passed")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_creation_only()
    print(f"\n🎯 {'Success!' if success else 'Failed!'}")
