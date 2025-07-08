# settings/production.py
import os
from pathlib import Path
from cryptography.fernet import Fernet

# Base settings
from .base import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = [
    'canvasops-django-production.up.railway.app',
    '.up.railway.app',  # Railway subdomains
    'localhost',  # For local testing
]

# Database security
DATABASES['default'].update({
    'CONN_MAX_AGE': 600,
    'OPTIONS': {
        'sslmode': 'require',
    }
})

# LTI-specific security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Session security for LTI
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'  # Required for Canvas iframe
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF protection (with LTI exemptions)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_TRUSTED_ORIGINS = [
    'https://canvas.instructure.com',
    'https://*.instructure.com',
    'https://aculeo.beta.instructure.com',
    'https://canvasops-django-production.up.railway.app',
]

# Content Security Policy for Canvas embedding
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'ALLOWALL'  # Required for Canvas embedding

# Encryption for sensitive data
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is required")

# LTI Configuration
LTI_CONFIG = {
    'tool': {
        'title': 'CanvasOps',
        'description': 'Canvas Automation Tools for Educational Excellence',
        'target_link_uri': 'https://canvasops-django-production.up.railway.app/lti/launch/',
        'oidc_login_url': 'https://canvasops-django-production.up.railway.app/lti/login/',
        'public_jwk_url': 'https://canvasops-django-production.up.railway.app/lti/jwks/',
    },
    'platforms': {
        'https://canvas.instructure.com': {
            'client_id': os.getenv('CANVAS_CLIENT_ID'),
            'auth_login_url': 'https://sso.canvaslms.com/api/lti/authorize_redirect',
            'auth_token_url': 'https://sso.canvaslms.com/login/oauth2/token',
            'key_set_url': 'https://sso.canvaslms.com/api/lti/security/jwks',
            'deployment_ids': os.getenv('CANVAS_DEPLOYMENT_IDS', '').split(','),
        }
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': 'SECURITY {levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'security',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'pylti1p3': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'canvasops.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'canvasops.lti': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'canvasops',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Canvas API configuration
CANVAS_API_CONFIG = {
    'rate_limit': {
        'requests_per_hour': 3000,  # Conservative limit
        'burst_limit': 10,
    },
    'timeout': 30,
    'retries': 3,
    'backoff_factor': 2,
}

# Celery configuration for production
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Email configuration for notifications
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@canvasops.acu.edu')

# Security monitoring
SECURITY_MONITORING = {
    'max_failed_logins': 5,
    'lockout_duration': 300,  # 5 minutes
    'suspicious_activity_threshold': 10,
    'alert_email': os.getenv('SECURITY_ALERT_EMAIL'),
}

# Data retention policies
DATA_RETENTION = {
    'lti_sessions': 30,  # days
    'audit_logs': 90,   # days
    'security_events': 365,  # days
    'execution_logs': 60,   # days
}

# Feature flags
FEATURE_FLAGS = {
    'deep_linking': True,
    'assignment_grade_services': True,
    'names_roles_service': True,
    'submission_review': True,
    'analytics_dashboard': os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true',
    'advanced_security': True,
}

# Middleware with LTI-specific additions
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'lti.middleware.LTISecurityMiddleware',  # Custom LTI security
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'lti.middleware.LTICSRFMiddleware',  # Custom CSRF handling for LTI
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

# Custom middleware for LTI CSRF handling
# lti/middleware.py
class LTICSRFMiddleware:
    """Custom CSRF middleware that exempts LTI endpoints"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Exempt LTI endpoints from CSRF
        if request.path.startswith('/lti/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        response = self.get_response(request)
        return response

# Health check configuration
HEALTH_CHECK = {
    'database': True,
    'cache': True,
    'celery': True,
    'external_apis': ['canvas'],
}

# Static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files with security
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Admin security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')  # Customize admin URL
ADMINS = [
    ('CanvasOps Admin', os.getenv('ADMIN_EMAIL', 'admin@canvasops.acu.edu')),
]
MANAGERS = ADMINS