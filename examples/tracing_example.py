"""
Example script demonstrating CanvasOps tracing functionality.
Run this script to see tracing in action.
"""

import os
import time
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canvasops.settings')
django.setup()

from canvasops.tracing import (
    tracer, add_metadata, add_event, trace_function, 
    get_current_span, get_current_span_context
)
from canvasops.db_tracing import (
    trace_queryset, trace_create, trace_update, trace_delete, trace_transaction
)


def example_basic_tracing():
    """Example of basic span creation and metadata addition."""
    print("=== Basic Tracing Example ===")
    
    with tracer.span("example.basic_operation") as span:
        # Add metadata to the span
        add_metadata("user.id", 123, span)
        add_metadata("operation.type", "example", span)
        add_metadata("service.version", "1.0.0", span)
        
        # Add events
        add_event("operation.started", {"timestamp": time.time()}, span)
        
        # Simulate some work
        time.sleep(0.1)
        
        # Add more events
        add_event("operation.processing", {"step": "data_processing"}, span)
        
        # Simulate more work
        time.sleep(0.05)
        
        # Add completion event
        add_event("operation.completed", {"result": "success"}, span)
        
        print("✓ Basic tracing completed")


@trace_function("example.function_tracing")
def example_function_tracing():
    """Example of function tracing with decorator."""
    print("=== Function Tracing Example ===")
    
    # This function is automatically traced
    time.sleep(0.05)
    
    # Add custom metadata to the current span
    current_span = get_current_span()
    if current_span:
        add_metadata("function.custom_data", "example_value", current_span)
        add_event("function.custom_event", {"data": "example"})
    
    print("✓ Function tracing completed")
    return "function_result"


def example_error_tracing():
    """Example of error tracing."""
    print("=== Error Tracing Example ===")
    
    @trace_function("example.error_function")
    def function_with_error():
        # Simulate an error
        raise ValueError("This is a test error for tracing")
    
    try:
        function_with_error()
    except ValueError as e:
        print(f"✓ Error caught and traced: {e}")


def example_external_request():
    """Example of external request tracing."""
    print("=== External Request Tracing Example ===")
    
    with tracer.trace_external_request("GET", "https://api.example.com/data") as span:
        add_metadata("external.service", "example-api", span)
        add_metadata("external.endpoint", "/data", span)
        
        # Simulate network request
        time.sleep(0.02)
        
        # Simulate response
        add_metadata("external.response.status", 200, span)
        add_metadata("external.response.size", 1024, span)
        
        add_event("external.request.completed", {
            "status": 200,
            "duration": 0.02
        }, span)
    
    print("✓ External request tracing completed")


def example_database_tracing():
    """Example of database operation tracing."""
    print("=== Database Tracing Example ===")
    
    @trace_transaction("example.db_operation")
    def database_operation():
        # Simulate database query
        time.sleep(0.01)
        return "query_result"
    
    try:
        result = database_operation()
        print(f"✓ Database operation completed: {result}")
    except Exception as e:
        print(f"✗ Database operation failed: {e}")


def example_span_context():
    """Example of span context management (Arize pattern)."""
    print("=== Span Context Example ===")
    
    # Get current span context
    current_span = get_current_span()
    span_context = get_current_span_context()
    
    if current_span:
        print(f"Current span: {current_span.name}")
        add_metadata("context.example", "span_context_demo", current_span)
        add_event("context.accessed", {"timestamp": time.time()})
    
    if span_context:
        print(f"Span context trace ID: {span_context.trace_id}")
        print(f"Span context span ID: {span_context.span_id}")
    
    print("✓ Span context example completed")


def example_nested_spans():
    """Example of nested spans."""
    print("=== Nested Spans Example ===")
    
    with tracer.span("example.parent_operation") as parent_span:
        add_metadata("parent.level", "root", parent_span)
        add_event("parent.started", {"level": "root"})
        
        # Nested span 1
        with tracer.span("example.child_operation_1") as child1_span:
            add_metadata("child.level", "first", child1_span)
            add_event("child.started", {"level": "first"})
            time.sleep(0.02)
            add_event("child.completed", {"level": "first"})
        
        # Nested span 2
        with tracer.span("example.child_operation_2") as child2_span:
            add_metadata("child.level", "second", child2_span)
            add_event("child.started", {"level": "second"})
            time.sleep(0.03)
            add_event("child.completed", {"level": "second"})
        
        add_event("parent.completed", {"level": "root"})
    
    print("✓ Nested spans example completed")


def main():
    """Run all tracing examples."""
    print("CanvasOps Tracing Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_tracing()
        example_function_tracing()
        example_error_tracing()
        example_external_request()
        example_database_tracing()
        example_span_context()
        example_nested_spans()
        
        print("\n" + "=" * 50)
        print("All tracing examples completed successfully!")
        print("\nCheck your tracing backend (Jaeger/Arize) to see the traces.")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure Django is properly configured and tracing is initialized.")


if __name__ == "__main__":
    main() 