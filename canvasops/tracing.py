"""
Tracing implementation based on Arize principles.
Provides span context management and tracer utilities for CanvasOps.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.context import Context
from opentelemetry.trace.span import SpanContext
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

# Arize integration
try:
    from arize import Client
    from arize.trace import Tracer as ArizeTracer
    ARIZE_AVAILABLE = True
except ImportError:
    ARIZE_AVAILABLE = False
    Client = None
    ArizeTracer = None

logger = logging.getLogger(__name__)

class CanvasOpsTracer:
    """
    CanvasOps tracing implementation following Arize principles.
    Provides span context management and metadata handling.
    """
    
    def __init__(self, service_name: str = "canvasops", environment: str = "development"):
        self.service_name = service_name
        self.environment = environment
        self.tracer_provider = None
        self.tracer = None
        self.arize_tracer = None
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing with Arize integration."""
        # Initialize tracer provider
        self.tracer_provider = TracerProvider()
        
        # Configure exporters based on environment
        exporters = []
        
        # OTLP exporter for production
        if os.getenv('OTLP_ENDPOINT'):
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv('OTLP_ENDPOINT'),
                headers={
                    'Authorization': f"Bearer {os.getenv('OTLP_API_KEY', '')}"
                }
            )
            exporters.append(otlp_exporter)
        
        # Jaeger exporter for development
        if self.environment == 'development' or os.getenv('JAEGER_ENDPOINT'):
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv('JAEGER_HOST', 'localhost'),
                agent_port=int(os.getenv('JAEGER_PORT', 6831))
            )
            exporters.append(jaeger_exporter)
        
        # Add span processors
        for exporter in exporters:
            self.tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set the tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get the tracer
        self.tracer = trace.get_tracer(self.service_name)
        
        # Initialize Arize tracer if available
        if ARIZE_AVAILABLE and os.getenv('ARIZE_API_KEY'):
            try:
                arize_client = Client(
                    api_key=os.getenv('ARIZE_API_KEY'),
                    space_key=os.getenv('ARIZE_SPACE_KEY', 'default')
                )
                self.arize_tracer = ArizeTracer(arize_client)
                logger.info("Arize tracing initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Arize tracing: {e}")
    
    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return trace.get_current_span()
    
    def get_current_span_context(self) -> Optional[SpanContext]:
        """Get the current span context."""
        current_span = self.get_current_span()
        return current_span.get_span_context() if current_span else None
    
    def get_tracer(self) -> trace.Tracer:
        """Get the OpenTelemetry tracer."""
        return self.tracer
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Create a span with the given name and attributes.
        Follows Arize span context management principles.
        """
        if attributes is None:
            attributes = {}
        
        # Add service and environment attributes
        attributes.update({
            'service.name': self.service_name,
            'service.environment': self.environment,
        })
        
        with self.tracer.start_as_current_span(name, attributes=attributes) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def add_metadata(self, key: str, value: Any, span: Optional[Span] = None):
        """
        Add metadata to a span.
        If no span is provided, uses the current span.
        """
        target_span = span or self.get_current_span()
        if target_span:
            target_span.set_attribute(key, value)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None, span: Optional[Span] = None):
        """
        Add an event to a span.
        If no span is provided, uses the current span.
        """
        target_span = span or self.get_current_span()
        if target_span:
            target_span.add_event(name, attributes or {})
    
    def set_status(self, status: Status, span: Optional[Span] = None):
        """
        Set the status of a span.
        If no span is provided, uses the current span.
        """
        target_span = span or self.get_current_span()
        if target_span:
            target_span.set_status(status)
    
    def trace_function(self, name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """
        Decorator to trace function execution.
        Automatically captures function metadata and execution time.
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                func_attributes = attributes or {}
                
                # Add function metadata
                func_attributes.update({
                    'function.name': func.__name__,
                    'function.module': func.__module__,
                    'function.args_count': len(args),
                    'function.kwargs_count': len(kwargs),
                })
                
                with self.span(span_name, func_attributes) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            return wrapper
        return decorator
    
    def trace_request(self, request, view_func=None, view_args=None, view_kwargs=None):
        """
        Trace Django request processing.
        Captures request metadata and view information.
        """
        attributes = {
            'http.method': request.method,
            'http.url': request.get_full_path(),
            'http.user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'http.remote_addr': request.META.get('REMOTE_ADDR', ''),
            'http.host': request.META.get('HTTP_HOST', ''),
        }
        
        if view_func:
            attributes.update({
                'view.function': view_func.__name__,
                'view.module': view_func.__module__,
            })
        
        if view_args:
            attributes['view.args'] = str(view_args)
        
        if view_kwargs:
            attributes['view.kwargs'] = str(view_kwargs)
        
        return self.span(f"django.request.{request.method}", attributes)
    
    def trace_database_query(self, query: str, table: Optional[str] = None):
        """
        Trace database query execution.
        Captures query metadata and performance.
        """
        attributes = {
            'db.statement': query,
            'db.type': 'sql',
        }
        
        if table:
            attributes['db.table'] = table
        
        return self.span("db.query", attributes)
    
    def trace_external_request(self, method: str, url: str, service: Optional[str] = None):
        """
        Trace external HTTP requests.
        Captures request metadata and service information.
        """
        attributes = {
            'http.method': method,
            'http.url': url,
            'http.target': url,
        }
        
        if service:
            attributes['service.name'] = service
        
        return self.span(f"http.request.{method}", attributes)

# Global tracer instance
tracer = CanvasOpsTracer()

# Convenience functions following Arize patterns
def get_current_span() -> Optional[Span]:
    """Get the current active span."""
    return tracer.get_current_span()

def get_current_span_context() -> Optional[SpanContext]:
    """Get the current span context."""
    return tracer.get_current_span_context()

def get_tracer() -> trace.Tracer:
    """Get the OpenTelemetry tracer."""
    return tracer.get_tracer()

def add_metadata(key: str, value: Any, span: Optional[Span] = None):
    """Add metadata to a span."""
    tracer.add_metadata(key, value, span)

def add_event(name: str, attributes: Optional[Dict[str, Any]] = None, span: Optional[Span] = None):
    """Add an event to a span."""
    tracer.add_event(name, attributes, span)

def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace function execution."""
    return tracer.trace_function(name, attributes)

def trace_request(request, view_func=None, view_args=None, view_kwargs=None):
    """Trace Django request processing."""
    return tracer.trace_request(request, view_func, view_args, view_kwargs)

def trace_database_query(query: str, table: Optional[str] = None):
    """Trace database query execution."""
    return tracer.trace_database_query(query, table)

def trace_external_request(method: str, url: str, service: Optional[str] = None):
    """Trace external HTTP requests."""
    return tracer.trace_external_request(method, url, service) 