from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.oidc_login import OIDCLogin
from pylti1p3.exception import LtiException
from Crypto.PublicKey import RSA
import json
import uuid
import base64
import os

@csrf_exempt
def lti_launch(request):
    """Handle LTI 1.3 launch from Canvas"""
    try:
        tool_config = get_tool_config()
        message_launch = MessageLaunch(request, tool_config)
        message_launch_data = message_launch.get_launch_data()
        canvas_user_id = message_launch_data.get('sub')
        canvas_course_id = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id')
        canvas_roles = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        canvas_url = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/tool_platform', {}).get('url', '')
        session_id = str(uuid.uuid4())
        request.session['lti_session_id'] = session_id
        request.session['canvas_user_id'] = canvas_user_id
        request.session['canvas_course_id'] = canvas_course_id
        request.session['canvas_roles'] = canvas_roles
        request.session['canvas_url'] = canvas_url
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
        oidc_login = OIDCLogin(request, tool_config)
        return oidc_login.redirect()
    except LtiException as e:
        return HttpResponse(f"OIDC Login Error: {str(e)}", status=400)

def lti_jwks(request):
    """Provide public JWK for LTI authentication"""
    private_key = get_or_create_private_key()
    public_key = private_key.publickey()
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
        with open(key_path, 'rb') as f:
            key_data = f.read()
        return RSA.import_key(key_data)
    else:
        key = RSA.generate(2048)
        with open(key_path, 'wb') as f:
            f.write(key.export_key())
        return key

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

def lti_config(request):
    """Provide LTI configuration XML for Canvas"""
    xml_config = '''<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link
    xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0
    http://www.imsglobal.org/xsd/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0
    http://www.imsglobal.org/xsd/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0
    http://www.imsglobal.org/xsd/imslticp_v1p0.xsd">
    <blti:title>CanvasOps</blti:title>
    <blti:description>Canvas Automation Tools</blti:description>
    <blti:launch_url>https://canvasops-django-production.up.railway.app/lti/launch/</blti:launch_url>
    <blti:extensions platform="canvas.instructure.com">
        <lticm:property name="tool_id">canvasops</lticm:property>
        <lticm:property name="privacy_level">public</lticm:property>
        <lticm:options name="course_navigation">
            <lticm:property name="url">https://canvasops-django-production.up.railway.app/lti/launch/</lticm:property>
            <lticm:property name="text">CanvasOps</lticm:property>
            <lticm:property name="enabled">true</lticm:property>
        </lticm:options>
    </blti:extensions>
</cartridge_basiclti_link>'''
    return HttpResponse(xml_config, content_type='application/xml')

def lti_config_json(request):
    """Provide LTI 1.3 JSON configuration for Canvas"""
    config = {
        "title": "CanvasOps",
        "description": "Canvas Automation Tools for ACU",
        "oidc_initiation_url": "https://canvasops-django-production.up.railway.app/lti/login/",
        "target_link_uri": "https://canvasops-django-production.up.railway.app/lti/launch/",
        "public_jwk_url": "https://canvasops-django-production.up.railway.app/lti/jwks/",
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score"
        ],
        "extensions": {
            "platform": "canvas.instructure.com",
            "settings": {
                "placements": [
                    {
                        "placement": "course_navigation",
                        "message_type": "LtiResourceLinkRequest",
                        "target_link_uri": "https://canvasops-django-production.up.railway.app/lti/launch/",
                        "text": "CanvasOps",
                        "icon_url": "https://canvasops-django-production.up.railway.app/static/icon.png"
                    }
                ]
            }
        },
        "custom_fields": {}
    }
    return JsonResponse(config)