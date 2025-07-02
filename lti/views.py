from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.exception import LtiException
import json
import uuid

@csrf_exempt
def lti_launch(request):
    """Handle LTI 1.3 launch from Canvas"""
    try:
        # Initialize LTI message launch
        tool_config = get_tool_config()
        message_launch = MessageLaunch(request, tool_config)
        message_launch_data = message_launch.get_launch_data()
        
        # Extract Canvas user and course info
        canvas_user_id = message_launch_data.get('sub')
        canvas_course_id = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id')
        canvas_roles = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        canvas_url = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/tool_platform', {}).get('url', '')
        
        # Create session
        session_id = str(uuid.uuid4())
        request.session['lti_session_id'] = session_id
        request.session['canvas_user_id'] = canvas_user_id
        request.session['canvas_course_id'] = canvas_course_id
        request.session['canvas_roles'] = canvas_roles
        request.session['canvas_url'] = canvas_url
        
        # Redirect to tool selection
        return redirect('tool_selection')
        
    except LtiException as e:
        return HttpResponse(f"LTI Launch Error: {str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

def get_tool_config():
    """Get LTI tool configuration"""
    config = {
        "title": "CanvasOps",
        "description": "Canvas Automation Tools",
        "oidc_login_url": "/lti/login/",
        "target_link_uri": "/lti/launch/",
        "https://canvas.instructure.com": {
            "client_id": "test_client_id",  # Will be configured later
            "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
            "auth_token_url": "https://sso.canvaslms.com/login/oauth2/token",
            "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
            "private_key_file": "private.key"
        }
    }
    return ToolConfJsonFile(config)

def tool_selection(request):
    """Show available tools to user"""
    if 'lti_session_id' not in request.session:
        return HttpResponse("Invalid session - please launch from Canvas", status=400)
    
    context = {
        'canvas_user_id': request.session.get('canvas_user_id'),
        'canvas_course_id': request.session.get('canvas_course_id'),
        'canvas_roles': request.session.get('canvas_roles', []),
        'canvas_url': request.session.get('canvas_url')
    }
    
    return render(request, 'lti/tool_selection.html', context)