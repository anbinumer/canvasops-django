# Cursor AI Implementation Guide - CanvasOps LTI Security & Cookie Fixes

## 🎯 CRITICAL TASKS - Execute in Order

### TASK 1: IMMEDIATE SECURITY FIX (Priority 1)
**CRITICAL**: Private key is exposed in repository - security breach

- [x] Private key removed from git history and repository

```bash
# 1. Remove private key from git history
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch private.key.b64' --prune-empty --tag-name-filter cat -- --all

# 2. Add to .gitignore
echo "*.key" >> .gitignore
echo "private.key.b64" >> .gitignore
echo ".env" >> .gitignore

# 3. Generate new RSA keys
python manage.py generate_lti_keys --force
```

### TASK 2: FIX COOKIE/IFRAME ISSUE (Priority 1)
**Problem**: LTI launch blocked in Canvas iframe - users forced to open new tab

- [x] Cookie and iframe settings updated in settings.py
- [x] LTI launches now work directly in Canvas iframe

**Replace settings.py with these critical sections:**

```python
# Cookie settings for Canvas iframe compatibility
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True  
SESSION_COOKIE_SAMESITE = 'None'  # CRITICAL for iframe
SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'  # CRITICAL for iframe

# Allow Canvas embedding
X_FRAME_OPTIONS = 'ALLOWALL'

# Trust Canvas domains
CSRF_TRUSTED_ORIGINS = [
    'https://canvas.instructure.com',
    'https://*.instructure.com', 
    'https://aculeo.beta.instructure.com',
    'https://canvasops-django-production.up.railway.app',
]

# Environment variables
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Add this
```

**Update lti/views.py - Add decorators:**

```python
from django.views.decorators.clickjacking import xframe_options_exempt

@csrf_exempt
@xframe_options_exempt  # ADD THIS
def launch(request):
    # Existing code...
    # Add session creation check:
    if not request.session.session_key:
        request.session.create()
    # Rest of existing code...

@csrf_exempt  
@xframe_options_exempt  # ADD THIS
def login(request):
    # Existing code...
```

### TASK 3: ENVIRONMENT VARIABLES (Priority 1)
**Set in Railway dashboard:**

```bash
ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
PRIVATE_KEY_B64=<base64 encode of private.key file>
SECRET_KEY=<new Django secret key>
DEBUG=False
```

### TASK 4: IMPLEMENT SECURITY MODELS (Priority 2)
**Create new files exactly as provided in artifacts:**

1. **Replace `lti/models.py`** with production models artifact
2. **Create `lti/security.py`** from security fixes artifact  
3. **Create `lti/compliance.py`** from compliance artifact
4. **Create `lti/middleware.py`** from middleware artifacts

### TASK 5: DATABASE MIGRATION (Priority 2)
```bash
python manage.py makemigrations
python manage.py migrate
```

### TASK 6: TESTING IMPLEMENTATION (Priority 3)
**Create `tests/test_lti_compliance.py`** from testing artifact

```bash
# Run tests
python manage.py test tests.test_lti_compliance
```

## 📁 FILES TO CREATE/MODIFY

### New Files to Create:
- `lti/security.py` - Security validation & key management
- `lti/compliance.py` - LTI 1.3 compliance features  
- `lti/middleware.py` - Cookie & iframe handling
- `tests/test_lti_compliance.py` - Comprehensive test suite
- `templates/lti/cookie_test.html` - Browser compatibility
- `lti/management/commands/cleanup_lti_sessions.py` - Maintenance

### Files to Modify:
- `lti/models.py` - Replace with production models
- `lti/views.py` - Add decorators & session handling
- `canvasops/settings.py` - Cookie & security settings
- `requirements.txt` - Add cryptography package

### Files to Remove:
- `private.key.b64` - SECURITY BREACH
- Any other `.key` files in repository

## 🔧 SPECIFIC CURSOR AI COMMANDS

### 1. Security Implementation
```
Implement the LTISecurityManager class from the security artifact into lti/security.py. Include all methods for nonce validation, state validation, and input sanitization.
```

### 2. Database Models  
```
Replace the existing lti/models.py with the production-ready models that include proper encryption, indexing, and audit logging.
```

### 3. Middleware Addition
```
Create lti/middleware.py with LTIEmbeddingMiddleware and LTISessionMiddleware classes for handling iframe embedding and cookie compatibility.
```

### 4. View Updates
```
Update lti/views.py to add @xframe_options_exempt decorators and enhance session handling for iframe compatibility.
```

### 5. Settings Configuration
```
Update canvasops/settings.py with production security settings, proper cookie configuration, and middleware order.
```

## ✅ VALIDATION CHECKLIST

After implementation, verify:

- [ ] Private key removed from git history
- [ ] Environment variables set in Railway
- [ ] LTI launch works in Canvas iframe (no "new tab" message)
- [ ] Database migrations successful
- [ ] Tests pass: `python manage.py test`
- [ ] Security scan clean (no exposed secrets)

## 🚨 CRITICAL SUCCESS CRITERIA

1. **Cookie/Iframe Issue Fixed**: LTI launches directly in Canvas without browser warnings
2. **Security Breach Resolved**: No private keys in repository
3. **Database Working**: All migrations apply successfully  
4. **Tests Pass**: Compliance test suite runs without errors

## 📋 IMPLEMENTATION ORDER

1. Fix security breach (remove keys, set env vars)
2. Fix cookie/iframe issue (settings + decorators)
3. Implement new models and security features
4. Run migrations and tests
5. Deploy and verify in Canvas

## 💡 CURSOR AI OPTIMIZATION TIPS

- Use "Apply All" when modifying multiple related files
- Test each priority group before moving to next
- Use git commits between major changes for rollback
- Verify Railway deployment after each priority group
- **NEW:** Always follow the commit-push-deploy cycle for every major change to ensure updates are visible in production.
