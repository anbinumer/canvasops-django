from django.shortcuts import render

# Create your views here.

def tool_selection(request):
    return render(request, 'tools/tool_selection.html')
