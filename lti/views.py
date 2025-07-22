from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings
from pylti1p3.contrib.django import (
    DjangoOIDCLogin,
    DjangoMessageLaunch,
    DjangoCacheDataStorage
)
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.exception import LtiException, OIDCException
import json
import os
from .models import LTISession, LTIPlatform, LTIDeployment
from django.views.decorators.clickjacking import xframe_options_exempt


class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):
    """Extended message launch to store session data"""
    
    def validate(self):
        """Override to store session data after validation"""
        super().validate()
        self._store_launch_data()
        return self
    
    def _store_launch_data(self):
        """Store launch data in session"""
        try:
            launch_data = self.get_launch_data()
            request = self._request
            
            # Extract Canvas data
            canvas_user_id = launch_data.get('sub')
            context = launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {})
            canvas_course_id = context.get('id', '')
            canvas_roles = launch_data.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
            
            # Extract platform info
            platform = launch_data.get('https://purl.imsglobal.org/spec/lti/claim/tool_platform', {})
            canvas_url = platform.get('url', 'https://canvas.instructure.com')
            
            # Store in Django session
            request.session['lti_launch_data'] = launch_data
            request.session['canvas_user_id'] = canvas_user_id
            request.session['canvas_course_id'] = canvas_course_id
            request.session['canvas_roles'] = canvas_roles
            request.session['canvas_url'] = canvas_url
            request.session['canvas_course_name'] = context.get('title', 'Unknown Course')
            
            # Store launch ID for grade passback
            request.session['launch_id'] = self.get_launch_id()
            
            # Create or update LTI session record
            # Note: This needs to be updated to work with new model structure
            # For now, just store in Django session
            pass
        except Exception as e:
            print(f"Error storing launch data: {e}")


def get_lti_config_path():
    """Get the path to the LTI configuration file"""
    return os.path.join(settings.BASE_DIR, 'lti_config.json')


def get_launch_data_storage():
    """Get the data storage for launch data"""
    return DjangoCacheDataStorage()


def get_tool_conf():
    """Get the tool configuration"""
    return ToolConfJsonFile(get_lti_config_path())


