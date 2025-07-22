from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.clickjacking import xframe_options_exempt
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
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_tool_conf():
    """Get the tool configuration"""
    config_path = os.path.join(settings.BASE_DIR, 'lti_config.json')
    return ToolConfJsonFile(config_path)

def get_launch_data_storage():
    """Get the data storage for launch data"""
    return DjangoCacheDataStorage()

@csrf_exempt
@xframe_options_exempt
def login(request):
    """Enhanced OIDC login with improved state handling"""
    logger.info(f"LTI Login initiated: {request.method}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request GET params: {dict(request.GET)}")
    logger.info(f"Request POST params: {dict(request.POST)}")
    
    # Ensure session exists and is properly configured
    if not request.session.session_key:
        request.session.create()
        logger.info(f"Created new session: {request.session.session_key}")
    
    # Test cookie functionality first
    test_cookie_key = 'lti_cookie_test'
    if not request.session.get(test_cookie_key):
        request.session[test_cookie_key] = 'working'
        request.session.save()
        logger.info("Set test cookie in session")
    
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    try:
        oidc_login = DjangoOIDCLogin(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        
        # Get target_link_uri from request or use default
        target_link_uri = (
            request.POST.get('target_link_uri') or 
            request.GET.get('target_link_uri') or
            request.build_absolute_uri(reverse('lti_launch'))
        )
        
        logger.info(f"Target link URI: {target_link_uri}")
        
        # Store additional debug info in session
        request.session['lti_login_time'] = datetime.now().isoformat()
        request.session['lti_target_uri'] = target_link_uri
        request.session.save()
        
        # Enable cookie checks and redirect
        redirect_response = oidc_login.enable_check_cookies().redirect(target_link_uri)
        
        # Ensure response cookies are iframe-compatible
        if hasattr(redirect_response, 'cookies'):
            for cookie in redirect_response.cookies.values():
                cookie['samesite'] = 'None'
                cookie['secure'] = True
        
        logger.info(f"OIDC redirect URL: {redirect_response.url}")
        return redirect_response
        
    except Exception as e:
        logger.error(f"OIDC login failed: {str(e)}", exc_info=True)
        return HttpResponse(f"OIDC Login Error: {str(e)}", status=400)

@csrf_exempt
@xframe_options_exempt
@require_POST
def launch(request):
    """Enhanced LTI launch with better error handling"""
    logger.info("=== LTI LAUNCH STARTED ===")
    logger.info(f"Session key: {request.session.session_key}")
    logger.info(f"Session data: {dict(request.session)}")
    logger.info(f"POST data keys: {list(request.POST.keys())}")
    
    # Check if session was preserved
    if not request.session.session_key:
        logger.error("No session key found during launch")
        return HttpResponse("Session lost - cookie issue. Please ensure cookies are enabled.", status=400)
    
    # Check for test cookie
    if not request.session.get('lti_cookie_test'):
        logger.error("Test cookie not found - session not preserved")
        return HttpResponse("Cookie test failed - session not preserved", status=400)
    
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    try:
        message_launch = DjangoMessageLaunch(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        
        # Validate the launch
        launch_data = message_launch.get_launch_data()
        logger.info(f"Launch data received successfully")
        logger.info(f"User ID: {launch_data.get('sub')}")
        logger.info(f"Context ID: {launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id')}")
        
        # Store launch data in session
        request.session['lti_launch_data'] = launch_data
        request.session['lti_launch_time'] = datetime.now().isoformat()
        request.session.save()
        
        # Check message type and redirect accordingly
        if message_launch.is_deep_link_launch():
            logger.info("Deep linking launch detected")
            return redirect('lti_configure')
        
        logger.info("Regular resource launch - redirecting to tool selection")
        return redirect('/lti/tools/')
        
    except LtiException as e:
        logger.error(f"LTI launch failed: {str(e)}", exc_info=True)
        return HttpResponse(f"LTI launch failed: {str(e)}", status=400)
    except Exception as e:
        logger.error(f"Unexpected launch error: {str(e)}", exc_info=True)
        return HttpResponse(f"Launch failed: {str(e)}", status=500)

@csrf_exempt
@xframe_options_exempt
def cookie_test(request):
    """Test cookie compatibility for iframe embedding"""
    if request.method == 'POST':
        # Test setting a cookie
        response = JsonResponse({'status': 'cookie_set'})
        response.set_cookie(
            'lti_test_cookie', 
            'test_value',
            max_age=300,
            secure=True,
            httponly=True,
            samesite='None'
        )
        return response
    
    # Render cookie test page
    context = {
        'cookies_enabled': request.COOKIES.get('lti_test_cookie') == 'test_value'
    }
    return render(request, 'lti/cookie_test.html', context)

@xframe_options_exempt
def jwks(request):
    """Serve public key in JWKS format"""
    try:
        tool_conf = get_tool_conf()
        return JsonResponse(tool_conf.get_jwks(), safe=False)
    except Exception as e:
        logger.error(f"JWKS error: {str(e)}")
        return JsonResponse({'error': 'Unable to generate JWKS'}, status=500)