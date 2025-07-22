"""
Database query tracing utilities for CanvasOps.
Integrates with Django's database operations to trace queries.
"""

import time
import logging
from typing import Optional, Dict, Any
from django.db import connection
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import QuerySet
from django.db.models.sql.query import Query

from .tracing import tracer, add_metadata, add_event, trace_database_query

logger = logging.getLogger(__name__)


class DatabaseQueryTracer:
    """
    Tracer for database queries that integrates with Django's database operations.
    """
    
    def __init__(self):
        self.query_count = 0
        self.total_time = 0.0
    
    def trace_query(self, query: str, params: Optional[tuple] = None, 
                   table: Optional[str] = None, duration: Optional[float] = None):
        """
        Trace a database query with metadata.
        """
        attributes = {
            'db.statement': query,
            'db.type': 'sql',
            'db.query_number': self.query_count,
        }
        
        if params:
            attributes['db.params'] = str(params)
        
        if table:
            attributes['db.table'] = table
        
        if duration:
            attributes['db.duration'] = duration
            self.total_time += duration
        
        self.query_count += 1
        
        with trace_database_query(query, table) as span:
            for key, value in attributes.items():
                add_metadata(key, value, span)
            
            if duration:
                add_event('query.executed', {
                    'duration': duration,
                    'query_number': self.query_count - 1
                }, span)
            
            yield span
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        return {
            'total_queries': self.query_count,
            'total_time': self.total_time,
            'average_time': self.total_time / self.query_count if self.query_count > 0 else 0
        }


# Global database tracer instance
db_tracer = DatabaseQueryTracer()


def trace_queryset(queryset: QuerySet, operation: str = "queryset.operation"):
    """
    Decorator to trace QuerySet operations.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get query information
            query = queryset.query
            sql, params = query.sql_with_params()
            
            # Extract table information
            tables = []
            if hasattr(query, 'tables'):
                tables = list(query.tables)
            elif hasattr(query, 'model'):
                tables = [query.model._meta.db_table]
            
            table = tables[0] if tables else None
            
            # Trace the operation
            with db_tracer.trace_query(sql, params, table) as span:
                add_metadata('queryset.operation', operation, span)
                add_metadata('queryset.model', str(queryset.model), span)
                add_metadata('queryset.tables', tables, span)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    add_metadata('queryset.result_count', len(result) if hasattr(result, '__len__') else 1, span)
                    add_metadata('queryset.duration', duration, span)
                    
                    add_event('queryset.completed', {
                        'operation': operation,
                        'duration': duration,
                        'result_count': len(result) if hasattr(result, '__len__') else 1
                    }, span)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    add_metadata('queryset.error', str(e), span)
                    add_metadata('queryset.duration', duration, span)
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_model_operation(model_class, operation: str):
    """
    Decorator to trace model operations (create, update, delete).
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            table = model_class._meta.db_table
            
            with tracer.span(f"model.{operation}", {
                'db.table': table,
                'model.name': model_class.__name__,
                'model.app': model_class._meta.app_label,
                'operation': operation
            }) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    add_metadata('model.operation.duration', duration, span)
                    add_metadata('model.operation.success', True, span)
                    
                    # Add result metadata
                    if hasattr(result, 'pk'):
                        add_metadata('model.instance.pk', result.pk, span)
                    
                    add_event('model.operation.completed', {
                        'operation': operation,
                        'duration': duration,
                        'model': model_class.__name__
                    }, span)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    add_metadata('model.operation.duration', duration, span)
                    add_metadata('model.operation.success', False, span)
                    add_metadata('model.operation.error', str(e), span)
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


class DatabaseConnectionTracer:
    """
    Tracer for database connection operations.
    """
    
    def __init__(self, db_wrapper: BaseDatabaseWrapper):
        self.db_wrapper = db_wrapper
        self.connection_alias = db_wrapper.alias
    
    def trace_connection(self):
        """Trace database connection operations."""
        with tracer.span("db.connection", {
            'db.alias': self.connection_alias,
            'db.engine': self.db_wrapper.settings_dict.get('ENGINE', ''),
            'db.name': self.db_wrapper.settings_dict.get('NAME', ''),
        }) as span:
            try:
                # Test connection
                with self.db_wrapper.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    add_metadata('db.connection.status', 'connected', span)
                    add_event('db.connection.success', {
                        'alias': self.connection_alias
                    }, span)
            except Exception as e:
                add_metadata('db.connection.status', 'failed', span)
                add_metadata('db.connection.error', str(e), span)
                span.record_exception(e)
                raise


def trace_transaction(operation: str = "transaction"):
    """
    Decorator to trace database transactions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with tracer.span(f"db.transaction.{operation}", {
                'db.transaction.operation': operation,
                'db.transaction.autocommit': connection.autocommit,
            }) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    add_metadata('db.transaction.duration', duration, span)
                    add_metadata('db.transaction.success', True, span)
                    
                    add_event('db.transaction.completed', {
                        'operation': operation,
                        'duration': duration
                    }, span)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    add_metadata('db.transaction.duration', duration, span)
                    add_metadata('db.transaction.success', False, span)
                    add_metadata('db.transaction.error', str(e), span)
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


# Utility functions for common database operations
def trace_create(model_class):
    """Trace model creation operations."""
    return trace_model_operation(model_class, "create")

def trace_update(model_class):
    """Trace model update operations."""
    return trace_model_operation(model_class, "update")

def trace_delete(model_class):
    """Trace model deletion operations."""
    return trace_model_operation(model_class, "delete")

def trace_save(model_class):
    """Trace model save operations."""
    return trace_model_operation(model_class, "save")

def trace_bulk_create(model_class):
    """Trace bulk create operations."""
    return trace_model_operation(model_class, "bulk_create")

def trace_bulk_update(model_class):
    """Trace bulk update operations."""
    return trace_model_operation(model_class, "bulk_update") 