# CanvasOps Tracing Implementation

This document describes the tracing implementation in CanvasOps, which is based on the principles from [Arize's tracing documentation](https://arize.com/docs/ax/observe/tracing/add-metadata/get-the-current-span-context-and-tracer).

## Overview

The tracing system provides comprehensive observability for the CanvasOps Django application, following Arize's best practices for span context management and metadata handling.

## Key Features

### 1. Span Context Management
- **Current Span Access**: Get the current active span and its context
- **Context Propagation**: Automatic context propagation across function calls
- **Nested Spans**: Support for parent-child span relationships

### 2. Metadata Management
- **Rich Metadata**: Add custom attributes to spans
- **Structured Data**: Support for various data types (strings, numbers, booleans)
- **Contextual Information**: User IDs, request IDs, operation parameters

### 3. Event Tracking
- **Milestone Events**: Record important events within spans
- **Timing Information**: Track operation timing and performance
- **Error Events**: Automatic error capture and recording

### 4. Database Integration
- **Query Tracing**: Monitor database query performance
- **Transaction Tracking**: Trace database transactions
- **Model Operations**: Track Django model operations (create, update, delete)

### 5. Request Tracing
- **Automatic Middleware**: Trace all Django requests automatically
- **Request Metadata**: Capture request details, user information, and timing
- **Response Tracking**: Monitor response status and performance

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │    │   Tracing       │    │   Observability │
│                 │    │   System        │    │   Backends      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Views         │───▶│ • CanvasOps     │───▶│ • Jaeger        │
│ • Models        │    │   Tracer        │    │ • Arize         │
│ • Middleware    │    │ • Span Context  │    │ • OTLP          │
│ • Database      │    │ • Metadata      │    │ • Custom        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. CanvasOpsTracer (`canvasops/tracing.py`)
The main tracing class that provides:
- OpenTelemetry integration
- Arize client integration
- Span creation and management
- Metadata and event handling

### 2. TracingMiddleware (`canvasops/middleware.py`)
Django middleware that automatically:
- Traces all HTTP requests
- Captures request/response metadata
- Handles exceptions and errors
- Manages span lifecycle

### 3. DatabaseQueryTracer (`canvasops/db_tracing.py`)
Specialized tracer for database operations:
- Query performance monitoring
- Transaction tracking
- Model operation tracing
- Connection monitoring

## Arize Principles Implementation

### 1. Get Current Span Context
```python
from canvasops.tracing import get_current_span, get_current_span_context

# Get current span (Arize pattern)
current_span = get_current_span()

# Get span context
span_context = get_current_span_context()
```

### 2. Add Metadata to Spans
```python
from canvasops.tracing import add_metadata

# Add metadata to current span
add_metadata("user.id", 123)
add_metadata("operation.type", "create")

# Add metadata to specific span
add_metadata("custom.key", "value", span)
```

### 3. Add Events to Spans
```python
from canvasops.tracing import add_event

# Add event to current span
add_event("user.login", {"user_id": 123, "timestamp": time.time()})

# Add event to specific span
add_event("operation.completed", {"result": "success"}, span)
```

### 4. Span Creation and Management
```python
from canvasops.tracing import tracer

# Create span with context manager
with tracer.span("my.operation") as span:
    add_metadata("operation.data", "example", span)
    # Your code here
    add_event("operation.completed", span=span)
```

## Usage Examples

### Basic View Tracing
```python
from canvasops.tracing import trace_function, add_metadata, add_event

@trace_function("user.profile")
def user_profile(request, user_id):
    add_metadata("user.id", user_id)
    add_event("profile.viewed", {"user_id": user_id})
    
    user = User.objects.get(id=user_id)
    return render(request, 'profile.html', {'user': user})
```

### Database Operation Tracing
```python
from canvasops.db_tracing import trace_create, trace_update

@trace_create(User)
def create_user(username, email):
    return User.objects.create(username=username, email=email)

@trace_update(User)
def update_user(user, **kwargs):
    for key, value in kwargs.items():
        setattr(user, key, value)
    return user.save()
```

### External API Tracing
```python
from canvasops.tracing import tracer

with tracer.trace_external_request("GET", "https://api.example.com/data") as span:
    add_metadata("external.service", "example-api", span)
    response = requests.get("https://api.example.com/data")
    add_metadata("external.response.status", response.status_code, span)
```

## Configuration

### Environment Variables
```bash
# OpenTelemetry
OTLP_ENDPOINT=https://your-otlp-endpoint.com:4317
OTLP_API_KEY=your-otlp-api-key

# Jaeger (development)
JAEGER_HOST=localhost
JAEGER_PORT=6831

# Arize
ARIZE_API_KEY=your-arize-api-key
ARIZE_SPACE_KEY=your-arize-space-key
```

### Django Settings
```python
MIDDLEWARE = [
    'canvasops.middleware.TracingMiddleware',
    # ... other middleware
]
```

## Testing

### Run Tracing Tests
```bash
python manage.py init_tracing --test
```

### Check Configuration
```bash
python manage.py init_tracing --check-config
```

### Run Examples
```bash
python examples/tracing_example.py
```

## Monitoring

### Development
- **Jaeger UI**: `http://localhost:16686`
- **Console Logs**: Check Django logs for tracing information

### Production
- **Arize Dashboard**: View traces in your Arize space
- **OTLP Backend**: Configure your preferred observability platform

## Best Practices

### 1. Span Naming
- Use dot notation: `service.operation.suboperation`
- Be descriptive and consistent
- Include service name prefix

### 2. Metadata
- Include relevant context (user ID, request ID)
- Avoid sensitive data (passwords, tokens)
- Use consistent key naming

### 3. Events
- Record important milestones
- Include timing information
- Use structured data

### 4. Error Handling
- Always record exceptions in spans
- Include error context and stack traces
- Set appropriate span status

## Performance Considerations

- **Minimal Overhead**: <1ms per span typically
- **Sampling**: Configure sampling in production
- **Batch Processing**: Use batch span processors
- **Storage**: Monitor trace storage and retention

## Integration Points

### Django Integration
- Automatic request tracing via middleware
- Database query monitoring
- Model operation tracking

### External Services
- HTTP request tracing
- API call monitoring
- Service-to-service communication

### Custom Applications
- Function-level tracing
- Business logic monitoring
- Performance profiling

## Troubleshooting

### Common Issues
1. **No traces appearing**: Check environment variables and exporter configuration
2. **High latency**: Ensure exporters are properly configured
3. **Missing metadata**: Verify span context is properly managed

### Debug Commands
```bash
# Check configuration
python manage.py init_tracing --check-config

# Test tracing
python manage.py init_tracing --test

# Run examples
python examples/tracing_example.py
```

## Future Enhancements

- **Custom Exporters**: Support for additional observability platforms
- **Advanced Sampling**: Intelligent sampling based on request patterns
- **Metrics Integration**: Correlation between traces and metrics
- **Alerting**: Trace-based alerting and monitoring

## Contributing

When adding new tracing features:
1. Follow Arize principles for span context management
2. Add comprehensive metadata and events
3. Include error handling and status setting
4. Write tests for new functionality
5. Update documentation

## References

- [Arize Tracing Documentation](https://arize.com/docs/ax/observe/tracing/add-metadata/get-the-current-span-context-and-tracer)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Django Middleware](https://docs.djangoproject.com/en/stable/topics/http/middleware/) 