# lti/compliance.py
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import time

logger = logging.getLogger(__name__)

class LTIComplianceManager:
    """LTI 1.3 compliance and validation manager"""
    
    @staticmethod
    def validate_launch_claims(launch_data):
        """Validate all required LTI 1.3 launch claims"""
        required_claims = [
            'iss', 'sub', 'aud', 'exp', 'iat', 'nonce',
            'https://purl.imsglobal.org/spec/lti/claim/message_type',
            'https://purl.imsglobal.org/spec/lti/claim/version',
            'https://purl.imsglobal.org/spec/lti/claim/deployment_id'
        ]
        
        missing_claims = []
        for claim in required_claims:
            if claim not in launch_data:
                missing_claims.append(claim)
        
        if missing_claims:
            raise ValueError(f"Missing required claims: {missing_claims}")
        
        return True
    
    @staticmethod
    def validate_message_type(message_type):
        """Validate LTI message type"""
        valid_types = [
            'LtiResourceLinkRequest',
            'LtiDeepLinkingRequest',
            'LtiSubmissionReviewRequest'
        ]
        
        if message_type not in valid_types:
            raise ValueError(f"Invalid message type: {message_type}")
        
        return True
    
    @staticmethod
    def validate_version(version):
        """Validate LTI version"""
        if version != '1.3.0':
            raise ValueError(f"Unsupported LTI version: {version}")
        
        return True
    
    @staticmethod
    def validate_context_claims(launch_data):
        """Validate context-related claims"""
        context_claim = 'https://purl.imsglobal.org/spec/lti/claim/context'
        
        if context_claim in launch_data:
            context = launch_data[context_claim]
            if not isinstance(context, dict):
                raise ValueError("Context claim must be an object")
            
            if 'id' not in context:
                raise ValueError("Context must have an 'id' field")
        
        return True
    
    @staticmethod
    def validate_role_claims(launch_data):
        """Validate role-related claims"""
        roles_claim = 'https://purl.imsglobal.org/spec/lti/claim/roles'
        
        if roles_claim in launch_data:
            roles = launch_data[roles_claim]
            if not isinstance(roles, list):
                raise ValueError("Roles claim must be an array")
            
            # Validate role URIs
            valid_role_prefixes = [
                'http://purl.imsglobal.org/vocab/lis/v2/membership#',
                'http://purl.imsglobal.org/vocab/lis/v2/system/person#',
                'http://purl.imsglobal.org/vocab/lis/v2/institution/person#'
            ]
            
            for role in roles:
                if not any(role.startswith(prefix) for prefix in valid_role_prefixes):
                    logger.warning(f"Unknown role URI: {role}")
        
        return True
    
    @staticmethod
    def validate_custom_claims(launch_data):
        """Validate custom claims"""
        custom_claim = 'https://purl.imsglobal.org/spec/lti/claim/custom'
        
        if custom_claim in launch_data:
            custom = launch_data[custom_claim]
            if not isinstance(custom, dict):
                raise ValueError("Custom claim must be an object")
            
            # Validate custom claim keys (should be simple strings)
            for key in custom.keys():
                if not isinstance(key, str) or ' ' in key:
                    raise ValueError(f"Invalid custom claim key: {key}")
        
        return True
    
    @staticmethod
    def validate_resource_link_claims(launch_data):
        """Validate resource link claims"""
        resource_link_claim = 'https://purl.imsglobal.org/spec/lti/claim/resource_link'
        
        if resource_link_claim in launch_data:
            resource_link = launch_data[resource_link_claim]
            if not isinstance(resource_link, dict):
                raise ValueError("Resource link claim must be an object")
            
            if 'id' not in resource_link:
                raise ValueError("Resource link must have an 'id' field")
        
        return True
    
    @staticmethod
    def validate_tool_platform_claims(launch_data):
        """Validate tool platform claims"""
        platform_claim = 'https://purl.imsglobal.org/spec/lti/claim/tool_platform'
        
        if platform_claim in launch_data:
            platform = launch_data[platform_claim]
            if not isinstance(platform, dict):
                raise ValueError("Tool platform claim must be an object")
            
            if 'name' not in platform:
                raise ValueError("Tool platform must have a 'name' field")
        
        return True
    
    @staticmethod
    def validate_launch_presentation_claims(launch_data):
        """Validate launch presentation claims"""
        presentation_claim = 'https://purl.imsglobal.org/spec/lti/claim/launch_presentation'
        
        if presentation_claim in launch_data:
            presentation = launch_data[presentation_claim]
            if not isinstance(presentation, dict):
                raise ValueError("Launch presentation claim must be an object")
            
            # Validate document target
            if 'document_target' in presentation:
                valid_targets = ['iframe', 'window', 'embed']
                if presentation['document_target'] not in valid_targets:
                    raise ValueError(f"Invalid document target: {presentation['document_target']}")
        
        return True
    
    @staticmethod
    def validate_all_claims(launch_data):
        """Validate all LTI claims comprehensively"""
        try:
            LTIComplianceManager.validate_launch_claims(launch_data)
            LTIComplianceManager.validate_message_type(
                launch_data.get('https://purl.imsglobal.org/spec/lti/claim/message_type')
            )
            LTIComplianceManager.validate_version(
                launch_data.get('https://purl.imsglobal.org/spec/lti/claim/version')
            )
            LTIComplianceManager.validate_context_claims(launch_data)
            LTIComplianceManager.validate_role_claims(launch_data)
            LTIComplianceManager.validate_custom_claims(launch_data)
            LTIComplianceManager.validate_resource_link_claims(launch_data)
            LTIComplianceManager.validate_tool_platform_claims(launch_data)
            LTIComplianceManager.validate_launch_presentation_claims(launch_data)
            
            return True
        except ValueError as e:
            logger.error(f"LTI compliance validation failed: {e}")
            raise

