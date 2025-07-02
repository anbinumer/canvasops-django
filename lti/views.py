from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.message_launch import DjangoMessageLaunch
from pylti1p3.oidc_login import DjangoOIDCLogin
from pylti1p3.exception import LtiException
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import json
import uuid
import base64
import os

@csrf_exempt
def lti_launch(request):
    """Handle LTI 1.3 launch from Canvas"""
    try:
        # Initialize LTI message launch
        tool_config = get_tool_config()
        message_launch = DjangoMessageLaunch(request, tool_config)
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

@csrf_exempt
def lti_login(request):
    """Handle OIDC login initiation"""
    try:
        tool_config = get_tool_config()
        oidc_login = DjangoOIDCLogin(request, tool_config)
        return oidc_login.redirect()
    except LtiException as e:
        return HttpResponse(f"OIDC Login Error: {str(e)}", status=400)

def lti_jwks(request):
    """Provide public JWK for LTI authentication"""
    private_key = get_or_create_private_key()
    public_key = private_key.publickey()
    
    # Convert to JWK format
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": "canvas-ops-key",
        "n": base64.urlsafe_b64encode(public_key.n.to_bytes((public_key.n.bit_length() + 7) // 8, 'big')).decode().rstrip('='),
        "e": base64.urlsafe_b64encode(public_key.e.to_bytes((public_key.e.bit_length() + 7) // 8, 'big')).decode().rstrip('='),
        "alg": "RS256"
    }
    
    return JsonResponse({"keys": [jwk]})

def get_or_create_private_key():
    """Get or create RSA private key"""
    key_path = "/tmp/canvas_ops_private.key"
    
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            key_data = f.read()
        return RSA.import_key(key_data)
    else:
        key = RSA.generate(2048)
        with open(key_path, 'w') as f:
            f.write(key.export_key().decode())
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

def get_tool_config():
    """Get LTI tool configuration"""
    config = {
        "title": "CanvasOps",
        "description": "Canvas Automation Tools",
        "oidc_login_url": "https://canvasops-django-production.up.railway.app/lti/login/",
        "target_link_uri": "https://canvasops-django-production.up.railway.app/lti/launch/",
        "https://canvas.instructure.com": {
            "client_id": os.getenv('CANVAS_CLIENT_ID'),
            "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
            "auth_token_url": "https://sso.canvaslms.com/login/oauth2/token", 
            "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
            "private_key_file": "/tmp/canvas_ops_private.key"
        }
    }
    return ToolConfJsonFile(config)