"""
Django management command to initialize and test the tracing system.
"""

import os
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

from canvasops.tracing import tracer, add_metadata, add_event, trace_function
from canvasops.db_tracing import db_tracer, trace_transaction


class Command(BaseCommand):
    help = 'Initialize and test the CanvasOps tracing system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run tracing tests',
        )
        parser.add_argument(
            '--check-config',
            action='store_true',
            help='Check tracing configuration',
        )
    
    def handle(self, *args, **options):
        if options['check_config']:
            self.check_configuration()
        elif options['test']:
            self.run_tests()
        else:
            self.stdout.write(
                self.style.SUCCESS('CanvasOps tracing system initialized successfully!')
            )
            self.check_configuration()
    
    def check_configuration(self):
        """Check tracing configuration and environment."""
        self.stdout.write('Checking tracing configuration...')
        
        # Check environment variables
        env_vars = {
            'OTLP_ENDPOINT': os.getenv('OTLP_ENDPOINT'),
            'OTLP_API_KEY': os.getenv('OTLP_API_KEY'),
            'JAEGER_HOST': os.getenv('JAEGER_HOST'),
            'JAEGER_PORT': os.getenv('JAEGER_PORT'),
            'ARIZE_API_KEY': os.getenv('ARIZE_API_KEY'),
            'ARIZE_SPACE_KEY': os.getenv('ARIZE_SPACE_KEY'),
        }
        
        for var, value in env_vars.items():
            status = '✓' if value else '✗'
            self.stdout.write(f'  {status} {var}: {value or "Not set"}')
        
        # Check tracer status
        current_span = tracer.get_current_span()
        if current_span:
            self.stdout.write(f'  ✓ Current span: {current_span.name}')
        else:
            self.stdout.write('  ✓ No current span (expected)')
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write('  ✓ Database connection: OK')
        except Exception as e:
            self.stdout.write(f'  ✗ Database connection: {e}')
    
    @trace_function("test.tracing")
    def run_tests(self):
        """Run tracing tests."""
        self.stdout.write('Running tracing tests...')
        
        # Test 1: Basic span creation
        with tracer.span("test.basic_span") as span:
            add_metadata("test.type", "basic_span", span)
            add_event("test.started", {"timestamp": time.time()}, span)
            time.sleep(0.1)  # Simulate work
            add_event("test.completed", {"timestamp": time.time()}, span)
        
        self.stdout.write('  ✓ Basic span test completed')
        
        # Test 2: Function tracing
        @trace_function("test.function")
        def test_function():
            time.sleep(0.05)
            return "test_result"
        
        result = test_function()
        self.stdout.write(f'  ✓ Function tracing test completed: {result}')
        
        # Test 3: Database tracing
        @trace_transaction("test.db")
        def test_database():
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                return cursor.fetchone()[0]
        
        try:
            count = test_database()
            self.stdout.write(f'  ✓ Database tracing test completed: {count} migrations')
        except Exception as e:
            self.stdout.write(f'  ✗ Database tracing test failed: {e}')
        
        # Test 4: Error tracing
        @trace_function("test.error")
        def test_error():
            raise ValueError("Test error for tracing")
        
        try:
            test_error()
        except ValueError:
            self.stdout.write('  ✓ Error tracing test completed')
        
        # Test 5: Metadata and events
        with tracer.span("test.metadata") as span:
            add_metadata("user.id", 123, span)
            add_metadata("request.id", "test-request-123", span)
            add_metadata("service.version", "1.0.0", span)
            
            add_event("user.login", {"user_id": 123, "timestamp": time.time()}, span)
            add_event("request.processed", {"request_id": "test-request-123"}, span)
        
        self.stdout.write('  ✓ Metadata and events test completed')
        
        # Test 6: External request tracing
        with tracer.trace_external_request("GET", "https://api.example.com/test") as span:
            add_metadata("external.service", "example-api", span)
            time.sleep(0.02)  # Simulate network delay
            add_event("external.request.completed", {"status": 200}, span)
        
        self.stdout.write('  ✓ External request tracing test completed')
        
        # Display query statistics
        stats = db_tracer.get_query_stats()
        self.stdout.write(f'  📊 Query statistics: {stats}')
        
        self.stdout.write(
            self.style.SUCCESS('All tracing tests completed successfully!')
        ) 