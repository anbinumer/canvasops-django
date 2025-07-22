from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

@csrf_exempt
@xframe_options_exempt
def session_debug(request):
    """Debug endpoint to check session status"""
    debug_data = {
        'session_key': request.session.session_key,
        'session_data': dict(request.session),
        'cookies': dict(request.COOKIES),
        'method': request.method,
        'path': request.path,
        'session_exists': bool(request.session.session_key),
        'csrf_token': request.META.get('CSRF_COOKIE'),
    }
    
    # Force session creation if it doesn't exist
    if not request.session.session_key:
        request.session.create()
        debug_data['session_created'] = True
        debug_data['new_session_key'] = request.session.session_key
    
    # Set test cookie
    request.session['debug_test'] = True
    request.session.save()
    
    return JsonResponse(debug_data) 