# lti/middleware.py
import logging
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.clickjacking import xframe_options_exempt

logger = logging.getLogger(__name__)

class LTIEmbeddingMiddleware(MiddlewareMixin):
    """Middleware to handle iframe embedding for LTI"""
    
    def process_response(self, request, response):
        # Allow embedding in iframes for LTI endpoints
        if hasattr(request, 'resolver_match') and request.resolver_match:
            url_name = request.resolver_match.url_name
            if url_name and url_name.startswith('lti_'):
                # Remove X-Frame-Options header for LTI endpoints
                if 'X-Frame-Options' in response:
                    del response['X-Frame-Options']
                
                # Set additional headers for iframe compatibility
                response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
                response['Cross-Origin-Resource-Policy'] = 'cross-origin'
        
        return response

class LTISessionMiddleware(MiddlewareMixin):
    """Enhanced session middleware for LTI compatibility"""
    
    def process_request(self, request):
        # Enhanced session handling for LTI requests
        if self._is_lti_request(request):
            # Force session creation if it doesn't exist
            if not hasattr(request, 'session') or not request.session.session_key:
                request.session.create()
            
            # Log session information for debugging
            logger.debug(f"LTI Session Key: {request.session.session_key}")
            logger.debug(f"LTI Session Data: {dict(request.session)}")
    
    def process_response(self, request, response):
        if self._is_lti_request(request):
            # Ensure cookies are set with proper attributes for iframe
            if hasattr(response, 'cookies'):
                for cookie in response.cookies.values():
                    cookie['samesite'] = 'None'
                    cookie['secure'] = True
                    cookie['httponly'] = True
        
        return response
    
    def _is_lti_request(self, request):
        """Check if this is an LTI-related request"""
        return (
            request.path.startswith('/lti/') or 
            'lti' in request.path or
            request.GET.get('lti_message_hint') or
            request.POST.get('lti_message_hint')
        ) 