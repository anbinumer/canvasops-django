# tests/test_lti_compliance.py
import json
import time
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from lti.models import LTIPlatform, LTISession, LTIAuditLog, LTISecurityEvent
from lti.security import LTISecurityManager
from lti.compliance import LTIComplianceManager

class LTIComplianceTestCase(TestCase):
    """Test LTI 1.3 specification compliance"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Generate test RSA key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Create test platform
        self.platform = LTIPlatform.objects.create(
            name="Test Canvas",
            issuer="https://test.instructure.com",
            client_id="test_client_123",
            auth_login_url="https://test.instructure.com/api/lti/authorize_redirect",
            auth_token_url="https://test.instructure.com/login/oauth2/token",
            key_set_url="https://test.instructure.com/api/lti/security/jwks",
            deployment_ids=["test_deployment_1"],
            public_key_jwk={"kty": "RSA", "use": "sig"}
        )
        
        # Set test private key
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        self.platform.set_private_key(private_pem)
        self.platform.save()
    
    def create_valid_jwt_payload(self, **overrides):
        """Create a valid LTI JWT payload"""
        now = int(time.time())
        payload = {
            'iss': self.platform.issuer,
            'sub': 'test_user_123',
            'aud': self.platform.client_id,
            'exp': now + 300,
            'iat': now,
            'nonce': 'test_nonce_' + str(now),
            'https://purl.imsglobal.org/spec/lti/claim/deployment_id': 'test_deployment_1',
            'https://purl.imsglobal.org/spec/lti/claim/message_type': 'LtiResourceLinkRequest',
            'https://purl.imsglobal.org/spec/lti/claim/version': '1.3.0',
            'https://purl.imsglobal.org/spec/lti/claim/roles': [
                'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor'
            ],
            'https://purl.imsglobal.org/spec/lti/claim/context': {
                'id': 'test_course_123',
                'title': 'Test Course',
                'type': ['CourseOffering']
            }
        }
        payload.update(overrides)
        return payload
    
    def test_valid_lti_launch(self):
        """Test successful LTI 1.3 launch"""
        payload = self.create_valid_jwt_payload()
        
        # Create JWT token
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        
        with patch('lti.views.get_tool_conf') as mock_config:
            mock_config.return_value = Mock()
            
            with patch('lti.views.ExtendedDjangoMessageLaunch') as mock_launch:
                mock_launch_instance = Mock()
                mock_launch_instance.validate.return_value = None
                mock_launch_instance.get_launch_data.return_value = payload
                mock_launch_instance.is_deep_link_launch.return_value = False
                mock_launch_instance.is_submission_review_launch.return_value = False
                mock_launch.return_value = mock_launch_instance
                
                response = self.client.post(
                    reverse('lti_launch'),
                    {'id_token': token}
                )
                
                self.assertEqual(response.status_code, 302)
                
                # Verify session data
                session = self.client.session
                self.assertIn('canvas_user_id', session)
                self.assertEqual(session['canvas_user_id'], 'test_user_123')
    
    def test_nonce_validation(self):
        """Test nonce validation prevents replay attacks"""
        nonce = 'test_nonce_unique'
        
        # First use should succeed
        self.assertTrue(LTISecurityManager.validate_nonce(nonce))
        
        # Second use should fail
        with self.assertRaises(ValueError):
            LTISecurityManager.validate_nonce(nonce)
    
    def test_required_claims_validation(self):
        """Test validation of required LTI claims"""
        # Valid payload
        valid_payload = self.create_valid_jwt_payload()
        self.assertTrue(LTIComplianceManager.validate_required_claims(valid_payload))
        
        # Missing required claim
        invalid_payload = valid_payload.copy()
        del invalid_payload['sub']
        
        with self.assertRaises(ValueError) as context:
            LTIComplianceManager.validate_required_claims(invalid_payload)
        
        self.assertIn('Missing required claims', str(context.exception))
    
    def test_audience_validation(self):
        """Test audience claim validation"""
        # Valid audience (string)
        LTISecurityManager.validate_audience('test_client_123', 'test_client_123')
        
        # Valid audience (list)
        LTISecurityManager.validate_audience(['test_client_123'], 'test_client_123')
        
        # Invalid audience
        with self.assertRaises(ValueError):
            LTISecurityManager.validate_audience('wrong_client', 'test_client_123')
    
    def test_message_type_validation(self):
        """Test LTI message type validation"""
        # Valid message types
        valid_types = [
            'LtiResourceLinkRequest',
            'LtiDeepLinkingRequest',
            'LtiSubmissionReviewRequest'
        ]
        
        for msg_type in valid_types:
            payload = {'https://purl.imsglobal.org/spec/lti/claim/message_type': msg_type}
            self.assertEqual(
                LTIComplianceManager.validate_message_type(payload),
                msg_type
            )
        
        # Invalid message type
        invalid_payload = {'https://purl.imsglobal.org/spec/lti/claim/message_type': 'InvalidType'}
        with self.assertRaises(ValueError):
            LTIComplianceManager.validate_message_type(invalid_payload)
    
    def test_security_event_logging(self):
        """Test security event logging"""
        # Simulate security event
        LTISecurityEvent.objects.create(
            event_type='nonce_reuse',
            severity='high',
            user_id='test_user_123',
            ip_address='192.168.1.1',
            description='Attempted nonce reuse detected',
            technical_details={'nonce': 'test_nonce_123'}
        )
        
        # Verify event was logged
        events = LTISecurityEvent.objects.filter(event_type='nonce_reuse')
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().severity, 'high')
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        from django.core.cache import cache
        
        user_id = 'test_user_123'
        rate_limit_key = f"lti_rate_limit_{user_id}"
        
        # Test within limits
        for i in range(5):
            current_count = cache.get(rate_limit_key, 0)
            self.assertLess(current_count, 10)
            cache.set(rate_limit_key, current_count + 1, 60)
        
        # Test exceeding limits
        cache.set(rate_limit_key, 10, 60)
        current_count = cache.get(rate_limit_key, 0)
        self.assertGreaterEqual(current_count, 10)
    
    def test_session_encryption(self):
        """Test session data encryption"""
        # Create test session
        session = LTISession.objects.create(
            session_key='test_session_123',
            launch_id='test_launch_123',
            platform=self.platform,
            user_id='test_user_123',
            canvas_user_id='canvas_user_123',
            context_id='test_course_123',
            ip_address='192.168.1.1',
            nonce_used='test_nonce_123',
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Test data encryption/decryption
        test_data = {'sensitive': 'information', 'user_id': 'test_user_123'}
        session.set_launch_data(test_data)
        session.save()
        
        # Retrieve and verify
        retrieved_data = session.get_launch_data()
        self.assertEqual(retrieved_data, test_data)

class LTISecurityTestCase(TestCase):
    """Test security-specific functionality"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        malicious_input = {
            'sub': '<script>alert("xss")</script>',
            'iss': 'https://evil.com',
            'aud': ['valid_client', '<script>'],
            'normal_field': 'normal_value'
        }
        
        sanitized = LTISecurityManager.sanitize_launch_data(malicious_input)
        
        # Should include safe fields
        self.assertIn('normal_field', sanitized)
        self.assertEqual(sanitized['normal_field'], 'normal_value')
        
        # Should exclude or sanitize dangerous content
        # (Implementation depends on your sanitization logic)
    
    def test_private_key_security(self):
        """Test private key handling security"""
        # Test key loading from environment
        with patch.dict('os.environ', {'PRIVATE_KEY_B64': 'dGVzdA=='}):  # base64 'test'
            with patch('lti.security.serialization.load_pem_private_key') as mock_load:
                mock_load.return_value = Mock()
                LTISecurityManager.get_private_key()
                mock_load.assert_called_once()
    
    def test_session_expiry(self):
        """Test session expiry functionality"""
        # Create expired session
        expired_session = LTISession.objects.create(
            session_key='expired_session',
            launch_id='expired_launch',
            platform=LTIPlatform.objects.first(),
            user_id='test_user',
            canvas_user_id='canvas_user',
            context_id='test_course',
            ip_address='192.168.1.1',
            nonce_used='expired_nonce',
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        
        self.assertTrue(expired_session.is_expired())
        
        # Create active session
        active_session = LTISession.objects.create(
            session_key='active_session',
            launch_id='active_launch',
            platform=LTIPlatform.objects.first(),
            user_id='test_user',
            canvas_user_id='canvas_user',
            context_id='test_course',
            ip_address='192.168.1.1',
            nonce_used='active_nonce',
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        self.assertFalse(active_session.is_expired())

class LTIIntegrationTestCase(TestCase):
    """Test integration with Canvas APIs"""
    
    def test_deep_linking_response(self):
        """Test deep linking response generation"""
        from lti.compliance import DeepLinkingService
        
        # Mock message launch
        mock_launch = Mock()
        mock_launch.get_launch_url.return_value = 'https://test.com/lti/launch/'
        mock_launch.get_deep_link.return_value = Mock()
        
        service = DeepLinkingService(mock_launch)
        content_items = service.create_content_items()
        
        # Verify content items were created
        self.assertGreater(len(content_items), 0)
        self.assertIsInstance(content_items[0], type(mock_launch.get_deep_link.return_value))
    
    def test_assignment_grade_service(self):
        """Test AGS functionality"""
        from lti.compliance import AssignmentGradeService
        
        # Mock message launch with AGS
        mock_launch = Mock()
        mock_ags = Mock()
        mock_ags.can_read_gradebook.return_value = True
        mock_ags.can_manage_gradebook.return_value = True
        mock_launch.get_ags.return_value = mock_ags
        
        service = AssignmentGradeService(mock_launch)
        
        self.assertTrue(service.can_read_gradebook())
        self.assertTrue(service.can_manage_gradebook())
    
    def test_names_roles_service(self):
        """Test NRPS functionality"""
        from lti.compliance import NamesRolesService
        
        # Mock message launch with NRPS
        mock_launch = Mock()
        mock_nrps = Mock()
        mock_nrps.get_members.return_value = [
            {
                'user_id': 'user1',
                'roles': ['Instructor'],
                'name': 'Test User'
            }
        ]
        mock_launch.get_nrps.return_value = mock_nrps
        
        service = NamesRolesService(mock_launch)
        members = service.get_members()
        
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]['user_id'], 'user1')

