#!/usr/bin/env python
"""
LTI Fix Validation Script
Run this after deployment to verify everything is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canvasops.settings')
django.setup()

from django.conf import settings
from django.test import Client

def validate_settings():
    """Validate Django settings for LTI compatibility"""
    print("🔍 Validating Django settings...")
    
    checks = [
        ('SESSION_COOKIE_SAMESITE', 'None'),
        ('SESSION_COOKIE_SECURE', True),
        ('CSRF_COOKIE_SAMESITE', 'None'),
        ('CSRF_COOKIE_SECURE', True),
        ('X_FRAME_OPTIONS', 'ALLOWALL'),
    ]
    
    for setting_name, expected_value in checks:
        actual_value = getattr(settings, setting_name, None)
        if actual_value == expected_value:
            print(f"✅ {setting_name}: {actual_value}")
        else:
            print(f"❌ {setting_name}: Expected {expected_value}, got {actual_value}")

def test_session_endpoint():
    """Test the session debug endpoint"""
    print("\n🧪 Testing session endpoint...")
    
    client = Client()
    try:
        response = client.get('/lti/session-debug/')
        if response.status_code == 200:
            print("✅ Session debug endpoint working")
            data = response.json()
            print(f"   Session key exists: {bool(data.get('session_key'))}")
        else:
            print(f"❌ Session debug endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Session test failed: {e}")

def test_lti_endpoints():
    """Test LTI endpoints are accessible"""
    print("\n🔗 Testing LTI endpoints...")
    
    endpoints = [
        '/lti/login/',
        '/lti/jwks/',
        '/lti/cookie-test/',
    ]
    
    client = Client()
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            if response.status_code in [200, 405]:  # 405 is OK for POST-only endpoints
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == '__main__':
    print("🚀 CanvasOps LTI Fix Validation")
    print("=" * 40)
    
    validate_settings()
    test_session_endpoint()
    test_lti_endpoints()
    
    print("\n📋 Next Steps:")
    print("1. Deploy these changes to Railway")
    print("2. Update environment variables using railway_env_template.txt")
    print("3. Run 'python manage.py migrate' on Railway")
    print("4. Test LTI launch in Canvas") 