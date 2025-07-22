import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']  # Railway handles domain routing

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lti',
    'tools',
    'tasks',
]

# CRITICAL: Proper middleware ordering for LTI
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # LTI middleware that does NOT access request.session
    'lti.middleware.LTIEmbeddingMiddleware',
    # Session middleware must come BEFORE any middleware that uses request.session
    'django.contrib.sessions.middleware.SessionMiddleware',
    # LTI middleware that needs request.session
    'lti.middleware.LTISessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # LTI security middleware (if it does not use request.session, can be here)
    'lti.middleware.LTISecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'canvasops.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'canvasops.wsgi.application'

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PGDATABASE'),
            'USER': os.getenv('PGUSER'),
            'PASSWORD': os.getenv('PGPASSWORD'),
            'HOST': os.getenv('PGHOST'),
            'PORT': os.getenv('PGPORT', '5432'),
        }
    }

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Cache configuration for LTI data storage
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'canvasops',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# CRITICAL: Session configuration for LTI iframe compatibility
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use DB for reliability
SESSION_COOKIE_NAME = 'canvasops_sessionid'  # Unique name to avoid conflicts
SESSION_COOKIE_SECURE = True  # HTTPS required
SESSION_COOKIE_HTTPONLY = True  # Security
SESSION_COOKIE_SAMESITE = 'None'  # CRITICAL for iframe embedding
SESSION_COOKIE_AGE = 7200  # 2 hours (longer than default for LTI sessions)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep sessions persistent
SESSION_SAVE_EVERY_REQUEST = True  # Ensure session persistence
SESSION_COOKIE_DOMAIN = None  # Let Django handle this

# CSRF protection with LTI considerations
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_HTTPONLY = False  # Needed for AJAX requests
CSRF_USE_SESSIONS = True  # Store CSRF tokens in session for iframe compatibility

# Canvas domains to trust
CSRF_TRUSTED_ORIGINS = [
    'https://canvasops-django-production.up.railway.app',
    'https://canvas.instructure.com',
    'https://*.instructure.com',
    'https://aculeo.test.instructure.com',
    'https://*.beta.instructure.com',
    'https://canvas.beta.instructure.com',
]

# Security headers for iframe embedding
X_FRAME_OPTIONS = 'ALLOWALL'  # Allow Canvas iframe embedding
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Production security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    SECURE_HSTS_SECONDS = 0  # Disabled for LTI compatibility
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# Logging configuration for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'lti_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'lti': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'pylti1p3': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# LTI specific settings
LTI_CONFIG = {
    'https://aculeo.test.instructure.com': {
        'default': True,
        'client_id': os.getenv('CANVAS_CLIENT_ID'),
        'auth_login_url': 'https://aculeo.test.instructure.com/api/lti/authorize_redirect',
        'auth_token_url': 'https://aculeo.test.instructure.com/login/oauth2/token',
        'auth_audience': None,
        'key_set_url': 'https://aculeo.test.instructure.com/api/lti/security/jwks',
        'key_set': None,
        'private_key_file': 'private.key',
        'public_key_file': 'public.key',
        'deployment_ids': [os.getenv('CANVAS_DEPLOYMENT_ID')]
    },
}

# LTI 1.3 Configuration file
LTI_TOOL_CONFIG = os.path.join(BASE_DIR, 'lti_config.json')

# Environment variables validation
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY and not DEBUG:
    raise ValueError("ENCRYPTION_KEY environment variable is required in production")

# Canvas API configuration
CANVAS_CLIENT_ID = os.getenv('CANVAS_CLIENT_ID')
CANVAS_DEPLOYMENT_ID = os.getenv('CANVAS_DEPLOYMENT_ID')
CANVAS_INSTANCE_URL = os.getenv('CANVAS_INSTANCE_URL', 'https://aculeo.test.instructure.com')

if not CANVAS_CLIENT_ID:
    print("WARNING: CANVAS_CLIENT_ID not set")
if not CANVAS_DEPLOYMENT_ID:
    print("WARNING: CANVAS_DEPLOYMENT_ID not set")

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True