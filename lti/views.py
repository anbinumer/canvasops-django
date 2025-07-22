import logging
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.clickjacking import xframe_options_exempt
from django.urls import reverse
from django.conf import settings
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch
from .utils import get_tool_conf, get_launch_data_storage

logger = logging.getLogger(__name__)

@csrf_exempt
@xframe_options_exempt
@require_http_methods(["GET", "POST"])
def cookie_test(request):
    """Enhanced cookie compatibility test for iframe embedding"""
    if request.method == 'POST':
        # Handle AJAX cookie test
        try:
            data = json.loads(request.body)
            if data.get('test') == 'server_cookie':
                # Set a test cookie and mark session
                response = JsonResponse({'success': True, 'message': 'Server cookie test passed'})
                response.set_cookie(
                    'lti_server_test', 
                    'server_test_value',
                    max_age=300,
                    secure=True,
                    httponly=False,
                    samesite='None'
                )
                request.session['cookie_test_passed'] = True
                request.session.save()
                return response
        except Exception as e:
            logger.error(f"Cookie test error: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    # GET request - show cookie test page
    context = {
        'session_key': request.session.session_key,
        'debug_info': {
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'in_iframe': request.META.get('HTTP_SEC_FETCH_DEST') == 'iframe',
            'referer': request.META.get('HTTP_REFERER', ''),
            'cookies_count': len(request.COOKIES)
        }
    }
    return render(request, 'lti/cookie_test.html', context)

@csrf_exempt
@xframe_options_exempt
def login(request):
    """OIDC login with cookie compatibility check"""
    logger.info(f"=== LTI LOGIN STARTED ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Session key: {request.session.session_key}")
    # Check for fallback modes
    if request.GET.get('new_tab'):
        request.session['lti_new_tab'] = True
        logger.info("LTI: New tab mode enabled")
    # Cookie compatibility check (skip for new tab or if already passed)
    cookie_test_passed = (
        request.session.get('cookie_test_passed') or
        request.GET.get('skip_cookie_test') or
        request.GET.get('new_tab')
    )
    if not cookie_test_passed and request.method == 'POST':
        # Redirect to cookie test first
        logger.info("LTI: Redirecting to cookie test")
        return redirect('lti_cookie_test')
    if request.method == 'GET':
        # Handle Canvas GET requests (tool selection)
        return HttpResponseRedirect('/tool_selection/')
    # POST request - OIDC initiation
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    try:
        oidc_login = DjangoOIDCLogin(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        target_link_uri = request.POST.get('target_link_uri', 
                                         request.build_absolute_uri(reverse('lti_launch')))
        # Mark session as OIDC initiated
        request.session['oidc_state'] = 'initiated'
        request.session.save()
        # Enable cookie checks and redirect
        redirect_response = oidc_login.enable_check_cookies().redirect(target_link_uri)
        # Ensure response cookies are iframe-compatible
        if hasattr(redirect_response, 'cookies'):
            for cookie in redirect_response.cookies.values():
                cookie['samesite'] = 'None'
                cookie['secure'] = True
        logger.info(f"OIDC redirecting to: {target_link_uri}")
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
        return render(request, 'lti/launch_error.html', {
            'error': 'Session Lost',
            'message': 'Cookie issue detected. Please ensure cookies are enabled and try again.',
            'debug_info': {
                'session_exists': False,
                'cookies': dict(request.COOKIES),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
            }
        })
    # Check for cookie test marker with fallback options
    cookie_test_passed = (
        request.session.get('lti_cookie_test') or 
        request.session.get('oidc_state') == 'initiated' or
        request.POST.get('skip_cookie_test') or
        request.GET.get('new_tab')
    )
    if not cookie_test_passed:
        logger.error("Cookie test failed - session not preserved")
        return render(request, 'lti/launch_error.html', {
            'error': 'Cookie Compatibility Issue',
            'message': 'Browser is blocking cookies in iframe context.',
            'solutions': [
                'Enable cookies for this site in your browser settings',
                'Disable enhanced tracking protection',
                'Open the tool in a new tab using the link below'
            ],
            'new_tab_url': request.build_absolute_uri() + '?new_tab=1',
            'debug_info': {
                'session_key': request.session.session_key,
                'session_data': dict(request.session),
                'cookies': dict(request.COOKIES),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
            }
        })
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    try:
        message_launch = DjangoMessageLaunch(
            request,
            tool_conf,
            launch_data_storage=launch_data_storage
        )
        launch_data = message_launch.get_launch_data()
        logger.info("LTI Launch successful!")
        logger.info(f"User: {launch_data.get('name', 'Unknown')}")
        logger.info(f"Course: {launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('title', 'Unknown')}")
        # Store launch data in session for later use
        request.session['lti_launch_data'] = launch_data
        request.session['lti_authenticated'] = True
        request.session.save()
        # Redirect to main application
        return redirect('tool_selection')
    except Exception as e:
        logger.error(f"LTI Launch failed: {str(e)}", exc_info=True)
        return render(request, 'lti/launch_error.html', {
            'error': 'LTI Launch Failed',
            'message': str(e),
            'debug_info': {
                'session_key': request.session.session_key,
                'post_data': {k: v for k, v in request.POST.items() if 'token' not in k.lower()},
                'error_type': type(e).__name__
            }
        })

@xframe_options_exempt
def jwks(request):
    """Serve public key in JWKS format"""
    try:
        tool_conf = get_tool_conf()
        return JsonResponse(tool_conf.get_jwks(), safe=False)
    except Exception as e:
        logger.error(f"JWKS error: {str(e)}")
        return JsonResponse({'error': 'Unable to generate JWKS'}, status=500)

# Debug endpoints for troubleshooting
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
        'path': request.path,
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'referer': request.META.get('HTTP_REFERER', 'None'),
        'in_iframe': request.META.get('HTTP_SEC_FETCH_DEST') == 'iframe'
    }
    return JsonResponse(debug_data, indent=2)