# lti/compliance.py
from pylti1p3.deep_link import DeepLink
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.names_roles import NamesRoles
import json
import logging

logger = logging.getLogger(__name__)

class LTIComplianceManager:
    """Ensures full LTI 1.3 specification compliance"""
    
    @staticmethod
    def validate_message_type(launch_data):
        """Validate LTI message type"""
        message_type = launch_data.get(
            'https://purl.imsglobal.org/spec/lti/claim/message_type'
        )
        
        valid_types = [
            'LtiResourceLinkRequest',
            'LtiDeepLinkingRequest',
            'LtiSubmissionReviewRequest'
        ]
        
        if message_type not in valid_types:
            raise ValueError(f"Invalid message type: {message_type}")
        
        return message_type
    
    @staticmethod
    def validate_required_claims(launch_data):
        """Validate all required LTI claims are present"""
        required_claims = [
            'iss',  # Issuer
            'sub',  # Subject (user ID)
            'aud',  # Audience
            'exp',  # Expiration
            'iat',  # Issued at
            'nonce',  # Nonce
            'https://purl.imsglobal.org/spec/lti/claim/deployment_id',
            'https://purl.imsglobal.org/spec/lti/claim/message_type',
            'https://purl.imsglobal.org/spec/lti/claim/version',
        ]
        
        missing_claims = []
        for claim in required_claims:
            if claim not in launch_data:
                missing_claims.append(claim)
        
        if missing_claims:
            raise ValueError(f"Missing required claims: {missing_claims}")
        
        return True
    
    @staticmethod
    def extract_context_info(launch_data):
        """Extract and validate context information"""
        context_claim = 'https://purl.imsglobal.org/spec/lti/claim/context'
        context = launch_data.get(context_claim, {})
        
        return {
            'id': context.get('id'),
            'label': context.get('label'),
            'title': context.get('title'),
            'type': context.get('type', [])
        }
    
    @staticmethod
    def extract_user_info(launch_data):
        """Extract user information with privacy considerations"""
        user_info = {
            'id': launch_data.get('sub'),
            'roles': launch_data.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        }
        
        # Optional user information (privacy dependent)
        user_info.update({
            'name': launch_data.get('name'),
            'given_name': launch_data.get('given_name'),
            'family_name': launch_data.get('family_name'),
            'email': launch_data.get('email'),
            'picture': launch_data.get('picture')
        })
        
        return user_info

class DeepLinkingService:
    """Complete Deep Linking implementation"""
    
    def __init__(self, message_launch):
        self.message_launch = message_launch
        self.deep_link = message_launch.get_deep_link()
    
    def create_content_items(self):
        """Create content items for deep linking"""
        items = []
        
        # Main tool link
        main_tool = DeepLink() \
            .set_url(self.get_launch_url()) \
            .set_title("CanvasOps Tools") \
            .set_text("Access Canvas automation tools") \
            .set_icon("https://your-domain.com/static/icon.png") \
            .set_thumbnail("https://your-domain.com/static/thumbnail.png")
        
        items.append(main_tool)
        
        # Individual tool links
        tools = [
            {
                'id': 'link-checker',
                'title': 'Link Checker',
                'description': 'Scan course content for broken links'
            },
            {
                'id': 'find-replace',
                'title': 'Find & Replace URLs',
                'description': 'Update URLs in course content'
            },
            {
                'id': 'due-date-audit',
                'title': 'Due Date Audit',
                'description': 'Review assignment due dates'
            }
        ]
        
        for tool in tools:
            tool_link = DeepLink() \
                .set_url(f"{self.get_launch_url()}?tool={tool['id']}") \
                .set_title(tool['title']) \
                .set_text(tool['description'])
            
            items.append(tool_link)
        
        return items
    
    def get_launch_url(self):
        """Get the launch URL for content items"""
        return self.message_launch.get_launch_url()
    
    def respond_with_content_items(self, items):
        """Send deep linking response"""
        return self.deep_link.output_response_form(items)

