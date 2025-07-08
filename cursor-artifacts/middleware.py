# lti/middleware.py - Cookie and iframe handling for LTI

import logging
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)

class LTIEmbeddingMiddleware:
    """Middleware to handle LTI embedding and cookie issues"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an LTI request
        is_lti_request = (
            request.path.startswith('/lti/') or 
            request.GET.get('lti_launch') or
            'lti' in request.session
        )
        
        if is_lti_request:
            # Add LTI-specific headers before processing
            request.lti_embedding = True
            
            # Handle cookie test for iframe compatibility
            if request.path == '/lti/cookie-test/':
                return self.handle_cookie_test(request)
        
        response = self.get_response(request)
        
        # Add iframe-friendly headers for LTI requests
        if hasattr(request, 'lti_embedding'):
            response['X-Frame-Options'] = 'ALLOWALL'
            response['Content-Security-Policy'] = (
                "frame-ancestors 'self' https://*.instructure.com https://canvas.instructure.com"
            )
            
            # Ensure SameSite=None for all cookies in LTI context
            if hasattr(response, 'cookies'):
                for cookie in response.cookies.values():
                    cookie['samesite'] = 'None'
                    cookie['secure'] = True
        
        return response
    
    def handle_cookie_test(self, request):
        """Handle cookie compatibility test for browsers"""
        if request.method == 'POST':
            # Test if cookies work in iframe
            test_cookie_name = 'lti_cookie_test'
            test_cookie_value = 'test_value'
            
            # Try to set and read a test cookie
            response = HttpResponse('Cookie test successful')
            response.set_cookie(
                test_cookie_name, 
                test_cookie_value,
                secure=True,
                samesite='None',
                httponly=False
            )
            
            # Log the test for debugging
            logger.info(f"Cookie test for IP: {request.META.get('REMOTE_ADDR')}")
            
            return response
        
        # Show cookie test page
        return render(request, 'lti/cookie_test.html')

class LTISessionMiddleware:
    """Enhanced session handling for LTI context"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # For LTI requests, ensure session works in iframe
        if hasattr(request, 'lti_embedding'):
            # Force session creation if it doesn't exist
            if not request.session.session_key:
                request.session.create()
            
            # Mark session as LTI-compatible
            request.session['lti_compatible'] = True
            request.session.modified = True
        
        response = self.get_response(request)
        return response

# Add to MIDDLEWARE in settings.py:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'lti.middleware.LTIEmbeddingMiddleware',  # Add this first
    'django.contrib.sessions.middleware.SessionMiddleware',
    'lti.middleware.LTISessionMiddleware',     # Add this after sessions
    'django.middleware.common.CommonMiddleware',
    'lti.middleware.LTICSRFMiddleware',        # Custom CSRF handling
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]