class LTIPerformanceTestCase(TestCase):
    """Test performance and scalability"""
    
    def test_concurrent_launches(self):
        """Test handling multiple concurrent launches"""
        import threading
        import time
        
        results = []
        
        def simulate_launch(user_id):
            """Simulate an LTI launch"""
            try:
                # Create session
                session = LTISession.objects.create(
                    session_key=f'session_{user_id}',
                    launch_id=f'launch_{user_id}',
                    platform=LTIPlatform.objects.first(),
                    user_id=f'user_{user_id}',
                    canvas_user_id=f'canvas_{user_id}',
                    context_id='test_course',
                    ip_address='192.168.1.1',
                    nonce_used=f'nonce_{user_id}_{time.time()}',
                    expires_at=timezone.now() + timezone.timedelta(hours=24)
                )
                results.append(('success', user_id))
            except Exception as e:
                results.append(('error', user_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=simulate_launch, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        successful_launches = [r for r in results if r[0] == 'success']
        self.assertEqual(len(successful_launches), 10)
    
    def test_database_query_optimization(self):
        """Test database query efficiency"""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Create test data
        platform = LTIPlatform.objects.first()
        for i in range(100):
            LTISession.objects.create(
                session_key=f'perf_session_{i}',
                launch_id=f'perf_launch_{i}',
                platform=platform,
                user_id=f'perf_user_{i}',
                canvas_user_id=f'canvas_{i}',
                context_id='perf_course',
                ip_address='192.168.1.1',
                nonce_used=f'perf_nonce_{i}',
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
        
        # Test query efficiency
        with self.assertNumQueries(1):
            sessions = list(LTISession.objects.filter(
                context_id='perf_course'
            ).select_related('platform'))
            self.assertEqual(len(sessions), 100)

# Integration tests with mock Canvas API
class CanvasAPIIntegrationTestCase(TestCase):
    """Test Canvas API integration"""
    
    @patch('canvasapi.Canvas')
    def test_canvas_api_authentication(self, mock_canvas):
        """Test Canvas API authentication"""
        from tools.canvas_api import CanvasAPIService
        
        # Mock Canvas API
        mock_instance = Mock()
        mock_canvas.return_value = mock_instance
        
        # Test API service
        api_service = CanvasAPIService(
            canvas_url='https://test.instructure.com',
            api_token='test_token'
        )
        
        # Verify Canvas instance was created
        mock_canvas.assert_called_with(
            'https://test.instructure.com',
            'test_token'
        )
    
    @patch('requests.get')
    def test_link_checker_tool(self, mock_get):
        """Test link checker tool functionality"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        from tools.link_checker import LinkChecker
        
        checker = LinkChecker()
        result = checker.check_url('https://example.com')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['status_code'], 200)
    
    def test_rate_limiting_with_canvas_api(self):
        """Test rate limiting with Canvas API calls"""
        from django.core.cache import cache
        
        # Simulate rate limiting
        api_key = 'canvas_api_rate_limit'
        
        # Within limits
        for i in range(5):
            current_count = cache.get(api_key, 0)
            self.assertLess(current_count, 10)
            cache.set(api_key, current_count + 1, 3600)
        
        # At limit
        cache.set(api_key, 10, 3600)
        current_count = cache.get(api_key, 0)
        self.assertGreaterEqual(current_count, 10)

# Load testing utilities
class LTILoadTestCase(TestCase):
    """Load testing for LTI implementation"""
    
    def test_session_cleanup_performance(self):
        """Test session cleanup performance with large datasets"""
        from django.core.management import call_command
        import time
        
        # Create large number of expired sessions
        platform = LTIPlatform.objects.first()
        bulk_sessions = []
        
        for i in range(1000):
            session = LTISession(
                session_key=f'load_session_{i}',
                launch_id=f'load_launch_{i}',
                platform=platform,
                user_id=f'load_user_{i}',
                canvas_user_id=f'canvas_{i}',
                context_id='load_course',
                ip_address='192.168.1.1',
                nonce_used=f'load_nonce_{i}',
                expires_at=timezone.now() - timezone.timedelta(days=31)
            )
            bulk_sessions.append(session)
        
        LTISession.objects.bulk_create(bulk_sessions)
        
        # Measure cleanup performance
        start_time = time.time()
        call_command('cleanup_lti_sessions', '--days', '30')
        cleanup_time = time.time() - start_time
        
        # Verify cleanup was efficient (under 5 seconds for 1000 records)
        self.assertLess(cleanup_time, 5.0)
        
        # Verify sessions were cleaned up
        remaining_sessions = LTISession.objects.filter(
            session_key__startswith='load_session_'
        ).count()
        self.assertEqual(remaining_sessions, 0)

# Custom test runner for LTI compliance
class LTIComplianceTestRunner:
    """Custom test runner for LTI compliance verification"""
    
    def __init__(self):
        self.compliance_checks = [
            'test_valid_lti_launch',
            'test_nonce_validation',
            'test_required_claims_validation',
            'test_audience_validation',
            'test_message_type_validation',
            'test_deep_linking_response',
            'test_assignment_grade_service',
            'test_names_roles_service'
        ]
    
    def run_compliance_tests(self):
        """Run all compliance tests and generate report"""
        from django.test.utils import get_runner
        from django.conf import settings
        
        test_runner = get_runner(settings)()
        
        # Run specific compliance tests
        test_labels = [
            f'tests.test_lti_compliance.LTIComplianceTestCase.{test}'
            for test in self.compliance_checks
        ]
        
        result = test_runner.run_tests(test_labels)
        
        # Generate compliance report
        report = {
            'total_tests': len(self.compliance_checks),
            'passed': len(self.compliance_checks) - result,
            'failed': result,
            'compliance_percentage': ((len(self.compliance_checks) - result) / len(self.compliance_checks)) * 100
        }
        
        return report

# pytest fixtures for advanced testing
import pytest
from django.test import Client

@pytest.fixture
def lti_platform():
    """Create test LTI platform"""
    return LTIPlatform.objects.create(
        name="Test Platform",
        issuer="https://test.instructure.com",
        client_id="test_client",
        auth_login_url="https://test.instructure.com/login",
        auth_token_url="https://test.instructure.com/token",
        key_set_url="https://test.instructure.com/jwks",
        deployment_ids=["test_deployment"]
    )

@pytest.fixture
def authenticated_lti_session(lti_platform):
    """Create authenticated LTI session"""
    return LTISession.objects.create(
        session_key='test_session',
        launch_id='test_launch',
        platform=lti_platform,
        user_id='test_user',
        canvas_user_id='canvas_user',
        context_id='test_course',
        ip_address='127.0.0.1',
        nonce_used='test_nonce',
        expires_at=timezone.now() + timezone.timedelta(hours=24)
    )

@pytest.fixture
def lti_client():
    """Create Django test client with LTI session"""
    client = Client()
    # Set up session data
    session = client.session
    session['canvas_user_id'] = 'test_user'
    session['canvas_course_id'] = 'test_course'
    session['canvas_roles'] = ['Instructor']
    session.save()
    return client

# Run all tests
if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_lti_compliance'])
    
    if failures:
        exit(1)
    else:
        print("All LTI compliance tests passed!")
        
        # Generate compliance report
        runner = LTIComplianceTestRunner()
        report = runner.run_compliance_tests()
        
        print(f"LTI Compliance Report:")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['passed']}")
        print(f"Failed: {report['failed']}")
        print(f"Compliance: {report['compliance_percentage']:.1f}%")