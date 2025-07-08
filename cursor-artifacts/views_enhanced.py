# lti/views.py - Enhanced with cookie/iframe handling

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@xframe_options_exempt  # Allow embedding in Canvas iframe
def login(request):
    """Enhanced OIDC login with cookie compatibility check"""
    
    # Check if this is a new tab request (fallback)
    if request.GET.get('new_tab'):
        # Skip iframe compatibility checks for new tab
        request.session['lti_new_tab'] = True
    
    # Test cookie compatibility first
    if not request.session.get('cookie_test_passed') and not request.GET.get('skip_test'):
        return redirect('lti_cookie_test')
    
    # Original OIDC login logic
    if request.method == 'GET':
        return HttpResponseRedirect('/tool_selection/')
    
    # POST logic for OIDC initiation
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
        
        # Enable cookie checks and add SameSite=None support
        redirect_response = oidc_login.enable_check_cookies().redirect(target_link_uri)
        
        # Ensure response cookies are iframe-compatible
        if hasattr(redirect_response, 'cookies'):
            for cookie in redirect_response.cookies.values():
                cookie['samesite'] = 'None'
                cookie['secure'] = True
        
        return redirect_response
        
    except Exception as e:
        logger.error(f"OIDC login failed: {e}")
        return render(request, 'lti/login_error.html', {
            'error': str(e),
            'new_tab_url': request.build_absolute_uri() + '?new_tab=1'
        })

@csrf_exempt
@xframe_options_exempt
def cookie_test(request):
    """Test cookie compatibility for iframe embedding"""
    
    if request.method == 'POST':
        # Mark cookie test as passed
        request.session['cookie_test_passed'] = True
        request.session['lti_iframe_compatible'] = True
        
        # Log successful test
        logger.info(f"Cookie test passed for {request.META.get('REMOTE_ADDR')}")
        
        # Return success response
        response = JsonResponse({'status': 'success', 'message': 'Cookies working'})
        response['X-Frame-Options'] = 'ALLOWALL'
        return response
    
    # GET request - show test page
    context = {
        'test_url': reverse('lti_cookie_test'),
        'skip_url': reverse('lti_login') + '?skip_test=1',
        'new_tab_url': reverse('lti_login') + '?new_tab=1'
    }
    
    response = render(request, 'lti/cookie_test.html', context)
    response['X-Frame-Options'] = 'ALLOWALL'
    return response

@csrf_exempt
@require_POST
@xframe_options_exempt
def enhanced_launch(request):
    """Enhanced LTI launch with cookie failure handling"""
    
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
        launch_data = message_launch.get_launch_data()
        
        # Enhanced cookie/session handling
        if not request.session.session_key:
            request.session.create()
        
        # Store launch data with iframe-safe methods
        request.session.update({
            'lti_launch_data': launch_data,
            'canvas_user_id': launch_data.get('sub'),
            'canvas_course_id': launch_data.get(
                'https://purl.imsglobal.org/spec/lti/claim/context', {}
            ).get('id'),
            'canvas_roles': launch_data.get(
                'https://purl.imsglobal.org/spec/lti/claim/roles', []
            ),
            'lti_session_active': True,
            'launch_timestamp': timezone.now().isoformat()
        })
        
        # Force session save
        request.session.save()
        
        # Check if session is working
        if not request.session.get('lti_session_active'):
            logger.warning("Session not working in iframe context")
            return handle_session_failure(request, launch_data)
        
        # Successful launch - redirect based on message type
        if message_launch.is_deep_link_launch():
            return redirect('lti_configure')
        elif message_launch.is_submission_review_launch():
            return redirect('lti_submission_review')
        else:
            response = redirect('/tool_selection/')
            
            # Ensure iframe-compatible headers
            response['X-Frame-Options'] = 'ALLOWALL'
            response['Content-Security-Policy'] = (
                "frame-ancestors 'self' https://*.instructure.com"
            )
            
            return response
        
    except LtiException as e:
        logger.error(f"LTI launch failed: {e}")
        return handle_launch_failure(request, str(e))
    except Exception as e:
        logger.error(f"Unexpected launch error: {e}")
        return handle_launch_failure(request, "Launch failed")

def handle_session_failure(request, launch_data):
    """Handle session failures in iframe context"""
    
    # Try alternative storage methods
    context = {
        'error_type': 'session_failure',
        'user_id': launch_data.get('sub'),
        'course_id': launch_data.get(
            'https://purl.imsglobal.org/spec/lti/claim/context', {}
        ).get('id'),
        'new_tab_url': request.build_absolute_uri() + '?new_tab=1',
        'browser_instructions': True
    }
    
    response = render(request, 'lti/session_failure.html', context)
    response['X-Frame-Options'] = 'ALLOWALL'
    return response

def handle_launch_failure(request, error_message):
    """Handle general launch failures"""
    
    context = {
        'error_message': error_message,
        'retry_url': request.build_absolute_uri(),
        'new_tab_url': request.build_absolute_uri() + '?new_tab=1',
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@canvasops.acu.edu')
    }
    
    response = render(request, 'lti/launch_error.html', context)
    response['X-Frame-Options'] = 'ALLOWALL'
    return response

@xframe_options_exempt
def tool_selection(request):
    """Enhanced tool selection with session validation"""
    
    # Check for valid LTI session
    if not request.session.get('lti_session_active'):
        return redirect('lti_cookie_test')
    
    # Check session age (refresh if too old)
    launch_timestamp = request.session.get('launch_timestamp')
    if launch_timestamp:
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        launch_time = datetime.fromisoformat(launch_timestamp.replace('Z', '+00:00'))
        if timezone.now() - launch_time > timedelta(hours=24):
            logger.info("LTI session expired, requiring re-launch")
            return redirect('lti_login')
    
    # Original tool selection logic
    context = {
        'canvas_user_id': request.session.get('canvas_user_id'),
        'canvas_course_id': request.session.get('canvas_course_id'),
        'canvas_roles': request.session.get('canvas_roles', []),
        'iframe_mode': not request.session.get('lti_new_tab', False),
        'session_id': request.session.session_key
    }
    
    response = render(request, 'lti/tool_selection.html', context)
    response['X-Frame-Options'] = 'ALLOWALL'
    return response

# Add these URL patterns to lti/urls.py
urlpatterns = [
    # ... existing patterns
    path('cookie-test/', cookie_test, name='lti_cookie_test'),
    path('login/', login, name='lti_login'),  # Enhanced version
    path('launch/', enhanced_launch, name='lti_launch'),  # Enhanced version
    # ... rest of patterns
]