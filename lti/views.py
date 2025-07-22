from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.urls import reverse
from django.conf import settings
from datetime import datetime
import logging

from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch
from pylti1p3.exception import LtiException

logger = logging.getLogger(__name__)

def get_tool_conf():
    # Your existing tool configuration function
    pass

def get_launch_data_storage():
    # Your existing launch data storage function
    pass

@csrf_exempt
@xframe_options_exempt
def login(request):
    """Enhanced OIDC login with proper session handling"""
    logger.info("=== OIDC LOGIN STARTED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Session exists: {hasattr(request, 'session')}")
    logger.info(f"Session key before: {getattr(request.session, 'session_key', 'None')}")
    
    # Force session creation if it doesn't exist
    if not request.session.session_key:
        request.session.create()
        logger.info(f"Created new session: {request.session.session_key}")
    
    # Set cookie test marker immediately
    request.session['lti_cookie_test'] = True
    request.session['oidc_login_time'] = datetime.now().isoformat()
    request.session.save()
    
    logger.info(f"Session key after setup: {request.session.session_key}")
    logger.info(f"Cookie test marker set: {request.session.get('lti_cookie_test')}")
    
    if request.method == 'GET':
        # Handle GET requests with proper session setup
        context = {
            'session_key': request.session.session_key,
            'debug_info': {
                'session_exists': bool(request.session.session_key),
                'cookie_test_set': request.session.get('lti_cookie_test', False),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
            }
        }
        return render(request, 'lti/login_form.html', context)
    
    # POST request - handle OIDC initiation
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    
    try:
        oidc_login = DjangoOIDCLogin(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        
        # Get target link URI
        target_link_uri = request.POST.get('target_link_uri', 
                                         request.build_absolute_uri(reverse('lti_launch')))
        
        logger.info(f"Target link URI: {target_link_uri}")
        
        # Store session info before redirect
        request.session['oidc_state'] = 'initiated'
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
    """Enhanced LTI launch with comprehensive session validation"""
    logger.info("=== LTI LAUNCH STARTED ===")
    logger.info(f"Session key: {request.session.session_key}")
    logger.info(f"Session data: {dict(request.session)}")
    logger.info(f"POST data keys: {list(request.POST.keys())}")
    
    # Enhanced session validation
    if not request.session.session_key:
        logger.error("No session key found during launch")
        return HttpResponse(
            "Session lost - cookie issue. Please ensure cookies are enabled and try again.", 
            status=400
        )
    
    # Check for cookie test marker with fallback
    cookie_test_passed = (
        request.session.get('lti_cookie_test') or 
        request.session.get('oidc_state') == 'initiated' or
        request.POST.get('skip_cookie_test')  # Emergency bypass
    )
    
    if not cookie_test_passed:
        logger.error("Cookie test failed - session not preserved")
        logger.error(f"Available session keys: {list(request.session.keys())}")
        
        # Provide helpful error message with debugging info
        debug_info = {
            'session_key': request.session.session_key,
            'session_data': dict(request.session),
            'cookies': dict(request.COOKIES),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
        }
        
        error_html = f"""
        <h3>Cookie Test Failed - Session Not Preserved</h3>
        <p>The LTI launch cannot proceed because session cookies are not working properly in this browser/iframe context.</p>
        
        <h4>Possible Solutions:</h4>
        <ul>
            <li><strong>Safari:</strong> Disable \"Prevent cross-site tracking\" in Privacy settings</li>
            <li><strong>Chrome:</strong> Allow all cookies for this site</li>
            <li><strong>Firefox:</strong> Disable Enhanced Tracking Protection for this site</li>
            <li><strong>Alternative:</strong> <a href=\"{request.build_absolute_uri()}?skip_cookie_test=1\" target=\"_blank\">Open in new tab</a></li>
        </ul>
        
        <details>
            <summary>Debug Information</summary>
            <pre>{debug_info}</pre>
        </details>
        """
        
        return HttpResponse(error_html, status=400)
    
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
        request.session['lti_launch_success'] = True
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
    """Enhanced cookie compatibility test"""
    if request.method == 'POST':
        # Create response with test cookies
        response = JsonResponse({
            'status': 'cookie_set',
            'timestamp': datetime.now().isoformat(),
            'session_key': request.session.session_key
        })
        
        # Set test cookie with proper attributes
        response.set_cookie(
            'lti_test_cookie', 
            'test_value',
            max_age=300,
            secure=True,
            httponly=False,  # Needs to be readable by JavaScript
            samesite='None'
        )
        
        # Also set session marker
        request.session['cookie_test_completed'] = True
        request.session.save()
        
        return response
    
    # GET request - render test page
    context = {
        'session_key': request.session.session_key,
        'cookies_enabled': request.COOKIES.get('lti_test_cookie') == 'test_value',
        'debug_info': {
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'in_iframe': request.META.get('HTTP_SEC_FETCH_DEST') == 'iframe',
            'existing_cookies': len(request.COOKIES),
            'session_exists': bool(request.session.session_key)
        }
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

# Health check endpoint for debugging
@xframe_options_exempt
def debug_session(request):
    """Debug endpoint to check session status"""
    if not settings.DEBUG:
        return HttpResponse("Not available in production", status=404)
    
    debug_data = {
        'session_key': request.session.session_key,
        'session_data': dict(request.session),
        'cookies': dict(request.COOKIES),
        'headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
        'method': request.method,
        'path': request.path
    }
    
    return JsonResponse(debug_data, indent=2)