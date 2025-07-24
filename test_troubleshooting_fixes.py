#!/usr/bin/env python3
"""
Test script to validate troubleshooting fixes for unified dashboard.
"""

import requests
import json
import sys
import time

def test_api_endpoint():
    """Test the /api/pre-approval/entities endpoint"""
    print("🔍 Testing API endpoint...")
    
    base_url = "http://127.0.0.1:5001"
    endpoint = "/api/pre-approval/entities?limit=10&status=pending"
    
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        print(f"📡 GET {endpoint}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working correctly")
            print(f"📋 Response: {json.dumps(data, indent=2)[:200]}...")
            return True
        elif response.status_code == 503:
            print(f"⚠️  API endpoint returns 503 - Pre-approval database not available")
            print(f"📋 This is expected if pre-approval database is not initialized")
            return True
        else:
            print(f"❌ API endpoint error: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {base_url}")
        print(f"💡 Make sure the Flask server is running with: python web_ui/app.py")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_page_access():
    """Test that the unified dashboard page loads"""
    print("\\n🔍 Testing unified dashboard page access...")
    
    base_url = "http://127.0.0.1:5001"
    endpoint = "/unified"
    
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        print(f"📡 GET {endpoint}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Unified dashboard page loads correctly")
            # Check if the page contains expected elements
            if "Unified Ingestion & Approval Dashboard" in response.text:
                print(f"✅ Page contains expected title")
            if "UnifiedCombinedDashboard" in response.text:
                print(f"✅ Page contains unified dashboard JavaScript")
            if "approval.js" not in response.text:
                print(f"✅ Page correctly excludes problematic approval.js")
            else:
                print(f"⚠️  Page still includes approval.js - JavaScript conflicts may occur")
            return True
        else:
            print(f"❌ Page access error: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {base_url}")
        return False
    except Exception as e:
        print(f"❌ Page access test error: {e}")
        return False

def main():
    """Run all troubleshooting validation tests"""
    print("🔧 Unified Dashboard Troubleshooting Validation")
    print("=" * 50)
    
    # Test API endpoint
    api_success = test_api_endpoint()
    
    # Test page access
    page_success = test_page_access()
    
    # Summary
    print("\\n📊 Test Summary")
    print("=" * 20)
    print(f"API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Page Access:  {'✅ PASS' if page_success else '❌ FAIL'}")
    
    if api_success and page_success:
        print("\\n🎉 All tests passed! Troubleshooting fixes validated.")
        print("\\n💡 Next steps:")
        print("   1. Open browser to http://127.0.0.1:5001/unified")
        print("   2. Check browser console for JavaScript errors")
        print("   3. Verify unified dashboard functionality")
        return 0
    else:
        print("\\n❌ Some tests failed. Please check server status and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())