# lti/security.py
from django.conf import settings
from django.core.cache import cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import secrets
import hashlib
import time
import logging
import os

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