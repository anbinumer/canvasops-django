from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .find_replace import LTIFindReplaceService
import ast

# Create your views here.

def tool_selection(request):
    # Handle missing LTI session gracefully
    context = {
        'canvas_user_id': request.session.get('canvas_user_id', 'Unknown'),
        'canvas_course_id': request.session.get('canvas_course_id', 'Unknown'),
        'canvas_roles': request.session.get('canvas_roles', []),
        'canvas_url': request.session.get('canvas_url', ''),
    }
    return render(request, 'tools/tool_selection.html', context)

@require_http_methods(["GET", "POST"])
def find_replace_tool(request):
    if request.method == "GET":
        return render(request, 'tools/find_replace.html', {
            'canvas_user_id': request.session.get('canvas_user_id'),
            'canvas_course_id': request.session.get('canvas_course_id'),
            'canvas_url': request.session.get('canvas_url'),
        })
    # POST: Process find/replace request
    return handle_find_replace_request(request)

def handle_find_replace_request(request):
    # Extract form data
    canvas_user_id = request.session.get('canvas_user_id')
    canvas_course_id = request.session.get('canvas_course_id')
    canvas_url = request.session.get('canvas_url')
    api_token = request.session.get('canvas_api_token')  # TODO: Implement LTI token exchange for real use

    # Fallback for testing: allow token in POST (remove in production)
    if not api_token:
        api_token = request.POST.get('api_token')

    content_type = request.POST.get('content_type', 'url')
    search_value = request.POST.get('search_value', '').strip()
    areas = request.POST.getlist('areas')
    scope = request.POST.get('scope', 'current')
    env = request.POST.get('env', 'beta')
    action = request.POST.get('action', 'preview')

    # For now, only support current course
    if scope != 'current':
        return render(request, 'tools/find_replace.html', {
            'error': 'Only current course scope is supported in this version.'
        })
    if not (canvas_url and api_token and canvas_course_id and search_value):
        return render(request, 'tools/find_replace.html', {
            'error': 'Missing required information (Canvas URL, API token, course, or search value).'
        })

    # Build url_mappings (for now, just replace search_value with itself as a demo)
    # In production, add a field for replacement value
    url_mappings = {search_value: request.POST.get('replace_value', search_value)}
    search_targets = [search_value]
    is_beta = (env == 'beta')
    preview_only = (action == 'preview')

    service = LTIFindReplaceService(canvas_url, api_token, url_mappings, is_beta=is_beta)
    try:
        findings = service.scan_content(canvas_course_id, areas, search_targets, preview_only=preview_only)
        results = {
            'summary': f"Found {len(findings)} matches.",
            'findings': findings
        }
        return render(request, 'tools/find_replace.html', {
            'results': results,
            'canvas_user_id': canvas_user_id,
            'canvas_course_id': canvas_course_id,
            'canvas_url': canvas_url,
        })
    except Exception as e:
        return render(request, 'tools/find_replace.html', {
            'error': f'Error during Find & Replace: {str(e)}'
        })