@csrf_exempt
@xframe_options_exempt
def login(request):
    """Handle OIDC login initiation"""
    # Ensure session exists for iframe compatibility
    if not request.session.session_key:
        request.session.create()
    
    try:
        tool_conf = get_tool_conf()
        launch_data_storage = get_launch_data_storage()
        oidc_login = DjangoOIDCLogin(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        # Use the target_link_uri from the request if present
        target_link_uri = request.GET.get('target_link_uri')
        if not target_link_uri:
            # Fallback to default if not provided
            from django.urls import reverse
            target_link_uri = request.build_absolute_uri(reverse('lti_launch'))
        
        response = oidc_login.enable_check_cookies().redirect(target_link_uri)
        
        # Ensure iframe compatibility
        response['X-Frame-Options'] = 'ALLOWALL'
        response['Content-Security-Policy'] = 'frame-ancestors *;'
        
        return response
    except LtiException as e:
        return HttpResponse(f"OIDC Login Error: {str(e)}", status=400)


@csrf_exempt
@xframe_options_exempt
@require_POST
def launch(request):
    """LTI 1.3 launch endpoint"""
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    message_launch = ExtendedDjangoMessageLaunch(
        request,
        tool_conf,
        launch_data_storage=launch_data_storage
    )
    
    try:
        # Validate the launch
        message_launch.validate()
        
        # Debug: print session key and data
        print("[DEBUG] Session key after launch:", request.session.session_key)
        print("[DEBUG] Session data after launch:", dict(request.session))
        
        # Check if this is a deep linking request
        if message_launch.is_deep_link_launch():
            return redirect('lti_configure')
        
        # Check if this is a submission review request
        if message_launch.is_submission_review_launch():
            return redirect('lti_submission_review')
        
        # Regular resource launch - redirect to tool selection
        return redirect('/lti/tools/')
        
    except LtiException as e:
        return HttpResponse(f"LTI launch failed: {str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"Launch error: {str(e)}", status=500)


def jwks(request):
    """JSON Web Key Set endpoint for public key"""
    tool_conf = get_tool_conf()
    
    # Get all public keys from the tool configuration
    jwks_dict = {"keys": []}
    
    # In production, this would read from the actual key files
    # For now, we'll generate a placeholder response
    # You'll need to generate actual RSA keys and place them in the project
    
    try:
        # Read public key file
        public_key_path = os.path.join(settings.BASE_DIR, 'public.key')
        if os.path.exists(public_key_path):
            with open(public_key_path, 'r') as f:
                public_key = f.read()
            
            # Convert to JWK format (simplified - in production use a proper library)
            jwk = {
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "kid": "canvasops-key-1",
                "n": "base64url_encoded_modulus",  # This needs proper RSA key parsing
                "e": "AQAB"  # Standard RSA exponent
            }
            jwks_dict["keys"].append(jwk)
    except Exception as e:
        print(f"Error reading public key: {e}")
    
    return JsonResponse(jwks_dict)


def configure(request):
    """Deep linking configuration endpoint"""
    if 'lti_launch_data' not in request.session:
        return HttpResponse("No active LTI session", status=400)
    # For now, just return a placeholder response
    return HttpResponse("Deep linking configuration is not yet implemented.")


def submission_review(request):
    """Handle submission review launches"""
    if 'lti_launch_data' not in request.session:
        return HttpResponse("No active LTI session", status=400)
    
    # Handle submission review logic here
    context = {
        'canvas_user_id': request.session.get('canvas_user_id'),
        'canvas_course_id': request.session.get('canvas_course_id'),
        'canvas_course_name': request.session.get('canvas_course_name'),
    }
    
    return render(request, 'lti/submission_review.html', context)


@csrf_exempt
@xframe_options_exempt
def tool_selection(request):
    """Display available tools"""
    if 'canvas_user_id' not in request.session:
        return HttpResponse("Please launch this tool from Canvas", status=400)
    
    # Tool definitions (port from React prototype)
    tools = [
        {
            'id': 'link-checker',
            'name': 'Link Checker',
            'description': 'Scan course content for broken or invalid links',
            'tags': ['QA', 'Links'],
            'is_destructive': False,
            'scope': 'Pages, Modules, Assignments, Announcements',
        },
        {
            'id': 'find-replace',
            'name': 'Find & Replace URLs',
            'description': 'Search for specific URLs in course content and replace them with new ones',
            'tags': ['QA', 'URLs', 'Content'],
            'is_destructive': True,
            'scope': 'Course content, modules, assignments, pages, quizzes, discussions',
        },
        {
            'id': 'due-date-audit',
            'name': 'Due Date Audit',
            'description': 'List and optionally fix assignment and quiz due dates',
            'tags': ['Dates'],
            'is_destructive': False,
            'scope': 'Assignments, Quizzes, Discussions',
        },
        {
            'id': 'navigation-cleaner',
            'name': 'Navigation Cleaner',
            'description': 'Check and clean up course navigation menu items',
            'tags': ['UX', 'Menus'],
            'is_destructive': False,
            'scope': 'Course Navigation',
        },
        {
            'id': 'orphaned-pages',
            'name': 'Orphaned Pages Finder',
            'description': 'Find pages not linked in any module or navigation',
            'tags': ['Pages'],
            'is_destructive': False,
            'scope': 'Course Pages and Modules',
        },
    ]
    
    # Check user permissions based on Canvas roles
    canvas_roles = request.session.get('canvas_roles', [])
    is_instructor = any('Instructor' in role for role in canvas_roles)
    is_admin = any('Administrator' in role for role in canvas_roles)
    
    context = {
        'canvas_user_id': request.session.get('canvas_user_id'),
        'canvas_course_id': request.session.get('canvas_course_id'),
        'canvas_course_name': request.session.get('canvas_course_name'),
        'canvas_roles': canvas_roles,
        'is_instructor': is_instructor,
        'is_admin': is_admin,
        'canvas_url': request.session.get('canvas_url'),
        'tools': tools,
    }
    
    return render(request, 'lti/tool_selection.html', context)


def xml_config(request):
    """Generate XML configuration for Canvas"""
    domain = request.build_absolute_uri('/').rstrip('/')
    
    xml_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti = "http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm ="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp ="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi = "http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation = "http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">
    <blti:title>CanvasOps</blti:title>
    <blti:description>Canvas Automation Tools for ACU</blti:description>
    <blti:launch_url>{domain}/lti/launch/</blti:launch_url>
    <blti:extensions platform="canvas.instructure.com">
      <lticm:property name="privacy_level">public</lticm:property>
      <lticm:property name="domain">{domain}</lticm:property>
      <lticm:options name="course_navigation">
        <lticm:property name="url">{domain}/lti/launch/</lticm:property>
        <lticm:property name="text">CanvasOps</lticm:property>
        <lticm:property name="visibility">admins</lticm:property>
        <lticm:property name="default">disabled</lticm:property>
        <lticm:property name="enabled">true</lticm:property>
      </lticm:options>
    </blti:extensions>
    <blti:custom>
      <lticm:property name="canvas_api_domain">$Canvas.api.domain</lticm:property>
      <lticm:property name="canvas_course_id">$Canvas.course.id</lticm:property>
      <lticm:property name="canvas_user_id">$Canvas.user.id</lticm:property>
    </blti:custom>
</cartridge_basiclti_link>"""
    
    return HttpResponse(xml_config, content_type='application/xml')


@csrf_exempt
@xframe_options_exempt
def iframe_test(request):
    """Simple test view to verify iframe compatibility"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LTI Iframe Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f0f8ff; }
            .success { color: green; font-size: 18px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="success">✅ Iframe Test Successful!</div>
        <p>If you can see this page without being forced to open in a new tab, iframe compatibility is working.</p>
        <p>Session ID: {}</p>
        <p>Headers set for iframe compatibility:</p>
        <ul>
            <li>X-Frame-Options: ALLOWALL</li>
            <li>Content-Security-Policy: frame-ancestors *;</li>
            <li>SESSION_COOKIE_SAMESITE: None</li>
        </ul>
    </body>
    </html>
    """.format(request.session.session_key or "No session")
    
    response = HttpResponse(html)
    response['X-Frame-Options'] = 'ALLOWALL'
    response['Content-Security-Policy'] = 'frame-ancestors *;'
    return response