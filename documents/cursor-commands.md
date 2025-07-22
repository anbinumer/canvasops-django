# Cursor AI Specific Implementation Commands

# IMMEDIATE SECURITY FIX
@cursor: Remove private.key.b64 from repository and git history immediately
- [x] Completed
git rm --cached private.key.b64
git commit -m "Remove exposed private key"

# COOKIE FIX - Update these exact lines in settings.py
@cursor: Replace the session/cookie configuration in canvasops/settings.py with:
- [x] Completed
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'
X_FRAME_OPTIONS = 'ALLOWALL'
CSRF_COOKIE_SAMESITE = 'None'
CSRF_TRUSTED_ORIGINS = ['https://*.instructure.com', 'https://canvasops-django-production.up.railway.app']

# VIEW DECORATORS - Add to lti/views.py
@cursor: Add these imports and decorators to lti/views.py:
- [x] Completed
from django.views.decorators.clickjacking import xframe_options_exempt

@csrf_exempt
@xframe_options_exempt
def launch(request):
    # existing code

@csrf_exempt
@xframe_options_exempt  
def login(request):
    # existing code

# NOTE: Always follow the commit-push-deploy cycle for template/UI changes to ensure updates are visible in production.

# DATABASE MODELS - Replace entire file
@cursor: Replace lti/models.py completely with the production models from the artifacts

# SECURITY MODULE - Create new file
@cursor: Create lti/security.py with the LTISecurityManager class from artifacts

# MIDDLEWARE - Create new file  
@cursor: Create lti/middleware.py with LTIEmbeddingMiddleware class from artifacts

# REQUIREMENTS - Add dependency
@cursor: Add to requirements.txt:
cryptography==41.0.7

# MIGRATION
@cursor: Run these commands in order:
python manage.py makemigrations lti
python manage.py migrate

# ENVIRONMENT SETUP
@cursor: Add these environment variables to Railway:
ENCRYPTION_KEY=<generate_new_key>
PRIVATE_KEY_B64=<base64_encoded_private_key>
DEBUG=False

# TEST VALIDATION
@cursor: Create tests/test_lti_compliance.py from artifacts and run:
python manage.py test tests.test_lti_compliance