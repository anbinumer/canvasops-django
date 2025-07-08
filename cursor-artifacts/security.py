# lti/security.py
from django.conf import settings
from django.core.cache import cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import secrets
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

class LTISecurityManager:
    """Enhanced security for LTI 1.3 implementation"""
    
    @staticmethod
    def validate_nonce(nonce, max_age=300):
        """Validate nonce to prevent replay attacks"""
        if not nonce:
            raise ValueError("Nonce is required")
        
        cache_key = f"lti_nonce_{hashlib.sha256(nonce.encode()).hexdigest()}"
        
        if cache.get(cache_key):
            raise ValueError("Nonce already used (replay attack)")
        
        # Store nonce with expiration
        cache.set(cache_key, True, max_age)
        return True
    
    @staticmethod
    def validate_state(state, session_state):
        """Validate OIDC state parameter"""
        if not state or not session_state:
            raise ValueError("State validation failed")
        
        if not secrets.compare_digest(state, session_state):
            raise ValueError("Invalid state parameter")
        
        return True
    
    @staticmethod
    def sanitize_launch_data(launch_data):
        """Sanitize and validate launch data before storage"""
        sanitized = {}
        
        # Define allowed fields with validation
        allowed_fields = {
            'sub': str,
            'iss': str,
            'aud': (str, list),
            'exp': int,
            'iat': int,
            'nonce': str,
        }
        
        for field, field_type in allowed_fields.items():
            if field in launch_data:
                value = launch_data[field]
                if isinstance(field_type, tuple):
                    if not any(isinstance(value, t) for t in field_type):
                        logger.warning(f"Invalid type for {field}: {type(value)}")
                        continue
                elif not isinstance(value, field_type):
                    logger.warning(f"Invalid type for {field}: {type(value)}")
                    continue
                
                sanitized[field] = value
        
        return sanitized
    
    @staticmethod
    def validate_audience(aud, expected_client_id):
        """Validate audience claim"""
        if isinstance(aud, str):
            aud = [aud]
        
        if expected_client_id not in aud:
            raise ValueError(f"Invalid audience. Expected {expected_client_id}, got {aud}")
        
        return True
    
    @staticmethod
    def get_private_key():
        """Securely load private key from environment or file"""
        # Try environment variable first (base64 encoded)
        private_key_b64 = os.getenv('PRIVATE_KEY_B64')
        if private_key_b64:
            import base64
            private_key_pem = base64.b64decode(private_key_b64).decode('utf-8')
            return serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None
            )
        
        # Fallback to file (for development only)
        private_key_path = os.path.join(settings.BASE_DIR, 'private.key')
        if not os.path.exists(private_key_path):
            raise FileNotFoundError("Private key not found")
        
        with open(private_key_path, 'rb') as f:
            return serialization.load_pem_private_key(f.read(), password=None)

# lti/middleware.py
from django.http import HttpResponseForbidden
from django.urls import reverse
import re

class LTISecurityMiddleware:
    """Security middleware for LTI endpoints"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.lti_patterns = [
            re.compile(r'^/lti/'),
        ]
    
    def __call__(self, request):
        # Apply security headers for LTI endpoints
        if any(pattern.match(request.path) for pattern in self.lti_patterns):
            request.is_lti_request = True
        
        response = self.get_response(request)
        
        if hasattr(request, 'is_lti_request'):
            # Security headers for LTI
            response['X-Frame-Options'] = 'ALLOWALL'  # Allow Canvas embedding
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'no-referrer-when-downgrade'
        
        return response

# Enhanced views.py security integration
from .security import LTISecurityManager

@csrf_exempt
@require_POST
def enhanced_launch(request):
    """Enhanced secure LTI launch with proper validation"""
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    message_launch = ExtendedDjangoMessageLaunch(
        request,
        tool_conf,
        launch_data_storage=launch_data_storage
    )
    
    try:
        # Validate the launch with enhanced security
        message_launch.validate()
        launch_data = message_launch.get_launch_data()
        
        # Enhanced security validations
        LTISecurityManager.validate_nonce(launch_data.get('nonce'))
        LTISecurityManager.validate_audience(
            launch_data.get('aud'), 
            tool_conf.get_client_id()
        )
        
        # Sanitize launch data before storage
        sanitized_data = LTISecurityManager.sanitize_launch_data(launch_data)
        
        # Store sanitized data in session
        request.session['lti_launch_data'] = sanitized_data
        request.session['launch_validated_at'] = time.time()
        
        # Rate limiting per user
        user_id = launch_data.get('sub')
        rate_limit_key = f"lti_rate_limit_{user_id}"
        current_count = cache.get(rate_limit_key, 0)
        
        if current_count >= 10:  # 10 launches per minute
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return HttpResponse("Rate limit exceeded", status=429)
        
        cache.set(rate_limit_key, current_count + 1, 60)
        
        # Continue with normal launch flow
        if message_launch.is_deep_link_launch():
            return redirect('lti_configure')
        
        return redirect('/tool_selection/')
        
    except ValueError as e:
        logger.error(f"LTI security validation failed: {e}")
        return HttpResponse(f"Security validation failed: {str(e)}", status=400)
    except LtiException as e:
        logger.error(f"LTI launch failed: {e}")
        return HttpResponse(f"LTI launch failed: {str(e)}", status=400)
    except Exception as e:
        logger.error(f"Unexpected launch error: {e}")
        return HttpResponse("Launch failed", status=500)