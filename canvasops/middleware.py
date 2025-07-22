"""
Django middleware for automatic request tracing.
Integrates with the CanvasOps tracing system.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from django.urls import resolve

from .tracing import tracer, add_metadata, add_event


class TracingMiddleware(MiddlewareMixin):
    """
    Middleware that automatically traces all Django requests.
    Captures request metadata, response status, and timing information.
    """
    
    def process_request(self, request: HttpRequest):
        """Process incoming request and start tracing."""
        # Start timing
        request.start_time = time.time()
        
        # Resolve the view function
        try:
            resolver_match = resolve(request.path_info)
            view_func = resolver_match.func
            view_args = resolver_match.args
            view_kwargs = resolver_match.kwargs
        except Exception:
            view_func = None
            view_args = None
            view_kwargs = None
        
        # Start tracing span
        request.trace_span = tracer.trace_request(
            request, view_func, view_args, view_kwargs
        ).__enter__()
        
        # Add additional request metadata
        add_metadata('request.path', request.path, request.trace_span)
        add_metadata('request.query_params', dict(request.GET), request.trace_span)
        add_metadata('request.content_type', request.content_type, request.trace_span)
        add_metadata('request.content_length', request.content_length, request.trace_span)
        
        # Add user information if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_metadata('user.id', request.user.id, request.trace_span)
            add_metadata('user.username', request.user.username, request.trace_span)
        
        # Add session information
        if hasattr(request, 'session'):
            add_metadata('session.id', request.session.session_key, request.trace_span)
        
        add_event('request.started', {
            'timestamp': request.start_time,
            'method': request.method,
            'path': request.path
        }, request.trace_span)
    
    def process_response(self, request: HttpRequest, response: HttpResponse):
        """Process response and complete tracing."""
        if hasattr(request, 'trace_span'):
            # Calculate request duration
            duration = time.time() - request.start_time
            
            # Add response metadata
            add_metadata('response.status_code', response.status_code, request.trace_span)
            add_metadata('response.content_type', response.get('Content-Type', ''), request.trace_span)
            add_metadata('response.content_length', len(response.content) if hasattr(response, 'content') else 0, request.trace_span)
            add_metadata('request.duration', duration, request.trace_span)
            
            # Add response headers (filtered for sensitive data)
            safe_headers = {
                k: v for k, v in response.items() 
                if k.lower() not in ['authorization', 'cookie', 'set-cookie']
            }
            add_metadata('response.headers', safe_headers, request.trace_span)
            
            # Add event for response completion
            add_event('request.completed', {
                'timestamp': time.time(),
                'duration': duration,
                'status_code': response.status_code
            }, request.trace_span)
            
            # Close the span
            request.trace_span.__exit__(None, None, None)
        
        return response
    
    def process_exception(self, request: HttpRequest, exception):
        """Process exceptions and add error information to trace."""
        if hasattr(request, 'trace_span'):
            # Add exception metadata
            add_metadata('exception.type', type(exception).__name__, request.trace_span)
            add_metadata('exception.message', str(exception), request.trace_span)
            
            # Record the exception in the span
            request.trace_span.record_exception(exception)
            
            # Add error event
            add_event('request.error', {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception)
            }, request.trace_span)
            
            # Close the span
            request.trace_span.__exit__(type(exception), exception, None)
        
        return None 