class AssignmentGradeService:
    """Assignment and Grade Services (AGS) implementation"""
    
    def __init__(self, message_launch):
        self.message_launch = message_launch
        self.ags = message_launch.get_ags()
    
    def can_read_gradebook(self):
        """Check if tool can read gradebook"""
        return self.ags and self.ags.can_read_gradebook()
    
    def can_manage_gradebook(self):
        """Check if tool can manage gradebook"""
        return self.ags and self.ags.can_manage_gradebook()
    
    def get_line_items(self):
        """Get all line items from gradebook"""
        if not self.can_read_gradebook():
            raise PermissionError("Cannot read gradebook")
        
        return self.ags.get_lineitems()
    
    def create_line_item(self, label, score_maximum, resource_link_id=None):
        """Create a new line item"""
        if not self.can_manage_gradebook():
            raise PermissionError("Cannot manage gradebook")
        
        line_item = LineItem()
        line_item.set_label(label) \
                 .set_score_maximum(score_maximum) \
                 .set_resource_link_id(resource_link_id)
        
        return self.ags.put_lineitem(line_item)
    
    def submit_grade(self, line_item_id, user_id, score, comment=None):
        """Submit a grade for a user"""
        if not self.can_manage_gradebook():
            raise PermissionError("Cannot manage gradebook")
        
        grade = Grade()
        grade.set_score_given(score) \
             .set_user_id(user_id) \
             .set_timestamp() \
             .set_activity_progress('Completed') \
             .set_grading_progress('FullyGraded')
        
        if comment:
            grade.set_comment(comment)
        
        return self.ags.put_grade(line_item_id, grade)

class NamesRolesService:
    """Names and Role Provisioning Service (NRPS) implementation"""
    
    def __init__(self, message_launch):
        self.message_launch = message_launch
        self.nrps = message_launch.get_nrps()
    
    def can_access_names_roles(self):
        """Check if tool can access names and roles"""
        return self.nrps is not None
    
    def get_members(self):
        """Get all members of the context"""
        if not self.can_access_names_roles():
            raise PermissionError("Cannot access names and roles")
        
        members = []
        for member in self.nrps.get_members():
            member_data = {
                'user_id': member.get('user_id'),
                'roles': member.get('roles', []),
                'name': member.get('name'),
                'given_name': member.get('given_name'),
                'family_name': member.get('family_name'),
                'email': member.get('email'),
                'picture': member.get('picture')
            }
            members.append(member_data)
        
        return members
    
    def get_members_by_role(self, role):
        """Get members filtered by role"""
        all_members = self.get_members()
        return [
            member for member in all_members 
            if role in member.get('roles', [])
        ]

# Updated views.py with full compliance
from .compliance import (
    LTIComplianceManager, 
    DeepLinkingService, 
    AssignmentGradeService,
    NamesRolesService
)

@csrf_exempt
@require_POST
def compliant_launch(request):
    """Fully LTI 1.3 compliant launch handler"""
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    message_launch = ExtendedDjangoMessageLaunch(
        request,
        tool_conf,
        launch_data_storage=launch_data_storage
    )
    
    try:
        # Validate launch
        message_launch.validate()
        launch_data = message_launch.get_launch_data()
        
        # Full compliance validation
        LTIComplianceManager.validate_required_claims(launch_data)
        message_type = LTIComplianceManager.validate_message_type(launch_data)
        
        # Extract context and user info
        context_info = LTIComplianceManager.extract_context_info(launch_data)
        user_info = LTIComplianceManager.extract_user_info(launch_data)
        
        # Store in session
        request.session.update({
            'lti_launch_data': launch_data,
            'lti_context': context_info,
            'lti_user': user_info,
            'lti_message_type': message_type
        })
        
        # Handle different message types
        if message_type == 'LtiDeepLinkingRequest':
            return handle_deep_linking(request, message_launch)
        elif message_type == 'LtiSubmissionReviewRequest':
            return handle_submission_review(request, message_launch)
        else:  # LtiResourceLinkRequest
            return redirect('/tool_selection/')
        
    except Exception as e:
        logger.error(f"LTI launch compliance error: {e}")
        return HttpResponse(f"Launch failed: {str(e)}", status=400)

def handle_deep_linking(request, message_launch):
    """Handle deep linking requests"""
    try:
        deep_linking = DeepLinkingService(message_launch)
        content_items = deep_linking.create_content_items()
        response_form = deep_linking.respond_with_content_items(content_items)
        
        return HttpResponse(response_form)
    
    except Exception as e:
        logger.error(f"Deep linking error: {e}")
        return HttpResponse("Deep linking failed", status=400)

def handle_submission_review(request, message_launch):
    """Handle submission review requests"""
    try:
        # Get submission data from launch
        launch_data = message_launch.get_launch_data()
        submission_review = launch_data.get(
            'https://purl.imsglobal.org/spec/lti-sr/claim/submission_review'
        )
        
        context = {
            'submission_review': submission_review,
            'user_info': request.session.get('lti_user'),
            'context_info': request.session.get('lti_context')
        }
        
        return render(request, 'lti/submission_review.html', context)
    
    except Exception as e:
        logger.error(f"Submission review error: {e}")
        return HttpResponse("Submission review failed", status=400)