class LTIAdvantageServices:
    """LTI Advantage services implementation"""
    
    @staticmethod
    def validate_ags_scope(launch_data):
        """Validate Assignment and Grade Services scope"""
        scopes_claim = 'https://purl.imsglobal.org/spec/lti/claim/custom'
        
        if scopes_claim in launch_data:
            custom = launch_data[scopes_claim]
            ags_scope = custom.get('ags_scope', '')
            
            valid_scopes = [
                'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem',
                'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly',
                'https://purl.imsglobal.org/spec/lti-ags/scope/result',
                'https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly',
                'https://purl.imsglobal.org/spec/lti-ags/scope/score'
            ]
            
            if ags_scope and ags_scope not in valid_scopes:
                logger.warning(f"Unknown AGS scope: {ags_scope}")
        
        return True
    
    @staticmethod
    def validate_nrps_scope(launch_data):
        """Validate Names and Roles Provisioning Services scope"""
        scopes_claim = 'https://purl.imsglobal.org/spec/lti/claim/custom'
        
        if scopes_claim in launch_data:
            custom = launch_data[scopes_claim]
            nrps_scope = custom.get('nrps_scope', '')
            
            valid_scopes = [
                'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'
            ]
            
            if nrps_scope and nrps_scope not in valid_scopes:
                logger.warning(f"Unknown NRPS scope: {nrps_scope}")
        
        return True

# Compliance endpoints
@csrf_exempt
def compliance_status(request):
    """Return LTI compliance status"""
    status = {
        'lti_version': '1.3.0',
        'services': {
            'ags': True,  # Assignment and Grade Services
            'nrps': True,  # Names and Roles Provisioning Services
            'deep_linking': True,
            'submission_review': True
        },
        'security': {
            'nonce_validation': True,
            'jwt_validation': True,
            'audience_validation': True
        },
        'compliance_level': 'full'
    }
    
    return JsonResponse(status)

@csrf_exempt
@require_POST
def validate_launch_data(request):
    """Validate launch data for compliance"""
    try:
        launch_data = json.loads(request.body)
        LTIComplianceManager.validate_all_claims(launch_data)
        
        return JsonResponse({
            'valid': True,
            'message': 'Launch data is compliant'
        })
    except ValueError as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in launch validation: {e}")
        return JsonResponse({
            'valid': False,
            'error': 'Internal validation error'
        }, status=500) 