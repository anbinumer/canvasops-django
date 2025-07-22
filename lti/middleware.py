# lti/middleware.py
import logging
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class LTIEmbeddingMiddleware(MiddlewareMixin):
    """Middleware to handle iframe embedding for LTI"""
    
    def process_request(self, request):
        """Process LTI requests before they reach views"""
        # Check if this is an LTI request
        is_lti_request = (
            request.path.startswith('/lti/') or 
            'lti_message_hint' in request.GET or
            'lti_message_hint' in request.POST or
            request.GET.get('lti_launch') or
            'iss' in request.POST  # OIDC issuer parameter
        )
        
        if is_lti_request:
            # Mark this as an LTI request for other middleware
            request.lti_embedding = True
            
            # Ensure session exists for LTI requests
            if hasattr(request, 'session'):
                if not request.session.session_key:
                    # Force session creation
                    request.session.create()
                    logger.info(f"LTI: Created session {request.session.session_key}")
                # Log LTI request details
                logger.info(f"LTI Request: {request.method} {request.path}")
                logger.info(f"Session Key: {request.session.session_key}")
            else:
                logger.warning("LTIEmbeddingMiddleware: request.session is not available. Check middleware order.")
    
    def process_response(self, request, response):
        """Add iframe-friendly headers for LTI requests"""
        if hasattr(request, 'lti_embedding'):
            # Remove restrictive headers
            if 'X-Frame-Options' in response:
                del response['X-Frame-Options']
            
            # Add LTI-friendly headers
            response['X-Frame-Options'] = 'ALLOWALL'
            response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'
            
            # Set Content Security Policy for Canvas
            response['Content-Security-Policy'] = (
                "frame-ancestors 'self' https://*.instructure.com https://canvas.instructure.com; "
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:;"
            )
            
            # Ensure SameSite=None for all cookies in LTI context
            if hasattr(response, 'cookies'):
                for cookie in response.cookies.values():
                    cookie['samesite'] = 'None'
                    cookie['secure'] = True
                    # Keep httponly for security except for test cookies
                    if 'test' not in cookie.key.lower():
                        cookie['httponly'] = True
        
        return response

class LTISessionMiddleware(MiddlewareMixin):
    """Enhanced session middleware for LTI compatibility"""
    
    def process_request(self, request):
        """Enhanced session handling for LTI requests"""
        if hasattr(request, 'lti_embedding'):
            if hasattr(request, 'session'):
                # Force session creation if it doesn't exist
                if not request.session.session_key:
                    request.session.create()
                    logger.info(f"LTI Session: Created {request.session.session_key}")
                # Mark session as LTI-compatible
                request.session['lti_compatible'] = True
                request.session.modified = True
                # Log session information for debugging
                logger.debug(f"LTI Session Key: {request.session.session_key}")
                logger.debug(f"LTI Session Data Keys: {list(request.session.keys())}")
            else:
                logger.warning("LTISessionMiddleware: request.session is not available. Check middleware order.")
    
    def process_response(self, request, response):
        """Ensure session cookies are properly set for LTI"""
        if hasattr(request, 'lti_embedding'):
            # Force session save for LTI requests
            if hasattr(request, 'session'):
                request.session.save()
            
            # Set session cookie with proper attributes
            if hasattr(response, 'cookies') and hasattr(request, 'session'):
                session_cookie_name = settings.SESSION_COOKIE_NAME
                if session_cookie_name in response.cookies:
                    cookie = response.cookies[session_cookie_name]
                    cookie['samesite'] = 'None'
                    cookie['secure'] = True
                    cookie['httponly'] = True
                    # Ensure max_age is set for persistence
                    cookie['max_age'] = settings.SESSION_COOKIE_AGE
        
        return response

class LTISecurityMiddleware(MiddlewareMixin):
    """Security middleware specifically for LTI requests"""
    
    def process_request(self, request):
        """Add security context for LTI requests"""
        if hasattr(request, 'lti_embedding'):
            # Add Canvas-specific security context
            request.canvas_integration = True
            
            # Validate Canvas origins if in production
            if not settings.DEBUG:
                referer = request.META.get('HTTP_REFERER', '')
                if referer and 'instructure.com' not in referer:
                    logger.warning(f"LTI request from unexpected referer: {referer}")
    
    def process_response(self, request, response):
        """Add security headers for LTI responses"""
        if hasattr(request, 'lti_embedding'):
            # Add security headers
            response['Referrer-Policy'] = 'no-referrer-when-downgrade'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Remove potentially problematic headers for iframe embedding
            headers_to_remove = [
                'X-Frame-Options',  # Will be re-added with ALLOWALL
                'Strict-Transport-Security'  # Can cause issues in some iframe contexts
            ]
            
            for header in headers_to_remove:
                if header in response:
                    del response[header]
        
        return response 