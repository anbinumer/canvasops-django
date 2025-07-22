from pylti1p3.launch_data_storage.base import LaunchDataStorageBase
from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseLaunchDataStorage(LaunchDataStorageBase):
    """
    Alternative launch data storage using database instead of session cookies.
    This bypasses the SameSite cookie restrictions in iframes.
    """
    
    def __init__(self, cache_timeout=3600):
        self.cache_timeout = cache_timeout
    
    def _generate_key(self, key):
        """Generate a unique cache key"""
        return f"lti_launch_data_{hashlib.md5(key.encode()).hexdigest()}"
    
    def can_set_keys_expiration_time(self):
        """Whether this storage can set expiration time"""
        return True
    
    def set_launch_data(self, launch_data_key, launch_data):
        """Store launch data"""
        cache_key = self._generate_key(launch_data_key)
        logger.info(f"Storing launch data with key: {cache_key}")
        
        try:
            # Store as JSON string to ensure it's serializable
            serialized_data = json.dumps(launch_data)
            cache.set(cache_key, serialized_data, self.cache_timeout)
            logger.info(f"Successfully stored launch data for key: {launch_data_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store launch data: {e}")
            return False
    
    def get_launch_data(self, launch_data_key):
        """Retrieve launch data"""
        cache_key = self._generate_key(launch_data_key)
        logger.info(f"Retrieving launch data with key: {cache_key}")
        
        try:
            serialized_data = cache.get(cache_key)
            if serialized_data:
                launch_data = json.loads(serialized_data)
                logger.info(f"Successfully retrieved launch data for key: {launch_data_key}")
                return launch_data
            else:
                logger.warning(f"No launch data found for key: {launch_data_key}")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve launch data: {e}")
            return None
    
    def set_launch_data_expiration_time(self, launch_data_key, expiration_time):
        """Set expiration time for launch data"""
        cache_key = self._generate_key(launch_data_key)
        
        try:
            # Get existing data
            serialized_data = cache.get(cache_key)
            if serialized_data:
                # Reset with new expiration time
                cache.set(cache_key, serialized_data, expiration_time)
                logger.info(f"Updated expiration time for key: {launch_data_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set expiration time: {e}")
            return False

class StatelessLaunchDataStorage(LaunchDataStorageBase):
    """
    Stateless storage that encodes state in the URL parameters instead of server-side storage.
    This completely bypasses the need for any server-side session storage.
    """
    
    def can_set_keys_expiration_time(self):
        return False
    
    def set_launch_data(self, launch_data_key, launch_data):
        """Store launch data by encoding it in the launch URL"""
        logger.info(f"Encoding launch data in URL for key: {launch_data_key}")
        # In this approach, the data is passed through URL parameters
        # The actual storage happens in the OIDC redirect URL
        return True
    
    def get_launch_data(self, launch_data_key):
        """Retrieve launch data from URL parameters"""
        logger.info(f"Decoding launch data from URL for key: {launch_data_key}")
        # This will be handled by the modified OIDC login flow
        return None
    
    def set_launch_data_expiration_time(self, launch_data_key, expiration_time):
        """Not applicable for stateless storage"""
        return False 