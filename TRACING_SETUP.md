# CanvasOps Tracing Setup Guide

This guide explains how to set up and use the tracing system in CanvasOps, which is based on Arize principles and OpenTelemetry.

## Overview

The tracing system provides:
- **Span Context Management**: Track the current span and its context
- **Metadata Addition**: Add custom metadata to spans
- **Event Tracking**: Record events within spans
- **Database Query Tracing**: Monitor database operations
- **Request Tracing**: Automatically trace Django requests
- **Error Tracking**: Capture and trace exceptions

## Environment Variables

Set these environment variables for tracing configuration:

```bash
# OpenTelemetry Configuration
OTLP_ENDPOINT=https://your-otlp-endpoint.com:4317
OTLP_API_KEY=your-otlp-api-key

# Jaeger Configuration (for development)
JAEGER_HOST=localhost
JAEGER_PORT=6831

# Arize Configuration
ARIZE_API_KEY=your-arize-api-key
ARIZE_SPACE_KEY=your-arize-space-key

# Environment
ENVIRONMENT=development
```

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Add the tracing middleware to your Django settings:
```python
MIDDLEWARE = [
    'canvasops.middleware.TracingMiddleware',
    # ... other middleware
]
```

3. Initialize the tracing system:
```bash
python manage.py init_tracing
```

## Usage Examples

### Basic Span Creation

```python
from canvasops.tracing import tracer, add_metadata, add_event

# Create a span
with tracer.span("my.operation") as span:
    # Add metadata
    add_metadata("user.id", 123, span)
    add_metadata("operation.type", "create", span)
    
    # Add events
    add_event("operation.started", {"timestamp": time.time()}, span)
    
    # Your code here
    result = perform_operation()
    
    # Add result metadata
    add_metadata("operation.result", result, span)
    add_event("operation.completed", {"result": result}, span)
```

### Function Tracing

```python
from canvasops.tracing import trace_function

@trace_function("user.create")
def create_user(username, email):
    # Function automatically traced
    user = User.objects.create(username=username, email=email)
    return user
```

### Database Query Tracing

```python
from canvasops.db_tracing import trace_queryset, trace_create, trace_update

# Trace QuerySet operations
@trace_queryset(User.objects.all(), "users.fetch_all")
def get_all_users():
    return list(User.objects.all())

# Trace model operations
@trace_create(User)
def create_user_instance():
    return User.objects.create(username="test")

@trace_update(User)
def update_user(user):
    user.username = "updated"
    return user.save()
```

### Request Tracing

The middleware automatically traces all Django requests. You can add custom metadata:

```python
from canvasops.tracing import add_metadata, add_event

def my_view(request):
    # Add custom request metadata
    add_metadata("custom.param", request.GET.get('param'))
    add_event("custom.event", {"user_id": request.user.id})
    
    # Your view logic
    return response
```

### External Request Tracing

```python
from canvasops.tracing import tracer

with tracer.trace_external_request("GET", "https://api.example.com/data") as span:
    add_metadata("external.service", "example-api", span)
    response = requests.get("https://api.example.com/data")
    add_metadata("external.response.status", response.status_code, span)
```

## Arize Integration

The tracing system integrates with Arize for advanced observability:

1. Set your Arize API key and space key
2. The system will automatically send traces to Arize
3. View traces in the Arize dashboard

### Arize-Specific Features

```python
from canvasops.tracing import get_current_span, get_current_span_context

# Get current span context (Arize pattern)
current_span = get_current_span()
span_context = get_current_span_context()

# Add Arize-specific metadata
add_metadata("arize.feature", "user_management", current_span)
add_metadata("arize.version", "1.0.0", current_span)
```

## Testing the Tracing System

Run the tracing tests:

```bash
python manage.py init_tracing --test
```

Check configuration:

```bash
python manage.py init_tracing --check-config
```

## Monitoring and Debugging

### View Traces in Development

1. **Jaeger UI**: Visit `http://localhost:16686` (if using Jaeger)
2. **Arize Dashboard**: View traces in your Arize space
3. **Console Logs**: Check Django logs for tracing information

### Common Issues

1. **No traces appearing**: Check environment variables and exporter configuration
2. **High latency**: Ensure exporters are properly configured
3. **Missing metadata**: Verify span context is properly managed

## Best Practices

1. **Use Descriptive Span Names**: Use dot notation (e.g., `user.create`, `order.process`)
2. **Add Relevant Metadata**: Include user IDs, request IDs, and operation parameters
3. **Handle Errors Properly**: Always record exceptions in spans
4. **Avoid Sensitive Data**: Don't include passwords or tokens in metadata
5. **Use Events for Milestones**: Record important events within spans

## Performance Considerations

- Tracing adds minimal overhead (typically <1ms per span)
- Use sampling in production to reduce trace volume
- Configure appropriate batch sizes for exporters
- Monitor trace storage and retention policies

## Integration with Existing Code

The tracing system is designed to be non-intrusive. You can:

1. Add tracing to existing views gradually
2. Use decorators for automatic tracing
3. Keep existing error handling intact
4. Maintain backward compatibility

## Advanced Configuration

### Custom Tracer Setup

```python
from canvasops.tracing import CanvasOpsTracer

# Create custom tracer
custom_tracer = CanvasOpsTracer(
    service_name="my-service",
    environment="production"
)
```

### Custom Exporters

```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Add custom exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="custom-jaeger-host",
    agent_port=6831
)
```

## Support

For issues with the tracing system:

1. Check the configuration with `--check-config`
2. Review environment variables
3. Check exporter connectivity
4. Review Django logs for errors
5. Consult Arize documentation for advanced features 