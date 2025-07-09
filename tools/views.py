from django.shortcuts import render

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
